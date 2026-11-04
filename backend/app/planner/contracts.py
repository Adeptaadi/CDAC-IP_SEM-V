import uuid
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

PlannerDecisionType = Literal[
    "continue_investigation",
    "replan",
    "request_human_review",
    "complete_investigation",
    "escalate",
    "blocked",
]


class PlannerDecisionPayload(BaseModel):
    """Structured decision produced by the autonomous Planner (Phase 9)."""
    model_config = ConfigDict(extra="allow")

    decision_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    investigation_id: uuid.UUID
    cycle_number: int
    decision_type: PlannerDecisionType
    selected_capability: Optional[str] = None
    selected_worker: str
    selection_score: float = 0.5
    confidence_before: float
    target_confidence: float = 0.85
    reasoning: str
    suggested_task_input: Dict[str, Any] = Field(default_factory=dict)
    unresolved_questions: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class InvestigationGraphState(BaseModel):
    """State schema passed through the non-linear LangGraph-style workflow nodes."""
    model_config = ConfigDict(extra="allow")

    investigation_id: uuid.UUID
    cycle_number: int = 0
    current_status: str = "investigating"
    current_confidence: float = 0.10
    current_goal: str = ""
    facts: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    last_decision: Optional[PlannerDecisionPayload] = None
    last_task_output: Optional[Dict[str, Any]] = None
    execution_history: List[str] = Field(default_factory=list)
    requires_human_review: bool = False
    termination_reason: Optional[str] = None
