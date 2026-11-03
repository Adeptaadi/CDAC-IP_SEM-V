import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.contracts import TelemetryEvent
from app.ingest.aligner import TimelineAligner
from app.ingest.scenarios import SCENARIO_REGISTRY
from app.database import SessionLocal
from app.repositories.dataset_repo import DatasetRepository


class ReplayState(str, Enum):
    IDLE = "IDLE"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class TelemetryReplayer:
    """Configurable streaming telemetry replay engine with batching and persistent session tracking (Phase 3)."""

    def __init__(self):
        self.current_scenario: Optional[str] = None
        self.session_id: Optional[uuid.UUID] = None
        self.state: ReplayState = ReplayState.IDLE
        self.speed: float = 1.0  # 1x, 5x, 10x, or inf (instant)
        self.batch_size: int = 50
        self.events: List[TelemetryEvent] = []
        self.current_index: int = 0
        self.dispatched_events: List[TelemetryEvent] = []
        self.records_rejected: int = 0
        self._task: Optional[asyncio.Task] = None
        self._event_callbacks: List[Callable[[TelemetryEvent], None]] = []

    def register_callback(self, callback: Callable[[TelemetryEvent], None]):
        """Registers a listener callback for dispatched events."""
        self._event_callbacks.append(callback)

    def load_scenario(
        self,
        scenario_id: str,
        speed: float = 1.0,
        batch_size: int = 50,
        db: Optional[Session] = None,
        dataset_id: Optional[uuid.UUID] = None,
    ):
        """Loads and aligns scenario events, initializing or syncing a ReplaySession."""
        if scenario_id not in SCENARIO_REGISTRY:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        self.current_scenario = scenario_id
        self.speed = max(0.1, speed)
        self.batch_size = max(1, batch_size)
        self.events = TimelineAligner.load_scenario_events(scenario_id, realign_to_now=True)
        self.current_index = 0
        self.dispatched_events = []
        self.records_rejected = 0
        self.state = ReplayState.IDLE

        # Create persistent session if database session and dataset_id provided
        if db and dataset_id:
            repo = DatasetRepository(db)
            session = repo.create_replay_session(
                dataset_id=dataset_id,
                speed=self.speed,
                configuration={
                    "scenario_id": scenario_id,
                    "batch_size": self.batch_size,
                    "total_events": len(self.events),
                },
            )
            db.commit()
            self.session_id = session.id
        else:
            self.session_id = uuid.uuid4()

    def step(self, count: int = 1) -> List[TelemetryEvent]:
        """Dispatches next N events incrementally (for interactive step debugging)."""
        dispatched: List[TelemetryEvent] = []
        while self.current_index < len(self.events) and len(dispatched) < count:
            evt = self.events[self.current_index]
            self.dispatched_events.append(evt)
            dispatched.append(evt)
            self.current_index += 1
            for cb in self._event_callbacks:
                cb(evt)

        if self.current_index >= len(self.events):
            self.state = ReplayState.COMPLETED
        else:
            self.state = ReplayState.PAUSED

        self._sync_db_progress()
        return dispatched

    def replay_all(self):
        """Synchronously replays all events instantly (for testing, batch jobs, and offline benchmarking)."""
        if not self.events:
            raise RuntimeError("No scenario loaded. Load scenario before starting.")
        self.state = ReplayState.PLAYING
        while self.current_index < len(self.events):
            evt = self.events[self.current_index]
            self.dispatched_events.append(evt)
            self.current_index += 1
            for cb in self._event_callbacks:
                cb(evt)

        self.state = ReplayState.COMPLETED
        self._sync_db_progress()

    async def start(self):
        """Starts asynchronous replay loop."""
        if not self.events:
            raise RuntimeError("No scenario loaded. Load scenario before starting.")

        if self.state == ReplayState.PLAYING:
            return

        self.state = ReplayState.PLAYING
        self._sync_db_progress()
        self._task = asyncio.create_task(self._run_loop())

    def pause(self):
        if self.state == ReplayState.PLAYING:
            self.state = ReplayState.PAUSED
            if self._task and not self._task.done():
                self._task.cancel()
            self._sync_db_progress()

    def cancel(self):
        self.state = ReplayState.CANCELLED
        if self._task and not self._task.done():
            self._task.cancel()
        self._sync_db_progress()

    def reset(self):
        if self._task and not self._task.done():
            self._task.cancel()
        self.current_index = 0
        self.dispatched_events = []
        self.records_rejected = 0
        self.state = ReplayState.IDLE
        self._sync_db_progress()

    async def _run_loop(self):
        try:
            while self.current_index < len(self.events) and self.state == ReplayState.PLAYING:
                current_event = self.events[self.current_index]
                self.dispatched_events.append(current_event)
                self.current_index += 1

                for cb in self._event_callbacks:
                    cb(current_event)

                # Delay calculation
                if self.current_index < len(self.events) and self.speed != float("inf"):
                    next_event = self.events[self.current_index]
                    delay_seconds = (next_event.timestamp - current_event.timestamp).total_seconds()
                    scaled_delay = max(0.01, delay_seconds / self.speed)
                    await asyncio.sleep(scaled_delay)
                elif self.speed == float("inf"):
                    await asyncio.sleep(0)

                # Periodically sync to database
                if self.current_index % self.batch_size == 0:
                    self._sync_db_progress()

            if self.current_index >= len(self.events):
                self.state = ReplayState.COMPLETED
                self._sync_db_progress()

        except asyncio.CancelledError:
            pass

    def _sync_db_progress(self):
        """Persists progress to database ReplaySession if valid session exists."""
        if not self.session_id:
            return
        try:
            db = SessionLocal()
            try:
                repo = DatasetRepository(db)
                repo.update_session_progress(
                    session_id=self.session_id,
                    records_read=self.current_index,
                    records_accepted=len(self.dispatched_events),
                    records_rejected=self.records_rejected,
                    status=self.state.value.lower(),
                )
                db.commit()
            finally:
                db.close()
        except Exception:
            pass

    def get_status(self) -> Dict[str, Any]:
        return {
            "session_id": str(self.session_id) if self.session_id else None,
            "scenario": self.current_scenario,
            "state": self.state.value,
            "speed": self.speed,
            "batch_size": self.batch_size,
            "total_events": len(self.events),
            "records_read": self.current_index,
            "dispatched_events_count": len(self.dispatched_events),
            "records_rejected": self.records_rejected,
            "progress_percent": round((self.current_index / max(1, len(self.events))) * 100, 1),
            "latest_event": self.dispatched_events[-1].model_dump() if self.dispatched_events else None,
        }


# Global singleton instance for API usage
replayer_instance = TelemetryReplayer()
