import pytest
from app.eval.metrics import (
    compute_evidence_coverage,
    compute_hallucination_rate,
    compute_expected_calibration_error
)
from app.eval.runner import BenchmarkRunner
from app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


def test_evidence_coverage_calculation():
    extracted = ["T1059.001", "T1071.001", "T1046"]
    gold = ["T1059.001", "T1071.001", "T1046", "T1021.002"]
    cov = compute_evidence_coverage(extracted, gold)
    assert cov == 0.75

    # 100% match
    assert compute_evidence_coverage(gold, gold) == 1.0
    # Empty gold edge case
    assert compute_evidence_coverage(extracted, []) == 1.0


def test_hallucination_rate_calculation():
    verified_eids = ["eid-1", "eid-2", "eid-3"]
    grounded_claims = [
        {"claim_id": "c1", "evidence_ids": ["eid-1"]},
        {"claim_id": "c2", "evidence_ids": ["eid-2", "eid-3"]},
    ]
    hallucinated_claims = [
        {"claim_id": "c3", "evidence_ids": []},
        {"claim_id": "c4", "evidence_ids": ["eid-999_fake"]},
    ]
    assert compute_hallucination_rate(grounded_claims, verified_eids) == 0.0
    assert compute_hallucination_rate(hallucinated_claims, verified_eids) == 1.0
    assert compute_hallucination_rate(grounded_claims + hallucinated_claims, verified_eids) == 0.5


def test_expected_calibration_error_calculation():
    confidences = [0.90, 0.85, 0.80, 0.20, 0.10]
    labels = [1, 1, 1, 0, 0]
    ece = compute_expected_calibration_error(confidences, labels, num_bins=5)
    assert 0.0 <= ece <= 0.25


def test_end_to_end_scenario_benchmark_evaluation():
    db = TestSession()
    try:
        runner = BenchmarkRunner()
        res = runner.evaluate_scenario("infiltration", db, max_cycles=4)
        assert res["status"] == "passed"
        assert res["accuracy"] >= 0.85
        assert res["evidence_coverage"] > 0.50
        assert res["hallucination_rate"] <= 0.05
    finally:
        db.close()
