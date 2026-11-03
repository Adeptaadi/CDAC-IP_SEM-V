import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.orchestration import AgentTask, TaskAttempt, TaskDependency
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[AgentTask]):
    def __init__(self, db: Session):
        super().__init__(AgentTask, db)

    def create_task(
        self,
        investigation_id: uuid.UUID,
        worker_type: str,
        objective: str,
        input_payload: Optional[Dict[str, Any]] = None,
        capability_id: Optional[uuid.UUID] = None,
        depends_on: Optional[List[uuid.UUID]] = None,
    ) -> AgentTask:
        task = AgentTask(
            investigation_id=investigation_id,
            capability_id=capability_id,
            worker_type=worker_type,
            status="pending",
            objective=objective,
            input_payload=input_payload or {},
        )
        self.db.add(task)
        self.db.flush()

        if depends_on:
            for dep_id in depends_on:
                dep = TaskDependency(task_id=task.id, depends_on_task_id=dep_id)
                self.db.add(dep)
            self.db.flush()

        return task

    def record_attempt(
        self,
        task_id: uuid.UUID,
        status: str,
        latency_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> TaskAttempt:
        task = self.db.query(AgentTask).filter(AgentTask.id == task_id).first()
        if not task:
            raise ValueError(f"AgentTask {task_id} not found")

        # Determine attempt number
        existing_attempts = self.db.query(TaskAttempt).filter(TaskAttempt.task_id == task_id).count()
        attempt_number = existing_attempts + 1

        attempt = TaskAttempt(
            task_id=task_id,
            attempt_number=attempt_number,
            status=status,
            latency_ms=latency_ms,
            error_message=error_message,
        )
        self.db.add(attempt)

        task.status = "running" if status == "running" else task.status
        self.db.flush()
        return attempt

    def complete_task(
        self,
        task_id: uuid.UUID,
        output_payload: Dict[str, Any],
        status: str = "completed",
    ) -> AgentTask:
        task = self.db.query(AgentTask).filter(AgentTask.id == task_id).first()
        if not task:
            raise ValueError(f"AgentTask {task_id} not found")

        task.status = status
        task.output_payload = output_payload
        task.completed_at = datetime.utcnow()
        self.db.flush()
        return task
