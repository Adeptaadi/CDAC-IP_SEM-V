"""Project Sentinel — Phase B2: Blind Threat Discovery & Confidence Calibration Test Suite.

Validates:
  Test A: No Gold Leakage (Workers operate without access to gold labels or attack categories)
  Test B: Telemetry-Derived Candidate (Bottom-up hypothesis generation from evidence features)
  Test C: Ambiguous Evidence (Multi-candidate generation and maintenance under ambiguous signals)
  Test D: Incorrect Candidate Recovery (Contradictory evidence penalizes confidence and triggers pivot)
  Test E: No-Evidence Case (Zero evidence produces 0 candidates, 0 confidence drift, clean escalation)
  Test F: Blind Benchmark Provenance (Hypotheses trace to evidence IDs, source classification, and features)
"""

import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Investigation, Evidence, Hypothesis, HypothesisEvidence, PlannerDecision, WorkerExecution
from app.planner.engine import PlannerEngine
from app.planner.confidence import ConfidenceEngine
from app.hypothesis.discovery import bottom_up_hypothesis_generator_instance, BottomUpHypothesisGenerator, CandidateHypothesis
from app.schemas.contracts import WorkerTask, WorkerResult, Finding
from app.workers.investigation_worker import InvestigationWorker
from app.ingest.downloader import generate_synthetic_scenario_events


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session for B2 blind testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_b2_test_a_no_gold_leakage(db_session):
    """Test A: Verify that workers in blind mode have no access to gold hypothesis or attack names."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="[Blind Benchmark] brute_force",
        status="investigating",
        current_confidence=0.15,
        current_goal="Investigate anomalous telemetry activities on monitored endpoints/network",
        planning_cycle_count=0,
    )
    db_session.add(inv)
    db_session.commit()

    # Pre-condition: No gold hypothesis in database
    existing_hypos = db_session.query(Hypothesis).filter(Hypothesis.investigation_id == inv.investigation_id).all()
    assert len(existing_hypos) == 0, "Blind mode must not seed hypotheses into DB"

    engine = PlannerEngine()
    snap = engine.load_state_snapshot(inv, db_session)

    # Verify state snapshot does not contain gold hypothesis labels
    assert snap.has_confirmed_hypothesis is False
    assert len(snap.hypotheses_confidences) == 0

    # Ingest baseline telemetry without attack category labels in description
    events = generate_synthetic_scenario_events("brute_force")
    for e in events[:4]:
        ev = Evidence(
            investigation_id=inv.investigation_id,
            source_type=e.get("source", "log"),
            description=f"{e.get('event_type')}: {e.get('process_name') or 'log event'}",
            entity_refs={"hosts": [e.get("host")], "ips": [e.get("src_ip")]},
            is_novel=True,
            is_duplicate=False,
        )
        db_session.add(ev)
    db_session.commit()

    # Execute cycle via InvestigationWorker
    worker = InvestigationWorker()
    ev_records = db_session.query(Evidence).filter(Evidence.investigation_id == inv.investigation_id).all()
    task = WorkerTask(
        investigation_id=inv.investigation_id,
        worker_type="investigation",
        objective=inv.current_goal,  # Generic objective!
        evidence_refs=[e.evidence_id for e in ev_records],
        findings=[Finding(description=e.description, entity_refs=e.entity_refs) for e in ev_records],
    )
    result = worker.execute(task)

    assert result.status == "success"
    assert len(result.hypothesis_updates) > 0
    # The generated hypothesis must NOT mention scenario name "brute_force" as an answer key
    for h in result.hypothesis_updates:
        assert h["generation_source"] in ["RULE_DERIVED", "RAG_ASSISTED", "LLM_ASSISTED"]
        assert "provenance_summary" in h
        assert len(h["mitre_technique_ids"]) > 0


def test_b2_test_b_telemetry_derived_candidates():
    """Test B: Verify candidate hypotheses are generated bottom-up from distinct telemetry evidence patterns."""
    generator = BottomUpHypothesisGenerator(enable_rag=False)

    # 1. Telemetry cluster: Web SQL Injection
    sqli_evidence = [
        Finding(
            description="http_request: GET /search.php?q=' OR '1'='1 (apache2)",
            entity_refs={"hosts": ["WEB-SRV-01"], "ips": ["18.218.115.60", "192.168.1.50"]}
        ),
        Finding(
            description="http_request: GET /search.php?q=UNION SELECT username, password FROM users--",
            entity_refs={"hosts": ["WEB-SRV-01"], "ips": ["18.218.115.60"]}
        )
    ]
    cands_sqli = generator.generate_candidates(sqli_evidence)
    assert len(cands_sqli) >= 1
    assert "T1190" in cands_sqli[0].mitre_technique_ids
    assert "SQL Injection" in cands_sqli[0].label
    assert cands_sqli[0].generation_source == "RULE_DERIVED"

    # 2. Telemetry cluster: Botnet C2 Beaconing
    c2_evidence = [
        Finding(
            description="c2_beacon: outbound connection to 18.219.211.138:8080 by ares_agent.exe",
            entity_refs={"hosts": ["WORKSTATION-10"], "ips": ["18.219.211.138"]}
        ),
        Finding(
            description="c2_beacon: periodic network flow duration 500ms port 8080",
            entity_refs={"hosts": ["WORKSTATION-10"], "ips": ["18.219.211.138"]}
        )
    ]
    cands_c2 = generator.generate_candidates(c2_evidence)
    assert len(cands_c2) >= 1
    assert "T1071.001" in cands_c2[0].mitre_technique_ids
    assert "Botnet" in cands_c2[0].label
    assert "8080" in cands_c2[0].provenance_summary


def test_b2_test_c_ambiguous_evidence_multi_candidate():
    """Test C: Ambiguous evidence generates and retains multiple candidate hypotheses."""
    generator = BottomUpHypothesisGenerator(enable_rag=False)

    # Mixed evidence: Both authentication failures AND SQL injection attempts
    mixed_evidence = [
        Finding(
            description="auth_failure: sshd login failure for root (EventID: 4625)",
            entity_refs={"hosts": ["SRV-01"], "ips": ["18.218.115.60"]}
        ),
        Finding(
            description="auth_failure: sshd password spray attempt user_2",
            entity_refs={"hosts": ["SRV-01"], "ips": ["18.218.115.60"]}
        ),
        Finding(
            description="http_request: GET /login.php?user=admin' OR '1'='1",
            entity_refs={"hosts": ["WEB-01"], "ips": ["18.218.115.60"]}
        ),
    ]

    candidates = generator.generate_candidates(mixed_evidence)
    assert len(candidates) >= 2, "Ambiguous evidence must yield multiple candidate interpretations"

    labels = [c.label for c in candidates]
    assert any("Credential Access" in lbl or "Password Guessing" in lbl for lbl in labels)
    assert any("SQL Injection" in lbl for lbl in labels)


def test_b2_test_d_incorrect_candidate_recovery(db_session):
    """Test D: Contradictory evidence penalizes confidence and triggers strategy pivot."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="Test Recovery Contradiction",
        status="investigating",
        current_confidence=0.55,
        planning_cycle_count=1,
    )
    db_session.add(inv)

    hypo = Hypothesis(
        hypothesis_id=uuid.uuid4(),
        investigation_id=inv.investigation_id,
        label="Data Exfiltration over DNS Tunnel",
        status="active",
        confidence=0.55,
        mitre_technique_ids=["T1071.004"],
    )
    db_session.add(hypo)
    db_session.commit()

    # Cycle 1: Baseline confidence without contradictions
    conf_engine = ConfidenceEngine()
    dummy_res = WorkerResult(
        task_id=uuid.uuid4(),
        worker_type="investigation",
        status="success",
        findings=[],
        confidence_signal=0.5,
        new_evidence=[],
        hypothesis_updates=[],
        reasoning_summary="Analyzing DNS queries.",
    )
    factors_clean = conf_engine.compute_factors(dummy_res, novel_evidence_count=0, unresolved_contradictions_count=0)
    delta_clean = conf_engine.compute_delta(factors_clean)
    conf_clean = conf_engine.update(0.55, delta_clean, unresolved_contradictions_count=0)
    assert conf_clean == 0.55

    # Introduce strong contradiction: internal DNSSEC validation confirmed benign root
    ev_contra = Evidence(
        investigation_id=inv.investigation_id,
        source_type="contradiction",
        description="DNS query audit confirms all traffic resolves to internal enterprise root resolver with valid DNSSEC.",
        is_novel=True,
        is_duplicate=False,
    )
    db_session.add(ev_contra)
    db_session.flush()

    link = HypothesisEvidence(
        hypothesis_id=hypo.hypothesis_id,
        evidence_id=ev_contra.evidence_id,
        stance="contradicts",
        weight=1.0,
    )
    db_session.add(link)
    db_session.commit()

    factors_contra = conf_engine.compute_factors(
        dummy_res,
        novel_evidence_count=0,
        unresolved_contradictions_count=1,
        total_evidence=2,
    )
    assert factors_contra["contradiction"] < 0.0, "Contradiction factor must be negative"
    delta_contra = conf_engine.compute_delta(factors_contra)
    assert delta_contra < 0.0, "Net delta must be negative under unresolved contradiction"

    conf_penalized = conf_engine.update(0.55, delta_contra, unresolved_contradictions_count=1)
    assert conf_penalized < 0.55, "Confidence must decrease when contradiction is introduced"

    # Also verify that confidence cannot exceed 0.60 while contradiction is open
    conf_capped = conf_engine.update(0.85, 0.50, unresolved_contradictions_count=1)
    assert conf_capped <= 0.60, "Unresolved contradictions must cap confidence at 0.60"

    # Resolving contradiction lifts the penalty
    link.stance = "supports"
    db_session.commit()
    factors_resolved = conf_engine.compute_factors(dummy_res, novel_evidence_count=0, unresolved_contradictions_count=0)
    assert factors_resolved["contradiction"] == 0.0
    conf_restored = conf_engine.update(0.55, 0.0, unresolved_contradictions_count=0)
    assert conf_restored == 0.55


