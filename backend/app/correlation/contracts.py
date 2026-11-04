import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field, ConfigDict


class ResolvedEntity(BaseModel):
    """Normalized resolved entity representation."""
    model_config = ConfigDict(extra="allow", from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    entity_type: str  # host, user, ip, process, domain
    identifier: str
    display_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)


class EntityRelationPayload(BaseModel):
    """Directed relationship between two resolved entities."""
    model_config = ConfigDict(extra="allow", from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    source_entity_id: uuid.UUID
    target_entity_id: uuid.UUID
    relationship_type: str  # authenticated_as, executed, communicates_with, spawned, bound_to
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    evidence_event_id: Optional[uuid.UUID] = None
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_to: Optional[datetime] = None


class CorrelatedGroup(BaseModel):
    """Cluster of correlated events and findings representing a potential incident candidate."""
    model_config = ConfigDict(extra="allow", from_attributes=True)

    group_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_ids: List[uuid.UUID] = Field(default_factory=list)
    entity_ids: List[uuid.UUID] = Field(default_factory=list)
    entity_identifiers: List[str] = Field(default_factory=list)
    time_window_start: datetime
    time_window_end: datetime
    correlation_score: float = Field(ge=0.0, le=1.0)
    severity: str = "medium"
    title: str
    description: str
    mitre_tactics: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
