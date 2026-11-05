import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.investigation import Investigation, InvestigationEvent, InvestigationStateVersion
from app.investigation import (
    InvestigationCreatePayload,
    InvestigationTransitionPayload,
    investigation_service_instance,
    workspace_projection_service_instance,
    InvalidStateTransitionError,
)
from app.schemas.workspace_projection import InvestigationWorkspaceProjection
from app.repositories.investigation_repo import OptimisticLockError

router = APIRouter(prefix="/api/investigations", tags=["Investigation Management"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_investigation(
    payload: InvestigationCreatePayload,
    db: Session = Depends(get_db),
):
    """Initiates a new investigation with durable initial state and version tracking (Phase 7)."""
    inv = investigation_service_instance.create_investigation(payload, db=db)
    return {
        "status": "created",
        "investigation_id": str(inv.investigation_id),
        "title": inv.title,
        "lifecycle_status": inv.status,
        "state_version": inv.state_version,
    }


@router.post("/from-candidate/{candidate_id}", status_code=status.HTTP_201_CREATED)
def promote_candidate_to_investigation(
    candidate_id: uuid.UUID,
    analyst_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
):
    """Promotes an IncidentCandidate into an active investigation."""
    try:
        inv = investigation_service_instance.create_from_candidate(candidate_id, db=db, analyst_id=analyst_id)
        return {
            "status": "promoted",
            "investigation_id": str(inv.investigation_id),
            "candidate_id": str(candidate_id),
            "title": inv.title,
            "lifecycle_status": inv.status,
            "state_version": inv.state_version,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("")
def list_investigations(
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Lists investigations with optional status filter."""
    query = db.query(Investigation)
    if status_filter:
        query = query.filter(Investigation.status == status_filter)
    results = query.order_by(Investigation.created_at.desc()).limit(limit).all()
    return [
        {
            "investigation_id": str(inv.investigation_id),
            "title": inv.title,
            "status": inv.status,
            "confidence": float(inv.current_confidence),
            "confidence_state": inv.confidence_state,
            "state_version": inv.state_version,
            "planning_cycle_count": inv.planning_cycle_count,
            "created_at": inv.created_at.isoformat(),
            "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        }
        for inv in results
    ]


@router.get("/{investigation_id}")
def get_investigation_details(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieves full details of an investigation."""
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {
        "investigation_id": str(inv.investigation_id),
        "title": inv.title,
        "status": inv.status,
        "confidence": float(inv.current_confidence),
        "confidence_state": inv.confidence_state,
        "current_goal": inv.current_goal,
        "state_version": inv.state_version,
        "planning_cycle_count": inv.planning_cycle_count,
        "incident_candidate_id": str(inv.incident_candidate_id) if inv.incident_candidate_id else None,
        "triggering_event_id": str(inv.triggering_event_id) if inv.triggering_event_id else None,
        "created_at": inv.created_at.isoformat(),
        "updated_at": inv.updated_at.isoformat() if inv.updated_at else None,
        "closed_at": inv.closed_at.isoformat() if inv.closed_at else None,
    }


@router.get("/{investigation_id}/workspace", response_model=InvestigationWorkspaceProjection)
def get_investigation_workspace(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieves the unified Agentic Investigation Workspace projection (P0)."""
    try:
        return workspace_projection_service_instance.build_workspace_projection(investigation_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{investigation_id}/transition")
def transition_investigation(
    investigation_id: uuid.UUID,
    payload: InvestigationTransitionPayload,
    db: Session = Depends(get_db),
):
    """Executes state machine transition with optimistic locking."""
    try:
        inv = investigation_service_instance.transition_status(
            investigation_id=investigation_id,
            target_status=payload.target_status,
            db=db,
            reason=payload.reason,
            expected_version=payload.expected_version,
        )
        return {
            "status": "transitioned",
            "investigation_id": str(inv.investigation_id),
            "new_status": inv.status,
            "state_version": inv.state_version,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OptimisticLockError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{investigation_id}/pause")
def pause_investigation(
    investigation_id: uuid.UUID,
    reason: str = "Analyst requested pause",
    db: Session = Depends(get_db),
):
    try:
        inv = investigation_service_instance.pause(investigation_id, db=db, reason=reason)
        return {"status": "paused", "investigation_id": str(inv.investigation_id), "state_version": inv.state_version}
    except (ValueError, InvalidStateTransitionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{investigation_id}/resume")
def resume_investigation(
    investigation_id: uuid.UUID,
    reason: str = "Analyst requested resume",
    db: Session = Depends(get_db),
):
    try:
        inv = investigation_service_instance.resume(investigation_id, db=db, reason=reason)
        return {"status": "resumed", "investigation_id": str(inv.investigation_id), "state_version": inv.state_version}
    except (ValueError, InvalidStateTransitionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{investigation_id}/cancel")
def cancel_investigation(
    investigation_id: uuid.UUID,
    reason: str = "Analyst requested cancellation",
    db: Session = Depends(get_db),
):
    try:
        inv = investigation_service_instance.cancel(investigation_id, db=db, reason=reason)
        return {"status": "cancelled", "investigation_id": str(inv.investigation_id), "state_version": inv.state_version}
    except (ValueError, InvalidStateTransitionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{investigation_id}/timeline")
def get_timeline(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieves chronological timeline reconstruction."""
    events = investigation_service_instance.get_timeline(investigation_id, db=db)
    return [
        {
            "event_id": str(e.event_id),
            "sequence_position": e.sequence_position,
            "occurred_at": e.occurred_at.isoformat(),
            "summary": e.event_summary,
            "mitre_technique_id": e.mitre_technique_id,
            "evidence_id": str(e.evidence_id) if e.evidence_id else None,
        }
        for e in events
    ]


@router.get("/{investigation_id}/events")
def get_investigation_events(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieves audit trail of investigation events."""
    events = (
        db.query(InvestigationEvent)
        .filter(InvestigationEvent.investigation_id == investigation_id)
        .order_by(InvestigationEvent.created_at.asc())
        .all()
    )
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "summary": e.summary,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.get("/{investigation_id}/snapshots")
def get_investigation_snapshots(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieves all version snapshots of investigation state."""
    snapshots = (
        db.query(InvestigationStateVersion)
        .filter(InvestigationStateVersion.investigation_id == investigation_id)
        .order_by(InvestigationStateVersion.version_number.asc())
        .all()
    )
    return [
        {
            "version_number": s.version_number,
            "confidence": float(s.confidence),
            "cycle_number": s.cycle_number,
            "state_snapshot": s.state_snapshot,
            "created_at": s.created_at.isoformat(),
        }
        for s in snapshots
    ]