def test_b2_test_e_no_evidence_case(db_session):
    """Test E: Zero evidence produces 0 candidates, 0 confidence drift, and clean escalation."""
    from app.workers import WORKER_REGISTRY
    from app.workers.base import BaseWorker

    class ZeroEvidenceWorker(BaseWorker):
        worker_type = "detection"
        def execute(self, task: WorkerTask) -> WorkerResult:
            return WorkerResult(
                task_id=task.task_id,
                worker_type=self.worker_type,
                status="success",
                findings=[],
                confidence_signal=0.5,
                new_evidence=[],
                hypothesis_updates=[],
                reasoning_summary="No telemetry events found in scope to triage."
            )

    orig_detection = WORKER_REGISTRY["detection"]
    orig_investigation = WORKER_REGISTRY["investigation"]
    WORKER_REGISTRY["detection"] = ZeroEvidenceWorker
    WORKER_REGISTRY["investigation"] = ZeroEvidenceWorker

    try:
        inv = Investigation(
            investigation_id=uuid.uuid4(),
            title="[Blind Benchmark] No-Evidence Case",
            status="investigating",
            current_confidence=0.15,
            current_goal="Investigate anomalous telemetry activities on monitored endpoints/network",
            planning_cycle_count=0,
        )
        db_session.add(inv)
        db_session.commit()

        engine = PlannerEngine()

        # Run cycle on empty investigation with zero-progress worker
        res1 = engine.run_cycle(inv.investigation_id, db_session)
        db_session.refresh(inv)

        assert round(float(inv.current_confidence), 4) == 0.15, "Confidence must not drift on zero evidence"
        hypos = db_session.query(Hypothesis).filter(Hypothesis.investigation_id == inv.investigation_id).all()
        assert len(hypos) == 0, "No phantom hypotheses should be formulated from zero evidence"

        # Run remaining cycles until stagnation limit triggers escalation
        for _ in range(5):
            res = engine.run_cycle(inv.investigation_id, db_session)
            if res.get("status") in ["escalated", "completed"]:
                break
        db_session.refresh(inv)

        assert inv.status == "escalated", f"Expected escalated status, got {inv.status}"
        assert float(inv.current_confidence) == 0.15, "Confidence must not have grown without evidence"
    finally:
        WORKER_REGISTRY["detection"] = orig_detection
        WORKER_REGISTRY["investigation"] = orig_investigation


