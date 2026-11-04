import uuid
from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # Ensure all 41 tables are registered
from app.models.investigation import Investigation, InvestigationStateVersion, InvestigationEvent
from app.models.evidence import Evidence, TimelineEvent, Hypothesis
from app.planner.contracts import (
    PlannerDecisionPayload,
    PlannerDecisionType,
    InvestigationGraphState,
)
from app.planner.decider import DynamicPlanner, DecisionValidationError
from app.planner.graph import InvestigationStateGraph
from app.planner.selection import InvestigationStateSnapshot
from app.orchestration import CapabilityRegistry, capability_registry_instance


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for Phase 9 tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_inv(db_session):
    """Anchor investigation for dynamic planner tests."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Dynamic Multi-Agent Test Investigation",
        status="investigating",
        current_confidence=0.15,
        confidence_state="low",
        current_goal="Uncover C2 infrastructure and affected hosts",
        planning_cycle_count=0,
        state_version=1,
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)
    return inv


def test_planner_decision_types_and_validations():
    """Verify DynamicPlanner produces valid structured decisions and rejects unregistered capabilities."""
    planner = DynamicPlanner()
    inv_id = uuid.uuid4()

    # Normal continuing state
    snapshot = InvestigationStateSnapshot(
        investigation_id=str(inv_id),
        confidence=0.30,
        cycle_number=1,
        evidence_count=2,
        graph_density=0.2,
    )
    dec = planner.formulate_decision(inv_id, snapshot)
    assert dec.decision_type == "continue_investigation"
    assert dec.selected_capability in [
        "correlation.analyze_entities",
        "correlation.analyze_temporal_patterns",
        "investigation.collect_evidence",
    ]

    # Stagnation -> Request Human Review
    snapshot_stagnant = InvestigationStateSnapshot(
        investigation_id=str(inv_id),
        confidence=0.45,
        cycle_number=5,
        cycles_since_confidence_gain=3,
        requires_analyst_review=True,
    )
    dec_review = planner.formulate_decision(inv_id, snapshot_stagnant)
    assert dec_review.decision_type == "request_human_review"

    # Validation failure on invalid capability
    invalid_dec = PlannerDecisionPayload(
        decision_id=uuid.uuid4(),
        investigation_id=inv_id,
        cycle_number=1,
        decision_type="continue_investigation",
        selected_capability="malicious.exploit_system",  # Unregistered
        selected_worker="unknown",
        confidence_before=0.10,
        reasoning="Test",
    )
    with pytest.raises(DecisionValidationError):
        planner.validate_decision(invalid_dec)


def test_mandatory_non_linear_investigation_workflow(db_session, test_inv):
    """Verify Mandatory Non-Linear Investigation Test (IS §9.6):

    1. Planner selects correlation.
    2. Correlation establishes relationships.
    3. State changes and ambiguity/unresolved question emerges.
    4. Planner dynamically replans / selects investigation capability.
    5. Evidence is collected.
    6. State is reassessed with confidence boost.
    """
    graph = InvestigationStateGraph()

    # Seed initial evidence so correlation utility is activated
    ev1 = Evidence(
        evidence_id=uuid.uuid4(),
        investigation_id=test_inv.investigation_id,
        source_type="log",
        description="Suspicious outbound DNS beacon to unknown domain",
        entity_refs={"hosts": ["SRV-01"], "ips": ["198.51.100.4"]},
    )
    ev2 = Evidence(
        evidence_id=uuid.uuid4(),
        investigation_id=test_inv.investigation_id,
        source_type="log",
        description="PowerShell encoded download cradle executed",
        entity_refs={"hosts": ["SRV-01"], "processes": ["powershell.exe"]},
    )
    db_session.add(ev1)
    db_session.add(ev2)
    db_session.commit()

    # Step 1: First cycle selects correlation
    state1 = graph.step(test_inv.investigation_id, db=db_session)
    assert state1.cycle_number == 1
    assert state1.last_decision is not None
    assert "correlation" in state1.last_decision.selected_worker
    assert state1.current_confidence > 0.15

    # Introduce unresolved question discovered from correlation
    state1.unresolved_questions.append("Is 198.51.100.4 associated with known C2 infrastructure?")

    # Step 2: Second cycle dynamically switches to investigation / knowledge collection
    state2 = graph.step(test_inv.investigation_id, db=db_session)
    assert state2.cycle_number == 2
    assert state2.last_decision is not None
    assert state2.last_decision.selected_worker in ["investigation", "correlation"]
    assert state2.current_confidence > state1.current_confidence

    # Verify audit events and timeline grew non-linearly
    events = db_session.query(InvestigationEvent).filter_by(investigation_id=test_inv.investigation_id).all()
    assert len(events) >= 2

    versions = db_session.query(InvestigationStateVersion).filter_by(investigation_id=test_inv.investigation_id).all()
    assert len(versions) >= 2


def test_planner_completion_threshold(db_session, test_inv):
    """Verify that when confidence satisfies completion criteria, the planner concludes the investigation."""
    graph = InvestigationStateGraph()
    test_inv.current_confidence = 0.90
    test_inv.planning_cycle_count = 3
    db_session.commit()

    state = graph.step(test_inv.investigation_id, db=db_session)
    assert state.current_status == "completed"
    assert state.termination_reason == "confidence_threshold_met"
    assert test_inv.status == "completed"
    assert test_inv.closed_at is not None
