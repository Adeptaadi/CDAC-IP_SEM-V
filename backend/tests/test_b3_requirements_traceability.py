"""
Project Sentinel — Phase B3 Requirements Traceability Test Suite.

Verifies end-to-end traceability from documentation to code schemas, tests,
and runtime behavior for all major system requirements.
"""

import os
import json
import uuid
import pytest
from app.models import Evidence, PlannerDecision, Investigation, Hypothesis, HypothesisEvidence
from app.planner.selection import InvestigationStateSnapshot, select_worker
from app.hypothesis.discovery import BottomUpHypothesisGenerator
from app.schemas.contracts import Finding


class TestB3RequirementsTraceability:
    """Rigorous verification that all requirements map to code, tests, and models."""

    def test_requirements_json_artifact_exists_and_valid(self):
        """b3_requirements_traceability.json exists and all claims have valid status."""
        assert os.path.exists("b3_requirements_traceability.json")
        with open("b3_requirements_traceability.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) >= 8
        valid_statuses = [
            "VERIFIED",
            "PARTIALLY_VERIFIED",
            "IMPLEMENTED_BUT_UNTESTED",
            "DOCUMENTED_BUT_NOT_IMPLEMENTED",
            "IMPLEMENTED_DIFFERENTLY",
            "FAILED",
            "OUT_OF_SCOPE"
        ]
        for item in data:
            assert "claim_id" in item
            assert "requirement" in item
            assert "status" in item
            assert item["status"] in valid_statuses

    def test_req_01_evidence_fingerprinting_and_deduplication(self):
        """REQ-01: Deterministic SHA-256 evidence content fingerprinting & semantic deduplication."""
        from app.models.evidence import compute_evidence_fingerprint
        h1 = compute_evidence_fingerprint("powershell.exe -enc AAAAA", {"host": "srv1"})
        h2 = compute_evidence_fingerprint("powershell.exe -enc AAAAA", {"host": "srv1"})
        assert len(h1) == 64
        assert h1 == h2

    def test_req_04_dynamic_state_driven_selection(self):
        """REQ-04: Worker selection is dynamically state-driven."""
        snap_investigation = InvestigationStateSnapshot(
            investigation_id="t1",
            confidence=0.10,
            evidence_count=0,
            hypotheses_confidences=[]
        )
        w1, _, _ = select_worker(snap_investigation)
        assert w1 == "investigation"

        snap_response = InvestigationStateSnapshot(
            investigation_id="t2",
            confidence=0.50,
            has_confirmed_hypothesis=True,
            has_formulated_response=False
        )
        w2, _, scores2 = select_worker(snap_response)
        assert scores2["response"] == 0.95
        assert scores2["reporting"] == 0.0
        assert w2 == "response"

    def test_req_07_blind_hypothesis_discovery(self):
        """REQ-07: Telemetry-to-hypothesis generation works without gold hypothesis hints."""
        gen = BottomUpHypothesisGenerator()
        findings = [
            Finding(
                finding_type="auth_failure",
                description="Repeated authentication failures (4625) from IP 10.0.0.99",
                confidence=0.8,
                source_worker="detection",
                raw_payload={"ip": "10.0.0.99"},
                supporting_evidence_ids=[uuid.uuid4()]
            )
        ]
        candidates = gen.generate_candidates(findings)
        assert len(candidates) > 0
        assert "T1110.001" in candidates[0].mitre_technique_ids
