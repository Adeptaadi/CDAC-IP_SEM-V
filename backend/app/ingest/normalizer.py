import os
import json
import ipaddress
import hashlib
from uuid import uuid4, UUID
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from app.schemas.contracts import TelemetryEvent, CanonicalSecurityEvent, RejectedRecord
from app.ingest.downloader import RAW_DIR, NORMALIZED_DIR, ensure_directories
from app.ingest.scenarios import SCENARIO_REGISTRY


class TelemetryNormalizer:
    """Enterprise Normalization Engine for heterogeneous cybersecurity telemetry (Phase 4).

    Standardizes raw Sysmon, Windows Event Logs, and CSE-CIC-IDS2018 network flows
    into the canonical SecurityEvent schema.
    """

    PROTOCOL_NUMBER_MAP = {
        0: "HOPOPT",
        1: "ICMP",
        2: "IGMP",
        6: "TCP",
        17: "UDP",
        41: "IPv6",
        47: "GRE",
        50: "ESP",
        51: "AH",
        58: "IPv6-ICMP",
        89: "OSPF",
    }

    TIMESTAMP_FORMATS = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %I:%M:%S %p",
    ]

    @classmethod
    def parse_timestamp(cls, raw_val: Any) -> datetime:
        """Parses various timestamp representations (ISO, CSE-CIC format, unix epoch)."""
        if isinstance(raw_val, datetime):
            return raw_val

        if isinstance(raw_val, (int, float)):
            # Epoch timestamp (check if seconds or milliseconds)
            if raw_val > 1e11:
                return datetime.utcfromtimestamp(raw_val / 1000.0)
            return datetime.utcfromtimestamp(raw_val)

        if not raw_val or not isinstance(raw_val, str):
            return datetime.utcnow()

        cleaned = raw_val.strip()
        for fmt in cls.TIMESTAMP_FORMATS:
            try:
                return datetime.strptime(cleaned, fmt)
            except (ValueError, TypeError):
                continue

        try:
            return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()

    @staticmethod
    def normalize_ip(ip_val: Any) -> Optional[str]:
        """Normalizes and validates IPv4/IPv6 addresses, stripping whitespace and port suffixes."""
        if not ip_val or not isinstance(ip_val, str):
            return None

        clean_ip = ip_val.strip()
        # If IP:port pattern (e.g. 192.168.1.10:443), extract IP
        if ":" in clean_ip and "." in clean_ip:
            clean_ip = clean_ip.split(":")[0]

        try:
            parsed = ipaddress.ip_address(clean_ip)
            return str(parsed)
        except ValueError:
            return None

    @staticmethod
    def normalize_port(port_val: Any) -> Optional[int]:
        """Validates and converts port to integer within standard 1-65535 range."""
        if port_val is None or port_val == "":
            return None
        try:
            p = int(port_val)
            if 1 <= p <= 65535:
                return p
        except (ValueError, TypeError):
            pass
        return None

    @classmethod
    def normalize_protocol(cls, proto_val: Any) -> str:
        """Maps numeric protocol or raw string to canonical uppercase protocol name."""
        if proto_val is None or proto_val == "":
            return "TCP"

        if isinstance(proto_val, int):
            return cls.PROTOCOL_NUMBER_MAP.get(proto_val, str(proto_val))

        try:
            # Check if numeric string
            p_int = int(str(proto_val).strip())
            return cls.PROTOCOL_NUMBER_MAP.get(p_int, str(p_int))
        except ValueError:
            pass

        return str(proto_val).strip().upper()

    @staticmethod
    def compute_content_hash(
        event_type: str,
        timestamp: datetime,
        src_ip: Optional[str],
        dest_ip: Optional[str],
        src_port: Optional[int],
        dest_port: Optional[int],
        details: Dict[str, Any],
    ) -> str:
        """Computes deterministic SHA-256 hash for deduplication and provenance."""
        key = (
            f"{event_type}|{timestamp.isoformat()}|{src_ip or ''}|{dest_ip or ''}|"
            f"{src_port or ''}|{dest_port or ''}|{sorted(details.items())}"
        )
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @classmethod
    def to_canonical_security_event(
        cls,
        raw: Dict[str, Any],
        replay_session_id: Optional[UUID] = None,
        dataset_file_id: Optional[UUID] = None,
        source_record_id: Optional[str] = None,
    ) -> Tuple[Optional[CanonicalSecurityEvent], Optional[RejectedRecord]]:
        """Transforms a raw telemetry record into a CanonicalSecurityEvent with strict field validation."""
        # 1. Extract and validate timestamp
        raw_ts = (
            raw.get("timestamp")
            or raw.get("Timestamp")
            or raw.get("Time")
            or raw.get("@timestamp")
        )
        event_timestamp = cls.parse_timestamp(raw_ts)

        # 2. Extract Event Type
        event_type = (
            raw.get("event_type")
            or raw.get("Label")
            or raw.get("Action")
            or raw.get("EventName")
            or "security_event"
        )
        if isinstance(event_type, str):
            event_type = event_type.strip().lower().replace(" ", "_")

        # 3. Network Attributes
        raw_src_ip = raw.get("src_ip") or raw.get("Src IP") or raw.get("Source IP") or raw.get("source_ip")
        raw_dst_ip = raw.get("dest_ip") or raw.get("Dst IP") or raw.get("Destination IP") or raw.get("destination_ip")
        src_ip = cls.normalize_ip(raw_src_ip)
        dest_ip = cls.normalize_ip(raw_dst_ip)

        raw_src_port = raw.get("source_port") or raw.get("Src Port") or raw.get("Source Port")
        raw_dst_port = raw.get("dest_port") or raw.get("destination_port") or raw.get("Dst Port") or raw.get("Destination Port")
        source_port = cls.normalize_port(raw_src_port)
        dest_port = cls.normalize_port(raw_dst_port)

        raw_protocol = raw.get("protocol") or raw.get("Protocol") or "TCP"
        protocol = cls.normalize_protocol(raw_protocol)

        source_identifier = (
            raw.get("host")
            or raw.get("Host")
            or raw.get("ComputerName")
            or raw.get("source_identifier")
            or raw.get("source")
        )

        # 4. Context & Attributes
        normalized_data: Dict[str, Any] = {}
        for k, v in raw.items():
            if k not in [
                "src_ip", "dest_ip", "source_ip", "destination_ip",
                "source_port", "dest_port", "destination_port",
                "protocol", "timestamp", "Timestamp", "event_type"
            ]:
                normalized_data[k] = v

        # Calculate content hash
        content_hash = cls.compute_content_hash(
            event_type=event_type,
            timestamp=event_timestamp,
            src_ip=src_ip,
            dest_ip=dest_ip,
            src_port=source_port,
            dest_port=dest_port,
            details=normalized_data,
        )

        event = CanonicalSecurityEvent(
            id=uuid4(),
            replay_session_id=replay_session_id,
            dataset_file_id=dataset_file_id,
            source_record_id=source_record_id,
            event_type=event_type,
            event_timestamp=event_timestamp,
            ingestion_timestamp=datetime.utcnow(),
            source_ip=src_ip,
            destination_ip=dest_ip,
            source_port=source_port,
            destination_port=dest_port,
            protocol=protocol,
            source_identifier=str(source_identifier) if source_identifier else None,
            normalized_data=normalized_data,
            normalization_version="1.0.0",
            content_hash=content_hash,
        )

        return event, None

    @classmethod
    def normalize_event(cls, raw: Dict[str, Any]) -> TelemetryEvent:
        """Converts raw heterogeneous log/flow fields into standard TelemetryEvent schema (backward compatible)."""
        event_id = uuid4()
        timestamp_str = raw.get("timestamp") or raw.get("Timestamp")
        ts = cls.parse_timestamp(timestamp_str)

        source = raw.get("source", "unknown")
        event_type = raw.get("event_type", "security_event")
        host = raw.get("host") or raw.get("ComputerName")
        user = raw.get("user") or raw.get("UserName")
        src_ip = cls.normalize_ip(raw.get("src_ip") or raw.get("Src IP") or raw.get("Source IP"))
        dest_ip = cls.normalize_ip(raw.get("dest_ip") or raw.get("Dst IP") or raw.get("Destination IP"))
        process_name = raw.get("process_name") or raw.get("ProcessName")
        command_line = raw.get("command_line") or raw.get("CommandLine")
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
                f.write(ev.model_dump_json() + "\n")

        return norm_path
