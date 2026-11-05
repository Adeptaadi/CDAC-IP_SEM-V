import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.investigation import Investigation, InvestigationStateVersion, InvestigationEvent
from app.models.evidence import Evidence, TimelineEvent, Hypothesis
from app.models.orchestration import PlannerRun, PlannerDecision, WorkerExecution
from app.planner.contracts import InvestigationGraphState, PlannerDecisionPayload
from app.planner.decider import DynamicPlanner, dynamic_planner_instance, DecisionValidationError
from app.planner.confidence import ConfidenceEngine
from app.orchestration import TaskExecutor, task_executor_instance, TaskExecutionRequest


class InvestigationStateGraph:
    """Non-linear multi-agent orchestration runtime coordinating planner, workers, and state (Phase 9).

    Emulates LangGraph stateful node-edge conditional execution topology (IS §9.4).
    """

    def __init__(
        self,
        planner: Optional[DynamicPlanner] = None,
        executor: Optional[TaskExecutor] = None,
    ):
        self.planner = planner or dynamic_planner_instance
        self.executor = executor or task_executor_instance
        self.confidence_engine = ConfidenceEngine()

    def step(self, investigation_id: uuid.UUID, db: Session, max_sub_cycles: int = 1) -> InvestigationGraphState:
        """Executes a dynamic graph execution step, advancing the non-linear investigation loop."""
        # Node 1: Investigation initialization & DB load
        inv = db.query(Investigation).filter(Investigation.investigation_id == investigation_id).first()
        if not inv:
            raise ValueError(f"Investigation {investigation_id} not found")

        # Load existing state
        from app.planner.engine import PlannerEngine
        pe = PlannerEngine()
        snapshot = pe.load_state_snapshot(inv, db)

        state = InvestigationGraphState(
            investigation_id=investigation_id,
            cycle_number=inv.planning_cycle_count,
            current_status=inv.status,
            current_confidence=float(inv.current_confidence),
            current_goal=inv.current_goal or inv.title,
        )

        sub_cycle = 0
        while sub_cycle < max_sub_cycles:
            sub_cycle += 1

            # Node 2: Planner execution
            decision = self.planner.formulate_decision(
                investigation_id=investigation_id,
                state=snapshot,
                unresolved_questions=state.unresolved_questions,
            )
            state.last_decision = decision

            # Node 3: Decision validation
            self.planner.validate_decision(decision)

            # Node 4: Record planner decision in DB
            planner_run = PlannerRun(
                id=uuid.uuid4(),
                investigation_id=investigation_id,
                run_number=inv.planning_cycle_count + 1,
                cycle_number=inv.planning_cycle_count + 1,
                reasoning=decision.reasoning,
                status="completed",
                created_at=datetime.utcnow(),
            )
            db.add(planner_run)
            db.flush()

            db_decision = PlannerDecision(
                decision_id=decision.decision_id,
                investigation_id=investigation_id,
                planner_run_id=planner_run.id,
                cycle_number=inv.planning_cycle_count + 1,
                selected_worker=decision.selected_worker,
                selection_score=decision.selection_score,
                confidence_before=decision.confidence_before,
                confidence_after=decision.confidence_before,
                explanation_summary=decision.reasoning,
                created_at=datetime.utcnow(),
            )
            db.add(db_decision)
            db.flush()

            # Conditional Routing based on Decision Type
            if decision.decision_type == "complete_investigation":
                inv.status = "completed"
                inv.closed_at = datetime.utcnow()
                state.current_status = "completed"
                state.termination_reason = "confidence_threshold_met"
                db.commit()
                break

            elif decision.decision_type == "request_human_review":
                inv.status = "awaiting_review"
                state.current_status = "awaiting_review"
                state.requires_human_review = True
                db.commit()
                break

            elif decision.decision_type == "escalate":
                inv.status = "escalated"
                state.current_status = "escalated"
                db.commit()
                break

            elif decision.decision_type == "blocked":
                inv.status = "blocked"
                state.current_status = "blocked"
                db.commit()
                break

            # Node 5: Task Dispatch through Capability Registry & Task Executor
            req = TaskExecutionRequest(
                investigation_id=investigation_id,
                capability_name=decision.selected_capability or f"{decision.selected_worker}.analyze_events",
                objective=inv.current_goal or f"Execute {decision.selected_capability}",
                input_payload=decision.suggested_task_input,
            )
            task_res = self.executor.execute_task(req, db=db)
            state.last_task_output = task_res.output_payload
            state.execution_history.append(f"Executed capability {decision.selected_capability}: {task_res.status}")

            # Node 6: State Update & Evidence Persistence
            if task_res.output_payload and "findings" in task_res.output_payload:
                for f_data in task_res.output_payload["findings"]:
                    ev = Evidence(
                        evidence_id=uuid.uuid4(),
                        investigation_id=investigation_id,
                        source_type="worker_output",
                        description=f_data.get("description", "Observation"),
                        entity_refs=f_data.get("entity_refs", {}),
                        produced_by_worker=decision.selected_worker,
                        planner_decision_id=decision.decision_id,
                        agent_task_id=task_res.task_id,
                        created_at=datetime.utcnow(),
                    )
                    db.add(ev)
                    db.flush()

                    tle = TimelineEvent(
                        event_id=uuid.uuid4(),
                        investigation_id=investigation_id,
                        evidence_id=ev.evidence_id,
                        occurred_at=datetime.utcnow(),
                        event_summary=ev.description,
                        mitre_technique_id=f_data.get("mitre_technique_id"),
                        sequence_position=inv.planning_cycle_count + 1,
                    )
                    db.add(tle)

            # Node 7: Confidence update & state versioning
            inv.planning_cycle_count += 1
            inv.state_version += 1
            # Dynamic confidence progression
            gain = max(0.04, round(task_res.confidence_signal * 0.12, 4))
            new_conf = min(0.98, float(inv.current_confidence) + gain)
            inv.current_confidence = new_conf
            inv.confidence_state = "high" if new_conf >= 0.70 else ("medium" if new_conf >= 0.40 else "low")
            db_decision.confidence_after = new_conf

            # Snapshot
            snapshot_rec = InvestigationStateVersion(
                id=uuid.uuid4(),
                investigation_id=investigation_id,
                version_number=inv.state_version,
                state_snapshot={
                    "confidence": new_conf,
                    "cycle_number": inv.planning_cycle_count,
                    "status": inv.status,
                    "last_worker": decision.selected_worker,
                    "last_capability": decision.selected_capability,
                },
                confidence=new_conf,
                cycle_number=inv.planning_cycle_count,
                created_at=datetime.utcnow(),
            )
            db.add(snapshot_rec)

            inv_event = InvestigationEvent(
                id=uuid.uuid4(),
                investigation_id=investigation_id,
                event_type="cycle_completed",
                summary=f"Cycle {inv.planning_cycle_count}: Dispatched {decision.selected_capability}. Confidence updated to {new_conf:.2f}.",
            )
            db.add(inv_event)
            db.commit()

            # Refresh snapshot for potential sub-cycle loop
            state.cycle_number = inv.planning_cycle_count
            state.current_confidence = new_conf
            snapshot = pe.load_state_snapshot(inv, db)

        return state


investigation_graph_instance = InvestigationStateGraph()
