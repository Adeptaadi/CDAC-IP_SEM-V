import os
import json
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.schemas.contracts import TelemetryEvent
from app.ingest.downloader import RAW_DIR, NORMALIZED_DIR, ensure_directories
from app.ingest.scenarios import SCENARIO_REGISTRY


class TelemetryNormalizer:
    @staticmethod
    def normalize_event(raw: Dict[str, Any]) -> TelemetryEvent:
        """Converts raw heterogeneous log/flow fields into standard TelemetryEvent schema."""
        event_id = uuid4()
        timestamp_str = raw.get("timestamp")
        if timestamp_str:
            try:
                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.utcnow()
        else:
            ts = datetime.utcnow()

        source = raw.get("source", "unknown")
        event_type = raw.get("event_type", "security_event")
        host = raw.get("host")
        user = raw.get("user")
        src_ip = raw.get("src_ip")
        dest_ip = raw.get("dest_ip")
        process_name = raw.get("process_name")
        command_line = raw.get("command_line")
        raw_log = raw.get("raw_log", {})

        return TelemetryEvent(
            event_id=event_id,
            timestamp=ts,
            source=source,
            event_type=event_type,
            host=host,
            user=user,
            src_ip=src_ip,
            dest_ip=dest_ip,
            process_name=process_name,
            command_line=command_line,
            raw_log=raw_log,
        )

    @classmethod
    def normalize_scenario_file(cls, scenario_id: str) -> str:
        """Normalizes a raw scenario file and saves output to normalized JSONL."""
        ensure_directories()
        scenario = SCENARIO_REGISTRY.get(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_id}")

        raw_path = os.path.join(RAW_DIR, scenario.raw_filename)
        if not os.path.exists(raw_path):
            from app.ingest.downloader import prepare_scenario
            prepare_scenario(scenario_id)

        with open(raw_path, "r", encoding="utf-8") as f:
            raw_events = json.load(f)

        normalized_events = [cls.normalize_event(ev) for ev in raw_events]

        norm_path = os.path.join(NORMALIZED_DIR, scenario.normalized_filename)
        with open(norm_path, "w", encoding="utf-8") as f:
            for ev in normalized_events:
                # write each event as a single JSON line
                f.write(ev.model_dump_json() + "\n")

        return norm_path
