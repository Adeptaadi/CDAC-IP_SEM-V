"""Project Sentinel — Phase B0: Backend Correctness Remediation Verification Suite.

Validates the behavioral correctness of the remediated investigation loop:
1. Duplicate evidence does not inflate information gain or meaningful evidence counts (B0.2).
2. Independent observation counts as corroboration, not completely new evidence (B0.2).
3. Genuinely new evidence increases information gain (B0.2).
4. Zero-novelty execution produces zero/negative net confidence progress (B0.3).
5. Confidence factor trace exposes factor names, contributions, and provenance (B0.3).
6. Stagnation counter increments under no-progress conditions (B0.4).
7. Meaningful new evidence resets stagnation counter (B0.4).
8. Response worker cannot be repeatedly selected without new expected utility (B0.5, B0.6).
9. Execution history applies repeat penalties while preserving legitimate revisits (B0.5).
10. Genuine replanning occurs and is persisted in the live PlannerEngine path (B0.7).
11. max_cycles is reported as safety_bound termination (B0.8).
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Investigation, Evidence, Hypothesis, PlannerDecision, WorkerExecution
from app.models.evidence import compute_evidence_fingerprint
from app.planner.engine import PlannerEngine
from app.planner.selection import InvestigationStateSnapshot, select_worker, should_terminate
from app.planner.confidence import ConfidenceEngine
from app.schemas.contracts import WorkerTask, WorkerResult, Finding
from app.workers.base import BaseWorker
from app.workers import get_worker
from app.config import settings


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for B0 remediation testing."""
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


class DummyZeroProgressWorker(BaseWorker):
    worker_type = "investigation"

    def execute(self, task: WorkerTask) -> WorkerResult:
        return WorkerResult(
            task_id=task.task_id,
            worker_type=self.worker_type,
            status="success",
            findings=[],
            confidence_signal=0.50,
            new_evidence=[],
            hypothesis_updates=[],
            reasoning_summary="No new progress or evidence generated.",
            next_task_suggestion=None,
        )


# =========================================================================
# Test 1: Duplicate evidence from same worker does not inflate meaningful evidence (B0.2 Test A)
# =========================================================================
def test_duplicate_evidence_does_not_inflate_meaningful_evidence(db_session):
    """Verify that repeated identical findings from ResponseWorker are flagged as duplicates,

    meaningful evidence count does not inflate, and confidence delta is zero.
    """
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Deduplication Verification",
        status="investigating",
        current_confidence=0.30,
        planning_cycle_count=1,
    )
    db_session.add(inv)
    hypo = Hypothesis(
        hypothesis_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        label="Adversary Infiltration Confirmed",
        status="confirmed",
        confidence=0.88,
    )
    db_session.add(hypo)
    db_session.commit()

    planner = PlannerEngine()

    # Cycle 1: First Response execution generates 4 novel items
    r1 = planner.run_cycle(inv.investigation_id, db_session)
    assert r1["selected_worker"] == "response"
    assert r1["novel_count"] == 4
    assert r1["duplicate_count"] == 0

    # Total evidence is 4, all novel
    ev_all = db_session.query(Evidence).filter(Evidence.investigation_id == inv.investigation_id).all()
    assert len(ev_all) == 4
    assert all(e.is_novel for e in ev_all)

    # Force Response worker to run again with identical findings (mocking repeat)
    # Manually trigger run_cycle while mocking select_worker to response
    import app.planner.engine as engine_mod
    orig_select = engine_mod.select_worker
    engine_mod.select_worker = lambda s, return_details=False: (
        ("response", 0.95, {"response": 0.95}, {}, "Forced repeat")
        if return_details else ("response", 0.95, {"response": 0.95})
    )
    try:
        r2 = planner.run_cycle(inv.investigation_id, db_session)
    finally:
        engine_mod.select_worker = orig_select

    # In cycle 2: all 4 items are duplicates!
    assert r2["novel_count"] == 0
    assert r2["duplicate_count"] == 4

    # Meaningful novel evidence count remains exactly 4
    novel_ev = db_session.query(Evidence).filter(
        Evidence.investigation_id == inv.investigation_id,
        Evidence.is_novel == True
    ).all()
    assert len(novel_ev) == 4

    # Duplicate records exist for provenance but are flagged
    dup_ev = db_session.query(Evidence).filter(
        Evidence.investigation_id == inv.investigation_id,
        Evidence.is_duplicate == True
    ).all()
    assert len(dup_ev) == 4

    # Confidence did NOT increase on duplicate cycle
    assert round(r2["confidence_after"], 4) == round(r2["confidence_before"], 4)


