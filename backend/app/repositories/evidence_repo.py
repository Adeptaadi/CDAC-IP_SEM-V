import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.evidence import Evidence, TimelineEvent, Hypothesis, HypothesisEvidence
from app.repositories.base import BaseRepository


class EvidenceRepository(BaseRepository[Evidence]):
    def __init__(self, db: Session):
        super().__init__(Evidence, db)

    def add_evidence(
        self,
        investigation_id: uuid.UUID,
        source_type: str,
        description: str,
        entity_refs: Optional[Dict[str, Any]] = None,
        source_ref: Optional[str] = None,
        produced_by_worker: Optional[str] = None,
        corroborated_by: Optional[List[uuid.UUID]] = None,
    ) -> Evidence:
        ev = Evidence(
            investigation_id=investigation_id,
            source_type=source_type,
            description=description,
            entity_refs=entity_refs or {},
            source_ref=source_ref,
            produced_by_worker=produced_by_worker,
            corroborated_by=corroborated_by or [],
        )
        self.db.add(ev)
        self.db.flush()
        return ev

    def add_timeline_event(
        self,
        investigation_id: uuid.UUID,
        event_summary: str,
        occurred_at: Optional[datetime] = None,
        evidence_id: Optional[uuid.UUID] = None,
        mitre_technique_id: Optional[str] = None,
        sequence_position: Optional[int] = None,
    ) -> TimelineEvent:
        te = TimelineEvent(
            investigation_id=investigation_id,
            evidence_id=evidence_id,
            occurred_at=occurred_at or datetime.utcnow(),
            event_summary=event_summary,
            mitre_technique_id=mitre_technique_id,
            sequence_position=sequence_position,
        )
        self.db.add(te)
        self.db.flush()
        return te

    def upsert_hypothesis(
        self,
        investigation_id: uuid.UUID,
        label: str,
        confidence: float,
        status: str = "active",
        mitre_technique_ids: Optional[List[str]] = None,
    ) -> Hypothesis:
        hypo = self.db.query(Hypothesis).filter(
            Hypothesis.investigation_id == investigation_id,
            Hypothesis.label == label,
        ).first()

        if not hypo:
            hypo = Hypothesis(
                investigation_id=investigation_id,
                label=label,
                confidence=confidence,
                status=status,
                mitre_technique_ids=mitre_technique_ids or [],
            )
            self.db.add(hypo)
        else:
            hypo.confidence = confidence
            hypo.status = status
            if mitre_technique_ids:
                hypo.mitre_technique_ids = mitre_technique_ids
            hypo.updated_at = datetime.utcnow()

        self.db.flush()
        return hypo

    def link_hypothesis_evidence(
        self,
        hypothesis_id: uuid.UUID,
        evidence_id: uuid.UUID,
        stance: str = "supports",
        weight: float = 1.0,
    ) -> HypothesisEvidence:
        link = self.db.query(HypothesisEvidence).filter(
            HypothesisEvidence.hypothesis_id == hypothesis_id,
            HypothesisEvidence.evidence_id == evidence_id,
        ).first()

        if not link:
            link = HypothesisEvidence(
                hypothesis_id=hypothesis_id,
                evidence_id=evidence_id,
                stance=stance,
                weight=weight,
            )
            self.db.add(link)
        else:
            link.stance = stance
            link.weight = weight

        self.db.flush()
        return link
