from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import Investigation
from app.schemas.contracts import (
    InvestigationCreate,
    InvestigationResponse,
    TelemetryEvent,
)
from app.planner.confidence import ConfidenceEngine
from app.planner.selection import InvestigationStateSnapshot, select_worker

router = APIRouter(prefix="/api", tags=["Sentinel Core"])
confidence_engine = ConfidenceEngine()


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Project Sentinel API Gateway",
        "version": "1.0.0"
    }


@router.get("/investigations", response_model=List[InvestigationResponse])
def list_investigations(db: Session = Depends(get_db)):
    return db.query(Investigation).order_by(Investigation.created_at.desc()).all()


@router.post("/investigations", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
def create_investigation(payload: InvestigationCreate, db: Session = Depends(get_db)):
    inv = Investigation(
        title=payload.title,
        status="active",
        current_confidence=0.10,
        confidence_state="very_low",
        current_goal=payload.initial_goal or "Triage initial telemetry and assess attack hypothesis",
        triggering_event_id=payload.triggering_event_id,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.get("/investigations/{investigation_id}", response_model=InvestigationResponse)
def get_investigation(investigation_id: UUID, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


@router.post("/events/ingest")
def ingest_event(event: TelemetryEvent):
    """Ingests normalized telemetry event into the pipeline."""
    return {
        "status": "queued",
        "event_id": str(event.event_id),
        "source": event.source,
        "event_type": event.event_type,
    }


@router.post("/planner/dry-run-selection")
def dry_run_worker_selection(
    untriaged_events: int = 1,
    total_events: int = 5,
    evidence_count: int = 0,
    graph_density: float = 0.0,
    hypotheses_confidences: str = "0.2,0.4",
):
    confs = [float(x.strip()) for x in hypotheses_confidences.split(",") if x.strip()]
    state = InvestigationStateSnapshot(
        investigation_id="dry-run",
        untriaged_event_count=untriaged_events,
        total_event_count=total_events,
        evidence_count=evidence_count,
        graph_density=graph_density,
        hypotheses_confidences=confs,
    )
    worker, score, all_scores = select_worker(state)
    return {
        "selected_worker": worker,
        "utility_score": score,
        "utility_scores": all_scores,
    }
