import uuid
from typing import Literal, Optional, List, Dict, Any, Callable
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


TaskStatus = Literal[
    "proposed",
    "validating",
    "pending",
    "queued",
    "running",
    "completed",
    "failed",
    "blocked",
    "retrying",
    "cancelled",
]

RiskLevel = Literal["low", "medium", "high", "critical"]


class CapabilityDefinition(BaseModel):
    """Specification of a discrete agent capability registered in the system (Phase 8)."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    name: str
    version: str = "1.0.0"
    description: str
    capability_type: str  # detection, correlation, investigation, reporting, response, knowledge
    worker_type: str      # maps to BaseWorker worker_type
    risk_level: RiskLevel = "low"
    required_roles: List[str] = Field(default_factory=lambda: ["analyst"])
    timeout_seconds: int = 60
    max_retries: int = 2
    requires_human_approval: bool = False
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)


class TaskExecutionRequest(BaseModel):
    """Request to schedule and execute an agent task."""
    model_config = ConfigDict(extra="allow")

    investigation_id: uuid.UUID
    capability_name: str
    objective: str
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None
    dependency_task_ids: List[uuid.UUID] = Field(default_factory=list)


class TaskExecutionResult(BaseModel):
    """Validated structured result from task execution."""
    model_config = ConfigDict(extra="allow")

    task_id: uuid.UUID
    investigation_id: uuid.UUID
    capability_name: str
    worker_type: str
    status: TaskStatus
    output_payload: Optional[Dict[str, Any]] = None
    confidence_signal: float = 0.5
    latency_ms: int = 0
    attempt_count: int = 1
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None
