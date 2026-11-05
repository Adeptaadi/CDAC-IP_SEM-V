"""Unit & Integration Tests for P0 Unified Investigation Workspace Projection and Provenance Layer.

Verifies:
1. Basic Investigation Projection (no planner executions)
2. Planner Cognitive Projection (observations, unresolved questions, decisions, rationale)
3. Multi-Cycle Orchestration History (chronological order, deltas, evidence counts)
4. Worker Execution Failure Representation (truthful failure exposure)
5. Evidence -> Decision Provenance (direct vs derived vs legacy_unlinked)
6. Recommendation -> Evidence Provenance (direct supporting findings)
7. Human Review -> Recommendation Provenance (linked review requests and decisions)
8. Absence of Fabricated Recommendations (truthful null handling)
9. Backward Compatibility of Core Endpoints
10. HTTP Endpoint Integration via FastAPI TestClient (GET /api/investigations/{id}/workspace)
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app as fastapi_app
import app.models  # Ensure all 41 models are registered
from app.models.investigation import Investigation
from app.models.evidence import Evidence, TimelineEvent, Hypothesis
from app.models.orchestration import PlannerDecision, WorkerExecution, AgentTask
from app.models.reporting import Report
from app.models.response import Recommendation, HumanReview, ResponseSimulation
from app.investigation.workspace_service import workspace_projection_service_instance


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(fastapi_app)
    yield client
    fastapi_app.dependency_overrides.clear()


# =========================================================================
# Test 1: Basic Investigation Projection (Initial State, No Planner Runs)
# =========================================================================
def test_basic_investigation_projection_no_planner(db_session):
    """An investigation with no Planner execution returns valid threat data and null decision fields."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Infiltration Scenario: Initial Triage",
        status="investigating",
        current_confidence=0.15,
        confidence_state="low",
        current_goal="Identify suspicious outbound connections",
        planning_cycle_count=0,
        state_version=1,
    )
    db_session.add(inv)
    db_session.commit()

    proj = workspace_projection_service_instance.build_workspace_projection(inv.investigation_id, db=db_session)

    # Threat verification
    assert proj.threat.investigation_id == str(inv.investigation_id)
    assert proj.threat.title == inv.title
    assert proj.threat.status == "investigating"
    assert proj.threat.confidence == 0.15
    assert proj.threat.current_cycle == 0
    assert proj.threat.data_provenance is not None
    assert proj.threat.data_provenance.source_type == "benchmark_derived_scenario"

    # Planner cognitive state verification (no fabricated decisions)
    assert proj.planner.current_decision is None
    assert proj.planner.decision_rationale is None
    assert proj.planner.active_capability is None
    assert proj.planner.is_replanning is False
    assert len(proj.planner.unresolved_questions) > 0
    assert "No autonomous planning cycles" in proj.planner.current_observation

    # Collections must be empty/null, not fabricated
    assert len(proj.key_findings) == 0
    assert len(proj.orchestration_history) == 0
    assert proj.recommendation is None
    assert proj.human_review is None


