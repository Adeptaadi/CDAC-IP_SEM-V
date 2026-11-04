import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # Ensure all 41 tables are registered
from app.correlation.entity_resolver import EntityResolver
from app.correlation.temporal import TemporalCorrelator
from app.correlation.graph import CorrelationGraphEngine
from app.correlation.scorer import CorrelationScorer
from app.correlation.engine import CorrelationEngine
from app.workers.correlation_worker import CorrelationWorker
from app.schemas.contracts import WorkerTask
from app.models.correlation import Entity, EntityRelationship, IncidentCandidate


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for Phase 6 tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_entity_resolver_normalization_and_persistence(db_session):
    """Verify EntityResolver properly normalizes and persists heterogeneous entity identifiers."""
    resolver = EntityResolver()

    # Host normalization
    h1 = resolver.resolve_entity("host", "workstation-01.corp.internal", db=db_session)
    assert h1 is not None
    assert h1.identifier == "WORKSTATION-01"
    assert h1.entity_type == "host"

    # User normalization
    u1 = resolver.resolve_entity("user", "CORP\\Administrator", db=db_session)
    assert u1 is not None
    assert u1.identifier == "administrator"
    assert u1.entity_type == "user"

    # IP normalization (strip port)
    ip1 = resolver.resolve_entity("ip", "192.168.1.100:8080", db=db_session)
    assert ip1 is not None
    assert ip1.identifier == "192.168.1.100"

    # Process normalization (extract basename)
    p1 = resolver.resolve_entity("process", "C:\\Windows\\System32\\cmd.exe", db=db_session)
    assert p1 is not None
    assert p1.identifier == "cmd.exe"

    # Verify database persistence
    db_entities = db_session.query(Entity).all()
    assert len(db_entities) == 4
    stored_ids = {e.identifier for e in db_entities}
    assert "WORKSTATION-01" in stored_ids
    assert "administrator" in stored_ids
    assert "192.168.1.100" in stored_ids
    assert "cmd.exe" in stored_ids


