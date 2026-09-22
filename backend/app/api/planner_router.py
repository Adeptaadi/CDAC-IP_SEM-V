from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any

from app.database import get_db
from app.models import Investigation, PlannerDecision, Evidence, TimelineEvent, Hypothesis, Report
from app.planner.engine import planner_engine

planner_router = APIRouter(prefix="/api/planner", tags=["Planner Orchestrator"])


@planner_router.post("/investigations/{investigation_id}/step")
def execute_planning_step(investigation_id: UUID, db: Session = Depends(get_db)):
    """Executes a single autonomous planning cycle for the investigation."""
    try:
        result = planner_engine.run_cycle(investigation_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning cycle failed: {str(e)}")


@planner_router.post("/investigations/{investigation_id}/run")
def run_autonomous_investigation(investigation_id: UUID, max_steps: int = 10, db: Session = Depends(get_db)):
    """Runs the continuous multi-cycle autonomous planning loop until completion or stagnation."""
    try:
        result = planner_engine.run_autonomous(investigation_id, db, max_steps=max_steps)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autonomous loop failed: {str(e)}")


@planner_router.post("/investigations/{investigation_id}/pause")
def pause_investigation(investigation_id: UUID, db: Session = Depends(get_db)):
    """Pauses an active investigation."""
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    inv.status = "paused"
    db.commit()
    return {"status": "paused", "investigation_id": str(investigation_id)}


@planner_router.post("/investigations/{investigation_id}/resume")
def resume_investigation(investigation_id: UUID, db: Session = Depends(get_db)):
    """Resumes a paused investigation."""
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    inv.status = "active"
    db.commit()
    return {"status": "active", "investigation_id": str(investigation_id)}


@planner_router.get("/investigations/{investigation_id}/decisions")
def get_planner_decisions(investigation_id: UUID, db: Session = Depends(get_db)):
    """Returns the immutable audit trail of planner decisions (IS §2)."""
    decisions = (
        db.query(PlannerDecision)
        .filter(PlannerDecision.investigation_id == investigation_id)
        .order_by(PlannerDecision.cycle_number.asc())
        .all()
    )
    return [
        {
            "decision_id": str(d.decision_id),
            "cycle_number": d.cycle_number,
            "selected_worker": d.selected_worker,
            "selection_score": float(d.selection_score) if d.selection_score else None,
            "knowledge_need": d.knowledge_need,
            "confidence_before": float(d.confidence_before),
            "confidence_after": float(d.confidence_after),
            "explanation_summary": d.explanation_summary,
            "created_at": d.created_at.isoformat(),
        }
        for d in decisions
    ]


@planner_router.get("/investigations/{investigation_id}/state")
def get_investigation_full_state(investigation_id: UUID, db: Session = Depends(get_db)):
    """Returns a unified snapshot of the investigation state (timeline, evidence, hypotheses, reports)."""
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    evidence = db.query(Evidence).filter(Evidence.investigation_id == investigation_id).all()
    timeline = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.investigation_id == investigation_id)
        .order_by(TimelineEvent.sequence_position.asc())
        .all()
    )
    hypotheses = db.query(Hypothesis).filter(Hypothesis.investigation_id == investigation_id).all()
    reports = db.query(Report).filter(Report.investigation_id == investigation_id).all()

    return {
        "investigation_id": str(inv.investigation_id),
        "title": inv.title,
        "status": inv.status,
        "confidence": float(inv.current_confidence),
        "confidence_state": inv.confidence_state,
        "current_goal": inv.current_goal,
        "planning_cycles": inv.planning_cycle_count,
        "evidence_count": len(evidence),
        "timeline_events": [
            {
                "event_id": str(t.event_id),
                "summary": t.event_summary,
                "mitre_technique_id": t.mitre_technique_id,
                "sequence_position": t.sequence_position,
                "occurred_at": t.occurred_at.isoformat(),
            }
            for t in timeline
        ],
        "hypotheses": [
            {
                "hypothesis_id": str(h.hypothesis_id),
                "label": h.label,
                "status": h.status,
                "confidence": float(h.confidence),
                "mitre_technique_ids": h.mitre_technique_ids,
            }
            for h in hypotheses
        ],
        "reports": [
            {
                "report_id": str(r.report_id),
                "executive_summary": r.executive_summary,
                "technical_body": r.technical_body,
                "final_confidence": float(r.final_confidence),
                "generated_at": r.generated_at.isoformat(),
            }
            for r in reports
        ],
    }
