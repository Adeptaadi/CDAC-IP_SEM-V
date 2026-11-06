"""
Project Sentinel — Phase B3 Planner State Sensitivity Test Suite.

Executes controlled counterfactual experiments where exactly one state variable
changes at a time to verify genuine causality in planner decisions.
"""

import pytest
from app.planner.selection import InvestigationStateSnapshot, select_worker, should_terminate
from app.config import settings


class TestB3PlannerStateSensitivity:
    """Rigorous verification of planner causality across isolated state variations."""

    # ==========================================
    # Experiment A — Evidence State Sensitivity
    # ==========================================
    def test_experiment_a_evidence_state_sensitivity(self):
        """Worker selection changes appropriately when evidence state varies."""
        # Baseline: No evidence -> Favor investigation/formulation
        snap_no_evidence = InvestigationStateSnapshot(
            investigation_id="exp_a_1",
            confidence=0.20,
            evidence_count=0,
            graph_density=0.0
        )
        w_no_ev, _, scores_no_ev = select_worker(snap_no_evidence)
        assert w_no_ev == "investigation"
        assert scores_no_ev["correlation"] == 0.0

        # High evidence (5), sparse graph (0.1) -> Correlation utility surges
        snap_high_ev = InvestigationStateSnapshot(
            investigation_id="exp_a_2",
            confidence=0.20,
            evidence_count=5,
            graph_density=0.1
        )
        w_high_ev, _, scores_high_ev = select_worker(snap_high_ev)
        assert w_high_ev == "correlation"
        assert scores_high_ev["correlation"] == pytest.approx(5.0 * 0.9, rel=1e-3)

        # High evidence (5), fully saturated graph (1.0) -> Correlation drops to 0.0
        snap_sat_graph = InvestigationStateSnapshot(
            investigation_id="exp_a_3",
            confidence=0.20,
            evidence_count=5,
            graph_density=1.0
        )
        w_sat, _, scores_sat = select_worker(snap_sat_graph)
        assert scores_sat["correlation"] == 0.0
        assert w_sat != "correlation"

    # ==========================================
    # Experiment B — Worker History Sensitivity
    # ==========================================
    def test_experiment_b_worker_history_sensitivity(self):
        """Worker history dampens utility via exponential decay (0.25^k)."""
        snap_h0 = InvestigationStateSnapshot(
            investigation_id="exp_b_0",
            confidence=0.30,
            last_worker=None,
            consecutive_worker_count=0
        )
        _, _, s0 = select_worker(snap_h0)

        snap_h1 = InvestigationStateSnapshot(
            investigation_id="exp_b_1",
            confidence=0.30,
            last_worker="investigation",
            consecutive_worker_count=1
        )
        _, _, s1 = select_worker(snap_h1)

        snap_h2 = InvestigationStateSnapshot(
            investigation_id="exp_b_2",
            confidence=0.30,
            last_worker="investigation",
            consecutive_worker_count=2
        )
        _, _, s2 = select_worker(snap_h2)

        assert s1["investigation"] == pytest.approx(s0["investigation"] * 0.25, rel=1e-3)
        assert s2["investigation"] == pytest.approx(s0["investigation"] * 0.0625, rel=1e-3)

    # ==========================================
    # Experiment C — Hypothesis State Sensitivity
    # ==========================================
    def test_experiment_c_hypothesis_state_sensitivity(self):
        """Hypothesis status alters analytical need and worker selection."""
        # No hypothesis -> Investigation has baseline utility 0.80
        snap_no_hyp = InvestigationStateSnapshot(
            investigation_id="exp_c_1",
            confidence=0.20,
            hypotheses_confidences=[]
        )
        _, _, s_no_hyp = select_worker(snap_no_hyp)
        assert s_no_hyp["investigation"] == 0.80

        # Confirmed hypothesis, no response -> Response surges to 0.95
        snap_confirmed = InvestigationStateSnapshot(
            investigation_id="exp_c_2",
            confidence=0.88,
            has_confirmed_hypothesis=True,
            has_formulated_response=False
        )
        w_conf, _, s_conf = select_worker(snap_confirmed)
        assert w_conf == "response"
        assert s_conf["response"] == 0.95

        # Confirmed hypothesis, response ALREADY formulated -> Response utility drops to 0.05
        snap_responded = InvestigationStateSnapshot(
            investigation_id="exp_c_3",
            confidence=0.88,
            has_confirmed_hypothesis=True,
            has_formulated_response=True
        )
        _, _, s_resp = select_worker(snap_responded)
        assert s_resp["response"] == 0.05

        # Unresolved contradiction -> Investigation utility = 0.90, reporting = 0.0
        snap_contra = InvestigationStateSnapshot(
            investigation_id="exp_c_4",
            confidence=0.88,
            has_unresolved_contradictions=True
        )
        w_contra, _, s_contra = select_worker(snap_contra)
        assert s_contra["investigation"] == 0.90
        assert s_contra["reporting"] == 0.0
        assert w_contra == "investigation"

    # ==========================================
    # Experiment D — Failure and Stagnation State
    # ==========================================
    def test_experiment_d_failure_and_stagnation_sensitivity(self):
        """Replanning state and stagnation limits alter strategy decisively."""
        # Normal state
        snap_normal = InvestigationStateSnapshot(
            investigation_id="exp_d_1",
            confidence=0.30,
            last_worker="investigation",
            is_replanning=False
        )
        # Replan state: the failed/stagnated worker's utility is clamped to strictly 0.0
        snap_replan = InvestigationStateSnapshot(
            investigation_id="exp_d_2",
            confidence=0.30,
            last_worker="investigation",
            is_replanning=True
        )
        w_replan, _, s_replan = select_worker(snap_replan)
        assert s_replan["investigation"] == 0.0
        assert w_replan != "investigation"

        # Stagnation limit reached -> Termination escalation
        snap_stag = InvestigationStateSnapshot(
            investigation_id="exp_d_3",
            confidence=0.40,
            cycles_since_meaningful_progress=settings.STAGNATION_CYCLE_LIMIT
        )
        terminated = should_terminate(snap_stag)
        assert terminated is True
        assert snap_stag.termination_classification == "stagnation_escalation"
