import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum
from app.schemas.contracts import TelemetryEvent
from app.ingest.aligner import TimelineAligner
from app.ingest.scenarios import SCENARIO_REGISTRY


class ReplayState(str, Enum):
    IDLE = "IDLE"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


class TelemetryReplayer:
    def __init__(self):
        self.current_scenario: Optional[str] = None
        self.state: ReplayState = ReplayState.IDLE
        self.speed: float = 1.0  # 1x, 5x, 10x, or instant
        self.events: List[TelemetryEvent] = []
        self.current_index: int = 0
        self.dispatched_events: List[TelemetryEvent] = []
        self._task: Optional[asyncio.Task] = None

    def load_scenario(self, scenario_id: str, speed: float = 1.0):
        if scenario_id not in SCENARIO_REGISTRY:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        self.current_scenario = scenario_id
        self.speed = max(0.1, speed)
        self.events = TimelineAligner.load_scenario_events(scenario_id, realign_to_now=True)
        self.current_index = 0
        self.dispatched_events = []
        self.state = ReplayState.IDLE

    async def start(self):
        if not self.events:
            raise RuntimeError("No scenario loaded. Load scenario before starting.")

        if self.state == ReplayState.PLAYING:
            return

        self.state = ReplayState.PLAYING
        self._task = asyncio.create_task(self._run_loop())

    def pause(self):
        if self.state == ReplayState.PLAYING:
            self.state = ReplayState.PAUSED
            if self._task and not self._task.done():
                self._task.cancel()

    def reset(self):
        self.pause()
        self.current_index = 0
        self.dispatched_events = []
        self.state = ReplayState.IDLE

    async def _run_loop(self):
        try:
            while self.current_index < len(self.events) and self.state == ReplayState.PLAYING:
                current_event = self.events[self.current_index]
                self.dispatched_events.append(current_event)
                self.current_index += 1

                # Calculate delay to next event
                if self.current_index < len(self.events) and self.speed != float("inf"):
                    next_event = self.events[self.current_index]
                    delay_seconds = (next_event.timestamp - current_event.timestamp).total_seconds()
                    scaled_delay = max(0.05, delay_seconds / self.speed)
                    await asyncio.sleep(scaled_delay)
                elif self.speed == float("inf"):
                    # Instant mode
                    await asyncio.sleep(0.001)

            if self.current_index >= len(self.events):
                self.state = ReplayState.COMPLETED

        except asyncio.CancelledError:
            pass

    def get_status(self) -> Dict[str, Any]:
        return {
            "scenario": self.current_scenario,
            "state": self.state.value,
            "speed": self.speed,
            "total_events": len(self.events),
            "dispatched_events_count": len(self.dispatched_events),
            "progress_percent": round((self.current_index / max(1, len(self.events))) * 100, 1),
            "latest_event": self.dispatched_events[-1].model_dump() if self.dispatched_events else None,
        }


# Global singleton instance for API usage
replayer_instance = TelemetryReplayer()
