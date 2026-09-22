from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.schemas.contracts import WorkerTask, WorkerResult, WorkerType
from app.workers import get_worker, WORKER_REGISTRY

worker_router = APIRouter(prefix="/api/workers", tags=["Specialized Worker Agents"])


@worker_router.get("/registry")
def get_worker_registry():
    """Returns the list of all 5 available worker agents."""
    return {
        "available_workers": list(WORKER_REGISTRY.keys()),
        "descriptions": {
            "detection": "Heuristic & LLM-based threat detection and anomaly triage.",
            "correlation": "Entity graph construction linking hosts, users, IPs, and processes.",
            "investigation": "Hypothesis formulation, stance tracking, and MITRE ATT&CK RAG alignment.",
            "reporting": "Twin-tier report generation (Executive Summary + Technical Forensic Report).",
            "response": "Containment action formulation with risk assessment and human-in-the-loop approval."
        }
    }


@worker_router.post("/execute/{worker_type}", response_model=WorkerResult)
def execute_worker_agent(worker_type: WorkerType, task: WorkerTask):
    """Directly executes a specialized worker agent with the provided task payload."""
    try:
        worker = get_worker(worker_type)
        result = worker.execute(task)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Worker execution failed: {str(e)}")
