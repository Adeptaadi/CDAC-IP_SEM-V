"""Project Sentinel — Phase B1: Independent Behavioral Acceptance Test Suite.

Independently validates that Phase B0 remediations represent genuine behavioral
correctness rather than tailored regression passes.

Claims validated:
  Claim A: Duplicate evidence does not increase analytical information.
  Claim B: Duplicate or zero-yield execution produces zero artificial confidence growth.
  Claim C: Novel evidence legitimately increases confidence.
  Claim D: Repeated worker selection is penalized when it produces no new information.
  Claim E: Legitimate capability revisits remain possible after an intervening capability.
  Claim F: Stagnation is based on meaningful progress rather than arbitrary confidence drift.
  Claim G: A real stagnation condition creates a persisted replanning event.
  Claim H: Replanning actually changes the subsequent decision or strategy.
  Claim I: max_cycles is reported as a safety bound and not as successful convergence.
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Investigation, Evidence, Hypothesis, PlannerDecision, WorkerExecution, TimelineEvent
from app.models.evidence import compute_evidence_fingerprint
from app.planner.engine import PlannerEngine
from app.planner.selection import InvestigationStateSnapshot, select_worker, should_terminate
from app.planner.confidence import ConfidenceEngine
from app.schemas.contracts import WorkerTask, WorkerResult, Finding
from app.workers.base import BaseWorker
from app.config import settings


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for B1 validation testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_claim_a_duplicate_evidence_does_not_inflate_information(db_session):
    """Claim A: Duplicate evidence does not increase analytical information."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Test Investigation Claim A",
        status="investigating",
        current_confidence=0.20,
        planning_cycle_count=0,
    )
    db_session.add(inv)
    db_session.commit()

    engine = PlannerEngine()

    # Pre-insert one novel finding
    f_desc = "Suspicious outbound beacon to 198.51.100.22"
    f_ents = {"ips": ["198.51.100.22"]}
    f_hash = compute_evidence_fingerprint(f_desc, f_ents)

    ev1 = Evidence(
        investigation_id=inv.investigation_id,
        source_type="worker_output",
        description=f_desc,
        content_hash=f_hash,
        is_duplicate=False,
        is_novel=True,
        observation_count=1,
        entity_refs=f_ents,
        produced_by_worker="investigation",
    )
    db_session.add(ev1)
    db_session.commit()

    snap1 = engine.load_state_snapshot(inv, db_session)
    assert snap1.novel_evidence_count == 1
    assert snap1.duplicate_evidence_count == 0
    assert snap1.graph_density == pytest.approx(0.2)

    # Insert identical duplicate evidence from same worker
    ev2 = Evidence(
        investigation_id=inv.investigation_id,
        source_type="worker_output",
        description=f_desc,
        content_hash=f_hash,
        is_duplicate=True,
        is_novel=False,
        observation_count=1,
        entity_refs=f_ents,
        produced_by_worker="investigation",
    )
    db_session.add(ev2)
    db_session.commit()

    snap2 = engine.load_state_snapshot(inv, db_session)
    assert snap2.novel_evidence_count == 1, "Duplicate evidence must not increase novel evidence count"
    assert snap2.duplicate_evidence_count == 1, "Duplicate evidence must be identified as duplicate"
    assert snap2.graph_density == pytest.approx(0.2), "Graph density must be computed from novel evidence only"


def test_claim_b_zero_yield_produces_zero_confidence_growth():
    """Claim B: Duplicate or zero-yield execution produces zero artificial confidence growth."""
    conf_engine = ConfidenceEngine()

    # Worker output with zero novel evidence
    res = WorkerResult(
        task_id=uuid.uuid4(),
        worker_type="investigation",
        status="success",
        findings=[],
        confidence_signal=0.5,
        new_evidence=[],
        hypothesis_updates=[],
        reasoning_summary="No additional indicators uncovered.",
    )

    factors = conf_engine.compute_factors(
        worker_result=res,
        evidence_count_this_cycle=0,
        novel_evidence_count=0,
        duplicate_evidence_count=3,
        distinct_sources=1,
        total_evidence=3,
        corroborated=False,
        edges_added=0,
        nodes_in_graph=3,
        has_novel_knowledge=False,
        historical_sim_score=0.0,
    )

    delta = conf_engine.compute_delta(factors)
    assert delta == 0.0, f"Expected delta 0.0 on zero-yield cycle, got {delta}"

    init_conf = 0.3500
    updated_conf = conf_engine.update(current_confidence=init_conf, delta=delta)
    assert round(updated_conf, 4) == init_conf, "Confidence must not drift without novel findings"


