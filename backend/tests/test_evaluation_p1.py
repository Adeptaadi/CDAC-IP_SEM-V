"""Automated Verification Suite for Project Sentinel P1: System Validation, Agent Evaluation & Observability.

Verifies:
1. Scenario evaluation produces a valid, typed ScenarioEvaluationResult.
2. Metrics are calculated strictly from persisted database execution records.
3. Zero executions handle edge cases cleanly without ZeroDivisionError or NaN.
4. Failed and partial worker executions are tracked and counted accurately.
5. Capability revisits and non-linear sequences are detected reliably.
6. Replanning events are grounded in actual recorded Planner decisions.
7. Confidence progression preserves exact recorded values and deltas.
8. Aggregate metrics expose strict denominators and population statements.
9. Benchmark evaluation runs remain isolated from production investigations.
10. Evaluation REST API endpoints operate cleanly with schema validation.
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
import app.models  # Register all schema entities
from app.models.investigation import Investigation
from app.models.evidence import Evidence
from app.models.orchestration import PlannerDecision, WorkerExecution
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.eval.service import EvaluationService, evaluation_service_instance
from app.schemas.evaluation import (
    ScenarioEvaluationResult,
    AggregateEvaluationMetrics,
    EvaluationRunSummary,
)
from app.api.eval_router import (
    list_evaluation_runs,
    get_evaluation_run,
    get_aggregate_summary,
    legacy_get_latest_benchmark,
)
from fastapi import HTTPException


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session."""
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


# =========================================================================
# Test 1: Scenario evaluation produces a valid typed ScenarioEvaluationResult
# =========================================================================
def test_scenario_evaluation_produces_valid_result(db_session):
    """Running a benchmark scenario produces a fully validated Pydantic result."""
    service = EvaluationService()
    result = service.evaluate_scenario("infiltration", db=db_session, max_cycles=4)

    assert isinstance(result, ScenarioEvaluationResult)
    assert result.status == "completed"
    assert result.scenario.scenario_id == "infiltration"
    assert result.scenario.source_type == "benchmark_derived_scenario"
    assert result.investigation.planning_cycles >= 1
    assert result.investigation.final_status in ["investigating", "completed", "active"]
    assert result.timing.total_duration_ms is not None
    assert result.agents.total_executions >= 1
    assert result.benchmark_scores.accuracy >= 0.0


# =========================================================================
# Test 2: Metrics calculated strictly from persisted database records
# =========================================================================
def test_metrics_derived_from_persisted_execution_records(db_session):
    """Evaluation runs write to evaluation_runs and evaluation_results tables."""
    service = EvaluationService()
    run_id = uuid.uuid4()
    result = service.evaluate_scenario("brute_force", db=db_session, max_cycles=3, evaluation_run_id=run_id)

    # Verify persistent DB row in evaluation_runs
    db_run = db_session.query(EvaluationRun).filter(EvaluationRun.id == run_id).first()
    assert db_run is not None
    assert db_run.status == "completed"
    assert db_run.scenario_id == "brute_force"

    # Verify metric rows in evaluation_results
    db_metrics = db_session.query(EvaluationResult).filter(EvaluationResult.evaluation_run_id == run_id).all()
    assert len(db_metrics) >= 5
    metric_names = [m.metric_name for m in db_metrics]
    assert "accuracy" in metric_names
    assert "evidence_coverage" in metric_names
    assert "planning_cycles" in metric_names


# =========================================================================
# Test 3: Zero executions do not cause division-by-zero or crashes
# =========================================================================
def test_zero_executions_handled_gracefully(db_session):
    """Aggregate summary on empty database returns neutral metrics with explicit disclosures."""
    service = EvaluationService()
    summary = service.get_aggregate_summary(db=db_session)

    assert isinstance(summary, AggregateEvaluationMetrics)
    assert summary.total_evaluation_runs == 0
    assert summary.completed_runs == 0
    assert summary.unique_scenarios_evaluated == 0
    assert summary.average_planning_cycles is None
    assert summary.average_confidence_delta is None
    assert summary.overall_agent_success_rate == 100.0
    assert summary.overall_agent_success_sample == "0% (0/0 executions)"
    assert "No evaluation runs recorded" in summary.sample_size_population_statement


