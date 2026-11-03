import pytest
import os
import json
from uuid import uuid4
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models
from app.ingest.normalizer import TelemetryNormalizer
from app.ingest.pipeline import EventIngestionPipeline
from app.models.telemetry import SecurityEvent
from app.schemas.contracts import CanonicalSecurityEvent

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


def test_normalizer_timestamp_variations():
    # 1. ISO format
    ts1 = TelemetryNormalizer.parse_timestamp("2026-09-01T14:30:00Z")
    assert ts1.year == 2026 and ts1.month == 9 and ts1.hour == 14

    # 2. CSE-CIC-IDS2018 format (dd/MM/yyyy HH:mm:ss)
    ts2 = TelemetryNormalizer.parse_timestamp("14/02/2018 08:31:00")
    assert ts2.year == 2018 and ts2.month == 2 and ts2.day == 14 and ts2.minute == 31

    # 3. Unix epoch in seconds
    ts3 = TelemetryNormalizer.parse_timestamp(1518597060)
    assert ts3.year == 2018

    # 4. Fallback on invalid string
    ts4 = TelemetryNormalizer.parse_timestamp("not-a-timestamp")
    assert isinstance(ts4, datetime)


def test_normalizer_ip_and_port_validation():
    # Valid IPs
    assert TelemetryNormalizer.normalize_ip("192.168.1.50") == "192.168.1.50"
    assert TelemetryNormalizer.normalize_ip("10.0.0.1:8080") == "10.0.0.1"
    assert TelemetryNormalizer.normalize_ip("  172.16.0.4  ") == "172.16.0.4"
    assert TelemetryNormalizer.normalize_ip("2001:db8::1") == "2001:db8::1"

    # Invalid IPs
    assert TelemetryNormalizer.normalize_ip("999.999.999.999") is None
    assert TelemetryNormalizer.normalize_ip("localhost") is None
    assert TelemetryNormalizer.normalize_ip(None) is None

    # Port validation
    assert TelemetryNormalizer.normalize_port(80) == 80
    assert TelemetryNormalizer.normalize_port("443") == 443
    assert TelemetryNormalizer.normalize_port(65535) == 65535
    assert TelemetryNormalizer.normalize_port(70000) is None
    assert TelemetryNormalizer.normalize_port(-5) is None
    assert TelemetryNormalizer.normalize_port("invalid") is None


def test_normalizer_protocol_mapping():
    assert TelemetryNormalizer.normalize_protocol(6) == "TCP"
    assert TelemetryNormalizer.normalize_protocol(17) == "UDP"
    assert TelemetryNormalizer.normalize_protocol(1) == "ICMP"
    assert TelemetryNormalizer.normalize_protocol("6") == "TCP"
    assert TelemetryNormalizer.normalize_protocol("udp") == "UDP"
    assert TelemetryNormalizer.normalize_protocol("https") == "HTTPS"


def test_normalizer_canonical_conversion_and_content_hash():
    raw_event = {
        "timestamp": "2026-09-01T10:00:23Z",
        "source": "sysmon",
        "event_type": "process_creation",
        "host": "WORKSTATION-04",
        "src_ip": "192.168.1.104",
        "dest_ip": "13.58.225.34",
        "source_port": "49152",
        "dest_port": "443",
        "protocol": "6",
        "command_line": "powershell.exe -enc SQBFAFgA...",
        "process_name": "powershell.exe",
    }

    event, rejection = TelemetryNormalizer.to_canonical_security_event(
        raw=raw_event,
        source_record_id="test#1",
    )
    assert rejection is None
    assert isinstance(event, CanonicalSecurityEvent)
    assert event.source_ip == "192.168.1.104"
    assert event.destination_ip == "13.58.225.34"
    assert event.source_port == 49152
    assert event.destination_port == 443
    assert event.protocol == "TCP"
    assert event.source_identifier == "WORKSTATION-04"
    assert len(event.content_hash) == 64  # SHA-256


def test_event_ingestion_pipeline_batch_persistence(tmp_path):
    # Create temporary JSONL file with multiple records
    records = [
        {
            "timestamp": "2026-09-01T10:00:00Z",
            "event_type": "auth_failure",
            "source": "winevent_auth",
            "host": "AUTH-SRV-01",
            "src_ip": "18.218.115.60",
            "dest_ip": "192.168.1.10",
            "dest_port": 22,
            "protocol": 6,
            "raw_log": {"EventID": 4625, "FailureReason": "Unknown user"},
        }
        for _ in range(15)
    ]
    test_file = str(tmp_path / "test_auth_events.jsonl")
    with open(test_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    db = TestSession()
    try:
        pipeline = EventIngestionPipeline(db, batch_size=5)
        stats = pipeline.ingest_file(test_file)

        assert stats.total_records == 15
        assert stats.inserted_count == 15
        assert stats.rejected_count == 0
        assert stats.throughput_eps > 0

        # Verify PostgreSQL / SQLite records persisted
        events_in_db = db.query(SecurityEvent).all()
        assert len(events_in_db) == 15
        assert events_in_db[0].source_ip == "18.218.115.60"
        assert events_in_db[0].protocol == "TCP"
        assert events_in_db[0].destination_port == 22
    finally:
        db.close()