# =========================================================================
# Test 2: Planner Cognitive Projection (Active Investigation State)
# =========================================================================
def test_planner_cognitive_projection(db_session):
    """Planner decision appears correctly with observation, questions, decision, and rationale."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Botnet C2 Beaconing Hunt",
        status="investigating",
        current_confidence=0.68,
        confidence_state="high",
        current_goal="Uncover C2 infrastructure",
        planning_cycle_count=1,
        state_version=2,
    )
    db_session.add(inv)

    dec = PlannerDecision(
        decision_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        cycle_number=1,
        selected_worker="correlation",
        selection_score=1.15,
        knowledge_need="Evaluate network endpoints communicating with external IP",
        confidence_before=0.20,
        confidence_after=0.68,
        explanation_summary="Correlation worker constructed entity graph linking WORKSTATION-10 to external IP 18.219.211.138.",
    )
    db_session.add(dec)
    db_session.commit()

    proj = workspace_projection_service_instance.build_workspace_projection(inv.investigation_id, db=db_session)

    assert proj.planner.current_decision == "Execute capability for worker 'correlation' (Cycle 1)"
    assert proj.planner.current_observation == dec.explanation_summary
    assert proj.planner.decision_rationale == dec.explanation_summary
    assert proj.planner.rationale_source == "persisted"
    assert proj.planner.active_capability is not None
    assert proj.planner.active_capability.worker_type == "correlation"
    assert len(proj.planner.unresolved_questions) > 0


# =========================================================================
# Test 3: Multi-Cycle History (Chronological Order & Deltas)
# =========================================================================
def test_multi_cycle_orchestration_history(db_session):
    """Multiple Planner cycles appear in strict chronological order with calculated deltas."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Lateral Movement Multi-Cycle Hunt",
        status="investigating",
        current_confidence=0.82,
        confidence_state="high",
        planning_cycle_count=3,
        state_version=4,
    )
    db_session.add(inv)

    # Add 3 cycles
    dec1 = PlannerDecision(
        decision_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        cycle_number=1,
        selected_worker="detection",
        selection_score=1.0,
        confidence_before=0.10,
        confidence_after=0.35,
        explanation_summary="Detection worker flagged suspicious PowerShell execution.",
    )
    dec2 = PlannerDecision(
        decision_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        cycle_number=2,
        selected_worker="correlation",
        selection_score=1.2,
        confidence_before=0.35,
        confidence_after=0.65,
        explanation_summary="Correlation established host-to-process relationships.",
    )
    dec3 = PlannerDecision(
        decision_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        cycle_number=3,
        selected_worker="investigation",
        selection_score=0.9,
        confidence_before=0.65,
        confidence_after=0.82,
        explanation_summary="Investigation validated MITRE technique T1059.001.",
    )
    db_session.add_all([dec1, dec2, dec3])
    db_session.commit()

    proj = workspace_projection_service_instance.build_workspace_projection(inv.investigation_id, db=db_session)

    history = proj.orchestration_history
    assert len(history) == 3
    assert [s.cycle for s in history] == [1, 2, 3]
    assert history[0].selected_worker == "detection"
    assert history[0].confidence_delta == pytest.approx(0.25, abs=0.001)
    assert history[1].selected_worker == "correlation"
    assert history[1].confidence_delta == pytest.approx(0.30, abs=0.001)
    assert history[2].selected_worker == "investigation"
    assert history[2].confidence_delta == pytest.approx(0.17, abs=0.001)


# =========================================================================
# Test 4: Worker Failure Representation (Truthful Exposure)
# =========================================================================
def test_worker_failure_representation(db_session):
    """A failed worker execution is truthfully represented as status='failed'."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Failed Capability Investigation",
        status="investigating",
        current_confidence=0.20,
        confidence_state="low",
        planning_cycle_count=1,
        state_version=2,
    )
    db_session.add(inv)

    dec = PlannerDecision(
        decision_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        cycle_number=1,
        selected_worker="correlation",
        confidence_before=0.20,
        confidence_after=0.20,
        explanation_summary="Attempted correlation over corrupt telemetry.",
    )
    db_session.add(dec)

    exec_fail = WorkerExecution(
        execution_id=uuid.uuid4(),
        decision_id=dec.decision_id,
        worker_type="correlation",
        status="failed",
        raw_output={"error": "Telemetry stream timeout"},
        latency_ms=1200,
    )
    db_session.add(exec_fail)
    db_session.commit()

    proj = workspace_projection_service_instance.build_workspace_projection(inv.investigation_id, db=db_session)

    assert len(proj.orchestration_history) == 1
    step = proj.orchestration_history[0]
    assert step.status == "failed"
    assert step.latency_ms == 1200


# =========================================================================
# Test 5: Evidence -> Decision Provenance (Direct Linkage)
# =========================================================================
def test_evidence_decision_direct_provenance(db_session):
    """Directly linked evidence records report provenance_status='direct' with exact foreign keys."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Provenance Verification Hunt",
        status="investigating",
        current_confidence=0.45,
        confidence_state="medium",
        planning_cycle_count=1,
    )
    db_session.add(inv)

    dec_id = uuid.uuid4()
    exec_id = uuid.uuid4()
    dec = PlannerDecision(
        decision_id=dec_id,
        investigation_id=inv.investigation_id,
        cycle_number=1,
        selected_worker="detection",
        confidence_before=0.10,
        confidence_after=0.45,
        explanation_summary="Triage step completed.",
    )
    db_session.add(dec)

    ev = Evidence(
        evidence_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        source_type="worker_output",
        description="Encoded PowerShell cradle observed on host WS-01",
        entity_refs={"hosts": ["WS-01"], "processes": ["powershell.exe"]},
        produced_by_worker="detection",
        planner_decision_id=dec_id,
        worker_execution_id=exec_id,
    )
    db_session.add(ev)
    db_session.commit()

    proj = workspace_projection_service_instance.build_workspace_projection(inv.investigation_id, db=db_session)

    assert len(proj.key_findings) == 1
    kf = proj.key_findings[0]
    assert kf.provenance.provenance_status == "direct"
    assert kf.provenance.planner_decision_id == str(dec_id)
    assert kf.provenance.worker_execution_id == str(exec_id)
    assert kf.provenance.source_worker == "detection"