# =========================================================================
# Test 2: Independent observation counts as corroboration, not completely new evidence (B0.2 Test B)
# =========================================================================
def test_independent_observation_counts_as_corroboration(db_session):
    """Verify that when a second worker reports an observation with an identical fingerprint,

    it is classified as corroboration rather than completely new evidence.
    """
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Corroboration Verification",
        status="investigating",
        current_confidence=0.20,
    )
    db_session.add(inv)

    # First observation from detection worker
    desc = "Adversary beaconing to 13.58.225.34"
    ents = {"ips": ["13.58.225.34"]}
    f_hash = compute_evidence_fingerprint(desc, ents)

    ev1 = Evidence(
        evidence_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        source_type="worker_output",
        description=desc,
        content_hash=f_hash,
        is_novel=True,
        is_duplicate=False,
        entity_refs=ents,
        produced_by_worker="detection",
    )
    db_session.add(ev1)
    db_session.commit()

    # Create dummy worker result from correlation worker with identical observation
    class CorroboratingWorker(BaseWorker):
        worker_type = "correlation"
        def execute(self, task: WorkerTask) -> WorkerResult:
            f = Finding(description=desc, entity_refs=ents)
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_type,
                status="success",
                findings=[f],
                confidence_signal=0.85,
                new_evidence=[f],
                hypothesis_updates=[],
                reasoning_summary="Correlated beacon flow to existing finding.",
            )

    import app.planner.engine as engine_mod
    orig_get = engine_mod.get_worker
    orig_select = engine_mod.select_worker
    engine_mod.get_worker = lambda wt: CorroboratingWorker()
    engine_mod.select_worker = lambda s, return_details=False: (
        ("correlation", 0.8, {"correlation": 0.8}, {}, "Corroboration test")
        if return_details else ("correlation", 0.8, {"correlation": 0.8})
    )

    try:
        planner = PlannerEngine()
        res = planner.run_cycle(inv.investigation_id, db_session)
    finally:
        engine_mod.get_worker = orig_get
        engine_mod.select_worker = orig_select

    # The finding was identified as corroboration, NOT a completely new novel item
    assert res["novel_count"] == 0
    assert res["duplicate_count"] == 0  # not duplicate because produced by different worker!

    # Check that ev1 now has corroboration linked
    db_session.refresh(ev1)
    assert len(ev1.corroborated_by) >= 1