def test_claim_c_novel_evidence_increases_confidence():
    """Claim C: Novel evidence legitimately increases confidence."""
    conf_engine = ConfidenceEngine()

    res = WorkerResult(
        task_id=uuid.uuid4(),
        worker_type="investigation",
        status="success",
        findings=[
            Finding(
                description="PowerShell encoded command execution detected",
                entity_refs={"hosts": ["SRV-01"]},
                mitre_technique_id="T1059.001",
            )
        ],
        confidence_signal=0.85,
        new_evidence=[
            Finding(
                description="PowerShell encoded command execution detected",
                entity_refs={"hosts": ["SRV-01"]},
                mitre_technique_id="T1059.001",
            )
        ],
        hypothesis_updates=[{"label": "PowerShell Attack", "confidence": 0.85}],
        reasoning_summary="Corroborated execution of obfuscated command line.",
    )

    factors = conf_engine.compute_factors(
        worker_result=res,
        evidence_count_this_cycle=1,
        novel_evidence_count=1,
        duplicate_evidence_count=0,
        distinct_sources=2,
        total_evidence=1,
        corroborated=True,
        edges_added=1,
        nodes_in_graph=2,
        has_novel_knowledge=True,
        knowledge_similarities=[0.80],
        historical_sim_score=0.75,
    )

    delta = conf_engine.compute_delta(factors)
    assert delta > 0.0, f"Expected positive delta on novel validated evidence, got {delta}"

    init_conf = 0.2000
    updated_conf = conf_engine.update(current_confidence=init_conf, delta=delta)
    assert updated_conf > init_conf, "Confidence must legitimately increase when novel evidence arrives"


def test_claim_d_repeated_worker_selection_penalized():
    """Claim D: Repeated worker selection is penalized when it produces no new information."""
    # When a worker has been executed consecutively, utility drops exponentially (0.25^k)
    state_0 = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.40,
        cycle_number=1,
        evidence_count=2,
        novel_evidence_count=2,
        duplicate_evidence_count=0,
        last_worker=None,
        consecutive_worker_count=0,
    )
    w_0, u_0, scores_0 = select_worker(state_0)

    # Assume correlation is selected, and in next cycle it has consecutive_worker_count=1
    state_1 = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.40,
        cycle_number=2,
        evidence_count=2,
        novel_evidence_count=2,
        duplicate_evidence_count=0,
        last_worker="correlation",
        consecutive_worker_count=1,
    )
    w_1, u_1, scores_1 = select_worker(state_1)

    assert scores_1["correlation"] == pytest.approx(scores_0["correlation"] * 0.25), (
        "Repeated worker must suffer 0.25x penalty on consecutive invocation"
    )
    assert w_1 != "correlation", "Penalized worker should yield precedence to alternative worker"


def test_claim_e_legitimate_capability_revisit_possible():
    """Claim E: Legitimate capability revisits remain possible after an intervening capability."""
    # Sequence: correlation was executed in cycle 1, then investigation executed in cycle 2.
    # In cycle 3, correlation is considered again. Since last_worker == 'investigation', penalty is 1.0 (cleared).
    state = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.45,
        cycle_number=3,
        evidence_count=4,
        novel_evidence_count=4,
        graph_density=0.1,  # low density -> high utility for correlation
        last_worker="investigation",
        consecutive_worker_count=1,
        worker_history=["correlation", "investigation"],
    )
    w, u, scores, adjs, rationale = select_worker(state, return_details=True)

    assert adjs["correlation"] == 1.0, "Intervening worker must reset repeat penalty to 1.0"
    assert w == "correlation", "Correlation worker should be legitimately revisited when utility warrants"