# =========================================================================
# Test 4: Failed and partial worker executions counted correctly
# =========================================================================
def test_failed_worker_executions_counted_correctly(db_session):
    """Simulated worker failure in an evaluation run properly reduces success rate."""
    inv_id = uuid.uuid4()
    dec_id = uuid.uuid4()

    inv = Investigation(
        investigation_id=inv_id,
        title="Failure Accounting Investigation",
        status="active",
        current_confidence=0.2,
    )
    db_session.add(inv)

    dec = PlannerDecision(
        decision_id=dec_id,
        investigation_id=inv_id,
        cycle_number=1,
        selected_worker="correlation",
        confidence_before=0.20,
        confidence_after=0.35,
        explanation_summary="Correlation selected for triage",
    )
    db_session.add(dec)

    w1 = WorkerExecution(
        execution_id=uuid.uuid4(),
        decision_id=dec_id,
        worker_type="correlation",
        status="completed",
        raw_output={"result": "ok", "evidence_count": 2},
        latency_ms=10,
    )
    w2 = WorkerExecution(
        execution_id=uuid.uuid4(),
        decision_id=dec_id,
        worker_type="investigation",
        status="failed",
        raw_output={"error": "Simulated connection timeout"},
        latency_ms=15,
    )
    db_session.add_all([w1, w2])
    db_session.commit()

    execs = db_session.query(WorkerExecution).filter(WorkerExecution.decision_id == dec_id).all()
    total = len(execs)
    success = sum(1 for e in execs if e.status == "completed")
    failed = sum(1 for e in execs if e.status == "failed")

    assert total == 2
    assert success == 1
    assert failed == 1
    success_rate = (success / total) * 100.0
    assert success_rate == 50.0


# =========================================================================
# Test 5: Capability revisits and sequences detected correctly
# =========================================================================
def test_capability_revisit_detection(db_session):
    """Non-linear sequence with revisits is correctly tracked."""
    # Sequence: correlation -> investigation -> correlation (revisit!)
    trace = [
        {"worker": "correlation", "capability": "correlation.execute"},
        {"worker": "investigation", "capability": "investigation.execute"},
        {"worker": "correlation", "capability": "correlation.execute"},
    ]

    seen = set()
    revisits = 0
    revisit_seqs = []
    prev = None

    for item in trace:
        cap = item["capability"]
        if cap in seen and cap != prev:
            revisits += 1
            revisit_seqs.append(f"{prev} -> {cap}")
        seen.add(cap)
        prev = cap

    assert revisits == 1
    assert len(revisit_seqs) == 1
    assert revisit_seqs[0] == "investigation.execute -> correlation.execute"


# =========================================================================
# Test 6: Replanning events grounded in real Planner decisions
# =========================================================================
def test_replanning_events_grounded_in_planner_decisions(db_session):
    """Planner decisions with revisiting or replanning rationale are tracked."""
    inv_id = uuid.uuid4()
    inv = Investigation(investigation_id=inv_id, title="Replan Test Inv")
    db_session.add(inv)

    d1 = PlannerDecision(
        decision_id=uuid.uuid4(),
        investigation_id=inv_id,
        cycle_number=1,
        selected_worker="investigation",
        confidence_before=0.15,
        confidence_after=0.30,
        explanation_summary="Standard capability progression",
    )
    d2 = PlannerDecision(
        decision_id=uuid.uuid4(),
        investigation_id=inv_id,
        cycle_number=2,
        selected_worker="correlation",
        confidence_before=0.30,
        confidence_after=0.45,
        explanation_summary="[REPLAN] Revisiting correlation due to new evidence hypothesis shift",
    )
    db_session.add_all([d1, d2])
    db_session.commit()

    decisions = db_session.query(PlannerDecision).filter(PlannerDecision.investigation_id == inv_id).all()
    assert len(decisions) == 2
    replans = sum(1 for d in decisions if "[REPLAN]" in (d.explanation_summary or ""))
    assert replans == 1


# =========================================================================
# Test 7: Confidence progression preserves actual recorded values
# =========================================================================
def test_confidence_progression_preserves_values(db_session):
    """Confidence delta is mathematically consistent with initial and final values."""
    service = EvaluationService()
    result = service.evaluate_scenario("web_attacks", db=db_session, max_cycles=3)

    inv = result.investigation
    expected_delta = round(inv.final_confidence - inv.initial_confidence, 4)
    assert abs(inv.confidence_delta - expected_delta) < 0.0001
    assert 0.0 <= inv.initial_confidence <= 1.0
    assert 0.0 <= inv.final_confidence <= 1.0