def test_temporal_correlator_sliding_window():
    """Verify temporal correlator partitions events into clusters based on time deltas."""
    correlator = TemporalCorrelator(default_window_seconds=300)
    base_time = datetime(2026, 11, 4, 12, 0, 0)

    events = [
        {"id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=10)).isoformat()},
        {"id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=50)).isoformat()},
        {"id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=90)).isoformat()},
        # Gap of 1000 seconds -> separate cluster
        {"id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=1100)).isoformat()},
        {"id": str(uuid.uuid4()), "timestamp": (base_time + timedelta(seconds=1150)).isoformat()},
    ]

    clusters = correlator.group_by_sliding_window(events)
    assert len(clusters) == 2
    assert len(clusters[0]) == 3
    assert len(clusters[1]) == 2


def test_correlation_graph_engine_and_relationships(db_session):
    """Verify graph engine extracts multi-entity edges and persists them with accurate graph metrics."""
    resolver = EntityResolver()
    graph_engine = CorrelationGraphEngine(resolver=resolver)

    event = {
        "id": str(uuid.uuid4()),
        "host": "SERVER-APP-02",
        "user": "DOMAIN\\svc_backup",
        "process_name": "backup.exe",
        "src_ip": "10.0.1.50",
        "dest_ip": "10.0.2.100",
        "timestamp": datetime.utcnow().isoformat(),
    }

    resolved = resolver.extract_and_resolve_from_event(event, db=db_session)
    assert len(resolved) == 5  # Host, User, Process, Src_IP, Dest_IP

    relationships = graph_engine.build_relationships_for_event(event, resolved, db=db_session)
    assert len(relationships) >= 4

    rel_types = {r.relationship_type for r in relationships}
    assert "authenticated_as" in rel_types
    assert "executed" in rel_types
    assert "communicates_with" in rel_types
    assert "network_flow" in rel_types

    metrics = graph_engine.compute_graph_metrics(resolved, relationships)
    assert metrics["node_count"] == 5
    assert metrics["edge_count"] >= 4
    assert metrics["graph_density"] > 0.0

    # Check database persistence
    db_rels = db_session.query(EntityRelationship).all()
    assert len(db_rels) == len(relationships)


def test_correlation_scorer_formula():
    """Verify composite correlation scoring C = wt*T + we*E + ws*S adheres to boundary conditions."""
    scorer = CorrelationScorer(weight_temporal=0.35, weight_entity=0.40, weight_severity=0.25)
    now = datetime.utcnow()

    # Tight temporal cluster with high entity diversity and critical severity
    dummy_entities = [
        Entity(id=uuid.uuid4(), entity_type="host", identifier="SRV-01"),
        Entity(id=uuid.uuid4(), entity_type="user", identifier="admin"),
        Entity(id=uuid.uuid4(), entity_type="ip", identifier="10.0.0.1"),
        Entity(id=uuid.uuid4(), entity_type="process", identifier="powershell.exe"),
    ]

    score_high = scorer.compute_composite_score(
        start_time=now,
        end_time=now + timedelta(seconds=30),
        entities=dummy_entities,
        event_count=3,
        severities=["critical", "high"],
        confidences=[0.90, 0.85],
    )
    assert 0.70 <= score_high <= 1.0

    # Sparse events with low severity
    score_low = scorer.compute_composite_score(
        start_time=now,
        end_time=now + timedelta(seconds=3500),
        entities=[dummy_entities[0]],
        event_count=1,
        severities=["low"],
        confidences=[0.30],
    )
    assert score_low < score_high


def test_correlation_engine_incident_candidate_generation(db_session):
    """Verify end-to-end CorrelationEngine correlates related telemetry and elevates them to IncidentCandidates."""
    engine = CorrelationEngine(min_candidate_score=0.50)
    now = datetime.utcnow()

    correlated_events = [
        {
            "id": str(uuid.uuid4()),
            "host": "FINANCE-PC-12",
            "user": "CORP\\alice",
            "process_name": "cmd.exe",
            "severity": "high",
            "confidence": 0.88,
            "mitre_tactics": ["Execution"],
            "mitre_techniques": ["T1059.003"],
            "timestamp": now.isoformat(),
        },
        {
            "id": str(uuid.uuid4()),
            "host": "FINANCE-PC-12",
            "user": "CORP\\alice",
            "process_name": "powershell.exe",
            "src_ip": "10.0.5.12",
            "dest_ip": "185.220.101.5",
            "severity": "critical",
            "confidence": 0.92,
            "mitre_tactics": ["Command and Control"],
            "mitre_techniques": ["T1071"],
            "timestamp": (now + timedelta(seconds=45)).isoformat(),
        },
    ]

    candidates = engine.correlate(correlated_events, db=db_session)
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.severity == "critical"
    assert cand.confidence >= 0.60
    assert cand.status == "open"
    assert "FINANCE-PC-12" in cand.title
    assert cand.candidate_metadata["event_count"] == 2
    assert "Command and Control" in cand.candidate_metadata["mitre_tactics"]
    assert "T1071" in cand.candidate_metadata["mitre_techniques"]

    # Verify database persistence
    persisted = db_session.query(IncidentCandidate).filter_by(id=cand.id).first()
    assert persisted is not None
    assert persisted.title == cand.title


def test_correlation_worker_with_telemetry_events():
    """Verify CorrelationWorker extracts entities, establishes graph topology, and populates WorkerResult."""
    worker = CorrelationWorker()
    task = WorkerTask(
        task_id=uuid.uuid4(),
        investigation_id=uuid.uuid4(),
        worker_type="correlation",
        objective="Correlate host and network telemetry for lateral movement",
        events=[
            {
                "event_id": str(uuid.uuid4()),
                "host": "DOMAIN-CTRL-01",
                "user": "corp\\adm_bob",
                "process_name": "lsass.exe",
                "src_ip": "10.0.0.10",
                "dest_ip": "10.0.0.25",
            }
        ],
    )

    result = worker.execute(task)
    assert result.status == "success"
    assert len(result.findings) >= 1
    assert result.confidence_signal >= 0.50
    finding = result.findings[0]
    assert "DOMAIN-CTRL-01" in finding.entity_refs.get("hosts", [])
    assert "adm_bob" in finding.entity_refs.get("users", [])
    assert "lsass.exe" in finding.entity_refs.get("processes", [])
