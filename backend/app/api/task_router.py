import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.orchestration import AgentTask, TaskAttempt
from app.orchestration import (
    TaskExecutionRequest,
    TaskExecutionResult,
    capability_registry_instance,
    task_executor_instance,
)

router = APIRouter(prefix="/api/orchestration", tags=["Capability & Task Orchestration"])


@router.get("/capabilities")
def list_capabilities(capability_type: Optional[str] = None):
    """Lists registered worker capabilities with risk levels and schemas (Phase 8)."""
    caps = capability_registry_instance.list_capabilities(capability_type=capability_type)
    return [c.model_dump() for c in caps]


@router.post("/tasks", response_model=TaskExecutionResult)
def execute_task(
    payload: TaskExecutionRequest,
    db: Session = Depends(get_db),
):
    """Executes a capability task with idempotency, dependency validation, and attempt tracking."""
    try:
        return task_executor_instance.execute_task(payload, db=db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}")
def get_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieves task execution status, payload, and attempt history."""
    task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    attempts = (
        db.query(TaskAttempt)
        .filter(TaskAttempt.task_id == task_id)
        .order_by(TaskAttempt.attempt_number.asc())
        .all()
    )

    return {
        "task_id": str(task.id),
        "investigation_id": str(task.investigation_id),
        "worker_type": task.worker_type,
        "status": task.status,
        "objective": task.objective,
        "output_payload": task.output_payload,
        "created_at": task.created_at.isoformat(),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "attempts": [
            {
                "attempt_number": a.attempt_number,
                "status": a.status,
                "latency_ms": a.latency_ms,
                "error_message": a.error_message,
                "created_at": a.created_at.isoformat(),
            }
            for a in attempts
        ],
    }


@router.get("/investigations/{investigation_id}/tasks")
def list_investigation_tasks(investigation_id: uuid.UUID, db: Session = Depends(get_db)):
    """Lists all tasks executed for a given investigation."""
    tasks = (
        db.query(AgentTask)
        .filter(AgentTask.investigation_id == investigation_id)
        .order_by(AgentTask.created_at.asc())
        .all()
    )
    return [
        {
            "task_id": str(t.id),
            "worker_type": t.worker_type,
            "status": t.status,
            "objective": t.objective,
            "created_at": t.created_at.isoformat(),
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]
