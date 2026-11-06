"""
Project Sentinel — Phase B3 Metrics Mathematical Audit Test Suite.

Audits every formula, metric calculation, denominator boundary, and numerical invariant
against independent theoretical recomputations.
"""

import pytest
from app.planner.confidence import ConfidenceEngine, logit, sigmoid
from app.schemas.contracts import WorkerResult
from uuid import uuid4
from app.eval.metrics import (
    compute_expected_calibration_error,
    compute_planner_routing_precision,
    compute_replanning_effectiveness,
    compute_evidence_coverage,
    compute_evidence_precision,
    compute_citation_coverage,
    compute_hallucination_rate,
    compute_report_completeness,
    compute_detection_metrics,
)


class TestB3MetricsMathematicalAudit:
    """Rigorous numerical and formula verification."""

    def test_confidence_factor_numerical_trace(self):
        """Input -> Formula -> Weight -> Output -> Final Confidence trace holds exact math."""
        engine = ConfidenceEngine()
        res = WorkerResult(
            task_id=uuid4(),
            worker_type="detection",
            status="success",
            reasoning_summary="Detection completed",
            confidence_signal=0.8,
            findings=[],
            telemetry_consumed=10
        )
        # Factors:
        # detection: 0.8 - 0.5 = 0.30
        # evidence: 2 novel / 2.0 = 1.0 * source_diversity (1.0) = 1.0
        factors = engine.compute_factors(
            worker_result=res,
            evidence_count_this_cycle=2,
            novel_evidence_count=2,
            distinct_sources=2,
            total_evidence=2
        )
        assert factors["detection"] == pytest.approx(0.30, abs=1e-4)
        assert factors["evidence"] == pytest.approx(1.00, abs=1e-4)

        # Delta = sum(weight * factor)
        # weight detection: 0.15 * 0.30 = 0.045
        # weight evidence: 0.20 * 1.00 = 0.200
        # total delta = 0.245
        delta = engine.compute_delta(factors)
        assert delta == pytest.approx(0.045 + 0.200, abs=1e-4)

        # Logit update: sigmoid(logit(0.50) + 0.245)
        # logit(0.50) = 0.0
        # sigmoid(0.245) = 1 / (1 + exp(-0.245)) = 0.56096
        new_conf = engine.update(0.50, delta)
        expected_conf = 1.0 / (1.0 + 2.718281828459045 ** (-0.245))
        assert new_conf == pytest.approx(expected_conf, abs=1e-4)

    def test_no_confidence_increase_without_information_gain(self):
        """Zero novel evidence produces delta_evidence == 0.0 and no confidence increase."""
        engine = ConfidenceEngine()
        res = WorkerResult(
            task_id=uuid4(),
            worker_type="investigation",
            status="success",
            reasoning_summary="Zero yield investigation",
            confidence_signal=0.5,
            findings=[],
            telemetry_consumed=0
        )
        factors = engine.compute_factors(
            worker_result=res,
            evidence_count_this_cycle=0,
            novel_evidence_count=0,
            edges_added=0,
            has_novel_knowledge=False
        )
        assert factors["evidence"] == 0.0
        assert factors["correlation"] == 0.0
        assert factors["knowledge"] == 0.0

        delta = engine.compute_delta(factors)
        assert delta <= 0.0
        assert engine.update(0.60, delta) <= 0.60

    def test_contradiction_penalizes_and_caps_confidence(self):
        """Contradictory evidence produces negative delta and caps confidence at 0.60."""
        engine = ConfidenceEngine()
        res = WorkerResult(
            task_id=uuid4(),
            worker_type="investigation",
            status="success",
            reasoning_summary="Found contradictions",
            confidence_signal=0.5,
            findings=[],
            telemetry_consumed=0
        )
        factors = engine.compute_factors(
            worker_result=res,
            evidence_count_this_cycle=1,
            novel_evidence_count=1,
            total_evidence=5,
            unresolved_contradictions_count=2
        )
        # ratio = 2 / 5 = 0.40 -> delta_contradiction = -0.60 * 0.40 = -0.24
        assert factors["contradiction"] <= -0.24

        # Even starting at 0.85, update must clamp to <= 0.60
        capped_conf = engine.update(0.85, delta=0.5, unresolved_contradictions_count=2)
        assert capped_conf <= 0.60

    def test_metrics_empty_boundary_and_null_safety(self):
        """All evaluation metrics handle zero denominators gracefully without raising exceptions."""
        assert compute_expected_calibration_error([], []) == 0.0
        assert compute_planner_routing_precision([]) == 0.0
        assert compute_replanning_effectiveness([]) == 1.0
        assert compute_evidence_coverage([], []) == 1.0
        assert compute_evidence_precision([], []) == 1.0
        assert compute_citation_coverage([], []) == 1.0
        assert compute_hallucination_rate([], []) == 0.0
        assert compute_report_completeness({}) == 0.0
        cm = compute_detection_metrics([], [])
        assert cm["precision"] == 0.0
        assert cm["recall"] == 0.0
        assert cm["f1"] == 0.0
