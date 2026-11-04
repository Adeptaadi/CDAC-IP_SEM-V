import uuid
from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # Register all 41 schema entities
from app.models.investigation import Investigation, InvestigationEvent
from app.models.evidence import Evidence, TimelineEvent, Hypothesis
from app.models.reporting import Report, ReportSection
from app.models.response import HumanReview, ResponseSimulation, Recommendation
from app.reporting import (
    reporting_service_instance,
    IncidentReportPayload,
    ReportValidationResult,
)
from app.response import (
    response_simulation_service,
    human_review_service,
    SimulationRequest,
    ReviewSubmissionPayload,
)
from app.api.reporting_router import (
    generate_report as api_generate_report,
    get_report as api_get_report,
    validate_report as api_validate_report,
)
from app.api.review_router import (
    list_pending_reviews as api_list_pending_reviews,
    process_review_decision as api_process_review,
    simulate_response_action as api_simulate_response,
)


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for Phase 11 tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_investigation(db_session):
    """Creates a sample investigation with timeline, evidence, and hypotheses."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="APT29 Infiltration Investigation",
        status="investigating",
        current_confidence=0.88,
        confidence_state="high",
        current_goal="Identify exfiltration endpoints",
    )
    db_session.add(inv)
    db_session.flush()

    # Evidence
    ev = Evidence(
        evidence_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        source_type="log",
        description="Encrypted archive staging in C:\\ProgramData",
        entity_refs={"hosts": ["DC-01", "WS-04"], "ips": ["198.51.100.55"]},
    )
    db_session.add(ev)

    # Timeline
    te = TimelineEvent(
        event_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        evidence_id=ev.evidence_id,
        occurred_at=datetime.utcnow(),
        event_summary="Data staging in temporary directory",
        mitre_technique_id="T1074.001",
        sequence_position=1,
    )
    db_session.add(te)

    # Hypothesis
    hyp = Hypothesis(
        hypothesis_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        label="Data Staging prior to Exfiltration",
        confidence=0.88,
        status="confirmed",
        mitre_technique_ids=["T1074.001"],
    )
    db_session.add(hyp)
    db_session.commit()
    db_session.refresh(inv)
    return inv


def test_reporting_service_synthesis_and_db_persistence(db_session, test_investigation):
    """Verify ReportingService compiles all artifacts into an analyst-ready report with all required sections."""
    report_payload = reporting_service_instance.generate_report(
        investigation_id=test_investigation.investigation_id,
        db=db_session,
    )

    assert report_payload.report_id is not None
    assert report_payload.final_confidence == 0.88
    assert report_payload.severity == "critical"
    assert len(report_payload.sections) == 7
    assert "DC-01" in report_payload.affected_entities["hosts"]
    assert "198.51.100.55" in report_payload.affected_entities["ips"]

    # Verify database persistence
    db_report = db_session.query(Report).filter_by(report_id=report_payload.report_id).first()
    assert db_report is not None
    assert float(db_report.final_confidence) == 0.88

    sections = db_session.query(ReportSection).filter_by(report_id=report_payload.report_id).all()
    assert len(sections) == 7

    recs = db_session.query(Recommendation).filter_by(report_id=report_payload.report_id).all()
    assert len(recs) >= 2


def test_report_validation():
    """Verify report validation checks completeness, sections, and confidence bounds."""
    # Complete report
    rep = IncidentReportPayload(
        investigation_id=uuid.uuid4(),
        title="Test Incident Report",
        severity="high",
        incident_classification="Intrusion",
        executive_summary="Summary",
        technical_body="Body",
        final_confidence=0.80,
        sections=[
            {"title": "Executive Summary", "order": 1, "content": "Text"},
            {"title": "Technical Findings", "order": 2, "content": "Text"},
            {"title": "Incident Timeline", "order": 3, "content": "Text"},
            {"title": "Affected Entities", "order": 4, "content": "Text"},
            {"title": "Threat Hypotheses", "order": 5, "content": "Text"},
            {"title": "Recommended Remediation", "order": 6, "content": "Text"},
            {"title": "Confidence & Limitations", "order": 7, "content": "Text"},
        ],
    )
    val = reporting_service_instance.validate_report(rep)
    assert val.is_valid is True
    assert len(val.missing_sections) == 0

    # Incomplete report
    rep_incomplete = IncidentReportPayload(
        investigation_id=uuid.uuid4(),
        title="Incomplete Report",
        severity="low",
        incident_classification="Triage",
        executive_summary="Summary",
        technical_body="Body",
        final_confidence=0.30,
        sections=[{"title": "Executive Summary", "order": 1, "content": "Text"}],
    )
    val_incomplete = reporting_service_instance.validate_report(rep_incomplete)
    assert val_incomplete.is_valid is False
    assert len(val_incomplete.missing_sections) > 0


def test_response_simulation_service(db_session, test_investigation):
    """Verify response simulation computes blast radius and rollback plan while remaining non-destructive."""
    req = SimulationRequest(
        investigation_id=test_investigation.investigation_id,
        action_type="isolate_endpoint",
        target_identifier="WS-04",
    )
    res = response_simulation_service.simulate(req, db=db_session)

    assert res.simulation_id is not None
    assert res.status == "simulated"
    assert "WS-04" in res.blast_radius
    assert "SAFE" in res.safety_assessment
    assert "Re-enable network adapter" in res.rollback_plan

    # Check persistence
    sim_db = db_session.query(ResponseSimulation).filter_by(id=res.simulation_id).first()
    assert sim_db is not None
    assert sim_db.status == "simulated"


def test_human_review_workflow(db_session, test_investigation):
    """Verify HumanReview lifecycle: creation, queue listing, and analyst approval transition."""
    # 1. Create review request -> moves investigation to awaiting_review
    review = human_review_service.create_review_request(
        investigation_id=test_investigation.investigation_id,
        requested_action="Complete investigation and publish report",
        risk_level="high",
        db=db_session,
    )
    assert review.status == "pending"
    assert test_investigation.status == "awaiting_review"

    # 2. List pending
    pending = human_review_service.list_pending_reviews(db=db_session)
    assert any(r.id == review.id for r in pending)

    # 3. Process approval
    submission = ReviewSubmissionPayload(
        decision="approved",
        analyst_comments="Findings corroborated by forensic evidence. Approved.",
    )
    reviewed = human_review_service.process_review(review.id, submission, db=db_session)
    assert reviewed.status == "approved"
    assert test_investigation.status == "completed"
    assert test_investigation.closed_at is not None


def test_reporting_and_review_api_endpoints(db_session, test_investigation):
    """Verify API endpoints for report generation, validation, review queue, and response simulation."""
    # Generate & get report
    res_gen = api_generate_report(test_investigation.investigation_id, db=db_session)
    assert res_gen.report_id is not None

    res_get = api_get_report(res_gen.report_id, db=db_session)
    assert res_get.final_confidence == res_gen.final_confidence

    val_res = api_validate_report(res_gen)
    assert val_res.is_valid is True

    # Review API
    review = human_review_service.create_review_request(
        investigation_id=test_investigation.investigation_id,
        requested_action="Simulate host isolation",
        risk_level="medium",
        db=db_session,
    )
    pending_list = api_list_pending_reviews(db=db_session)
    assert len(pending_list) >= 1

    dec_res = api_process_review(
        review.id,
        ReviewSubmissionPayload(decision="approved", analyst_comments="Approved for simulation"),
        db=db_session,
    )
    assert dec_res["decision"] == "approved"

    # Simulation API
    sim_res = api_simulate_response(
        SimulationRequest(
            investigation_id=test_investigation.investigation_id,
            action_type="block_ip",
            target_identifier="198.51.100.55",
        ),
        db=db_session,
    )
    assert sim_res.status == "simulated"
    assert "198.51.100.55" in sim_res.action
