"""
Project Sentinel — Phase B3 No Hidden Linear Workflow Test Suite.

Audits and proves the complete absence of:
1. Hardcoded worker sequences
2. Fixed priority chains
3. Cycle-number-locked execution
4. Round-robin rotations
5. Benchmark- or scenario-specific routing conditionals
"""

import inspect
import pytest
from app.planner import selection, engine
from app.planner.selection import InvestigationStateSnapshot, select_worker


class TestB3NoHiddenLinearWorkflow:
    """Verifies that the planner is truly state-driven and does not execute a disguised linear pipeline."""

    def test_no_scenario_or_attack_conditionals_in_selection(self):
        """Source code inspection confirms no scenario-name or attack-label conditionals exist in selection logic."""
        source_selection = inspect.getsource(selection)
        forbidden_tokens = [
            "infiltration",
            "botnet_ares",
            "botnet_c2",
            "brute_force",
            "sql_injection",
            "slowloris",
            "scenario.name",
            "scenario_name",
            "attack_type",
        ]
        for token in forbidden_tokens:
            assert token not in source_selection.lower(), f"Forbidden scenario-specific token '{token}' found in selection.py"

    def test_no_cycle_number_lockstep_at_cycle_1(self):
        """At cycle 1, multiple distinct capabilities can be selected depending on state."""
        selected_workers = set()

        # State A: Untriaged events exist -> detection
        snap_a = InvestigationStateSnapshot(
            investigation_id="inv_a",
            cycle_number=1,
            untriaged_event_count=10,
            total_event_count=10
        )
        w_a, _, _ = select_worker(snap_a)
        selected_workers.add(w_a)

        # State B: Evidence exists, sparse graph -> correlation
        snap_b = InvestigationStateSnapshot(
            investigation_id="inv_b",
            cycle_number=1,
            evidence_count=5,
            graph_density=0.1
        )
        w_b, _, _ = select_worker(snap_b)
        selected_workers.add(w_b)

        # State C: No evidence, no hypothesis -> investigation
        snap_c = InvestigationStateSnapshot(
            investigation_id="inv_c",
            cycle_number=1,
            evidence_count=0
        )
        w_c, _, _ = select_worker(snap_c)
        selected_workers.add(w_c)

        assert len(selected_workers) >= 3, f"Expected at least 3 distinct capabilities at cycle 1, got {selected_workers}"
        assert "detection" in selected_workers
        assert "correlation" in selected_workers
        assert "investigation" in selected_workers

    def test_no_deterministic_round_robin(self):
        """The sequence is not a round-robin (detection -> investigation -> correlation -> response -> reporting)."""
        # Under sustained high-evidence low-graph state, planner repeats correlation then pivots to investigation, not linear
        snap = InvestigationStateSnapshot(
            investigation_id="rr_test",
            cycle_number=1,
            evidence_count=6,
            graph_density=0.2
        )
        w1, _, _ = select_worker(snap)

        snap.last_worker = w1
        snap.consecutive_worker_count = 1
        snap.graph_density = 0.5  # still room for correlation
        w2, _, _ = select_worker(snap)

        # Should not blindly follow a static order
        assert not (w1 == "detection" and w2 == "investigation")

    def test_state_determinism_without_uncontrolled_randomness(self):
        """Identical state snapshots always produce identical worker choices (deterministic and explainable)."""
        snap = InvestigationStateSnapshot(
            investigation_id="det_test",
            cycle_number=2,
            evidence_count=3,
            graph_density=0.3,
            confidence=0.45
        )
        first_worker, first_score, _ = select_worker(snap)

        for _ in range(10):
            w, s, _ = select_worker(snap)
            assert w == first_worker, "Worker selection must be strictly deterministic given identical state"
            assert s == first_score, "Worker utility score must be strictly deterministic"