# =========================================================================
# Test 3: Genuinely new evidence increases information gain (B0.2 Test C)
# =========================================================================
def test_genuinely_new_evidence_increases_information_gain(db_session):
    """Verify that genuinely novel findings increase confidence and reset stagnation."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Novel Evidence Test",
        status="investigating",
        current_confidence=0.15,
    )
    db_session.add(inv)
    db_session.commit()

    planner = PlannerEngine()
    res = planner.run_cycle(inv.investigation_id, db_session)

    # First cycle produces novel evidence
    assert res["novel_count"] > 0
    assert res["confidence_after"] > res["confidence_before"]


# =========================================================================
# Test 4: Zero-novelty execution produces zero or negative confidence progress (B0.3)
# =========================================================================
def test_zero_novelty_execution_produces_zero_confidence_progress(db_session, monkeypatch):
    """Verify that a worker producing 0 evidence results in exactly 0.0 confidence gain,

    proving artificial drift (cycle slope, RAG boost, agreement fallback) has been removed.
    """
    import app.planner.engine as engine_mod
    monkeypatch.setattr(engine_mod, "get_worker", lambda wt: DummyZeroProgressWorker())

    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Zero Novelty Stagnation Test",
        status="investigating",
        current_confidence=0.25,
        planning_cycle_count=1,
    )
    db_session.add(inv)
    db_session.commit()

    planner = PlannerEngine()
    cycle_res = planner.run_cycle(inv.investigation_id, db_session)

    gain = cycle_res["confidence_after"] - cycle_res["confidence_before"]
    assert gain <= 0.0, f"Expected zero or negative gain, got {gain}"
    assert cycle_res["confidence_after"] == 0.25


# =========================================================================
# Test 5: Confidence factor trace exposes factor names, contributions, and provenance (B0.3)
# =========================================================================
def test_confidence_factor_trace_structure(db_session):
    """Verify that ConfidenceEngine factor trace exposes factor name, input value, contribution, and source."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Factor Trace Test",
        status="investigating",
        current_confidence=0.15,
    )
    db_session.add(inv)
    db_session.commit()

    planner = PlannerEngine()
    cycle_res = planner.run_cycle(inv.investigation_id, db_session)

    trace = cycle_res.get("confidence_factor_trace")
    assert trace is not None
    assert len(trace) >= 6

    factor_names = [f["factor_name"] for f in trace]
    assert "detection" in factor_names
    assert "evidence" in factor_names
    assert "correlation" in factor_names
    assert "knowledge" in factor_names
    assert "agreement" in factor_names
    assert "historical" in factor_names

    for item in trace:
        assert "factor_name" in item
        assert "input_value" in item
        assert "contribution" in item
        assert "source" in item


# =========================================================================
# Test 6: Stagnation counter increments under no-progress conditions (B0.4)
# =========================================================================
def test_stagnation_counter_increments_under_no_progress(db_session, monkeypatch):
    """Verify that cycles producing no novel evidence increment cycles_since_meaningful_progress."""
    import app.planner.engine as engine_mod
    monkeypatch.setattr(engine_mod, "get_worker", lambda wt: DummyZeroProgressWorker())

    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Stagnation Increment Test",
        status="investigating",
        current_confidence=0.30,
        planning_cycle_count=0,
    )
    db_session.add(inv)
    db_session.commit()

    planner = PlannerEngine()

    # Cycle 1: No progress
    planner.run_cycle(inv.investigation_id, db_session)
    snap1 = planner.load_state_snapshot(inv, db_session)
    assert snap1.cycles_since_meaningful_progress == 1

    # Cycle 2: No progress
    planner.run_cycle(inv.investigation_id, db_session)
    snap2 = planner.load_state_snapshot(inv, db_session)
    assert snap2.cycles_since_meaningful_progress == 2


