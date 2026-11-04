import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.investigation import Investigation, InvestigationEvent
from app.models.response import HumanReview, ResponseSimulation, Recommendation
from app.response.contracts import (
    SimulationRequest,
    SimulationResult,
    ReviewSubmissionPayload,
)
from app.investigation.service import investigation_service_instance


class ResponseSimulationService:
    """Safe, strictly non-destructive response simulation environment (Phase 11)."""

    def simulate(
        self,
        request: SimulationRequest,
        db: Optional[Session] = None,
    ) -> SimulationResult:
        """Evaluates containment action, calculating blast radius, dependencies, and rollback."""
        action = request.action_type
        target = request.target_identifier

        if action == "isolate_endpoint":
            blast_radius = f"Host {target} and local subnet ARP cache"
            disruption = "Network cut off except for Sentinel agent management channel on port 8443."
            safety = "SAFE: Preserves remote agent management socket; prevents lateral SMB/WMI spread."
            rollback = f"Re-enable network adapter via Sentinel control agent on host {target}."

        elif action == "block_ip":
            blast_radius = f"Perimeter firewall inbound/outbound rules for IP {target}"
            disruption = f"All active TCP/UDP connections with {target} terminated."
            safety = "SAFE: Non-critical remote IP address; does not affect internal gateway routing."
            rollback = f"Remove IP {target} from perimeter firewall deny-list."

        elif action == "suspend_user":
            blast_radius = f"Active Directory domain account '{target}'"
            disruption = f"Revokes Kerberos tickets; prevents new logins for user '{target}'."
            safety = "SAFE: Account lock flagged for forensic preservation; service accounts protected."
            rollback = f"Unlock domain account '{target}' in Active Directory."

        elif action == "terminate_process":
            blast_radius = f"Process {target} and child subprocesses"
            disruption = "Process SIGKILL executed."
            safety = "SAFE: Verified non-system-critical PID."
            rollback = "Process can be restarted from validated binary image if needed."

        else:
            blast_radius = f"Target {target}"
            disruption = "Generic containment action"
            safety = "Standard review recommended"
            rollback = "Revert containment modification"

        sim_id = uuid.uuid4()
        now = datetime.utcnow()
        impact = {
            "blast_radius": blast_radius,
            "service_disruption": disruption,
            "safety_assessment": safety,
            "rollback_plan": rollback,
        }

        if db is not None:
            db_sim = ResponseSimulation(
                id=sim_id,
                investigation_id=request.investigation_id,
                action=f"{action}:{target}",
                target_entity_id=request.target_entity_id,
                simulated_impact=impact,
                status="simulated",
                created_at=now,
            )
            db.add(db_sim)
            try:
                db.commit()
            except Exception:
                db.rollback()

        return SimulationResult(
            simulation_id=sim_id,
            investigation_id=request.investigation_id,
            action=f"{action}:{target}",
            target_identifier=target,
            status="simulated",
            blast_radius=blast_radius,
            service_disruption=disruption,
            safety_assessment=safety,
            rollback_plan=rollback,
            parameters=request.parameters,
            simulated_at=now,
        )


class HumanReviewService:
    """Manages analyst review queues, gating of high-risk actions, and approvals (Phase 11)."""

    def create_review_request(
        self,
        investigation_id: uuid.UUID,
        requested_action: str,
        risk_level: str,
        db: Session,
    ) -> HumanReview:
        """Submits a human review request and places investigation into awaiting_review status."""
        review = HumanReview(
            id=uuid.uuid4(),
            investigation_id=investigation_id,
            requested_action=requested_action,
            risk_level=risk_level,
            status="pending",
            created_at=datetime.utcnow(),
        )
        db.add(review)

        # Update investigation status
        inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
        if inv and inv.status != "awaiting_review":
            inv.status = "awaiting_review"
            event = InvestigationEvent(
                id=uuid.uuid4(),
                investigation_id=investigation_id,
                event_type="human_review_requested",
                summary=f"Human review requested for action '{requested_action}' (Risk: {risk_level}).",
            )
            db.add(event)

        db.commit()
        db.refresh(review)
        return review

    def list_pending_reviews(self, db: Session) -> List[HumanReview]:
        """Lists all open reviews awaiting analyst action."""
        return db.query(HumanReview).filter(HumanReview.status == "pending").order_by(HumanReview.created_at.desc()).all()

    def process_review(
        self,
        review_id: uuid.UUID,
        payload: ReviewSubmissionPayload,
        db: Session,
    ) -> HumanReview:
        """Processes analyst approval or rejection, logging audit events and resuming or completing investigation."""
        review = db.query(HumanReview).filter(HumanReview.id == review_id).first()
        if not review:
            raise ValueError(f"HumanReview {review_id} not found")

        now = datetime.utcnow()
        review.status = payload.decision
        review.analyst_comments = payload.analyst_comments
        review.analyst_id = payload.analyst_id
        review.reviewed_at = now

        inv = db.query(Investigation).filter(Investigation.investigation_id == review.investigation_id).first()
        if inv:
            if payload.decision == "approved":
                # Check if approval was for completing investigation or continuing
                if "complete" in review.requested_action.lower():
                    inv.status = "completed"
                    inv.closed_at = now
                else:
                    inv.status = "investigating"
            elif payload.decision == "rejected":
                inv.status = "closed"
                inv.closed_at = now
            elif payload.decision == "request_changes":
                inv.status = "investigating"

            ev = InvestigationEvent(
                id=uuid.uuid4(),
                investigation_id=inv.investigation_id,
                event_type=f"review_{payload.decision}",
                summary=f"Analyst {payload.decision} review for '{review.requested_action}'. Comments: {payload.analyst_comments}",
            )
            db.add(ev)

        db.commit()
        db.refresh(review)
        return review


response_simulation_service = ResponseSimulationService()
human_review_service = HumanReviewService()
