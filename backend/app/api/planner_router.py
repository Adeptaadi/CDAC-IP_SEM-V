from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Dict, Any

from app.database import get_db
from app.models import (
    Investigation, PlannerDecision, Evidence, TimelineEvent,
    Hypothesis, Report, Recommendation, AuditLog
)
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
    """Returns a unified snapshot of the investigation state (timeline, evidence, hypotheses, reports, entity graph)."""
    inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    evidence_records = db.query(Evidence).filter(Evidence.investigation_id == investigation_id).all()
    timeline = (
        db.query(TimelineEvent)
        .filter(TimelineEvent.investigation_id == investigation_id)
        .order_by(TimelineEvent.sequence_position.asc())
        .all()
    )
    hypotheses = db.query(Hypothesis).filter(Hypothesis.investigation_id == investigation_id).all()
    reports = db.query(Report).filter(Report.investigation_id == investigation_id).all()
    
    # Collect all recommendations from reports
    recommendations_list = []
    for r in reports:
        recs = db.query(Recommendation).filter(Recommendation.report_id == r.report_id).all()
        for rec in recs:
            recommendations_list.append({
                "recommendation_id": str(rec.recommendation_id),
                "report_id": str(rec.report_id),
                "action": rec.action,
                "risk_level": rec.risk_level,
                "impact_summary": rec.impact_summary,
                "requires_approval": rec.requires_approval,
                "approval_status": rec.approval_status,
            })

    # Build cross-source entity graph from evidence
    nodes_map: Dict[str, Dict[str, Any]] = {}
    edges_list: List[Dict[str, Any]] = []

    for ev in evidence_records:
        refs = ev.entity_refs or {}
        hosts = refs.get("hosts", [])
        ips = refs.get("ips", [])
        users = refs.get("users", [])
        procs = refs.get("processes", [])

        # Add nodes
        for h in hosts:
            nodes_map[f"host:{h}"] = {"id": f"host:{h}", "label": str(h), "type": "host"}
        for ip in ips:
            nodes_map[f"ip:{ip}"] = {"id": f"ip:{ip}", "label": str(ip), "type": "ip"}
        for u in users:
            nodes_map[f"user:{u}"] = {"id": f"user:{u}", "label": str(u), "type": "user"}
        for p in procs:
            nodes_map[f"proc:{p}"] = {"id": f"proc:{p}", "label": str(p), "type": "process"}

        # Link related entities from this evidence
        all_nodes = [f"host:{h}" for h in hosts] + [f"ip:{ip}" for ip in ips] + [f"user:{u}" for u in users] + [f"proc:{p}" for p in procs]
        for i in range(len(all_nodes)):
            for j in range(i + 1, len(all_nodes)):
                edges_list.append({
                    "source": all_nodes[i],
                    "target": all_nodes[j],
                    "evidence_id": str(ev.evidence_id),
                })

    num_nodes = len(nodes_map)
    graph_density = round(len(edges_list) / max(1, num_nodes * (num_nodes - 1) / 2), 3) if num_nodes > 1 else 0.0

    return {
        "investigation_id": str(inv.investigation_id),
        "title": inv.title,
        "status": inv.status,
        "confidence": float(inv.current_confidence),
        "confidence_state": inv.confidence_state,
        "current_goal": inv.current_goal,
        "planning_cycles": inv.planning_cycle_count,
        "evidence_count": len(evidence_records),
        "evidence": [
            {
                "evidence_id": str(e.evidence_id),
                "source_type": e.source_type,
                "source_ref": e.source_ref,
                "description": e.description,
                "entity_refs": e.entity_refs or {},
                "produced_by_worker": e.produced_by_worker,
                "created_at": e.created_at.isoformat(),
            }
            for e in evidence_records
        ],
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
                "mitre_technique_ids": h.mitre_technique_ids or [],
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
        "recommendations": recommendations_list,
        "entity_graph": {
            "nodes": list(nodes_map.values()),
            "edges": edges_list,
            "density": graph_density,
        },
    }


@planner_router.post("/recommendations/{recommendation_id}/approve")
def approve_containment_recommendation(recommendation_id: UUID, db: Session = Depends(get_db)):
    """Analyst containment approval (Human-in-the-Loop requirement PRD FR-106)."""
    rec = db.query(Recommendation).filter(Recommendation.recommendation_id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.approval_status = "approved"
    
    # Audit log
    audit = AuditLog(
        actor_type="analyst",
        actor_id="SOC_Analyst_1",
        action="CONTAINMENT_APPROVED",
        details={"recommendation_id": str(recommendation_id), "action": rec.action, "risk_level": rec.risk_level},
    )
    db.add(audit)
    db.commit()

    return {
        "status": "approved",
        "recommendation_id": str(recommendation_id),
        "action": rec.action,
        "message": f"Containment action '{rec.action}' approved and queued for execution."
    }


@planner_router.post("/recommendations/{recommendation_id}/reject")
def reject_containment_recommendation(recommendation_id: UUID, db: Session = Depends(get_db)):
    """Analyst containment rejection."""
    rec = db.query(Recommendation).filter(Recommendation.recommendation_id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.approval_status = "rejected"
    
    # Audit log
    audit = AuditLog(
        actor_type="analyst",
        actor_id="SOC_Analyst_1",
        action="CONTAINMENT_REJECTED",
        details={"recommendation_id": str(recommendation_id), "action": rec.action},
    )
    db.add(audit)
    db.commit()

    return {
        "status": "rejected",
        "recommendation_id": str(recommendation_id),
        "action": rec.action,
        "message": f"Containment action '{rec.action}' was rejected by analyst."
    }