def test_claim_f_stagnation_tracking_meaningful_progress():
    """Claim F: Stagnation is based on meaningful progress rather than arbitrary confidence drift."""
    # Even if confidence is high (e.g. 0.70), if cycles_since_meaningful_progress >= STAGNATION_CYCLE_LIMIT (3), should_terminate flags stagnation
    state_stagnant = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.70,
        cycle_number=4,
        evidence_count=5,
        novel_evidence_count=5,
        cycles_since_meaningful_progress=settings.STAGNATION_CYCLE_LIMIT,
        cycles_since_confidence_gain=settings.STAGNATION_CYCLE_LIMIT,
    )
    term = should_terminate(state_stagnant)
    assert term is True
    assert state_stagnant.termination_reason == "stagnation"
    assert state_stagnant.termination_classification == "stagnation_escalation"

    # Conversely, if meaningful progress was made (cycles_since_meaningful_progress=0), loop continues
    state_progressing = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.50,
        cycle_number=4,
        evidence_count=5,
        novel_evidence_count=5,
        cycles_since_meaningful_progress=0,
        cycles_since_confidence_gain=0,
    )
    assert should_terminate(state_progressing) is False


def test_claim_g_real_stagnation_creates_persisted_replanning_event(db_session):
    """Claim G: A real stagnation condition creates a persisted replanning event in DB."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Test Investigation Claim G",
        status="investigating",
        current_confidence=0.25,
        planning_cycle_count=1,
    )
    db_session.add(inv)
    db_session.commit()

    # Cycle 1: Worker executed but produced zero novel evidence
    dec1 = PlannerDecision(
        decision_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        cycle_number=1,
        decision_type="continue_investigation",
        is_replanning=False,
        selected_worker="correlation",
        selection_score=0.85,
        confidence_before=0.25,
        confidence_after=0.25,
        explanation_summary="Correlation executed with 0 findings",
    )
    db_session.add(dec1)
    db_session.commit()

    engine = PlannerEngine()
    snap = engine.load_state_snapshot(inv, db_session)

    assert snap.cycles_since_meaningful_progress == 1
    assert snap.is_replanning is True
    assert "Strategy 'correlation' yielded no novel evidence" in (snap.replan_reason or "")

    # Execute cycle 2 via PlannerEngine
    res = engine.run_cycle(inv.investigation_id, db_session)

    dec2 = (
        db_session.query(PlannerDecision)
        .filter(PlannerDecision.investigation_id == inv.investigation_id, PlannerDecision.cycle_number == 2)
        .first()
    )
    assert dec2 is not None
    assert dec2.is_replanning is True
    assert dec2.decision_type == "replan"
    assert "Strategy 'correlation' yielded no novel evidence" in (dec2.replan_reason or "")


def test_claim_h_replanning_changes_subsequent_decision():
    """Claim H: Replanning actually changes the subsequent decision or strategy."""
    state = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.30,
        cycle_number=2,
        evidence_count=2,
        novel_evidence_count=2,
        last_worker="correlation",
        consecutive_worker_count=1,
        is_replanning=True,
        replan_reason="Strategy 'correlation' stalled",
    )
    w, u, scores, adjs, rationale = select_worker(state, return_details=True)

    # Stalled worker must be excluded (multiplier 0.0)
    assert adjs["correlation"] == 0.0, "Replan must exclude the stalled worker"
    assert scores["correlation"] == 0.0
    assert w != "correlation", "Planner must pivot to an alternative strategy"
    assert "[REPLAN]" in rationale


def test_claim_i_max_cycles_reported_as_safety_bound():
    """Claim I: max_cycles is reported as a safety bound and not as successful convergence."""
    state = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.60,  # Below completion threshold (0.85)
        cycle_number=settings.MAX_PLANNING_CYCLES,
        evidence_count=6,
        novel_evidence_count=6,
        cycles_since_meaningful_progress=0,
    )
    term = should_terminate(state)
    assert term is True
    assert state.termination_reason == "max_cycles_reached"
    assert state.termination_classification == "safety_bound", (
        f"Expected safety_bound classification, got {state.termination_classification}"
    )
