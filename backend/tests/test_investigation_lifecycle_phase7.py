import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # Ensure all 41 tables are registered
from app.investigation.contracts import (
    InvestigationCreatePayload,
    InvestigationTransitionPayload,
)
from app.investigation.state_machine import (
    InvestigationStateMachine,
    InvalidStateTransitionError,
)
from app.investigation.service import InvestigationService
from app.repositories.investigation_repo import OptimisticLockError
from app.models.investigation import Investigation, InvestigationEvent, InvestigationStateVersion
from app.models.correlation import IncidentCandidate
from app.models.evidence import Evidence, TimelineEvent, Hypothesis
from app.api.investigation_router import (
    create_investigation as api_create_investigation,
    promote_candidate_to_investigation as api_promote_candidate,
    list_investigations as api_list_investigations,
    get_investigation_details as api_get_details,
    transition_investigation as api_transition,
    pause_investigation as api_pause,
    resume_investigation as api_resume,
    cancel_investigation as api_cancel,
    get_timeline as api_get_timeline,
    get_investigation_events as api_get_events,
    get_investigation_snapshots as api_get_snapshots,
)


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for Phase 7 tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_investigation_state_machine_validations():
    """Verify state machine allows valid lifecycle progressions and strictly rejects invalid transitions."""
    sm = InvestigationStateMachine()

    # Valid transitions
    assert sm.can_transition("created", "queued")
    assert sm.can_transition("queued", "investigating")
    assert sm.can_transition("investigating", "awaiting_review")
    assert sm.can_transition("awaiting_review", "completed")
    assert sm.can_transition("completed", "closed")
    assert sm.can_transition("investigating", "paused")
    assert sm.can_transition("paused", "investigating")

    # Invalid transitions
    assert not sm.can_transition("closed", "investigating")
    assert not sm.can_transition("created", "completed")
    assert not sm.can_transition("cancelled", "queued")

    with pytest.raises(InvalidStateTransitionError):
        sm.validate_transition("closed", "queued")


def test_investigation_creation_and_snapshots(db_session):
    """Verify investigation creation initializes state version 1, records snapshot and audit event."""
    svc = InvestigationService()
    payload = InvestigationCreatePayload(
        title="APT29 Lateral Movement Investigation",
        current_goal="Assess scope of compromise on FINANCE-SRV-01",
    )

    inv = svc.create_investigation(payload, db=db_session)
    assert inv.investigation_id is not None
    assert inv.title == "APT29 Lateral Movement Investigation"
    assert inv.status == "created"
    assert inv.state_version == 1

    # Verify initial snapshot
    snapshots = db_session.query(InvestigationStateVersion).filter_by(investigation_id=inv.investigation_id).all()
    assert len(snapshots) == 1
    assert snapshots[0].version_number == 1

    # Verify audit event
    events = db_session.query(InvestigationEvent).filter_by(investigation_id=inv.investigation_id).all()
    assert len(events) == 1
    assert events[0].event_type == "investigation_created"


def test_investigation_promotion_from_candidate(db_session):
    """Verify IncidentCandidate can be promoted into an active Investigation."""
    svc = InvestigationService()

    cand = IncidentCandidate(
        id=uuid.uuid4(),
        title="Automated SQLi and Data Exfiltration",
        severity="high",
        confidence=0.85,
        status="open",
        candidate_metadata={
            "entity_identifiers": ["WEB-SRV-01", "203.0.113.5"],
            "event_count": 3,
        },
    )
    db_session.add(cand)
    db_session.commit()

    inv = svc.create_from_candidate(cand.id, db=db_session)
    assert inv.incident_candidate_id == cand.id
    assert inv.status == "investigating"
    assert cand.status == "promoted"

    # Verify candidate promotion event logged
    events = db_session.query(InvestigationEvent).filter_by(investigation_id=inv.investigation_id).all()
    assert any(e.event_type == "candidate_promoted" for e in events)


