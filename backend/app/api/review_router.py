import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.response import HumanReview
from app.response import (
    SimulationRequest,
    SimulationResult,
    ReviewSubmissionPayload,
    response_simulation_service,
    human_review_service,
)

review_router = APIRouter(prefix="/api/reviews", tags=["Human Review & Response Simulation"])


@review_router.get("/pending")
def list_pending_reviews(db: Session = Depends(get_db)):
    """Lists all active human reviews requiring analyst adjudication (Phase 11)."""
    reviews = human_review_service.list_pending_reviews(db=db)
    return [
        {
            "review_id": str(r.id),
            "investigation_id": str(r.investigation_id),
            "requested_action": r.requested_action,
            "risk_level": r.risk_level,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
        }
        for r in reviews
    ]


@review_router.post("/{review_id}/decision")
def process_review_decision(
    review_id: uuid.UUID,
    payload: ReviewSubmissionPayload,
    db: Session = Depends(get_db),
):
    """Submits analyst approval, rejection, or change request on a review item."""
    try:
        updated = human_review_service.process_review(review_id=review_id, payload=payload, db=db)
        return {
            "status": "processed",
            "review_id": str(updated.id),
            "decision": updated.status,
            "reviewed_at": updated.reviewed_at.isoformat() if updated.reviewed_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@review_router.post("/simulate", response_model=SimulationResult)
def simulate_response_action(
    payload: SimulationRequest,
    db: Session = Depends(get_db),
):
    """Simulates containment action, computing blast-radius, disruption, and rollback without operational risk."""
    return response_simulation_service.simulate(payload, db=db)
