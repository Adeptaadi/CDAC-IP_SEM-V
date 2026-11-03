import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.investigation import Investigation, InvestigationStateVersion, InvestigationEvent
from app.repositories.base import BaseRepository


class OptimisticLockError(Exception):
    """Raised when an investigation state update encounters a version mismatch."""
    pass


class InvestigationRepository(BaseRepository[Investigation]):
    def __init__(self, db: Session):
        super().__init__(Investigation, db)

    def create_investigation(
        self,
        title: str,
        current_goal: Optional[str] = None,
        triggering_event_id: Optional[uuid.UUID] = None,
        incident_candidate_id: Optional[uuid.UUID] = None,
        assigned_analyst_id: Optional[uuid.UUID] = None,
    ) -> Investigation:
        inv = Investigation(
            title=title,
            status="active",
            current_confidence=0.10,
            confidence_state="very_low",
            current_goal=current_goal or "Triage initial telemetry and evaluate threat hypotheses",
            planning_cycle_count=0,
            state_version=1,
            triggering_event_id=triggering_event_id,
            incident_candidate_id=incident_candidate_id,
            assigned_analyst_id=assigned_analyst_id,
        )
        self.db.add(inv)
        self.db.flush()

        # Record initial version snapshot
        snapshot = InvestigationStateVersion(
            investigation_id=inv.investigation_id,
            version_number=1,
            state_snapshot={
                "confidence": 0.10,
                "confidence_state": "very_low",
                "cycle_number": 0,
                "status": "active",
                "goal": inv.current_goal,
            },
            confidence=0.10,
            cycle_number=0,
        )
        self.db.add(snapshot)
        self.db.flush()
        return inv

    def update_state_optimistic(
        self,
        investigation_id: uuid.UUID,
        expected_version: int,
        confidence: float,
        confidence_state: str,
        cycle_number: int,
        status: Optional[str] = None,
        current_goal: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Investigation:
        """Atomically updates investigation state, strictly validating version concurrency."""
        inv = self.db.query(Investigation).filter(
            Investigation.investigation_id == investigation_id
        ).with_for_update().first()

        if not inv:
            raise ValueError(f"Investigation {investigation_id} not found")

        if inv.state_version != expected_version:
            raise OptimisticLockError(
                f"Concurrent modification detected on investigation {investigation_id}: "
                f"expected version {expected_version}, current version is {inv.state_version}."
            )

        new_version = expected_version + 1
        inv.current_confidence = confidence
        inv.confidence_state = confidence_state
        inv.planning_cycle_count = cycle_number
        inv.state_version = new_version
        inv.updated_at = datetime.utcnow()

        if status:
            inv.status = status
            if status in ["completed", "closed_no_threat"]:
                inv.closed_at = datetime.utcnow()
        if current_goal:
            inv.current_goal = current_goal

        # Create persistent state version
        version_rec = InvestigationStateVersion(
            investigation_id=inv.investigation_id,
            version_number=new_version,
            state_snapshot={
                "confidence": float(confidence),
                "confidence_state": confidence_state,
                "cycle_number": cycle_number,
                "status": inv.status,
                "goal": inv.current_goal,
            },
            confidence=confidence,
            cycle_number=cycle_number,
        )
        self.db.add(version_rec)

        # Record investigation event log
        event_rec = InvestigationEvent(
            investigation_id=inv.investigation_id,
            event_type="STATE_TRANSITION",
            summary=summary or f"Investigation advanced to cycle {cycle_number} (confidence: {confidence:.2f})",
            details={
                "version_before": expected_version,
                "version_after": new_version,
                "confidence": confidence,
                "confidence_state": confidence_state,
            },
        )
        self.db.add(event_rec)
        self.db.flush()
        return inv

    def list_active(self) -> List[Investigation]:
        return self.db.query(Investigation).filter(
            Investigation.status.in_(["active", "escalated"])
        ).order_by(Investigation.updated_at.desc()).all()
