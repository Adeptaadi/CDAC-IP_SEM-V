import uuid
from datetime import datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
import app.models  # Ensure all 41 tables are registered
from app.orchestration.contracts import (
    CapabilityDefinition,
    TaskExecutionRequest,
    TaskExecutionResult,
)
from app.orchestration.registry import CapabilityRegistry
from app.orchestration.executor import TaskExecutor
from app.models.investigation import Investigation
from app.models.orchestration import Capability, CapabilityVersion, AgentTask, TaskAttempt
from app.api.task_router import (
    list_capabilities as api_list_capabilities,
    execute_task as api_execute_task,
    get_task as api_get_task,
    list_investigation_tasks as api_list_inv_tasks,
)


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for Phase 8 tests."""
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
    """Creates a sample investigation to anchor task executions."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Orchestration Test Investigation",
        status="investigating",
        current_confidence=0.20,
        confidence_state="low",
        current_goal="Evaluate capability dispatch",
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)
    return inv


def test_capability_registry_and_db_sync(db_session):
    """Verify registry registers all 7 standard capabilities and synchronizes to database."""
    registry = CapabilityRegistry()
    caps = registry.list_capabilities()
    assert len(caps) >= 7

    names = {c.name for c in caps}
    assert "detection.analyze_events" in names
    assert "correlation.analyze_entities" in names
    assert "correlation.analyze_temporal_patterns" in names
    assert "investigation.collect_evidence" in names
    assert "knowledge.retrieve_context" in names
    assert "reporting.generate_report" in names
    assert "response.simulate_action" in names

    # High-risk response capability must enforce human review
    resp_cap = registry.get("response.simulate_action")
    assert resp_cap is not None
    assert resp_cap.risk_level == "high"
    assert resp_cap.requires_human_approval is True

    # Sync to DB
    registry.sync_to_db(db_session)
    db_caps = db_session.query(Capability).all()
    assert len(db_caps) >= 7
    db_versions = db_session.query(CapabilityVersion).all()
    assert len(db_versions) >= 7


def test_task_executor_successful_run(db_session, test_investigation):
    """Verify task execution creates AgentTask, TaskAttempt, and persists structured output."""
    executor = TaskExecutor()

    req = TaskExecutionRequest(
        investigation_id=test_investigation.investigation_id,
        capability_name="detection.analyze_events",
        objective="Analyze suspicious powershell execution",
        input_payload={
            "events": [
                {
                    "event_id": str(uuid.uuid4()),
                    "event_type": "process_creation",
                    "process_name": "powershell.exe",
                    "command_line": "powershell -enc JABzACAAPQ...",
                    "host": "WS-01",
                    "user": "SYSTEM",
                }
            ]
        },
    )

    res = executor.execute_task(req, db=db_session)
    assert res.status == "completed"
    assert res.output_payload is not None
    assert res.attempt_count == 1
    assert res.worker_type == "detection"

    # Verify database persistence
    db_task = db_session.query(AgentTask).filter_by(id=res.task_id).first()
    assert db_task is not None
    assert db_task.status == "completed"
    assert db_task.completed_at is not None

    db_attempts = db_session.query(TaskAttempt).filter_by(task_id=res.task_id).all()
    assert len(db_attempts) == 1
    assert db_attempts[0].status == "success"


def test_task_executor_idempotency(db_session, test_investigation):
    """Verify identical idempotency key returns cached task result without duplicate worker execution."""
    executor = TaskExecutor()
    key = "idem-check-12345"

    req = TaskExecutionRequest(
        investigation_id=test_investigation.investigation_id,
        capability_name="correlation.analyze_entities",
        objective="Extract entities",
        idempotency_key=key,
    )

    res1 = executor.execute_task(req, db=db_session)
    assert res1.status == "completed"

    res2 = executor.execute_task(req, db=db_session)
    assert res2.task_id == res1.task_id
    assert res2.status == "completed"


def test_task_executor_dependency_blocking(db_session, test_investigation):
    """Verify a task with an unfulfilled dependency is blocked."""
    executor = TaskExecutor()
    fake_prereq_id = uuid.uuid4()

    req = TaskExecutionRequest(
        investigation_id=test_investigation.investigation_id,
        capability_name="reporting.generate_report",
        objective="Draft incident report",
        dependency_task_ids=[fake_prereq_id],
    )

    res = executor.execute_task(req, db=db_session)
    assert res.status == "blocked"
    assert "Blocked on prerequisite task" in (res.error_message or "")


def test_task_executor_human_approval_enforcement(db_session, test_investigation):
    """Verify high-risk response simulation is blocked without explicit human approval, and succeeds when approved."""
    executor = TaskExecutor()

    # Attempt without approval -> blocked
    req_unapproved = TaskExecutionRequest(
        investigation_id=test_investigation.investigation_id,
        capability_name="response.simulate_action",
        objective="Simulate host network isolation",
        input_payload={"human_approved": False, "context": {"target_ip": "10.0.0.5"}},
    )
    res_unapproved = executor.execute_task(req_unapproved, db=db_session)
    assert res_unapproved.status == "blocked"
    assert "human-in-the-loop approval" in (res_unapproved.error_message or "")

    # Attempt with human approval -> executes successfully
    req_approved = TaskExecutionRequest(
        investigation_id=test_investigation.investigation_id,
        capability_name="response.simulate_action",
        objective="Simulate host network isolation",
        input_payload={"human_approved": True, "context": {"target_ip": "10.0.0.5"}},
    )
    res_approved = executor.execute_task(req_approved, db=db_session)
    assert res_approved.status == "completed"


def test_orchestration_api_endpoints(db_session, test_investigation):
    """Verify task orchestration API endpoints list capabilities, execute tasks, and return attempt history."""
    caps = api_list_capabilities()
    assert len(caps) >= 7

    req = TaskExecutionRequest(
        investigation_id=test_investigation.investigation_id,
        capability_name="investigation.collect_evidence",
        objective="Gather forensic evidence",
    )
    res = api_execute_task(req, db=db_session)
    assert res.status == "completed"

    task_data = api_get_task(res.task_id, db=db_session)
    assert task_data["task_id"] == str(res.task_id)
    assert len(task_data["attempts"]) >= 1

    inv_tasks = api_list_inv_tasks(test_investigation.investigation_id, db=db_session)
    assert len(inv_tasks) >= 1
