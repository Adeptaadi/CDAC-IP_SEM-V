import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.detection.contracts import DetectionFindingPayload
from app.detection.rules import rule_engine_instance, RuleEngine
from app.detection.ml import ml_detection_engine_instance, MLDetectionEngine
from app.models.detection import DetectionFinding


class HybridDetectionEngine:
    """Unified Detection Service coordinating Rule-Based and ML-Based engines (Phase 5)."""

    def __init__(self, rule_engine: Optional[RuleEngine] = None, ml_engine: Optional[MLDetectionEngine] = None):
        self.rule_engine = rule_engine or rule_engine_instance
        self.ml_engine = ml_engine or ml_detection_engine_instance

    def analyze_event(self, event: Dict[str, Any]) -> List[DetectionFindingPayload]:
        """Runs both rule-based and ML detection pipelines on an event, fusing corroborated signals."""
        rule_findings = self.rule_engine.evaluate_event(event)
        ml_finding = self.ml_engine.evaluate_event(event)

        if not rule_findings and not ml_finding:
            return []

        if rule_findings and not ml_finding:
            return rule_findings

        if ml_finding and not rule_findings:
            return [ml_finding]

        # Both matched -> Fused Corroborated Hybrid Finding
        fused_findings: List[DetectionFindingPayload] = []
        for rf in rule_findings:
            fused_conf = min(0.99, max(rf.confidence, ml_finding.confidence) + 0.05)
            fused = DetectionFindingPayload(
                finding_id=uuid.uuid4(),
                event_id=rf.event_id,
                detection_method="hybrid",
                rule_key=rf.rule_key,
                model_name=ml_finding.model_name,
                model_version=ml_finding.model_version,
                predicted_class=f"{rf.predicted_class} (Corroborated by ML Flow Anomaly)",
                severity="critical" if (rf.severity == "critical" or ml_finding.severity == "critical") else "high",
                confidence=round(fused_conf, 4),
                mitre_tactics=list(set(rf.mitre_tactics + ml_finding.mitre_tactics)),
                mitre_techniques=list(set(rf.mitre_techniques + ml_finding.mitre_techniques)),
                explanation=f"{rf.explanation} Independent statistical ML anomaly confirmed with score {ml_finding.confidence:.2f}.",
                details={
                    "rule_details": rf.details,
                    "ml_details": ml_finding.details,
                    "fusion_boost": 0.05,
                },
                entity_refs=rf.entity_refs,
                detected_at=datetime.utcnow(),
            )
            fused_findings.append(fused)

        return fused_findings

    def analyze_and_persist_event(
        self,
        event: Dict[str, Any],
        db: Session,
    ) -> List[DetectionFindingPayload]:
        """Analyzes event and records any generated findings in PostgreSQL detection_findings table."""
        findings = self.analyze_event(event)
        for f in findings:
            finding_rec = DetectionFinding(
                id=f.finding_id,
                security_event_id=f.event_id,
                finding_type=f.detection_method,
                confidence=f.confidence,
                severity=f.severity,
                details=f.details,
                detected_at=f.detected_at,
            )
            db.add(finding_rec)

        if findings:
            db.commit()
        return findings


hybrid_detection_engine_instance = HybridDetectionEngine()
