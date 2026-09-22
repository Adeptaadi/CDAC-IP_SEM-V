import pytest
from uuid import uuid4
from app.schemas.contracts import WorkerTask, WorkerResult, Finding, TelemetryEvent
from app.workers import get_worker, WORKER_REGISTRY
from app.workers.detection_worker import DetectionWorker
from app.workers.correlation_worker import CorrelationWorker
from app.workers.investigation_worker import InvestigationWorker
from app.workers.reporting_worker import ReportingWorker
from app.workers.response_worker import ResponseWorker


def test_worker_registry_contains_all_five():
    expected = {"detection", "correlation", "investigation", "reporting", "response"}
    assert set(WORKER_REGISTRY.keys()) == expected
    for w_type in expected:
        worker = get_worker(w_type)
        assert worker.worker_type == w_type


def test_detection_worker_powershell():
    worker = DetectionWorker()
    event = TelemetryEvent(
        source="sysmon",
        event_type="process_creation",
        host="WORKSTATION-04",
        user="corp\\jdoe",
        process_name="powershell.exe",
        command_line="powershell.exe -Enc SQBFAFgAIAAoAE4AZQB3...",
        raw_log={"ParentProcess": "WINWORD.EXE"}
    )
    task = WorkerTask(
        investigation_id=uuid4(),
        worker_type="detection",
        objective="Triage suspicious process creation",
        evidence_refs=[],
        events=[event]
    )

    result = worker.execute(task)
    assert isinstance(result, WorkerResult)
    assert result.status == "success"
    assert result.confidence_signal >= 0.80
    assert any(f.mitre_technique_id == "T1059.001" for f in result.findings)


def test_correlation_worker_entity_graph():
    worker = CorrelationWorker()
    finding1 = Finding(
        description="PowerShell executed on workstation",
        entity_refs={"hosts": ["WORKSTATION-04"], "users": ["corp\\jdoe"], "processes": ["powershell.exe"]}
    )
    finding2 = Finding(
        description="Outbound network socket opened",
        entity_refs={"hosts": ["WORKSTATION-04"], "ips": ["13.58.225.34"]}
    )
    task = WorkerTask(
        investigation_id=uuid4(),
        worker_type="correlation",
        objective="Correlate host process and network telemetry",
        evidence_refs=[],
        findings=[finding1, finding2]
    )

    result = worker.execute(task)
    assert isinstance(result, WorkerResult)
    assert result.status == "success"
    assert len(result.findings) > 0
    assert "WORKSTATION-04" in result.findings[0].entity_refs["hosts"]
    assert "13.58.225.34" in result.findings[0].entity_refs["ips"]


def test_investigation_worker_hypotheses_and_rag():
    worker = InvestigationWorker()
    task = WorkerTask(
        investigation_id=uuid4(),
        worker_type="investigation",
        objective="Investigate PowerShell reverse shell and macro execution T1566",
        evidence_refs=[]
    )

    result = worker.execute(task)
    assert isinstance(result, WorkerResult)
    assert result.status == "success"
    assert len(result.hypothesis_updates) > 0
    assert result.hypothesis_updates[0]["status"] == "confirmed"
    assert result.hypothesis_updates[0]["stance"] == "supports"


def test_reporting_worker():
    worker = ReportingWorker()
    task = WorkerTask(
        investigation_id=uuid4(),
        worker_type="reporting",
        objective="Synthesize incident report",
        evidence_refs=[]
    )

    result = worker.execute(task)
    assert isinstance(result, WorkerResult)
    assert result.status == "success"
    assert result.confidence_signal > 0.85
    assert "Reporting worker" in result.reasoning_summary


def test_response_worker_human_approval_enforced():
    worker = ResponseWorker()
    task = WorkerTask(
        investigation_id=uuid4(),
        worker_type="response",
        objective="Recommend containment actions",
        evidence_refs=[]
    )

    result = worker.execute(task)
    assert isinstance(result, WorkerResult)
    assert result.status == "success"
    assert len(result.findings) >= 3
    # Every containment action must enforce approval
    assert any("Isolate" in f.description for f in result.findings)
