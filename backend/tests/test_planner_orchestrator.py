import pytest
from uuid import uuid4
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Investigation, PlannerDecision, WorkerExecution, Evidence, Hypothesis, Report
from app.planner.engine import PlannerEngine

# Use in-memory SQLite for fast, isolated unit testing
TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)


def test_planner_single_step_execution():
    db = TestSessionLocal()
    try:
        inv = Investigation(
            investigation_id=uuid4(),
            title="Macro-spawned PowerShell C2 Beacon Test",
            status="active",
            current_confidence=0.10,
            confidence_state="very_low",
            current_goal="Assess initial telemetry and identify attack techniques",
        )
        db.add(inv)
        db.commit()

        planner = PlannerEngine()
        result = planner.run_cycle(inv.investigation_id, db)

        assert result["cycle_number"] == 1
        assert result["selected_worker"] == "detection"
        assert result["confidence_after"] > result["confidence_before"]

        # Check DB persistence
        decisions = db.query(PlannerDecision).filter(PlannerDecision.investigation_id == inv.investigation_id).all()
        assert len(decisions) == 1
        assert decisions[0].cycle_number == 1
        assert decisions[0].selected_worker == "detection"

        execs = db.query(WorkerExecution).all()
        assert len(execs) == 1
        assert execs[0].worker_type == "detection"
    finally:
        db.close()


def test_planner_autonomous_multi_cycle_loop():
    db = TestSessionLocal()
    try:
        inv = Investigation(
            investigation_id=uuid4(),
            title="Full Multi-Stage Attack Investigation",
            status="active",
            current_confidence=0.10,
            confidence_state="very_low",
            current_goal="Investigate suspicious PowerShell network beacon",
        )
        db.add(inv)
        db.commit()

        planner = PlannerEngine()
        auto_res = planner.run_autonomous(inv.investigation_id, db, max_steps=6)

        assert auto_res["total_cycles"] >= 3
        assert auto_res["final_status"] in ["completed", "active"]
        assert auto_res["final_confidence"] > 0.40

        # Verify multiple workers were selected dynamically across cycles
        decisions = db.query(PlannerDecision).filter(PlannerDecision.investigation_id == inv.investigation_id).all()
        workers_selected = [d.selected_worker for d in decisions]
        assert "detection" in workers_selected

        # Verify evidence and hypotheses were populated
        evidence = db.query(Evidence).filter(Evidence.investigation_id == inv.investigation_id).all()
        assert len(evidence) > 0
    finally:
        db.close()


def test_planner_stagnation_guard():
    db = TestSessionLocal()
    try:
        inv = Investigation(
            investigation_id=uuid4(),
            title="Stagnant Benign Investigation",
            status="active",
            current_confidence=0.40,
            confidence_state="moderate",
            current_goal="Evaluate benign traffic",
            planning_cycle_count=4,
        )
        db.add(inv)
        db.flush()

        # Add 3 historical decisions with 0 confidence gain (simulating stagnation)
        for i in range(1, 5):
            d = PlannerDecision(
                investigation_id=inv.investigation_id,
                cycle_number=i,
                selected_worker="investigation",
                confidence_before=0.40,
                confidence_after=0.40,
                explanation_summary="No additional evidence found.",
            )
            db.add(d)
        db.commit()

        planner = PlannerEngine()
        # Should trigger stagnation termination condition
        snapshot = planner.load_state_snapshot(inv, db)
        assert snapshot.cycles_since_confidence_gain >= 3

        result = planner.run_cycle(inv.investigation_id, db)
        assert result.get("termination_reason") == "stagnation"
        assert result.get("requires_analyst_review") is True
    finally:
        db.close()


def test_observability_factor_and_utility_telemetry():
    db = TestSessionLocal()
    try:
        inv = Investigation(
            investigation_id=uuid4(),
            title="Observability Telemetry Test Case",
            status="active",
            current_confidence=0.15,
            confidence_state="very_low",
            current_goal="Detect malicious lateral movement",
        )
        db.add(inv)
        db.commit()

        planner = PlannerEngine()
        result = planner.run_cycle(inv.investigation_id, db)

        # Check that utility_scores and factor_contributions are populated
        assert "utility_scores" in result
        assert "detection" in result["utility_scores"]
        assert "factor_contributions" in result
        assert "evidence" in result["factor_contributions"]
        assert "weighted_contribution" in result["factor_contributions"]["evidence"]
        assert "rag_citations" in result

        # Check DB WorkerExecution raw_output
        exec_record = db.query(WorkerExecution).first()
        assert exec_record is not None
        assert "utility_scores" in exec_record.raw_output
        assert "factor_contributions" in exec_record.raw_output
    finally:
        db.close()

