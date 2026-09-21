from uuid import UUID, uuid4
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

WorkerType = Literal["detection", "correlation", "investigation", "reporting", "response"]


class RetrievedChunk(BaseModel):
    doc_id: UUID
    category: str
    text: str
    similarity_score: float
    reliability_weight: float


class RetrievedContext(BaseModel):
    query: str
    chunks: List[RetrievedChunk] = Field(default_factory=list)
    assembled_at: datetime = Field(default_factory=datetime.utcnow)


class WorkerTask(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    investigation_id: UUID
    worker_type: WorkerType
    objective: str  # e.g., "assess PowerShell events for T1059"
    evidence_refs: List[UUID] = Field(default_factory=list)
    context: Optional[RetrievedContext] = None
    priority: int = 1


class Finding(BaseModel):
    description: str
    entity_refs: Dict[str, List[str]] = Field(default_factory=dict)  # {"hosts": [], "users": [], "ips": []}
    mitre_technique_id: Optional[str] = None
    supporting_evidence_ids: List[UUID] = Field(default_factory=list)


class WorkerResult(BaseModel):
    task_id: UUID
    worker_type: WorkerType
    status: Literal["success", "partial", "failed"]
    findings: List[Finding] = Field(default_factory=list)
    confidence_signal: float = 0.5  # worker confidence (0-1) for Worker Agreement factor
    new_evidence: List[Finding] = Field(default_factory=list)
    hypothesis_updates: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning_summary: str  # 1-3 analyst-facing sentences
    next_task_suggestion: Optional[str] = None


# Telemetry Schema
class TelemetryEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str  # e.g., 'sysmon', 'winevent', 'zeek'
    event_type: str  # e.g., 'process_creation', 'network_connection', 'auth_failure'
    host: Optional[str] = None
    user: Optional[str] = None
    src_ip: Optional[str] = None
    dest_ip: Optional[str] = None
    process_name: Optional[str] = None
    command_line: Optional[str] = None
    raw_log: Dict[str, Any] = Field(default_factory=dict)


# API response / request schemas
class InvestigationCreate(BaseModel):
    title: str
    triggering_event_id: Optional[UUID] = None
    initial_goal: Optional[str] = None


class InvestigationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    investigation_id: UUID
    title: str
    status: str
    current_confidence: float
    confidence_state: str
    current_goal: Optional[str] = None
    planning_cycle_count: int
    created_at: datetime
    updated_at: datetime
