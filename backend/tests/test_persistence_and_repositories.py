import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models
from app.repositories import (
    InvestigationRepository,
    OptimisticLockError,
    SecurityEventRepository,
    DatasetRepository,
    TaskRepository,
    EvidenceRepository,
)

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


def test_investigation_repository_lifecycle_and_optimistic_locking():
    db = TestSession()
    try:
        repo = InvestigationRepository(db)
        inv = repo.create_investigation(
            title="Suspicious Lateral Movement via WMI",
            current_goal="Identify source IP and compromised account",
        )
        db.commit()

        assert inv.investigation_id is not None
        assert inv.state_version == 1
        assert inv.status == "active"
        assert len(inv.state_versions) == 1
        assert inv.state_versions[0].version_number == 1

        # Advance state with matching version
        updated = repo.update_state_optimistic(
            investigation_id=inv.investigation_id,
            expected_version=1,
            confidence=0.45,
            confidence_state="low",
            cycle_number=1,
            current_goal="Inspect parent-child process tree",
        )
        db.commit()

        assert updated.state_version == 2
        assert float(updated.current_confidence) == 0.45
        assert len(updated.state_versions) == 2
        assert len(updated.investigation_events) == 1

        # Attempt concurrent update with stale expected version -> Must raise OptimisticLockError
        with pytest.raises(OptimisticLockError):
            repo.update_state_optimistic(
                investigation_id=inv.investigation_id,
                expected_version=1,  # Stale version! (Current is 2)
                confidence=0.85,
                confidence_state="high",
                cycle_number=2,
            )

        # Update with correct expected_version=2 succeeds
        completed = repo.update_state_optimistic(
            investigation_id=inv.investigation_id,
            expected_version=2,
            confidence=0.92,
            confidence_state="very_high",
            cycle_number=2,
            status="completed",
        )
        db.commit()

        assert completed.state_version == 3
        assert completed.status == "completed"
        assert completed.closed_at is not None
        assert len(completed.state_versions) == 3
    finally:
        db.close()


def test_security_event_repository_bulk_and_query():
    db = TestSession()
    try:
        repo = SecurityEventRepository(db)
        base_time = datetime(2026, 11, 3, 12, 0, 0)

        events_data = [
            {
                "id": str(uuid4()),
                "event_type": "network_flow",
                "event_timestamp": base_time + timedelta(seconds=i * 10),
                "ingestion_timestamp": datetime.utcnow(),
                "source_ip": "192.168.1.50",
                "destination_ip": "10.0.0.1",
                "source_port": 50000 + i,
                "destination_port": 443,
                "protocol": "TCP",
                "normalized_data": {"bytes_sent": 1024 * i},
                "normalization_version": "1.0.0",
            }
            for i in range(10)
        ]

        inserted_count = repo.bulk_insert_events(events_data)
        db.commit()
        assert inserted_count == 10

        # Query events by time range
        query_res = repo.query_events_by_timerange(
            start_time=base_time,
            end_time=base_time + timedelta(seconds=50),
            source_ip="192.168.1.50",
        )
        assert len(query_res) == 6
    finally:
        db.close()


def test_dataset_repository_and_ground_truth_isolation():
    db = TestSession()
    try:
        repo = DatasetRepository(db)
        ds = repo.register_dataset(
            name="CSE-CIC-IDS2018 Infiltration",
            dataset_type="network_flow",
            description="Reconstructed multi-stage infiltration dataset",
        )
        db.commit()

        df = repo.add_dataset_file(
            dataset_id=ds.id,
            filename="Thurs-01-03-2018_Infiltration.csv",
            storage_uri="/datasets/raw/Thurs-01-03-2018_Infiltration.csv",
            file_format="csv",
            record_count=100000,
        )
        db.commit()

        session = repo.create_replay_session(dataset_id=ds.id, speed=2.0)
        db.commit()

        updated_session = repo.update_session_progress(
            session_id=session.id,
            records_read=500,
            records_accepted=480,
            records_rejected=20,
            status="running",
        )
        db.commit()
        assert updated_session.records_accepted == 480
        assert updated_session.started_at is not None

        # Verify ground-truth label registration is isolated per dataset file
        gt = repo.add_ground_truth_label(
            dataset_file_id=df.id,
            source_record_id="row-4521",
            label="Infiltration - Attempted Portscan",
            evaluation_split="benchmark",
        )
        db.commit()
        assert gt.id is not None
        assert gt.label == "Infiltration - Attempted Portscan"
    finally:
        db.close()


def test_task_repository_dependencies_and_attempts():
    db = TestSession()
    try:
        inv_repo = InvestigationRepository(db)
        inv = inv_repo.create_investigation(title="Botnet C2 Beaconing Investigation")
        db.commit()

        task_repo = TaskRepository(db)
        task1 = task_repo.create_task(
            investigation_id=inv.investigation_id,
            worker_type="detection",
            objective="Detect beaconing patterns in outbound HTTP telemetry",
        )
        db.commit()

        # Task 2 depends on Task 1
        task2 = task_repo.create_task(
            investigation_id=inv.investigation_id,
            worker_type="investigation",
            objective="Map beaconing to known MITRE C2 techniques",
            depends_on=[task1.id],
        )
        db.commit()

        # Record attempts on Task 1
        attempt1 = task_repo.record_attempt(task1.id, status="error", error_message="Timeout")
        assert attempt1.attempt_number == 1

        attempt2 = task_repo.record_attempt(task1.id, status="success", latency_ms=450)
        assert attempt2.attempt_number == 2
        db.commit()

        # Complete Task 1
        completed_task = task_repo.complete_task(
            task_id=task1.id,
            output_payload={"findings": ["T1071.001 detected"]},
        )
        db.commit()
        assert completed_task.status == "completed"
        assert completed_task.completed_at is not None
    finally:
        db.close()


def test_evidence_and_hypothesis_provenance():
    db = TestSession()
    try:
        inv_repo = InvestigationRepository(db)
        inv = inv_repo.create_investigation(title="Credential Access Brute Force")
        db.commit()

        ev_repo = EvidenceRepository(db)
        evidence = ev_repo.add_evidence(
            investigation_id=inv.investigation_id,
            source_type="log",
            description="Failed authentication threshold exceeded on SSH port 22",
            entity_refs={"hosts": ["SRV-AUTH-01"], "ips": ["192.168.1.100"]},
            produced_by_worker="detection",
        )

        timeline = ev_repo.add_timeline_event(
            investigation_id=inv.investigation_id,
            evidence_id=evidence.evidence_id,
            event_summary="50 failed login attempts within 60 seconds",
            mitre_technique_id="T1110.001",
        )

        hypo = ev_repo.upsert_hypothesis(
            investigation_id=inv.investigation_id,
            label="Automated Password Spraying against SSH service",
            confidence=0.88,
            status="strengthened",
            mitre_technique_ids=["T1110.001"],
        )

        link = ev_repo.link_hypothesis_evidence(
            hypothesis_id=hypo.hypothesis_id,
            evidence_id=evidence.evidence_id,
            stance="supports",
            weight=1.0,
        )
        db.commit()

        assert link.stance == "supports"
        assert timeline.mitre_technique_id == "T1110.001"
    finally:
        db.close()
