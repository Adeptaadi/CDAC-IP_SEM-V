import time
import asyncio
from datetime import datetime
from uuid import UUID, uuid4
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models import (
    Investigation,
    Evidence,
    TimelineEvent,
    Hypothesis,
    HypothesisEvidence,
    PlannerDecision,
    WorkerExecution,
    Report,
    Recommendation,
    AuditLog,
)
from app.schemas.contracts import (
    WorkerTask,
    WorkerResult,
    Finding,
    WorkerType,
    RetrievedContext,
)
from app.planner.confidence import ConfidenceEngine
from app.planner.selection import (
    InvestigationStateSnapshot,
    select_worker,
    should_terminate,
)
from app.knowledge.retriever import rag_retriever
from app.workers import get_worker
from app.api.ws import ws_manager


class PlannerEngine:
    """The central autonomous decision-making and orchestration engine (IS §3, AAD §7, AIDD §6)."""

    def __init__(self):
        self.confidence_engine = ConfidenceEngine()
        self.retriever = rag_retriever

    def load_state_snapshot(self, investigation: Investigation, db: Session) -> InvestigationStateSnapshot:
        """Constructs an InvestigationStateSnapshot from database records."""
        evidence_list = db.query(Evidence).filter(Evidence.investigation_id == investigation.investigation_id).all()
        hypotheses = db.query(Hypothesis).filter(Hypothesis.investigation_id == investigation.investigation_id).all()
        decisions = db.query(PlannerDecision).filter(PlannerDecision.investigation_id == investigation.investigation_id).order_by(PlannerDecision.cycle_number.asc()).all()

        hypo_confs = [float(h.confidence) for h in hypotheses]
        has_confirmed = any(h.status == "confirmed" for h in hypotheses)

        # Check for stagnation: count cycles since last meaningful confidence gain (> 0.02)
        cycles_since_gain = 0
        if len(decisions) >= 2:
            for i in range(len(decisions) - 1, 0, -1):
                gain = float(decisions[i].confidence_after) - float(decisions[i].confidence_before)
                if gain > 0.02:
                    break
                cycles_since_gain += 1

        # Check for unresolved contradictions
        has_contradictions = False
        contradicting_links = (
            db.query(HypothesisEvidence)
            .join(Hypothesis, Hypothesis.hypothesis_id == HypothesisEvidence.hypothesis_id)
            .filter(Hypothesis.investigation_id == investigation.investigation_id, HypothesisEvidence.stance == "contradicts")
            .count()
        )
        if contradicting_links > 0:
            has_contradictions = True

        return InvestigationStateSnapshot(
            investigation_id=str(investigation.investigation_id),
            confidence=float(investigation.current_confidence),
            cycle_number=investigation.planning_cycle_count,
            untriaged_event_count=1 if investigation.planning_cycle_count == 0 else 0,
            total_event_count=max(1, len(evidence_list)),
            evidence_count=len(evidence_list),
            graph_density=min(1.0, len(evidence_list) * 0.2),
            hypotheses_confidences=hypo_confs,
            has_confirmed_hypothesis=has_confirmed,
            cycles_since_confidence_gain=cycles_since_gain,
            has_unresolved_contradictions=has_contradictions,
            analyst_requested_stop=(investigation.status in ["paused", "closed_no_threat"]),
        )

    def run_cycle(self, investigation_id: UUID, db: Session) -> Dict[str, Any]:
        """Executes one complete autonomous planning cycle (IS §3.1)."""
        investigation = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
        if not investigation:
            raise ValueError(f"Investigation {investigation_id} not found")

        if investigation.status in ["completed", "closed_no_threat"]:
            return {
                "status": investigation.status,
                "message": f"Investigation already {investigation.status}",
                "cycle_number": investigation.planning_cycle_count,
                "confidence": float(investigation.current_confidence),
            }

        state_snapshot = self.load_state_snapshot(investigation, db)

        # 1. Termination Check
        if should_terminate(state_snapshot):
            if state_snapshot.termination_reason == "confidence_threshold_met":
                investigation.status = "completed"
                investigation.closed_at = datetime.utcnow()
            elif state_snapshot.termination_reason == "stagnation":
                investigation.status = "escalated"
            elif state_snapshot.termination_reason == "max_cycles_reached":
                investigation.status = "escalated"

            db.commit()
            return {
                "status": investigation.status,
                "termination_reason": state_snapshot.termination_reason,
                "cycle_number": investigation.planning_cycle_count,
                "confidence": float(investigation.current_confidence),
                "requires_analyst_review": state_snapshot.requires_analyst_review,
            }

        # 2. Determine Knowledge Need & Retrieve RAG Context
        query_text = investigation.current_goal or investigation.title
        retrieved_ctx = self.retriever.retrieve(query=query_text, top_k=3)

        # 3. Dynamic Worker Selection (IS §3.2 Utility Function)
        worker_type, utility_score = select_worker(state_snapshot)

        # 4. Construct Task & Execute Worker (IS §4 BaseWorker contract)
        existing_evidence_ids = [
            e.evidence_id
            for e in db.query(Evidence).filter(Evidence.investigation_id == investigation_id).all()
        ]
        task = WorkerTask(
            investigation_id=investigation_id,
            worker_type=worker_type,
            objective=investigation.current_goal or f"Evaluate {worker_type} for {investigation.title}",
            evidence_refs=existing_evidence_ids,
            context=retrieved_ctx,
        )

        worker = get_worker(worker_type)
        t_start = time.time()
        worker_result: WorkerResult = worker.execute(task)
        latency_ms = int((time.time() - t_start) * 1000)

        # 5. Apply Worker Results to Database State
        for finding in worker_result.new_evidence:
            ev = Evidence(
                investigation_id=investigation_id,
                source_type="worker_output",
                description=finding.description,
                entity_refs=finding.entity_refs,
                produced_by_worker=worker_type,
            )
            db.add(ev)
            db.flush()

            # Record corresponding timeline event
            te = TimelineEvent(
                investigation_id=investigation_id,
                evidence_id=ev.evidence_id,
                occurred_at=datetime.utcnow(),
                event_summary=finding.description,
                mitre_technique_id=finding.mitre_technique_id,
                sequence_position=investigation.planning_cycle_count + 1,
            )
            db.add(te)

        # Apply hypothesis updates
        for h_update in worker_result.hypothesis_updates:
            existing_hypo = (
                db.query(Hypothesis)
                .filter(Hypothesis.investigation_id == investigation_id, Hypothesis.label == h_update["label"])
                .first()
            )
            if not existing_hypo:
                hypo = Hypothesis(
                    investigation_id=investigation_id,
                    label=h_update["label"],
                    status=h_update["status"],
                    confidence=h_update["confidence"],
                    mitre_technique_ids=h_update.get("mitre_technique_ids", []),
                )
                db.add(hypo)
                db.flush()
            else:
                existing_hypo.status = h_update["status"]
                existing_hypo.confidence = h_update["confidence"]

        # 6. Logit-Odds Confidence Update (IS §1)
        factors = self.confidence_engine.compute_factors(
            worker_result=worker_result,
            evidence_count_this_cycle=max(1, len(worker_result.new_evidence)),
            distinct_sources=2,
            total_evidence=state_snapshot.evidence_count + len(worker_result.new_evidence),
            corroborated=True,
            edges_added=2 if worker_type == "correlation" else 0,
            nodes_in_graph=max(1, state_snapshot.evidence_count),
            knowledge_similarities=[c.similarity_score for c in retrieved_ctx.chunks] if retrieved_ctx.chunks else [0.5],
            source_reliability=0.9,
            worker_confidences=[worker_result.confidence_signal],
            historical_sim_score=0.4,
        )
        delta = self.confidence_engine.compute_delta(factors)

        conf_before = float(investigation.current_confidence)
        conf_after = self.confidence_engine.update(current_confidence=conf_before, delta=delta)
        conf_state = self.confidence_engine.classify_state(conf_after)

        next_cycle = investigation.planning_cycle_count + 1
        investigation.current_confidence = conf_after
        investigation.confidence_state = conf_state
        investigation.planning_cycle_count = next_cycle

        if worker_result.next_task_suggestion:
            investigation.current_goal = f"Proceed to {worker_result.next_task_suggestion} following {worker_type} findings"

        # 7. Persist PlannerDecision & WorkerExecution (PostgreSQL Audit Trail)
        decision = PlannerDecision(
            investigation_id=investigation_id,
            cycle_number=next_cycle,
            selected_worker=worker_type,
            selection_score=utility_score,
            knowledge_need=query_text,
            confidence_before=conf_before,
            confidence_after=conf_after,
            explanation_summary=worker_result.reasoning_summary,
        )
        db.add(decision)
        db.flush()

        execution = WorkerExecution(
            decision_id=decision.decision_id,
            worker_type=worker_type,
            status=worker_result.status,
            raw_output=worker_result.model_dump(mode="json"),
            latency_ms=latency_ms,
            llm_token_usage=120,
        )
        db.add(execution)

        audit = AuditLog(
            investigation_id=investigation_id,
            actor_type="planner",
            actor_id="PlannerEngine_v1",
            action=f"CYCLE_{next_cycle}_COMPLETED",
            details={
                "selected_worker": worker_type,
                "confidence_before": conf_before,
                "confidence_after": conf_after,
                "delta": delta,
            },
        )
        db.add(audit)

        # If investigation meets completion threshold, generate final report and recommendations
        if conf_after >= 0.85 and next_cycle >= 3:
            investigation.status = "completed"
            investigation.closed_at = datetime.utcnow()

            # Generate Report record
            rep = Report(
                investigation_id=investigation_id,
                executive_summary=f"Incident confirmed for {investigation.title}. Adversary behavior identified with {conf_after*100:.1f}% confidence.",
                technical_body=f"Investigation completed across {next_cycle} autonomous planning cycles. Primary attack techniques validated.",
                final_confidence=conf_after,
            )
            db.add(rep)
            db.flush()

            # Generate Containment Recommendation
            rec = Recommendation(
                report_id=rep.report_id,
                action="Isolate affected host and block C2 IP at border firewall",
                risk_level="medium",
                impact_summary="Prevents lateral movement and active data exfiltration.",
                requires_approval=True,
                approval_status="pending",
            )
            db.add(rec)

        db.commit()

        # 8. Broadcast to WebSocket Subscribers (Stage 3 Real-time Stream)
        broadcast_payload = {
            "type": "PLANNER_DECISION",
            "investigation_id": str(investigation_id),
            "cycle_number": next_cycle,
            "selected_worker": worker_type,
            "utility_score": utility_score,
            "confidence_before": conf_before,
            "confidence_after": conf_after,
            "confidence_state": conf_state,
            "explanation": worker_result.reasoning_summary,
            "status": investigation.status,
        }
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    ws_manager.broadcast_to_investigation(str(investigation_id), broadcast_payload)
                )
        except Exception:
            pass

        return {
            "cycle_number": next_cycle,
            "selected_worker": worker_type,
            "utility_score": utility_score,
            "confidence_before": conf_before,
            "confidence_after": conf_after,
            "confidence_state": conf_state,
            "reasoning_summary": worker_result.reasoning_summary,
            "status": investigation.status,
        }

    def run_autonomous(self, investigation_id: UUID, db: Session, max_steps: int = 10) -> Dict[str, Any]:
        """Runs the autonomous investigation loop until completion, stagnation, or max steps."""
        cycle_results = []
        for _ in range(max_steps):
            res = self.run_cycle(investigation_id, db)
            cycle_results.append(res)
            if res.get("status") in ["completed", "escalated", "closed_no_threat", "paused"]:
                break

        investigation = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
        return {
            "investigation_id": str(investigation_id),
            "final_status": investigation.status,
            "total_cycles": investigation.planning_cycle_count,
            "final_confidence": float(investigation.current_confidence),
            "cycle_history": cycle_results,
        }


planner_engine = PlannerEngine()
