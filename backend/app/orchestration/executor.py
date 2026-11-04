import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.orchestration import AgentTask, TaskAttempt, TaskDependency
from app.workers import get_worker
from app.schemas.contracts import WorkerTask, WorkerResult
from app.orchestration.contracts import (
    TaskExecutionRequest,
    TaskExecutionResult,
    CapabilityDefinition,
    TaskStatus,
)
from app.orchestration.registry import CapabilityRegistry, capability_registry_instance


class TaskBlockedError(Exception):
    """Raised when a task cannot proceed because prerequisites/dependencies are unmet."""
    pass


class TaskExecutor:
    """Manages the full lifecycle, reliability, and execution of agent tasks (Phase 8)."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None):
        self.registry = registry or capability_registry_instance
        self._idempotency_cache: Dict[str, TaskExecutionResult] = {}

    def execute_task(
        self,
        request: TaskExecutionRequest,
        db: Session,
    ) -> TaskExecutionResult:
        """Executes a capability task through its complete lifecycle with idempotency and retry protection."""
        # 1. Idempotency Check
        if request.idempotency_key:
            cache_key = f"{request.investigation_id}:{request.idempotency_key}"
            if cache_key in self._idempotency_cache:
                return self._idempotency_cache[cache_key]

        # 2. Capability Lookup & Validation
        cap = self.registry.get(request.capability_name)
        if not cap:
            raise ValueError(f"Capability '{request.capability_name}' is not registered.")

        # 3. Create persistent AgentTask record
        task_id = uuid.uuid4()
        now = datetime.utcnow()
        agent_task = AgentTask(
            id=task_id,
            investigation_id=request.investigation_id,
            worker_type=cap.worker_type,
            status="pending",
            objective=request.objective,
            input_payload=request.input_payload,
            created_at=now,
        )
        db.add(agent_task)
        db.flush()

        # 4. Dependency Validation
        if request.dependency_task_ids:
            for dep_id in request.dependency_task_ids:
                dep_record = TaskDependency(task_id=task_id, depends_on_task_id=dep_id)
                db.add(dep_record)

                # Check if dependency completed
                dep_task = db.query(AgentTask).filter(AgentTask.id == dep_id).first()
                if not dep_task or dep_task.status != "completed":
                    agent_task.status = "blocked"
                    db.commit()
                    return TaskExecutionResult(
                        task_id=task_id,
                        investigation_id=request.investigation_id,
                        capability_name=cap.name,
                        worker_type=cap.worker_type,
                        status="blocked",
                        error_message=f"Blocked on prerequisite task {dep_id} (status: {dep_task.status if dep_task else 'not_found'}).",
                    )

        # 5. Worker Resolution
        worker = get_worker(cap.worker_type)
        if not worker:
            agent_task.status = "failed"
            db.commit()
            raise ValueError(f"Worker of type '{cap.worker_type}' not found in worker registry.")

        # 6. Execution with Retry Loop
        agent_task.status = "running"
        db.commit()

        raw_ctx = request.input_payload.get("context")
        worker_ctx = None
        if isinstance(raw_ctx, dict) and "query" in raw_ctx:
            from app.schemas.contracts import RetrievedContext
            worker_ctx = RetrievedContext(**raw_ctx)
        elif hasattr(raw_ctx, "query"):
            worker_ctx = raw_ctx

        worker_task = WorkerTask(
            task_id=task_id,
            investigation_id=request.investigation_id,
            worker_type=cap.worker_type,
            objective=request.objective,
            context=worker_ctx,
            events=request.input_payload.get("events", []),
            findings=request.input_payload.get("findings", []),
        )

        max_attempts = max(1, cap.max_retries + 1)
        attempt = 0
        last_error: Optional[str] = None
        result: Optional[WorkerResult] = None
        total_latency_ms = 0

        while attempt < max_attempts:
            attempt += 1
            t_start = time.perf_counter()
            try:
                # If human approval is required for response action, enforce approval check
                if cap.requires_human_approval:
                    is_approved = request.input_payload.get("human_approved", False)
                    if not is_approved:
                        agent_task.status = "blocked"
                        db.commit()
                        return TaskExecutionResult(
                            task_id=task_id,
                            investigation_id=request.investigation_id,
                            capability_name=cap.name,
                            worker_type=cap.worker_type,
                            status="blocked",
                            error_message="High-risk response capability requires explicit human-in-the-loop approval.",
                        )

                # Invoke worker
                result = worker.execute(worker_task)
                latency = int((time.perf_counter() - t_start) * 1000)
                total_latency_ms += latency

                # Record successful attempt
                att_rec = TaskAttempt(
                    id=uuid.uuid4(),
                    task_id=task_id,
                    attempt_number=attempt,
                    status="success",
                    latency_ms=latency,
                    created_at=datetime.utcnow(),
                )
                db.add(att_rec)
                break

            except Exception as e:
                latency = int((time.perf_counter() - t_start) * 1000)
                total_latency_ms += latency
                last_error = str(e)
                att_rec = TaskAttempt(
                    id=uuid.uuid4(),
                    task_id=task_id,
                    attempt_number=attempt,
                    status="error",
                    latency_ms=latency,
                    error_message=last_error,
                    created_at=datetime.utcnow(),
                )
                db.add(att_rec)
                if attempt < max_attempts:
                    agent_task.status = "retrying"
                    db.commit()

        # 7. Finalize Task Status
        completed_at = datetime.utcnow()
        if result and result.status in ["success", "completed"]:
            final_status: TaskStatus = "completed"
            output_payload = result.model_dump(mode="json")
            confidence_sig = result.confidence_signal
            error_msg = None
        else:
            final_status = "failed"
            output_payload = None
            confidence_sig = 0.0
            error_msg = last_error or "Worker execution failed"

        agent_task.status = final_status
        agent_task.output_payload = output_payload
        agent_task.completed_at = completed_at
        db.commit()

        exec_result = TaskExecutionResult(
            task_id=task_id,
            investigation_id=request.investigation_id,
            capability_name=cap.name,
            worker_type=cap.worker_type,
            status=final_status,
            output_payload=output_payload,
            confidence_signal=confidence_sig,
            latency_ms=total_latency_ms,
            attempt_count=attempt,
            error_message=error_msg,
            completed_at=completed_at,
        )

        if request.idempotency_key and final_status == "completed":
            cache_key = f"{request.investigation_id}:{request.idempotency_key}"
            self._idempotency_cache[cache_key] = exec_result

        return exec_result


task_executor_instance = TaskExecutor()