def test_investigation_lifecycle_transitions_and_optimistic_locking(db_session):
    """Verify lifecycle transitions increment version and optimistic locking prevents concurrent overwrites."""
    svc = InvestigationService()
    payload = InvestigationCreatePayload(title="Ransomware Outbreak Triage", initial_status="investigating")
    inv = svc.create_investigation(payload, db=db_session)

    # 1. Pause investigation (version 1 -> 2)
    inv_paused = svc.pause(inv.investigation_id, db=db_session, reason="Analyst shift change")
    assert inv_paused.status == "paused"
    assert inv_paused.state_version == 2

    # 2. Resume investigation (version 2 -> 3)
    inv_resumed = svc.resume(inv.investigation_id, db=db_session, reason="Shift handover complete")
    assert inv_resumed.status == "investigating"
    assert inv_resumed.state_version == 3

    # 3. Optimistic locking check: trying to transition with stale expected_version=1 must fail
    with pytest.raises(OptimisticLockError):
        svc.transition_status(
            inv.investigation_id,
            target_status="awaiting_review",
            db=db_session,
            expected_version=1,
        )

    # Transition with correct expected_version=3 succeeds
    inv_review = svc.transition_status(
        inv.investigation_id,
        target_status="awaiting_review",
        db=db_session,
        expected_version=3,
    )
    assert inv_review.status == "awaiting_review"
    assert inv_review.state_version == 4


def test_investigation_evidence_hypothesis_and_timeline(db_session):
    """Verify attaching evidence, formulating hypotheses, and timeline reconstruction."""
    svc = InvestigationService()
    payload = InvestigationCreatePayload(title="Credential Dumping Investigation", initial_status="investigating")
    inv = svc.create_investigation(payload, db=db_session)

    # Add Evidence
    ev = svc.add_evidence(
        investigation_id=inv.investigation_id,
        source_type="log",
        description="LSASS process memory read handle granted to unauthorized binary",
        entity_refs={"hosts": ["DC-01"], "processes": ["procdump.exe"]},
        db=db_session,
    )
    assert ev.evidence_id is not None

    # Add Hypothesis
    hyp = svc.add_hypothesis(
        investigation_id=inv.investigation_id,
        label="Adversary performing OS Credential Dumping via LSASS memory",
        confidence=0.88,
        mitre_technique_ids=["T1003.001"],
        db=db_session,
    )
    assert hyp.hypothesis_id is not None
    assert hyp.status == "active"

    # Add Timeline Event
    now = datetime.utcnow()
    svc.add_timeline_event(
        investigation_id=inv.investigation_id,
        summary="Execution of procdump against LSASS.exe",
        occurred_at=now,
        mitre_technique_id="T1003.001",
        evidence_id=ev.evidence_id,
        db=db_session,
    )

    timeline = svc.get_timeline(inv.investigation_id, db=db_session)
    assert len(timeline) == 1
    assert timeline[0].mitre_technique_id == "T1003.001"
    assert timeline[0].sequence_position == 1


def test_investigation_router_api_endpoints(db_session):
    """Verify investigation router endpoint functions return expected JSON payloads and handle errors."""
    payload = InvestigationCreatePayload(title="API Test Investigation")
    res_create = api_create_investigation(payload, db=db_session)
    assert res_create["status"] == "created"
    inv_id = uuid.UUID(res_create["investigation_id"])

    # List & Get
    res_list = api_list_investigations(db=db_session)
    assert len(res_list) >= 1
    res_get = api_get_details(inv_id, db=db_session)
    assert res_get["title"] == "API Test Investigation"

    # Transition to queued -> investigating
    api_transition(inv_id, InvestigationTransitionPayload(target_status="queued"), db=db_session)
    api_transition(inv_id, InvestigationTransitionPayload(target_status="investigating"), db=db_session)

    # Pause and Resume
    res_pause = api_pause(inv_id, db=db_session)
    assert res_pause["status"] == "paused"
    res_resume = api_resume(inv_id, db=db_session)
    assert res_resume["status"] == "resumed"

    # Snapshots & Events
    snapshots = api_get_snapshots(inv_id, db=db_session)
    assert len(snapshots) >= 3
    events = api_get_events(inv_id, db=db_session)
    assert len(events) >= 3