# =========================================================================
# Test 6: Legacy Evidence Graceful Handling (Unlinked Records)
# =========================================================================
def test_legacy_evidence_graceful_handling(db_session):
    """Evidence without FK relationships degrades gracefully to 'legacy_unlinked' without crash."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Legacy Data Triage",
        status="active",
        current_confidence=0.10,
        confidence_state="very_low",
    )
    db_session.add(inv)

    legacy_ev = Evidence(
        evidence_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        source_type="log",
        description="Historical log entry with unrecorded execution link",
        entity_refs={"hosts": ["SRV-LEGACY"]},
        produced_by_worker=None,
        planner_decision_id=None,
        worker_execution_id=None,
    )
    db_session.add(legacy_ev)
    db_session.commit()

    proj = workspace_projection_service_instance.build_workspace_projection(inv.investigation_id, db=db_session)

    assert len(proj.key_findings) == 1
    kf = proj.key_findings[0]
    assert kf.provenance.provenance_status == "legacy_unlinked"
    assert kf.provenance.planner_decision_id is None
    assert kf.provenance.worker_execution_id is None


# =========================================================================
# Test 7: Recommendation -> Evidence Provenance
# =========================================================================
def test_recommendation_evidence_provenance(db_session):
    """Recommendations with supporting_evidence_ids expose direct supporting findings."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Completed Containment Hunt",
        status="completed",
        current_confidence=0.92,
        confidence_state="confirmed",
    )
    db_session.add(inv)

    ev1 = Evidence(
        evidence_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        source_type="worker_output",
        description="Outbound C2 beaconing on port 443 to 13.58.225.34",
        entity_refs={"ips": ["13.58.225.34"]},
    )
    db_session.add(ev1)

    rep = Report(
        report_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        executive_summary="Incident verified.",
        technical_body="Detailed technical report body.",
        final_confidence=0.92,
    )
    db_session.add(rep)

    rec = Recommendation(
        recommendation_id=uuid.uuid4(),
        report_id=rep.report_id,
        action="Block IP 13.58.225.34 at border firewall",
        risk_level="medium",
        impact_summary="Prevents outbound C2 beaconing.",
        requires_approval=True,
        approval_status="pending",
        supporting_evidence_ids=[ev1.evidence_id],
    )
    db_session.add(rec)
    db_session.commit()

    proj = workspace_projection_service_instance.build_workspace_projection(inv.investigation_id, db=db_session)

    assert proj.recommendation is not None
    assert proj.recommendation.action == rec.action
    assert proj.recommendation.provenance_status == "direct"
    assert len(proj.recommendation.supporting_findings) == 1
    supp = proj.recommendation.supporting_findings[0]
    assert supp.finding_id == str(ev1.evidence_id)
    assert supp.summary == ev1.description


