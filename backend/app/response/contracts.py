import uuid
from typing import Literal, Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

SimulationActionType = Literal[
    "isolate_endpoint",
    "block_ip",
    "suspend_user",
    "terminate_process",
    "quarantine_file",
]

ReviewDecision = Literal["approved", "rejected", "request_changes"]


class SimulationRequest(BaseModel):
    """Request to safely simulate an active response action without operational disruption."""
    model_config = ConfigDict(extra="allow")

    investigation_id: uuid.UUID
    action_type: SimulationActionType
    target_identifier: str
    target_entity_id: Optional[uuid.UUID] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SimulationResult(BaseModel):
    """Calculated blast-radius and safety impact from simulated response action."""
    model_config = ConfigDict(extra="allow")

    simulation_id: uuid.UUID
    investigation_id: uuid.UUID
    action: str
    target_identifier: str
    status: str = "simulated"
    blast_radius: str
    service_disruption: str
    safety_assessment: str
    rollback_plan: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    simulated_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewSubmissionPayload(BaseModel):
    """Analyst review decision on a pending human review item."""
    decision: ReviewDecision
    analyst_comments: str
    analyst_id: Optional[uuid.UUID] = None
