import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.detection.contracts import DetectionFindingPayload
from app.models.correlation import IncidentCandidate


class AlertProjection(BaseModel):
    """Normalized projection of an actionable security alert ready for SOC ingestion and triage."""
    model_config = ConfigDict(extra="allow", from_attributes=True)

    alert_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    candidate_id: uuid.UUID
    title: str
    severity: str
    confidence: float
    mitre_tactics: List[str] = Field(default_factory=list)
    mitre_techniques: List[str] = Field(default_factory=list)
    affected_entities: Dict[str, List[str]] = Field(default_factory=dict)
    source_finding_id: uuid.UUID
    status: str = "open"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertGenerator:
    """Filters, deduplicates, and elevates high-confidence detection findings into Incident Candidates (Phase 5)."""

    def __init__(self, min_confidence: float = 0.70):
        self.min_confidence = min_confidence

    def is_actionable(self, finding: DetectionFindingPayload) -> bool:
        """Determines whether a detection finding qualifies for alert generation."""
        # Critical severity automatically qualifies
        if finding.severity == "critical":
            return True
        # High severity with at least 0.65 confidence
        if finding.severity == "high" and finding.confidence >= 0.65:
            return True
        # Medium or other findings meeting min_confidence threshold
        return finding.confidence >= self.min_confidence

    def create_candidate_from_finding(
        self,
        finding: DetectionFindingPayload,
        db: Optional[Session] = None,
    ) -> Optional[IncidentCandidate]:
        """Elevates an actionable detection finding to an IncidentCandidate."""
        if not self.is_actionable(finding):
            return None

        title = f"Threat Alert: {finding.predicted_class}"
        description = (
            f"Detected by {finding.detection_method.upper()} detection engine. "
            f"{finding.explanation}"
        )

        metadata = {
            "finding_id": str(finding.finding_id),
            "event_id": str(finding.event_id),
            "detection_method": finding.detection_method,
            "rule_key": finding.rule_key,
            "model_name": finding.model_name,
            "mitre_tactics": finding.mitre_tactics,
            "mitre_techniques": finding.mitre_techniques,
            "entity_refs": finding.entity_refs,
            "details": finding.details,
        }

        candidate = IncidentCandidate(
            id=uuid.uuid4(),
            title=title,
            description=description,
            severity=finding.severity,
            confidence=finding.confidence,
            candidate_metadata=metadata,
            status="open",
            created_at=datetime.utcnow(),
        )

        if db is not None:
            db.add(candidate)
            db.commit()
            db.refresh(candidate)

        return candidate

    def process_findings(
        self,
        findings: List[DetectionFindingPayload],
        db: Optional[Session] = None,
    ) -> List[IncidentCandidate]:
        """Batches findings and produces IncidentCandidate records for all qualifying detections."""
        candidates: List[IncidentCandidate] = []
        for finding in findings:
            candidate = self.create_candidate_from_finding(finding, db=db)
            if candidate:
                candidates.append(candidate)
        return candidates


alert_generator_instance = AlertGenerator()
