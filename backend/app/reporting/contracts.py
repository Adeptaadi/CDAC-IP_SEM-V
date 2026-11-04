import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ReportSectionPayload(BaseModel):
    """Structured section within an incident investigation report."""
    title: str
    order: int
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentReportPayload(BaseModel):
    """Complete analyst-ready incident investigation report (Phase 11)."""
    model_config = ConfigDict(extra="allow", from_attributes=True)

    report_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    investigation_id: uuid.UUID
    title: str
    severity: str
    incident_classification: str
    executive_summary: str
    technical_body: str
    final_confidence: float = Field(ge=0.0, le=1.0)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    affected_entities: Dict[str, List[str]] = Field(default_factory=dict)
    detection_findings: List[Dict[str, Any]] = Field(default_factory=list)
    hypotheses: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_citations: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_limitations: List[str] = Field(default_factory=list)
    sections: List[ReportSectionPayload] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by_user_id: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None


class ReportValidationResult(BaseModel):
    """Validation audit of report completeness, provenance, and structure."""
    is_valid: bool
    missing_sections: List[str] = Field(default_factory=list)
    has_citations: bool
    has_evidence: bool
    confidence_stated: bool
    validation_notes: List[str] = Field(default_factory=list)