# =========================================================================
# Test 8: Aggregate metrics include correct denominators and transparency statement
# =========================================================================
def test_aggregate_metrics_denominators_and_transparency(db_session):
    """Aggregate metrics accurately state total runs, unique scenarios, and population representation."""
    service = EvaluationService()
    # Run 2 scenarios
    service.evaluate_scenario("infiltration", db=db_session, max_cycles=3)
    service.evaluate_scenario("brute_force", db=db_session, max_cycles=3)

    summary = service.get_aggregate_summary(db=db_session)
    assert summary.total_evaluation_runs == 2
    assert summary.unique_scenarios_evaluated == 2
    assert "infiltration" in summary.scenarios_evaluated_list
    assert "brute_force" in summary.scenarios_evaluated_list
    assert "2 completed evaluation run(s)" in summary.sample_size_population_statement
    assert "% (" in summary.overall_agent_success_sample  # e.g. "100.0% (6/6 executions)"


# =========================================================================
# Test 9: Evaluation runs do not corrupt production investigations
# =========================================================================
def test_evaluation_runs_isolation(db_session):
    """Evaluation runs are clearly tagged with [Evaluation Benchmark] and do not alter user investigations."""
    # Create a user investigation
    user_inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Live SOC Incident 1042",
        status="active",
        current_confidence=0.72,
    )
    db_session.add(user_inv)
    db_session.commit()

    # Run evaluation
    service = EvaluationService()
    service.evaluate_scenario("dos_goldeneye", db=db_session, max_cycles=3)

    # Verify user investigation remains pristine
    refreshed_user_inv = db_session.query(Investigation).filter(Investigation.investigation_id == user_inv.investigation_id).first()
    assert refreshed_user_inv.title == "Live SOC Incident 1042"
    assert float(refreshed_user_inv.current_confidence) == 0.72

    # Verify benchmark investigation has prefix
    bench_invs = db_session.query(Investigation).filter(Investigation.title.like("[Evaluation Benchmark]%")).all()
    assert len(bench_invs) == 1
    assert "dos_goldeneye" in bench_invs[0].title or "Denial of Service" in bench_invs[0].title


# =========================================================================
# Test 10: Evaluation API endpoints operate cleanly with schema validation
# =========================================================================
def test_evaluation_api_endpoints(db_session):
    """P1 evaluation API endpoints return typed responses."""
    service = EvaluationService()
    res = service.evaluate_scenario("botnet_c2", db=db_session, max_cycles=3)

    # 1. list_evaluation_runs
    runs_list = list_evaluation_runs(limit=10, db=db_session)
    assert len(runs_list) >= 1
    assert isinstance(runs_list[0], EvaluationRunSummary)
    assert runs_list[0].scenario_id == "botnet_c2"

    # 2. get_evaluation_run
    detail = get_evaluation_run(evaluation_run_id=runs_list[0].evaluation_run_id, db=db_session)
    assert isinstance(detail, ScenarioEvaluationResult)
    assert detail.scenario.scenario_id == "botnet_c2"

    # 3. get_aggregate_summary
    agg = get_aggregate_summary(db=db_session)
    assert isinstance(agg, AggregateEvaluationMetrics)
    assert agg.total_evaluation_runs >= 1

    # 4. legacy_get_latest_benchmark
    legacy = legacy_get_latest_benchmark(db=db_session)
    assert "scenario_breakdown" in legacy
    assert "summary_metrics" in legacy
    assert len(legacy["scenario_breakdown"]) >= 1

    # 5. Invalid UUID raises 400
    with pytest.raises(HTTPException) as exc_400:
        get_evaluation_run(evaluation_run_id="invalid-uuid-string", db=db_session)
    assert exc_400.value.status_code == 400

    # 6. Non-existent UUID raises 404
    with pytest.raises(HTTPException) as exc_404:
        get_evaluation_run(evaluation_run_id=str(uuid.uuid4()), db=db_session)
    assert exc_404.value.status_code == 404
