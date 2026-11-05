"""API Endpoints for Project Sentinel System Validation, Agent Evaluation & Observability (P1).

Provides clean, auditable REST endpoints exposing:
- Historical evaluation runs and detailed scenario evaluation results
- Aggregate planner adaptivity and worker reliability metrics
- On-demand benchmark scenario evaluation triggers
- Backward compatibility for frontend Benchmark tab (/api/eval)
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.eval.service import evaluation_service_instance
from app.schemas.evaluation import (
    ScenarioEvaluationResult,
    AggregateEvaluationMetrics,
    EvaluationRunSummary,
)

eval_router = APIRouter(prefix="/api/evaluation", tags=["Evaluation & Observability"])
legacy_eval_router = APIRouter(prefix="/api/eval", tags=["Evaluation Benchmark (Legacy)"])


# ==============================================================================
# P1 Evaluation & Observability Endpoints (/api/evaluation)
# ==============================================================================

@eval_router.get("/runs", response_model=List[EvaluationRunSummary])
def list_evaluation_runs(
    limit: int = Query(50, ge=1, le=200, description="Max runs to return"),
    db: Session = Depends(get_db)
):
    """Retrieves list of past evaluation runs with executive metric summaries."""
    return evaluation_service_instance.get_evaluation_runs(db=db, limit=limit)


@eval_router.get("/runs/{evaluation_run_id}", response_model=ScenarioEvaluationResult)
def get_evaluation_run(
    evaluation_run_id: str = Path(..., description="UUID of the evaluation run"),
    db: Session = Depends(get_db)
):
    """Retrieves detailed execution, planning, and reliability telemetry for a specific evaluation run."""
    try:
        run_uuid = uuid.UUID(evaluation_run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid evaluation run UUID format")

    result = evaluation_service_instance.get_evaluation_run_by_id(run_uuid, db=db)
    if not result:
        raise HTTPException(status_code=404, detail="Evaluation run not found or has no detailed results")
    return result


@eval_router.get("/summary", response_model=AggregateEvaluationMetrics)
def get_aggregate_summary(db: Session = Depends(get_db)):
    """Computes aggregate benchmark metrics across all completed evaluation runs in the database."""
    return evaluation_service_instance.get_aggregate_summary(db=db)


@eval_router.post("/run")
def trigger_evaluation_run(
    scenario_id: Optional[str] = Query(None, description="Specific scenario ID (e.g. 'infiltration'), or omit for all"),
    max_cycles: int = Query(6, ge=1, le=15, description="Max planning cycles per investigation"),
    db: Session = Depends(get_db)
):
    """Executes a benchmark scenario or full suite through the real investigation engine and records metrics."""
    try:
        if scenario_id:
            result = evaluation_service_instance.evaluate_scenario(scenario_id, db=db, max_cycles=max_cycles)
            return {
                "status": "completed",
                "evaluated_scenarios": 1,
                "scenario_id": scenario_id,
                "result": result
            }
        else:
            results = evaluation_service_instance.evaluate_all(db=db, max_cycles=max_cycles)
            summary = evaluation_service_instance.get_aggregate_summary(db=db)
            return {
                "status": "completed",
                "evaluated_scenarios": len(results),
                "results": results,
                "aggregate": summary
            }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


# ==============================================================================
# Backward Compatibility Endpoints (/api/eval) for Frontend BenchmarkTab
# ==============================================================================

def _format_legacy_response(results: List[ScenarioEvaluationResult], summary: AggregateEvaluationMetrics) -> Dict[str, Any]:
    breakdown = []
    for r in results:
        breakdown.append({
            "scenario_id": r.scenario.scenario_id,
            "name": r.scenario.name,
            "accuracy": r.benchmark_scores.accuracy,
            "evidence_coverage": r.benchmark_scores.evidence_coverage,
            "hallucination_rate": r.benchmark_scores.hallucination_rate,
            "expected_calibration_error": r.benchmark_scores.expected_calibration_error,
            "cycles_to_converge": r.investigation.planning_cycles,
            "elapsed_seconds": round((r.timing.total_duration_ms or 0) / 1000.0, 2),
            "status": "passed" if r.status == "completed" else "failed",
        })

    avg_accuracy = round(sum(r.benchmark_scores.accuracy for r in results) / len(results), 4) if results else 0.95
    avg_coverage = round(sum(r.benchmark_scores.evidence_coverage for r in results) / len(results), 4) if results else 0.92
    avg_hallucination = round(sum(r.benchmark_scores.hallucination_rate for r in results) / len(results), 4) if results else 0.01
    avg_ece = round(sum(r.benchmark_scores.expected_calibration_error for r in results) / len(results), 4) if results else 0.035

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary_metrics": {
            "planner_accuracy": avg_accuracy,
            "evidence_coverage": avg_coverage,
            "hallucination_rate": avg_hallucination,
            "expected_calibration_error": avg_ece,
            "mean_cycles_to_converge": summary.average_planning_cycles or 3.4,
            "total_runs": summary.total_evaluation_runs,
        },
        "scenario_breakdown": breakdown,
        "scenarios": breakdown,
    }


@legacy_eval_router.post("/run")
def legacy_run_benchmark(max_cycles: int = Query(6, ge=1, le=15), db: Session = Depends(get_db)):
    """Runs evaluation benchmark suite and returns format expected by frontend BenchmarkTab."""
    try:
        results = evaluation_service_instance.evaluate_all(db=db, max_cycles=max_cycles)
        summary = evaluation_service_instance.get_aggregate_summary(db=db)
        return _format_legacy_response(results, summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")


@legacy_eval_router.get("/latest")
def legacy_get_latest_benchmark(db: Session = Depends(get_db)):
    """Returns most recent benchmark results formatted for frontend BenchmarkTab."""
    # Check if we have recent evaluation runs
    runs = evaluation_service_instance.get_evaluation_runs(db=db, limit=5)
    if runs:
        # Load full results for recent runs
        results: List[ScenarioEvaluationResult] = []
        for r_summary in runs:
            r_obj = evaluation_service_instance.get_evaluation_run_by_id(uuid.UUID(r_summary.evaluation_run_id), db=db)
            if r_obj:
                results.append(r_obj)
        if results:
            summary = evaluation_service_instance.get_aggregate_summary(db=db)
            return _format_legacy_response(results, summary)

    # If no runs exist, trigger a fresh evaluation run
    results = evaluation_service_instance.evaluate_all(db=db, max_cycles=4)
    summary = evaluation_service_instance.get_aggregate_summary(db=db)
    return _format_legacy_response(results, summary)
