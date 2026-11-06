"""
Phase B3 Agent Autonomy & State-Driven Planning Tests.

Verifies that Project Sentinel's planning engine makes genuinely state-driven,
adaptive decisions rather than executing a hardcoded linear sequence.
"""

import pytest
from app.planner.selection import InvestigationStateSnapshot, select_worker


class TestB3AgentAutonomy:
    """Rigorous verification of dynamic, state-driven worker selection."""

    def test_worker_selection_sensitive_to_evidence_volume(self):
        """Worker selection changes based on the volume of unanalyzed evidence."""
        # Low evidence (0): investigation has raw utility 0.80, correlation 0.0
        snap_zero = InvestigationStateSnapshot(
            investigation_id="test-autonomy-1",
            confidence=0.20,
            cycle_number=1,
            evidence_count=0,
            graph_density=0.1,
            last_worker=None,
            worker_history=[]
        )
        w_zero, s_zero, scores_zero = select_worker(snap_zero)

        # High evidence (4) with low graph density: correlation utility increases to 4.0 * (1 - 0.1) = 3.6
        snap_high = InvestigationStateSnapshot(
            investigation_id="test-autonomy-2",
            confidence=0.20,
            cycle_number=1,
            evidence_count=4,
            graph_density=0.1,
            last_worker=None,
            worker_history=[]
        )
        w_high, s_high, scores_high = select_worker(snap_high)

        assert scores_high["correlation"] > scores_zero["correlation"], "High evidence count must increase correlation utility"
        assert w_high == "correlation"

    def test_worker_selection_sensitive_to_contradiction(self):
        """Unresolved contradictions suppress reporting utility and force investigation."""
        snap_clear = InvestigationStateSnapshot(
            investigation_id="test-contra-clear",
            confidence=0.88,
            cycle_number=2,
            evidence_count=5,
            graph_density=0.8,
            has_unresolved_contradictions=False,
            last_worker="investigation",
            worker_history=["investigation"]
        )
        snap_contra = InvestigationStateSnapshot(
            investigation_id="test-contra-active",
            confidence=0.88,
            cycle_number=2,
            evidence_count=5,
            graph_density=0.8,
            has_unresolved_contradictions=True,
            last_worker="investigation",
            worker_history=["investigation"]
        )

        _, _, scores_clear = select_worker(snap_clear)
        _, _, scores_contra = select_worker(snap_contra)

        assert scores_clear["reporting"] > 0.8, "Reporting should have high utility when confidence >= 0.85 and no contradiction"
        assert scores_contra["reporting"] == 0.0, "Reporting must be completely zeroed out when unresolved contradictions exist"

        w_contra, _, _ = select_worker(snap_contra)
        assert w_contra != "reporting"

    def test_history_penalty_prevents_worker_lock_in(self):
        """Consecutive selections of the same worker suffer exponential dampening (0.25^k)."""
        snap_fresh = InvestigationStateSnapshot(
            investigation_id="test-lockin-1",
            confidence=0.30,
            cycle_number=1,
            evidence_count=0,
            last_worker=None,
            worker_history=[]
        )
        _, _, scores_fresh = select_worker(snap_fresh)

        snap_used_once = InvestigationStateSnapshot(
            investigation_id="test-lockin-2",
            confidence=0.30,
            cycle_number=2,
            evidence_count=0,
            last_worker="investigation",
            consecutive_worker_count=1,
            worker_history=["investigation"]
        )
        _, _, scores_used_once = select_worker(snap_used_once)

        snap_used_twice = InvestigationStateSnapshot(
            investigation_id="test-lockin-3",
            confidence=0.30,
            cycle_number=3,
            evidence_count=0,
            last_worker="investigation",
            consecutive_worker_count=2,
            worker_history=["investigation", "investigation"]
        )
        _, _, scores_used_twice = select_worker(snap_used_twice)

        # 0.25 penalty per repeat
        assert scores_used_once["investigation"] == pytest.approx(scores_fresh["investigation"] * 0.25, rel=1e-3)
        assert scores_used_twice["investigation"] == pytest.approx(scores_fresh["investigation"] * 0.0625, rel=1e-3)

    def test_replanning_exclusion_forces_alternative_worker(self):
        """Replanning exclusions set worker utility to 0.0, forcing alternative selection."""
        snap_normal = InvestigationStateSnapshot(
            investigation_id="test-replan-1",
            confidence=0.30,
            cycle_number=2,
            evidence_count=0,
            last_worker="correlation",
            worker_history=["correlation"]
        )
        w_normal, _, _ = select_worker(snap_normal)
        assert w_normal == "investigation"

        snap_replan = InvestigationStateSnapshot(
            investigation_id="test-replan-2",
            confidence=0.30,
            cycle_number=2,
            evidence_count=0,
            last_worker="investigation",
            consecutive_worker_count=2,
            is_replanning=True,
            worker_history=["investigation", "investigation"]
        )
        w_replan, _, scores_replan = select_worker(snap_replan)
        assert scores_replan["investigation"] == 0.0, "Replan excluded worker utility must be strictly 0.0"
        assert w_replan != "investigation"

    def test_no_linear_cycle_lockstep(self):
        """Cycle number alone does not determine selected worker; state governs decision."""
        workers_cycle_1 = set()
        # Varying states at cycle 1:
        states_cycle_1 = [
            InvestigationStateSnapshot(investigation_id="c1_a", cycle_number=1, untriaged_event_count=5, total_event_count=5),
            InvestigationStateSnapshot(investigation_id="c1_b", cycle_number=1, evidence_count=4, graph_density=0.1),
            InvestigationStateSnapshot(investigation_id="c1_c", cycle_number=1, has_confirmed_hypothesis=True, has_formulated_response=False),
        ]
        for st in states_cycle_1:
            w, _, _ = select_worker(st)
            workers_cycle_1.add(w)

        # Should produce diverse worker selections at cycle 1 itself
        assert len(workers_cycle_1) >= 2, f"Expected diverse workers at cycle 1, got {workers_cycle_1}"
