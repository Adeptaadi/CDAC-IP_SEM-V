"""
Phase B3 Backend Invariants Tests.

Verifies fundamental backend invariants:
1. Deduplication and content fingerprinting invariant
2. Confidence non-increase invariant under zero novelty
3. Contradiction penalty and ceiling invariant
4. Stagnation invariant
5. Termination safety invariant
"""

import uuid
import pytest
from app.models.evidence import Evidence, compute_evidence_fingerprint
from app.schemas.contracts import WorkerResult
from app.planner.confidence import ConfidenceEngine
from app.planner.selection import InvestigationStateSnapshot, should_terminate
from app.config import settings


class TestB3BackendInvariants:
    """Verifies that mathematical and architectural invariants hold strictly."""

    def test_deduplication_fingerprint_invariant(self):
        """Identical content generates identical sha256 fingerprint."""
        desc = "PowerShell encoded command execution"
        entity_refs = {"ip": "192.168.1.50", "cmd": "-enc AAAA"}
        hash1 = compute_evidence_fingerprint(desc, entity_refs)
        hash2 = compute_evidence_fingerprint(desc, entity_refs)

        assert hash1 == hash2
        assert len(hash1) == 64

        ev1 = Evidence(investigation_id="inv1", content_hash=hash1, is_novel=True, observation_count=1)
        ev2 = Evidence(investigation_id="inv1", content_hash=hash2, is_duplicate=True, is_novel=False, observation_count=2)

        assert ev1.content_hash == ev2.content_hash
        assert ev1.is_novel is True
        assert ev2.is_duplicate is True
        assert ev2.is_novel is False

    def test_confidence_non_increase_under_zero_novelty_invariant(self):
        """Zero novel evidence strictly prevents positive evidence delta regardless of cycle count."""
        engine = ConfidenceEngine()
        dummy_res = WorkerResult(
            task_id=uuid.uuid4(),
            worker_type="investigation",
            status="success",
            reasoning_summary="Completed investigation without new evidence",
            success=True,
            confidence_signal=0.8,
            findings=[],
            telemetry_consumed=0
        )
        factors = engine.compute_factors(
            worker_result=dummy_res,
            evidence_count_this_cycle=0,
            novel_evidence_count=0,
            total_evidence=5,
            edges_added=0,
            has_novel_knowledge=False
        )
        assert factors["evidence"] == 0.0, "Evidence factor delta must be 0.0 when novel evidence count is 0"

        delta = engine.compute_delta(factors)
        new_conf = engine.update(current_confidence=0.55, delta=delta)
        assert new_conf <= 0.55, f"Confidence grew from 0.55 to {new_conf} despite 0 novel evidence!"

    def test_contradiction_ceiling_invariant(self):
        """Active contradictions cap confidence strictly at <= 0.60 and apply significant penalty."""
        engine = ConfidenceEngine()
        dummy_res = WorkerResult(
            task_id=uuid.uuid4(),
            worker_type="investigation",
            status="success",
            reasoning_summary="Discovered contradictions",
            success=True,
            confidence_signal=0.9,
            findings=[],
            telemetry_consumed=0
        )
        # Even with high novel evidence and edges added, contradiction must penalize and cap
        factors = engine.compute_factors(
            worker_result=dummy_res,
            evidence_count_this_cycle=5,
            novel_evidence_count=5,
            total_evidence=10,
            edges_added=5,
            unresolved_contradictions_count=2
        )
        assert factors["contradiction"] <= -0.24, f"Contradiction penalty {factors['contradiction']} too weak"

        # Apply update to high initial confidence (e.g. 0.85)
        new_conf = engine.update(
            current_confidence=0.85,
            delta=0.5,  # even with a large positive delta
            unresolved_contradictions_count=2
        )
        assert new_conf <= 0.60, f"Contradiction ceiling violated: confidence {new_conf} > 0.60"

    def test_stagnation_detection_invariant(self):
        """Reaching STAGNATION_CYCLE_LIMIT consecutive zero-progress cycles triggers stagnation termination."""
        snap_stagnant = InvestigationStateSnapshot(
            investigation_id="test-stag",
            confidence=0.40,
            cycle_number=4,
            cycles_since_meaningful_progress=settings.STAGNATION_CYCLE_LIMIT,
            cycles_since_confidence_gain=settings.STAGNATION_CYCLE_LIMIT
        )
        terminated = should_terminate(snap_stagnant)

        assert terminated is True
        assert snap_stagnant.termination_reason == "stagnation"
        assert snap_stagnant.termination_classification == "stagnation_escalation"

    def test_max_cycles_safety_guard_invariant(self):
        """Reaching MAX_PLANNING_CYCLES forces termination as a safety guard regardless of confidence."""
        snap_max = InvestigationStateSnapshot(
            investigation_id="test-max",
            confidence=0.50,
            cycle_number=settings.MAX_PLANNING_CYCLES,
            cycles_since_meaningful_progress=0,
            cycles_since_confidence_gain=0
        )
        terminated = should_terminate(snap_max)

        assert terminated is True
        assert snap_max.termination_reason == "max_cycles_reached"
        assert snap_max.termination_classification == "safety_bound"
