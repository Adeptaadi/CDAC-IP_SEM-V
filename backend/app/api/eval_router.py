from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.eval.runner import benchmark_runner

eval_router = APIRouter(prefix="/api/eval", tags=["Evaluation Benchmark"])

LATEST_EVALUATION_CACHE = None


@eval_router.post("/run")
def run_benchmark_evaluation(max_cycles: int = 6, db: Session = Depends(get_db)):
    """Runs the full 5-scenario evaluation suite (Stage 5) and returns empirical scientific metrics."""
    global LATEST_EVALUATION_CACHE
    try:
        results = benchmark_runner.evaluate_all(db, max_cycles=max_cycles)
        LATEST_EVALUATION_CACHE = results
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Benchmark execution failed: {str(e)}")


@eval_router.get("/latest")
def get_latest_benchmark_evaluation(db: Session = Depends(get_db)):
    """Returns the most recent evaluation benchmark results or runs a new one."""
    global LATEST_EVALUATION_CACHE
    if LATEST_EVALUATION_CACHE:
        return LATEST_EVALUATION_CACHE
    results = benchmark_runner.evaluate_all(db, max_cycles=4)
    LATEST_EVALUATION_CACHE = results
    return results
