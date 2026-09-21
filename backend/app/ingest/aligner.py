import os
import json
from datetime import datetime, timedelta
from typing import List
from app.schemas.contracts import TelemetryEvent
from app.ingest.downloader import NORMALIZED_DIR, ensure_directories
from app.ingest.scenarios import SCENARIO_REGISTRY


class TimelineAligner:
    @staticmethod
    def align_events(events: List[TelemetryEvent], start_time: datetime = None) -> List[TelemetryEvent]:
        """Aligns event timestamps relative to start_time while preserving original inter-arrival intervals."""
        if not events:
            return []

        start = start_time or datetime.utcnow()
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        first_original_ts = sorted_events[0].timestamp

        aligned = []
        for ev in sorted_events:
            offset = ev.timestamp - first_original_ts
            new_ts = start + offset
            ev_dict = ev.model_dump()
            ev_dict["timestamp"] = new_ts
            aligned.append(TelemetryEvent(**ev_dict))

        return aligned

    @classmethod
    def load_scenario_events(cls, scenario_id: str, realign_to_now: bool = True) -> List[TelemetryEvent]:
        """Loads normalized events for a scenario, optionally realigning timestamps to now."""
        ensure_directories()
        scenario = SCENARIO_REGISTRY.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        norm_path = os.path.join(NORMALIZED_DIR, scenario.normalized_filename)
        if not os.path.exists(norm_path):
            from app.ingest.normalizer import TelemetryNormalizer
            TelemetryNormalizer.normalize_scenario_file(scenario_id)

        events = []
        with open(norm_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(TelemetryEvent(**json.loads(line.strip())))

        if realign_to_now and events:
            return cls.align_events(events, datetime.utcnow())
        return events
