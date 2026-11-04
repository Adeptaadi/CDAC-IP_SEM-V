import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.investigation import Investigation, InvestigationStateVersion, InvestigationEvent
from app.models.correlation import IncidentCandidate
from app.models.evidence import Evidence, TimelineEvent, Hypothesis
from app.repositories.investigation_repo import InvestigationRepository, OptimisticLockError
from app.investigation.contracts import (
    InvestigationStatus,
    InvestigationCreatePayload,
    InvestigationStructuredState,
)
from app.investigation.state_machine import InvestigationStateMachine, InvalidStateTransitionError


class InvestigationService:
    """Core domain service orchestrating the durable investigation lifecycle and state persistence (Phase 7)."""

    def __init__(self, state_machine: Optional[InvestigationStateMachine] = None):
        self.state_machine = state_machine or InvestigationStateMachine()

    def create_investigation(
        self,
        payload: InvestigationCreatePayload,
        db: Session,
    ) -> Investigation:
        """Creates a new persistent investigation and registers initial version snapshot."""
        now = datetime.utcnow()
        inv = Investigation(
            investigation_id=uuid.uuid4(),
            title=payload.title,
            status=payload.initial_status,
            current_confidence=0.10,
            confidence_state="very_low",
            current_goal=payload.current_goal or "Triage initial telemetry and assess attack hypothesis",
            planning_cycle_count=0,
            state_version=1,
            triggering_event_id=payload.triggering_event_id,
            incident_candidate_id=payload.incident_candidate_id,
            assigned_analyst_id=payload.assigned_analyst_id,
            created_at=now,
            updated_at=now,
        )
        db.add(inv)
        db.flush()

        # Initial structured state snapshot
        init_state = InvestigationStructuredState(
            facts=[{"event": "Investigation created", "timestamp": now.isoformat()}],
            completion_conditions={"max_cycles": 10, "target_confidence": 0.85},
        )
        version_snapshot = InvestigationStateVersion(
            id=uuid.uuid4(),
            investigation_id=inv.investigation_id,
            version_number=1,
            state_snapshot=init_state.model_dump(),
            confidence=0.10,
            cycle_number=0,
            created_at=now,
        )
        db.add(version_snapshot)

        # Log creation event
        inv_event = InvestigationEvent(
            id=uuid.uuid4(),
            investigation_id=inv.investigation_id,
            event_type="investigation_created",
            summary=f"Investigation '{inv.title}' initiated with status '{inv.status}'.",
        )
        db.add(inv_event)
        db.commit()
        db.refresh(inv)
        return inv

    def create_from_candidate(
        self,
        candidate_id: uuid.UUID,
        db: Session,
        analyst_id: Optional[uuid.UUID] = None,
    ) -> Investigation:
        """Promotes an IncidentCandidate into a full active Investigation."""
        candidate = db.query(IncidentCandidate).filter(IncidentCandidate.id == candidate_id).first()
        if not candidate:
            raise ValueError(f"IncidentCandidate {candidate_id} not found")

        candidate.status = "promoted"
        meta = candidate.candidate_metadata or {}

        payload = InvestigationCreatePayload(
            title=f"Investigation: {candidate.title}",
            current_goal=f"Investigate elevated incident candidate with severity {candidate.severity}",
            incident_candidate_id=candidate.id,
            assigned_analyst_id=analyst_id,
            initial_status="investigating",
            metadata=meta,
        )
        inv = self.create_investigation(payload, db=db)

        # Populate initial entities from candidate
        entity_ids = meta.get("entity_identifiers", [])
        if entity_ids:
            event_log = InvestigationEvent(
                id=uuid.uuid4(),
                investigation_id=inv.investigation_id,
                event_type="candidate_promoted",
                summary=f"Promoted from IncidentCandidate {candidate.id} involving entities: {', '.join(entity_ids[:5])}.",
            )
            db.add(event_log)
            db.commit()

        return inv

    def transition_status(
        self,
        investigation_id: uuid.UUID,
        target_status: InvestigationStatus,
        db: Session,
        reason: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> Investigation:
        """Validates and executes lifecycle state transition with optimistic locking."""
        inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
        if not inv:
            raise ValueError(f"Investigation {investigation_id} not found")

        # Validate state machine rules
        self.state_machine.validate_transition(inv.status, target_status)

        # Validate version if optimistic concurrency expected
        if expected_version is not None and inv.state_version != expected_version:
            raise OptimisticLockError(
                f"Version conflict on investigation {investigation_id}: "
                f"expected {expected_version}, current is {inv.state_version}."
            )

        old_status = inv.status
        inv.status = target_status
        inv.state_version += 1
        inv.updated_at = datetime.utcnow()

        if target_status in ["completed", "closed"]:
            inv.closed_at = datetime.utcnow()

        # Record version snapshot
        snapshot = InvestigationStateVersion(
            id=uuid.uuid4(),
            investigation_id=inv.investigation_id,
            version_number=inv.state_version,
            state_snapshot={
                "status": target_status,
                "previous_status": old_status,
                "reason": reason,
                "transitioned_at": datetime.utcnow().isoformat(),
            },
            confidence=inv.current_confidence,
            cycle_number=inv.planning_cycle_count,
            created_at=datetime.utcnow(),
        )
        db.add(snapshot)

        # Log event
        inv_event = InvestigationEvent(
            id=uuid.uuid4(),
            investigation_id=inv.investigation_id,
            event_type="status_transition",
            summary=f"Status transitioned from '{old_status}' to '{target_status}'. Reason: {reason or 'N/A'}.",
        )
        db.add(inv_event)
        db.commit()
        db.refresh(inv)
        return inv

    def pause(self, investigation_id: uuid.UUID, db: Session, reason: str = "Analyst paused investigation") -> Investigation:
        return self.transition_status(investigation_id, "paused", db, reason=reason)

    def resume(self, investigation_id: uuid.UUID, db: Session, reason: str = "Analyst resumed investigation") -> Investigation:
        return self.transition_status(investigation_id, "investigating", db, reason=reason)

    def cancel(self, investigation_id: uuid.UUID, db: Session, reason: str = "Analyst cancelled investigation") -> Investigation:
        return self.transition_status(investigation_id, "cancelled", db, reason=reason)

    def add_evidence(
        self,
        investigation_id: uuid.UUID,
        source_type: str,
        description: str,
        db: Session,
        entity_refs: Optional[Dict[str, Any]] = None,
        produced_by_worker: Optional[str] = None,
        source_ref: Optional[str] = None,
    ) -> Evidence:
        """Attaches durable evidence to an investigation."""
        ev = Evidence(
            evidence_id=uuid.uuid4(),
            investigation_id=investigation_id,
            source_type=source_type,
            source_ref=source_ref,
            description=description,
            entity_refs=entity_refs or {},
            produced_by_worker=produced_by_worker,
            created_at=datetime.utcnow(),
        )
        db.add(ev)
        db.commit()
        db.refresh(ev)
        return ev

    def add_hypothesis(
        self,
        investigation_id: uuid.UUID,
        label: str,
        confidence: float,
        db: Session,
        mitre_technique_ids: Optional[List[str]] = None,
    ) -> Hypothesis:
        """Registers a working threat hypothesis for an investigation."""
        hyp = Hypothesis(
            hypothesis_id=uuid.uuid4(),
            investigation_id=investigation_id,
            label=label,
            confidence=confidence,
            status="active",
            mitre_technique_ids=mitre_technique_ids or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(hyp)
        db.commit()
        db.refresh(hyp)
        return hyp

    def add_timeline_event(
        self,
        investigation_id: uuid.UUID,
        summary: str,
        occurred_at: datetime,
        db: Session,
        mitre_technique_id: Optional[str] = None,
        evidence_id: Optional[uuid.UUID] = None,
    ) -> TimelineEvent:
        """Appends a reconstructed event onto the investigation timeline."""
        count = db.query(TimelineEvent).filter(TimelineEvent.investigation_id == investigation_id).count()
        tle = TimelineEvent(
            event_id=uuid.uuid4(),
            investigation_id=investigation_id,
            evidence_id=evidence_id,
            occurred_at=occurred_at,
            event_summary=summary,
            mitre_technique_id=mitre_technique_id,
            sequence_position=count + 1,
        )
        db.add(tle)
        db.commit()
        db.refresh(tle)
        return tle

    def get_timeline(self, investigation_id: uuid.UUID, db: Session) -> List[TimelineEvent]:
        """Retrieves chronological timeline events for an investigation."""
        return (
            db.query(TimelineEvent)
            .filter(TimelineEvent.investigation_id == investigation_id)
            .order_by(TimelineEvent.sequence_position.asc(), TimelineEvent.occurred_at.asc())
            .all()
        )


investigation_service_instance = InvestigationService()
