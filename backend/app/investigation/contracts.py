import uuid
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


InvestigationStatus = Literal[
    "created",
    "queued",
    "initializing",
    "investigating",
    "awaiting_review",
    "paused",
    "blocked",
    "completed",
    "closed",
    "failed",
    "cancelled",
]


class InvestigationStructuredState(BaseModel):
    """Rich structured in-memory and serialized investigation state (IS §7.3)."""
    model_config = ConfigDict(extra="allow", from_attributes=True)

    facts: List[Dict[str, Any]] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    evidence_refs: List[uuid.UUID] = Field(default_factory=list)
    knowledge_refs: List[str] = Field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    task_history: List[str] = Field(default_factory=list)
    planner_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    execution_constraints: Dict[str, Any] = Field(default_factory=dict)
    completion_conditions: Dict[str, Any] = Field(default_factory=dict)


class InvestigationCreatePayload(BaseModel):
    """Payload to initiate a new investigation."""
    model_config = ConfigDict(extra="allow")

    title: str
    current_goal: Optional[str] = None
    incident_candidate_id: Optional[uuid.UUID] = None
    triggering_event_id: Optional[uuid.UUID] = None
    assigned_analyst_id: Optional[uuid.UUID] = None
    initial_status: InvestigationStatus = "created"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InvestigationTransitionPayload(BaseModel):
    """Request payload to advance an investigation's lifecycle status."""
    target_status: InvestigationStatus
    reason: Optional[str] = None
    expected_version: Optional[int] = None
