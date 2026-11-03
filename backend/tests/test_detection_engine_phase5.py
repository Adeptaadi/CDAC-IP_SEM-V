import uuid
from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # Ensure all 41 tables are registered
from app.detection.rules import RuleEngine, rule_engine_instance
from app.detection.ml import MLDetectionEngine, FlowFeatureExtractor
from app.detection.engine import HybridDetectionEngine
from app.detection.alerts import AlertGenerator
from app.workers.detection_worker import DetectionWorker
from app.schemas.contracts import WorkerTask


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for Phase 5 tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_rule_engine_matching():
    """Verify rule engine successfully identifies known malicious patterns and preserves MITRE tactics."""
    re = RuleEngine()
    ev_powershell = {
        "event_id": str(uuid.uuid4()),
        "event_type": "process_creation",
        "command_line": "powershell.exe -NoP -w hidden -enc JABzACAAPQAgAE4AZQB3AC0ATwBiAGo...",
        "process_name": "powershell.exe",
        "host": "WS-FINANCE-01",
        "user": "DOMAIN\\johndoe",
        "timestamp": datetime.utcnow().isoformat(),
    }
    findings = re.evaluate_event(ev_powershell)
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_key == "RULE_POWERSHELL_OBFUSCATION"
    assert f.severity == "high"
    assert f.confidence >= 0.85
    assert "Execution" in f.mitre_tactics
    assert "T1059.001" in f.mitre_techniques
    assert "WS-FINANCE-01" in f.entity_refs.get("hosts", [])


def test_ml_detection_engine_flow_anomaly_and_leakage_safety():
    """Verify flow feature extraction, leakage protection, and statistical anomaly detection."""
    ml_engine = MLDetectionEngine()

    # Normal baseline traffic
    normal_flow = {
        "event_id": str(uuid.uuid4()),
        "src_ip": "192.168.1.105",
        "dest_ip": "8.8.8.8",
        "dest_port": 53,
        "protocol": 17,
        "raw_log": {
            "Total Fwd Packets": 2,
            "Total Backward Packets": 2,
            "Flow Bytes/s": 300,
            "Flow Packets/s": 4,
            "Flow Duration": 1000,
            "Label": "BENIGN",  # Ground-truth label must be ignored during inference
        },
    }
    f_normal = ml_engine.evaluate_event(normal_flow)
    assert f_normal is None

    # Massive volumetric DoS flood traffic
    flood_flow = {
        "event_id": str(uuid.uuid4()),
        "src_ip": "10.0.0.99",
        "dest_ip": "192.168.1.1",
        "dest_port": 80,
        "protocol": 6,
        "raw_log": {
            "Total Fwd Packets": 50000,
            "Total Backward Packets": 10,
            "Flow Bytes/s": 45000000,
            "Flow Packets/s": 120000,
            "Flow Duration": 1000000,
            "Label": "DDoS",
        },
    }
    f_flood = ml_engine.evaluate_event(flood_flow)
    assert f_flood is not None
    assert f_flood.detection_method == "ml"
    assert f_flood.confidence >= 0.85
    assert f_flood.severity in ["high", "critical"]
    assert "T1498" in f_flood.mitre_techniques


def test_hybrid_detection_engine_corroboration():
    """Verify that events matching both rule-based heuristics and ML flow anomalies produce corroborated findings."""
    hybrid = HybridDetectionEngine()

    # Event matching Botnet C2 rule AND displaying high flow anomaly rates
    c2_event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "c2_beacon",
        "process_name": "ares.exe",
        "src_ip": "192.168.1.50",
        "dest_ip": "198.51.100.23",
        "dest_port": 4444,
        "raw_log": {
            "Total Fwd Packets": 40000,
            "Flow Packets/s": 80000,
            "Flow Bytes/s": 25000000,
        },
    }

    findings = hybrid.analyze_event(c2_event)
    assert len(findings) == 1
    f = findings[0]
    assert f.detection_method == "hybrid"
    assert "Corroborated by ML Flow Anomaly" in f.predicted_class
    assert f.details["fusion_boost"] == 0.05
    assert f.confidence > 0.80


def test_alert_generator_and_incident_candidate(db_session):
    """Verify alert generation elevates actionable high-severity findings into persistent IncidentCandidate records."""
    ag = AlertGenerator(min_confidence=0.70)
    re = RuleEngine()

    sqli_event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "web_request",
        "raw_log": {"uri": "/login.php?user=admin'%20OR%201=1--"},
        "src_ip": "203.0.113.42",
        "dest_ip": "192.168.1.200",
    }

    rule_findings = re.evaluate_event(sqli_event)
    assert len(rule_findings) == 1
    finding = rule_findings[0]

    candidate = ag.create_candidate_from_finding(finding, db=db_session)
    assert candidate is not None
    assert candidate.severity == "high"
    assert "SQL" in candidate.title
    assert candidate.status == "open"
    assert candidate.candidate_metadata["detection_method"] == "rule"
    assert candidate.candidate_metadata["rule_key"] == "RULE_WEB_SQLI"

    # Query from database to verify persistence
    from app.models.correlation import IncidentCandidate
    persisted = db_session.query(IncidentCandidate).filter_by(id=candidate.id).first()
    assert persisted is not None
    assert persisted.title == candidate.title


def test_detection_worker_with_hybrid_engine():
    """Verify DetectionWorker integrates HybridDetectionEngine while satisfying WorkerResult contracts."""
    worker = DetectionWorker()
    task = WorkerTask(
        task_id=uuid.uuid4(),
        investigation_id=uuid.uuid4(),
        worker_type="detection",
        objective="Triage anomalous host and network telemetry",
        events=[
            {
                "event_id": str(uuid.uuid4()),
                "event_type": "process_creation",
                "process_name": "powershell.exe",
                "command_line": "powershell -nop -enc RwBlAHQALQBQAHIAbwBjAGUAcwBzAA==",
                "host": "SERVER-SQL-01",
                "user": "SYSTEM",
            }
        ],
    )

    result = worker.execute(task)
    assert result.status == "success"
    assert len(result.findings) >= 1
    assert result.confidence_signal >= 0.85
    assert any("powershell" in f.description.lower() for f in result.findings)