# =========================================================================
# Test 7: Meaningful new evidence resets stagnation counter (B0.4)
# =========================================================================
def test_meaningful_new_evidence_resets_stagnation(db_session):
    """Verify that when novel evidence is produced, cycles_since_meaningful_progress resets to 0."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Stagnation Reset Test",
        status="investigating",
        current_confidence=0.30,
        planning_cycle_count=0,
    )
    db_session.add(inv)
    db_session.commit()

    planner = PlannerEngine()

    # Run cycle producing novel evidence
    planner.run_cycle(inv.investigation_id, db_session)
    snap = planner.load_state_snapshot(inv, db_session)
    assert snap.cycles_since_meaningful_progress == 0


# =========================================================================
# Test 8: Response worker cannot be repeatedly selected without new utility (B0.5, B0.6)
# =========================================================================
def test_response_worker_safety_and_no_perpetual_lock(db_session):
    """Verify that once Response worker has formulated containment recommendations,

    its utility drops and it is NOT selected on the subsequent cycle.
    """
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Response Safety Test",
        status="investigating",
        current_confidence=0.30,
        planning_cycle_count=1,
    )
    db_session.add(inv)
    hypo = Hypothesis(
        hypothesis_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        label="Adversary Infiltration Confirmed",
        status="confirmed",
        confidence=0.88,
    )
    db_session.add(hypo)
    db_session.commit()

    planner = PlannerEngine()

    # Cycle 1: Response worker executes to formulate initial containment
    r1 = planner.run_cycle(inv.investigation_id, db_session)
    assert r1["selected_worker"] == "response"

    # Cycle 2: Response should NOT be selected again!
    r2 = planner.run_cycle(inv.investigation_id, db_session)
    assert r2["selected_worker"] != "response", f"Pathological repeat: response was re-selected in cycle 2!"


# =========================================================================
# Test 9: Planner execution history applies repeat penalties while preserving revisits (B0.5)
# =========================================================================
def test_execution_history_repeat_penalty_and_legitimate_revisit():
    """Verify select_worker applies repeat penalties to consecutive selections

    while permitting legitimate revisits when another capability executes in between.
    """
    snap_initial = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.30,
        cycle_number=1,
        evidence_count=4,
        last_worker=None,
        consecutive_worker_count=0,
    )
    worker1, score1, _ = select_worker(snap_initial)

    # Simulate worker1 ran once: consecutive count = 1
    snap_repeated = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.30,
        cycle_number=2,
        evidence_count=4,
        last_worker=worker1,
        consecutive_worker_count=1,
    )
    _, score_penalized, adj_scores = select_worker(snap_repeated)
    assert adj_scores[worker1] < score1  # penalized!

    # Simulate another worker ran in between: last_worker is now different
    snap_revisit = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.30,
        cycle_number=3,
        evidence_count=6,
        last_worker="correlation",
        consecutive_worker_count=1,
    )
    _, _, revisit_scores = select_worker(snap_revisit)
    # worker1 is no longer penalized by repeat penalty!
    assert revisit_scores[worker1] >= adj_scores[worker1]


# =========================================================================
# Test 10: Genuine replanning occurs and is persisted in the live loop (B0.7)
# =========================================================================
def test_genuine_replanning_in_live_planner_engine(db_session, monkeypatch):
    """Verify that when a strategy produces no progress, the Planner persists a genuine

    replan decision with decision_type='replan', is_replanning=True, and pivots capability.
    """
    import app.planner.engine as engine_mod
    monkeypatch.setattr(engine_mod, "get_worker", lambda wt: DummyZeroProgressWorker())

    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Replanning Integration Test",
        status="investigating",
        current_confidence=0.20,
        planning_cycle_count=0,
    )
    db_session.add(inv)
    db_session.commit()

    planner = PlannerEngine()

    # Cycle 1: Worker executes, yields 0 progress
    r1 = planner.run_cycle(inv.investigation_id, db_session)
    assert r1["decision_type"] == "continue_investigation"
    assert r1["is_replanning"] is False

    # Cycle 2: Planner detects lack of progress from cycle 1 and initiates REPLAN!
    r2 = planner.run_cycle(inv.investigation_id, db_session)
    assert r2["decision_type"] == "replan"
    assert r2["is_replanning"] is True
    assert "replan_reason" in r2 and r2["replan_reason"] is not None

    # Verify DB persistence of PlannerDecision record
    replan_dec = db_session.query(PlannerDecision).filter(
        PlannerDecision.investigation_id == inv.investigation_id,
        PlannerDecision.cycle_number == 2
    ).first()
    assert replan_dec is not None
    assert replan_dec.decision_type == "replan"
    assert replan_dec.is_replanning is True
    assert "Pivoted" in replan_dec.explanation_summary or "replan" in replan_dec.explanation_summary.lower()


# =========================================================================
# Test 11: max_cycles is reported as safety_bound termination (B0.8)
# =========================================================================
def test_max_cycles_reported_as_safety_bound(db_session):
    """Verify should_terminate sets termination_classification = 'safety_bound' on max cycles."""
    snap = InvestigationStateSnapshot(
        investigation_id=str(uuid.uuid4()),
        confidence=0.45,
        cycle_number=settings.MAX_PLANNING_CYCLES,
    )
    assert should_terminate(snap) is True
    assert snap.termination_reason == "max_cycles_reached"
    assert snap.termination_classification == "safety_bound"
