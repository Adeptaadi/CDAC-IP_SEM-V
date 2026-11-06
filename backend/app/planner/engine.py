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
from app.models.evidence import compute_evidence_fingerprint
from app.models.investigation import InvestigationEvent
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
        """Constructs an InvestigationStateSnapshot with novelty and history awareness (B0.1, B0.4, B0.5)."""
        evidence_list = db.query(Evidence).filter(Evidence.investigation_id == investigation.investigation_id).all()
        novel_evidence_list = [e for e in evidence_list if getattr(e, "is_novel", True) and not getattr(e, "is_duplicate", False)]
        duplicate_evidence_list = [e for e in evidence_list if getattr(e, "is_duplicate", False)]
        hypotheses = db.query(Hypothesis).filter(Hypothesis.investigation_id == investigation.investigation_id).all()
        decisions = db.query(PlannerDecision).filter(PlannerDecision.investigation_id == investigation.investigation_id).order_by(PlannerDecision.cycle_number.asc()).all()

        hypo_confs = [float(h.confidence) for h in hypotheses]
        has_confirmed = any(h.status == "confirmed" for h in hypotheses)

        # Execution history tracking
        worker_history = [d.selected_worker for d in decisions]
        last_worker = worker_history[-1] if worker_history else None
        consecutive_count = 0
        if last_worker:
            for w in reversed(worker_history):
                if w == last_worker:
                    consecutive_count += 1
                else:
                    break

        # Check if ResponseWorker has already formulated containment recommendations (B0.6)
        has_formulated_response = False
        response_indices = [idx for idx, d in enumerate(decisions) if d.selected_worker == "response"]
        if response_indices:
            last_resp_idx = response_indices[-1]
            last_resp_cycle = decisions[last_resp_idx].cycle_number
            # Check if novel evidence arrived strictly AFTER the last response decision
            novel_since_resp = [
                e for e in novel_evidence_list
                if any(
                    d.cycle_number > last_resp_cycle
                    for d in decisions
                    if e.planner_decision_id and d.decision_id == e.planner_decision_id
                )
            ]
            if not novel_since_resp:
                has_formulated_response = True

        # Check for stagnation: count cycles since meaningful progress was made (B0.4)
        cycles_since_progress = 0
        if decisions:
            for d in reversed(decisions):
                # Novel evidence generated in this decision?
                novel_in_decision = any(
                    e.planner_decision_id == d.decision_id and getattr(e, "is_novel", True) and not getattr(e, "is_duplicate", False)
                    for e in evidence_list
                )
                exec_rec = d.executions[0] if d.executions else None
                raw_out = exec_rec.raw_output if (exec_rec and isinstance(exec_rec.raw_output, dict)) else {}
                hypo_modified_in_dec = raw_out.get("hypo_modified", False)
                
                if novel_in_decision or hypo_modified_in_dec:
                    break
                cycles_since_progress += 1

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

        # Replan trigger if strategy stagnated (B0.7)
        is_replanning = False
        replan_reason = None
        if cycles_since_progress >= 1 and last_worker:
            is_replanning = True
            replan_reason = f"Strategy '{last_worker}' yielded no novel evidence for {cycles_since_progress} cycle(s). Initiating explicit strategy pivot."

        return InvestigationStateSnapshot(
            investigation_id=str(investigation.investigation_id),
            confidence=float(investigation.current_confidence),
            cycle_number=investigation.planning_cycle_count,
            untriaged_event_count=1 if investigation.planning_cycle_count == 0 else 0,
            total_event_count=max(1, len(evidence_list)),
            evidence_count=len(evidence_list),
            novel_evidence_count=len(novel_evidence_list),
            duplicate_evidence_count=len(duplicate_evidence_list),
            graph_density=min(1.0, len(novel_evidence_list) * 0.2),
            hypotheses_confidences=hypo_confs,
            has_confirmed_hypothesis=has_confirmed,
            has_formulated_response=has_formulated_response,
            cycles_since_confidence_gain=cycles_since_progress,
            cycles_since_meaningful_progress=cycles_since_progress,
            has_unresolved_contradictions=has_contradictions,
            analyst_requested_stop=(investigation.status in ["paused", "closed_no_threat"]),
            last_worker=last_worker,
            consecutive_worker_count=consecutive_count,
            worker_history=worker_history,
            is_replanning=is_replanning,
            replan_reason=replan_reason,
        )

    def run_cycle(self, investigation_id: UUID, db: Session) -> Dict[str, Any]:
        """Executes one complete autonomous planning cycle without artificial drift (B0.1-B0.7)."""
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

        # 1. Termination Check (B0.8)
        if should_terminate(state_snapshot):
            if state_snapshot.termination_reason == "confidence_threshold_met":
                investigation.status = "completed"
                investigation.closed_at = datetime.utcnow()
            elif state_snapshot.termination_reason in ["stagnation", "max_cycles_reached"]:
                investigation.status = "escalated"

            db.commit()
            return {
                "status": investigation.status,
                "termination_reason": state_snapshot.termination_reason,
                "termination_classification": state_snapshot.termination_classification,
                "cycle_number": investigation.planning_cycle_count,
                "confidence": float(investigation.current_confidence),
                "requires_analyst_review": state_snapshot.requires_analyst_review,
            }

        # 2. Determine Knowledge Need & Retrieve RAG Context
        query_text = investigation.current_goal or investigation.title
        retrieved_ctx = self.retriever.retrieve(query=query_text, top_k=3)
        rag_citations = [
            {
                "category": c.category,
                "text": c.text,
                "similarity_score": round(float(c.similarity_score), 4),
                "reliability_weight": round(float(c.reliability_weight), 2),
            }
            for c in retrieved_ctx.chunks
        ]
        # Real historical similarity lookup (no synthetic formula B0.3!)
        hist_chunks = [c for c in retrieved_ctx.chunks if getattr(c, "category", "") == "historical"]
        historical_score = max([float(c.similarity_score) for c in hist_chunks], default=0.0) if hist_chunks else 0.0

        # 3. Dynamic Worker Selection with History & Replanning (B0.5, B0.7)
        worker_type, utility_score, utility_scores, history_adjustments, selection_rationale = select_worker(
            state_snapshot, return_details=True
        )

        decision_type = "continue_investigation"
        is_replanning = False
        replan_reason = None
        if state_snapshot.is_replanning:
            decision_type = "replan"
            is_replanning = True
            replan_reason = state_snapshot.replan_reason

        # 4. Construct Task & Execute Worker (IS §4 BaseWorker contract)
        existing_evidence_records = db.query(Evidence).filter(Evidence.investigation_id == investigation_id).all()
        existing_evidence_ids = [e.evidence_id for e in existing_evidence_records]
        existing_findings = [
            Finding(
                description=e.description,
                entity_refs=e.entity_refs or {},
                mitre_technique_id=None,
                supporting_evidence_ids=[e.evidence_id]
            )
            for e in existing_evidence_records
        ]
        task = WorkerTask(
            investigation_id=investigation_id,
            worker_type=worker_type,
            objective=investigation.current_goal or f"Evaluate {worker_type} for {investigation.title}",
            evidence_refs=existing_evidence_ids,
            findings=existing_findings,
            context=retrieved_ctx,
        )

        worker = get_worker(worker_type)
        t_start = time.time()
        worker_result: WorkerResult = worker.execute(task)
        latency_ms = int((time.time() - t_start) * 1000)

        # Pre-generate decision and execution IDs for direct provenance linkage
        cycle_decision_id = uuid4()
        cycle_execution_id = uuid4()
        created_evidence_ids: List[UUID] = []

        # 5. Apply Worker Results to Database State with Evidence Deduplication (B0.2)
        novel_count = 0
        duplicate_count = 0
        corroboration_count = 0

        existing_evidence_records = db.query(Evidence).filter(Evidence.investigation_id == investigation_id).all()
        existing_fingerprint_map = {
            (getattr(e, "content_hash", None) or compute_evidence_fingerprint(e.description, e.entity_refs)): e
            for e in existing_evidence_records
        }

        for finding in worker_result.new_evidence:
            f_hash = compute_evidence_fingerprint(finding.description, finding.entity_refs)
            existing_match = existing_fingerprint_map.get(f_hash)

            if existing_match:
                if existing_match.produced_by_worker == worker_type:
                    is_dup = True
                    is_nov = False
                    duplicate_count += 1
                    existing_match.observation_count = getattr(existing_match, "observation_count", 1) + 1
                else:
                    is_dup = False
                    is_nov = False
                    corroboration_count += 1
                    current_corroborated = list(existing_match.corroborated_by or [])
                    if existing_match.evidence_id not in current_corroborated:
                        current_corroborated.append(existing_match.evidence_id)
                        existing_match.corroborated_by = current_corroborated
            else:
                is_dup = False
                is_nov = True
                novel_count += 1

            ev = Evidence(
                investigation_id=investigation_id,
                source_type="worker_output",
                description=finding.description,
                content_hash=f_hash,
                is_duplicate=is_dup,
                is_novel=is_nov,
                observation_count=1,
                entity_refs=finding.entity_refs,
                produced_by_worker=worker_type,
                planner_decision_id=cycle_decision_id,
                worker_execution_id=cycle_execution_id,
            )
            db.add(ev)
            db.flush()
            created_evidence_ids.append(ev.evidence_id)
            existing_fingerprint_map[f_hash] = ev

            # Record corresponding timeline event only for novel findings
            if not is_dup:
                te = TimelineEvent(
                    investigation_id=investigation_id,
                    evidence_id=ev.evidence_id,
                    occurred_at=datetime.utcnow(),
                    event_summary=finding.description,
                    mitre_technique_id=finding.mitre_technique_id,
                    sequence_position=investigation.planning_cycle_count + 1,
                )
                db.add(te)

        # Apply hypothesis updates with B2 Bottom-Up Provenance Tracking
        hypo_modified = False
        for h_update in worker_result.hypothesis_updates:
            existing_hypo = (
                db.query(Hypothesis)
                .filter(Hypothesis.investigation_id == investigation_id, Hypothesis.label == h_update["label"])
                .first()
            )
            target_hypo = None
            if not existing_hypo:
                hypo = Hypothesis(
                    investigation_id=investigation_id,
                    label=h_update["label"],
                    status=h_update["status"],
                    confidence=h_update["confidence"],
                    mitre_technique_ids=h_update.get("mitre_technique_ids", []),
                    generation_source=h_update.get("generation_source", "RULE_DERIVED"),
                    provenance_summary=h_update.get("provenance_summary", None),
                )
                db.add(hypo)
                db.flush()
                hypo_modified = True
                target_hypo = hypo
            else:
                if existing_hypo.status != h_update["status"] or abs(float(existing_hypo.confidence) - float(h_update["confidence"])) >= 0.05:
                    hypo_modified = True
                existing_hypo.status = h_update["status"]
                existing_hypo.confidence = h_update["confidence"]
                if h_update.get("generation_source"):
                    existing_hypo.generation_source = h_update["generation_source"]
                if h_update.get("provenance_summary"):
                    existing_hypo.provenance_summary = h_update["provenance_summary"]
                target_hypo = existing_hypo

            # Record supporting/contradicting evidence links
            for sup_id_str in h_update.get("supporting_evidence_ids", []):
                try:
                    s_uuid = UUID(str(sup_id_str))
                    exists_link = db.query(HypothesisEvidence).filter_by(
                        hypothesis_id=target_hypo.hypothesis_id, evidence_id=s_uuid
                    ).first()
                    if not exists_link:
                        db.add(HypothesisEvidence(
                            hypothesis_id=target_hypo.hypothesis_id,
                            evidence_id=s_uuid,
                            stance="supports",
                            weight=1.0
                        ))
                except Exception:
                    pass

            for con_id_str in h_update.get("contradicting_evidence_ids", []):
                try:
                    c_uuid = UUID(str(con_id_str))
                    exists_link = db.query(HypothesisEvidence).filter_by(
                        hypothesis_id=target_hypo.hypothesis_id, evidence_id=c_uuid
                    ).first()
                    if not exists_link:
                        db.add(HypothesisEvidence(
                            hypothesis_id=target_hypo.hypothesis_id,
                            evidence_id=c_uuid,
                            stance="contradicts",
                            weight=1.0
                        ))
                except Exception:
                    pass

        # 6. Logit-Odds Confidence Update without Artificial Drift (B0.3 & B2.5)
        evidence_records_all = db.query(Evidence).filter(Evidence.investigation_id == investigation_id).all()
        distinct_sources_count = max(1, len(set(f"{e.source_type}:{e.produced_by_worker or 'default'}" for e in evidence_records_all)))
        nodes_count = max(1, len(state_snapshot.hypotheses_confidences) + len(existing_evidence_ids))
        edges_added_count = novel_count if worker_type in ["correlation", "investigation"] else 0
        has_novel_knowledge = bool(novel_count > 0 or hypo_modified)

        # Unresolved contradiction count from persisted hypothesis evidence relationships
        contradicting_links_count = (
            db.query(HypothesisEvidence)
            .join(Hypothesis, Hypothesis.hypothesis_id == HypothesisEvidence.hypothesis_id)
            .filter(Hypothesis.investigation_id == investigation_id, HypothesisEvidence.stance == "contradicts")
            .count()
        )

        factors = self.confidence_engine.compute_factors(
            worker_result=worker_result,
            evidence_count_this_cycle=novel_count,
            novel_evidence_count=novel_count,
            duplicate_evidence_count=duplicate_count,
            distinct_sources=distinct_sources_count,
            total_evidence=state_snapshot.evidence_count + novel_count,
            corroborated=bool(corroboration_count > 0 or (novel_count > 1 and worker_type == "correlation")),
            edges_added=edges_added_count,
            nodes_in_graph=nodes_count,
            knowledge_similarities=[c.similarity_score for c in retrieved_ctx.chunks] if retrieved_ctx.chunks else None,
            source_reliability=0.95 if any("MITRE" in (c.category or "") for c in retrieved_ctx.chunks) else 0.8,
            has_novel_knowledge=has_novel_knowledge,
            worker_confidences=[worker_result.confidence_signal],
            historical_sim_score=historical_score,
            unresolved_contradictions_count=contradicting_links_count,
        )
        delta = self.confidence_engine.compute_delta(factors)
        factor_contributions = self.confidence_engine.compute_factor_contributions(factors)
        
        avg_knowledge_sim = round(sum(c.similarity_score for c in retrieved_ctx.chunks)/len(retrieved_ctx.chunks), 4) if (retrieved_ctx.chunks and has_novel_knowledge) else 0.0
        factor_trace = self.confidence_engine.compute_factor_trace(
            factors,
            inputs={
                "detection": worker_result.confidence_signal if worker_type == "detection" else 0.0,
                "evidence": novel_count,
                "correlation": edges_added_count,
                "knowledge": avg_knowledge_sim,
                "agreement": 0.0,
                "historical": historical_score,
                "contradiction": contradicting_links_count,
            },
            sources={
                "detection": str(cycle_execution_id) if worker_type == "detection" else "none",
                "evidence": f"worker:{worker_type}:novel={novel_count}",
                "correlation": f"edges:{edges_added_count}",
                "knowledge": "rag_retriever" if has_novel_knowledge else "none",
                "agreement": "none",
                "historical": "chromadb_historical_cases" if historical_score > 0 else "none",
                "contradiction": f"unresolved_contradictions:{contradicting_links_count}",
            }
        )

        conf_before = float(investigation.current_confidence)
        conf_after = self.confidence_engine.update(
            current_confidence=conf_before,
            delta=delta,
            unresolved_contradictions_count=contradicting_links_count
        )
        conf_state = self.confidence_engine.classify_state(conf_after)

        next_cycle = investigation.planning_cycle_count + 1
        investigation.current_confidence = conf_after
        investigation.confidence_state = conf_state
        investigation.planning_cycle_count = next_cycle

        if worker_result.next_task_suggestion:
            investigation.current_goal = f"Proceed to {worker_result.next_task_suggestion} following {worker_type} findings"

        # 7. Persist PlannerDecision & WorkerExecution with Replan Metadata (B0.7)
        decision = PlannerDecision(
            decision_id=cycle_decision_id,
            investigation_id=investigation_id,
            cycle_number=next_cycle,
            decision_type=decision_type,
            is_replanning=is_replanning,
            replan_reason=replan_reason,
            selected_worker=worker_type,
            selection_score=utility_score,
            knowledge_need=query_text,
            confidence_before=conf_before,
            confidence_after=conf_after,
            explanation_summary=selection_rationale if is_replanning else worker_result.reasoning_summary,
        )
        db.add(decision)
        db.flush()

        raw_output_payload = worker_result.model_dump(mode="json")
        raw_output_payload["utility_scores"] = utility_scores
        raw_output_payload["history_adjustments"] = history_adjustments
        raw_output_payload["factor_contributions"] = factor_contributions
        raw_output_payload["confidence_factor_trace"] = factor_trace
        raw_output_payload["rag_citations"] = rag_citations
        raw_output_payload["delta"] = round(float(delta), 4)
        raw_output_payload["novel_evidence_count"] = novel_count
        raw_output_payload["duplicate_evidence_count"] = duplicate_count
        raw_output_payload["corroboration_count"] = corroboration_count
        raw_output_payload["decision_type"] = decision_type
        raw_output_payload["is_replanning"] = is_replanning
        raw_output_payload["replan_reason"] = replan_reason
        raw_output_payload["hypo_modified"] = hypo_modified

        execution = WorkerExecution(
            execution_id=cycle_execution_id,
            decision_id=decision.decision_id,
            worker_type=worker_type,
            status=worker_result.status,
            raw_output=raw_output_payload,
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
                "decision_type": decision_type,
                "is_replanning": is_replanning,
                "replan_reason": replan_reason,
                "confidence_before": conf_before,
                "confidence_after": conf_after,
                "delta": delta,
                "utility_scores": utility_scores,
                "history_adjustments": history_adjustments,
                "novel_evidence_count": novel_count,
                "duplicate_evidence_count": duplicate_count,
            },
        )
        db.add(audit)

        # If replanning occurred, record InvestigationEvent for durable event timeline
        if is_replanning:
            ev_event = InvestigationEvent(
                investigation_id=investigation_id,
                event_type="replanned",
                summary=replan_reason or f"Replanned strategy at cycle {next_cycle}",
                details={"pivoted_to": worker_type, "cycle": next_cycle, "previous_worker": state_snapshot.last_worker},
            )
            db.add(ev_event)

        # If investigation meets completion threshold, generate final report and recommendations
        if conf_after >= 0.85 and next_cycle >= 3:
            investigation.status = "completed"
            investigation.closed_at = datetime.utcnow()

            rep = Report(
                investigation_id=investigation_id,
                executive_summary=f"Incident confirmed for {investigation.title}. Adversary behavior identified with {conf_after*100:.1f}% confidence.",
                technical_body=f"Investigation completed across {next_cycle} autonomous planning cycles. Primary attack techniques validated.",
                final_confidence=conf_after,
            )
            db.add(rep)
            db.flush()

            all_evidence_ids = [
                str(e.evidence_id)
                for e in db.query(Evidence).filter(Evidence.investigation_id == investigation_id).all()
            ]

            rec = Recommendation(
                report_id=rep.report_id,
                action="Isolate affected host and block C2 IP at border firewall",
                risk_level="medium",
                impact_summary="Prevents lateral movement and active data exfiltration.",
                requires_approval=True,
                approval_status="pending",
                supporting_evidence_ids=all_evidence_ids,
            )
            db.add(rec)

        db.commit()

        # 8. Broadcast to WebSocket Subscribers
        broadcast_payload = {
            "type": "PLANNER_DECISION",
            "investigation_id": str(investigation_id),
            "cycle_number": next_cycle,
            "selected_worker": worker_type,
            "decision_type": decision_type,
            "is_replanning": is_replanning,
            "replan_reason": replan_reason,
            "utility_score": utility_score,
            "utility_scores": utility_scores,
            "history_adjustments": history_adjustments,
            "factor_contributions": factor_contributions,
            "confidence_factor_trace": factor_trace,
            "rag_citations": rag_citations,
            "confidence_before": conf_before,
            "confidence_after": conf_after,
            "confidence_delta": round(float(delta), 4),
            "confidence_state": conf_state,
            "explanation": selection_rationale if is_replanning else worker_result.reasoning_summary,
            "latency_ms": latency_ms,
            "status": investigation.status,
            "findings_count": len(worker_result.new_evidence),
            "novel_count": novel_count,
            "duplicate_count": duplicate_count,
        }
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(
                    ws_manager.broadcast_to_investigation(str(investigation_id), broadcast_payload)
                )
        except RuntimeError:
            pass

        return {
            "cycle_number": next_cycle,
            "selected_worker": worker_type,
            "decision_type": decision_type,
            "is_replanning": is_replanning,
            "replan_reason": replan_reason,
            "utility_score": utility_score,
            "utility_scores": utility_scores,
            "history_adjustments": history_adjustments,
            "factor_contributions": factor_contributions,
            "confidence_factor_trace": factor_trace,
            "rag_citations": rag_citations,
            "confidence_before": conf_before,
            "confidence_after": conf_after,
            "confidence_delta": round(float(delta), 4),
            "confidence_state": conf_state,
            "reasoning_summary": selection_rationale if is_replanning else worker_result.reasoning_summary,
            "latency_ms": latency_ms,
            "status": investigation.status,
            "novel_count": novel_count,
            "duplicate_count": duplicate_count,
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
