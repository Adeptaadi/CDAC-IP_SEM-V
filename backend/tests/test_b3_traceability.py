"""
Phase B3 Traceability Tests.

Verifies programmatic traceability between documented architecture requirements
and backend implementation schemas and components.
"""

import os
import uuid
import pytest
from app.models import Evidence, PlannerDecision, Investigation, Hypothesis
from app.planner.selection import InvestigationStateSnapshot
from app.hypothesis.discovery import BottomUpHypothesisGenerator
from app.schemas.contracts import Finding


class TestB3Traceability:
    """Verifies that all architectural requirements are grounded in source code schemas."""

    def test_state_snapshot_schema_completeness(self):
        """InvestigationStateSnapshot possesses all audited fields required for decision traceability."""
        snap = InvestigationStateSnapshot(investigation_id="test-trace-1")
        required_attrs = [
            "investigation_id",
            "confidence",
            "cycle_number",
            "evidence_count",
            "novel_evidence_count",
            "duplicate_evidence_count",
            "graph_density",
            "has_confirmed_hypothesis",
            "has_formulated_response",
            "cycles_since_meaningful_progress",
            "has_unresolved_contradictions",
            "last_worker",
            "consecutive_worker_count",
            "worker_history",
            "is_replanning",
            "selected_worker_details",
        ]
        for attr in required_attrs:
            assert hasattr(snap, attr), f"Missing required attribute {attr} on InvestigationStateSnapshot"

    def test_planner_decision_record_provenance_schema(self):
        """PlannerDecision table columns capture the full causal chain of decisions."""
        columns = PlannerDecision.__table__.columns.keys()
        required_cols = [
            "decision_id",
            "investigation_id",
            "planner_run_id",
            "cycle_number",
            "decision_type",
            "is_replanning",
            "replan_reason",
            "selected_worker",
            "selection_score",
            "confidence_before",
            "confidence_after",
            "explanation_summary",
            "created_at",
        ]
        for col in required_cols:
            assert col in columns, f"Missing required column {col} in PlannerDecision model"

    def test_evidence_deduplication_provenance_schema(self):
        """Evidence model table columns include content fingerprinting and deduplication fields."""
        columns = Evidence.__table__.columns.keys()
        required_cols = [
            "content_hash",
            "is_duplicate",
            "is_novel",
            "observation_count",
        ]
        for col in required_cols:
            assert col in columns, f"Missing deduplication column {col} in Evidence model"

    def test_blind_hypothesis_discovery_signature(self):
        """BottomUpHypothesisGenerator extracts hypotheses from raw findings without requiring gold hypotheses."""
        generator = BottomUpHypothesisGenerator()
        findings = [
            Finding(
                finding_type="anomalous_process_execution",
                description="PowerShell encoded command execution detected with -enc",
                confidence=0.85,
                source_worker="detection",
                raw_payload={"cmd": "powershell.exe -enc AAAAA", "host": "WORKSTATION-01"},
                supporting_evidence_ids=[uuid.uuid4()]
            )
        ]
        hypotheses = generator.generate_candidates(findings)
        assert len(hypotheses) > 0
        h = hypotheses[0]
        assert h.label is not None
        assert len(h.supporting_evidence_ids) > 0
        assert len(h.mitre_technique_ids) > 0

    def test_sentinel_core_documentation_exists(self):
        """Sentinel architectural documentation exists in docs/."""
        docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs"))
        expected_docs = [
            "PRD.md",
            "TDD.md",
            "ADAPTIVE_PLANNING_AND_DECISION_SPEC.md",
            "EVIDENCE_CONFIDENCE_AND_EVALUATION_SPEC.md",
        ]
        for doc in expected_docs:
            path = os.path.join(docs_dir, doc)
            assert os.path.exists(path), f"Expected Sentinel architectural doc not found: {path}"
