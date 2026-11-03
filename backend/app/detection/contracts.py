import uuid
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


DetectionMethod = Literal["rule", "ml", "hybrid", "heuristic"]
SeverityLevel = Literal["low", "medium", "high", "critical"]


class DetectionFindingPayload(BaseModel):
    """Canonical contract for findings produced by both rule-based and ML detection engines (Phase 5)."""
    model_config = ConfigDict(extra="allow", from_attributes=True)

    finding_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_id: uuid.UUID
    detection_method: DetectionMethod
    rule_key: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    predicted_class: str
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)
    mitre_tactics: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    explanation: str
    details: Dict[str, Any] = Field(default_factory=dict)
    entity_refs: Dict[str, List[str]] = Field(default_factory=dict)
    detected_at: datetime = Field(default_factory=datetime.utcnow)