# =========================================================================
# Test 8: Human Review -> Recommendation Provenance
# =========================================================================
def test_human_review_recommendation_provenance(db_session):
    """Human review requests link directly to the recommendation and reflect analyst decision."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Awaiting Review Incident",
        status="awaiting_review",
        current_confidence=0.88,
        confidence_state="confirmed",
    )
    db_session.add(inv)

    rep = Report(
        report_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        executive_summary="Report summary.",
        technical_body="Technical body.",
        final_confidence=0.88,
    )
    db_session.add(rep)

    rec = Recommendation(
        recommendation_id=uuid.uuid4(),
        report_id=rep.report_id,
        action="Isolate Host WORKSTATION-04",
        risk_level="high",
        impact_summary="Network isolation.",
        requires_approval=True,
        approval_status="approved",
    )
    db_session.add(rec)

    rev = HumanReview(
        id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        recommendation_id=rec.recommendation_id,
        requested_action=rec.action,
        risk_level="high",
        status="approved",
        analyst_comments="Validated CobaltStrike beaconing. Approved network containment.",
        reviewed_at=datetime.now(timezone.utc),
    )
    db_session.add(rev)
    db_session.commit()

    proj = workspace_projection_service_instance.build_workspace_projection(inv.investigation_id, db=db_session)

    assert proj.human_review is not None
    assert proj.human_review.recommendation_id == str(rec.recommendation_id)
    assert proj.human_review.status == "approved"
    assert proj.human_review.decision == "approved"
    assert proj.human_review.provenance_status == "direct"
    assert "CobaltStrike" in proj.human_review.analyst_comments


# =========================================================================
# Test 9: Absence of Fabricated Recommendations (Truthful Null)
# =========================================================================
def test_no_recommendation_returns_null(db_session):
    """When an investigation has no reports or recommendations, recommendation is null."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Early Stage Investigation",
        status="investigating",
        current_confidence=0.25,
        confidence_state="low",
    )
    db_session.add(inv)
    db_session.commit()

    proj = workspace_projection_service_instance.build_workspace_projection(inv.investigation_id, db=db_session)
    assert proj.recommendation is None
    assert proj.human_review is None


# =========================================================================
# Test 10: Backward Compatibility of Existing APIs
# =========================================================================
def test_existing_apis_remain_functional(test_client, db_session):
    """Existing endpoints continue to work without error."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Backward Compat Investigation",
        status="active",
        current_confidence=0.30,
        confidence_state="low",
    )
    db_session.add(inv)
    db_session.commit()

    # Core GET list
    res_list = test_client.get("/api/investigations")
    assert res_list.status_code == 200
    assert any(item["investigation_id"] == str(inv.investigation_id) for item in res_list.json())

    # Core GET single
    res_single = test_client.get(f"/api/investigations/{inv.investigation_id}")
    assert res_single.status_code == 200
    assert res_single.json()["title"] == inv.title

    # Planner state snapshot endpoint
    res_state = test_client.get(f"/api/planner/investigations/{inv.investigation_id}/state")
    assert res_state.status_code == 200
    assert res_state.json()["investigation_id"] == str(inv.investigation_id)


# =========================================================================
# Test 11: HTTP Endpoint Integration (GET /api/investigations/{id}/workspace)
# =========================================================================
def test_workspace_api_endpoint(test_client, db_session):
    """GET /api/investigations/{id}/workspace returns 200 with complete valid schema."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="HTTP Endpoint Integration Investigation",
        status="investigating",
        current_confidence=0.55,
        confidence_state="medium",
        planning_cycle_count=1,
    )
    db_session.add(inv)
    db_session.commit()

    # Successful call
    res = test_client.get(f"/api/investigations/{inv.investigation_id}/workspace")
    assert res.status_code == 200
    data = res.json()
    assert "threat" in data
    assert "planner" in data
    assert "key_findings" in data
    assert "orchestration_history" in data
    assert "recommendation" in data
    assert "human_review" in data
    assert "workspace_metadata" in data
    assert data["threat"]["investigation_id"] == str(inv.investigation_id)

    # 404 on nonexistent investigation
    missing_id = uuid.uuid4()
    res_404 = test_client.get(f"/api/investigations/{missing_id}/workspace")
    assert res_404.status_code == 404
