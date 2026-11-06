"""
Project Sentinel — Phase B3 Long-Run Orchestration Test Suite.

Audits extended multi-cycle investigations (up to 15 cycles) to verify that
planning behavior remains robust and does not degenerate into infinite loops,
hidden cycles, or premature termination.
"""

import os
import json
import pytest
from app.planner.selection import InvestigationStateSnapshot, select_worker, should_terminate
from app.planner.confidence import ConfidenceEngine
from app.config import settings


class TestB3LongRunOrchestration:
    """Verifies behavioral integrity across long-run investigation trajectories."""

    def test_long_run_artifact_generated_and_valid(self):
        """b3_long_run_execution_traces.json exists and captures all 6 conditions."""
        assert os.path.exists("b3_long_run_execution_traces.json")
        with open("b3_long_run_execution_traces.json", "r", encoding="utf-8") as f:
            runs = json.load(f)
        assert len(runs) == 6
        expected_conds = {
            "productive_telemetry",
            "duplicate_heavy_telemetry",
            "contradictory_telemetry",
            "ambiguous_telemetry",
            "zero_telemetry",
            "intermittent_worker_failures",
        }
        actual_conds = set(r["condition"] for r in runs)
        assert expected_conds.issubset(actual_conds)

    def test_long_run_duplicate_heavy_stagnation_termination(self):
        """Under duplicate-heavy telemetry, planner terminates via stagnation rather than looping indefinitely."""
        with open("b3_long_run_execution_traces.json", "r", encoding="utf-8") as f:
            runs = {r["condition"]: r for r in json.load(f)}

        dup_run = runs["duplicate_heavy_telemetry"]
        assert dup_run["final_status"] == "terminated"
        assert dup_run["termination_classification"] == "stagnation_escalation"
        # Stagnation happens within 4 cycles
        assert len(dup_run["cycles"]) <= 4

    def test_long_run_zero_telemetry_rapid_escalation(self):
        """Under zero telemetry, planner escalates via stagnation within STAGNATION_CYCLE_LIMIT cycles."""
        with open("b3_long_run_execution_traces.json", "r", encoding="utf-8") as f:
            runs = {r["condition"]: r for r in json.load(f)}

        zero_run = runs["zero_telemetry"]
        assert zero_run["final_status"] == "terminated"
        assert zero_run["termination_classification"] == "stagnation_escalation"
        assert len(zero_run["cycles"]) <= 4

    def test_long_run_productive_telemetry_successful_convergence(self):
        """Under productive telemetry, planner progresses confidence and reaches resolution."""
        with open("b3_long_run_execution_traces.json", "r", encoding="utf-8") as f:
            runs = {r["condition"]: r for r in json.load(f)}

        prod_run = runs["productive_telemetry"]
        # Confidence must grow and reach high confidence band
        final_conf = prod_run["cycles"][-1]["confidence_after"]
        assert final_conf >= 0.85
        assert prod_run["final_status"] == "terminated"
        assert prod_run["termination_classification"] == "uncalibrated_heuristic"

    def test_long_run_intermittent_failures_triggers_replans(self):
        """Intermittent worker failures trigger active replanning events without crashing."""
        with open("b3_long_run_execution_traces.json", "r", encoding="utf-8") as f:
            runs = {r["condition"]: r for r in json.load(f)}

        fail_run = runs["intermittent_worker_failures"]
        replans = [c for c in fail_run["cycles"] if c["is_replanning"]]
        assert len(replans) >= 2, "Expected multiple replan triggers during intermittent failures"