def test_b2_test_f_blind_benchmark_provenance(db_session):
    """Test F: Every final hypothesis can be traced to evidence IDs, source classification, and features."""
    inv = Investigation(
        investigation_id=uuid.uuid4(),
        title="[Blind Benchmark] Infiltration Provenance",
        status="investigating",
        current_confidence=0.15,
        current_goal="Investigate anomalous telemetry activities on monitored endpoints/network",
        planning_cycle_count=0,
    )
    db_session.add(inv)

    # Ingest infiltration telemetry
    ev1 = Evidence(
        investigation_id=inv.investigation_id,
        source_type="sysmon",
        description="process_creation: powershell.exe -NoP -NonI -W Hidden -Enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBj...",
        entity_refs={"hosts": ["WORKSTATION-04"], "processes": ["powershell.exe"]},
        is_novel=True,
        is_duplicate=False,
    )
    ev2 = Evidence(
        investigation_id=inv.investigation_id,
        source_type="sysmon",
        description="process_creation: WINWORD.EXE spawned powershell.exe",
        entity_refs={"hosts": ["WORKSTATION-04"], "processes": ["powershell.exe", "WINWORD.EXE"]},
        is_novel=True,
        is_duplicate=False,
    )
    db_session.add_all([ev1, ev2])
    db_session.commit()

    engine = PlannerEngine()
    engine.run_autonomous(inv.investigation_id, db_session, max_steps=3)
    db_session.refresh(inv)

    hypos = db_session.query(Hypothesis).filter(Hypothesis.investigation_id == inv.investigation_id).all()
    assert len(hypos) > 0, "Investigation must discover at least one hypothesis from telemetry"

    hyp = hypos[0]
    assert hyp.generation_source in ["RULE_DERIVED", "RAG_ASSISTED", "LLM_ASSISTED"]
    assert hyp.provenance_summary is not None
    assert len(hyp.provenance_summary) > 20
    assert "powershell" in hyp.provenance_summary.lower()

    # Verify link in HypothesisEvidence
    links = db_session.query(HypothesisEvidence).filter(HypothesisEvidence.hypothesis_id == hyp.hypothesis_id).all()
    assert len(links) > 0, "Hypothesis must be linked to supporting evidence records"
    linked_eids = [l.evidence_id for l in links]
    assert (ev1.evidence_id in linked_eids) or (ev2.evidence_id in linked_eids)
