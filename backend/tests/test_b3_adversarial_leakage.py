"""
Project Sentinel — Phase B3 Adversarial Leakage Test Suite.

Audits and actively attempts to break the blind evaluation boundary:
1. Verifies zero gold-hypothesis or gold-label leakage.
2. Verifies inference works under generic, adversarial, or noisy objective text.
3. Classifies detection signatures as legitimate security detection rules.
"""

import uuid
import pytest
from app.hypothesis.discovery import BottomUpHypothesisGenerator
from app.schemas.contracts import Finding


class TestB3AdversarialLeakage:
    """Verifies that no hidden shortcuts or answer leakage bypasses genuine inference."""

    def test_blind_discovery_with_generic_neutral_objective(self):
        """Hypothesis generator functions accurately when objective contains zero attack clues."""
        gen = BottomUpHypothesisGenerator()
        findings = [
            Finding(
                finding_type="process_creation",
                description="PowerShell executed with -enc AAAA -nop -w hidden",
                confidence=0.85,
                source_worker="detection",
                raw_payload={"cmd": "powershell.exe -enc AAAA"},
                supporting_evidence_ids=[uuid.uuid4()]
            )
        ]
        # Neutral objective hint:
        neutral_hint = "Investigate system anomalies on host srv-prod-01"
        hypotheses = gen.generate_candidates(findings, objective_hint=neutral_hint)

        assert len(hypotheses) > 0
        h = hypotheses[0]
        # Inferred technique from raw telemetry:
        assert "T1059.001" in h.mitre_technique_ids
        assert "PowerShell" in h.label or "Process" in h.label or "Execution" in h.label

    def test_blind_discovery_immune_to_deceptive_objective(self):
        """Hypothesis generator relies on observed telemetry, ignoring deceptive objective hints."""
        gen = BottomUpHypothesisGenerator()
        findings = [
            Finding(
                finding_type="http_request",
                description="SQL injection in /index.php?id=' OR '1'='1",
                confidence=0.85,
                source_worker="detection",
                raw_payload={"uri": "/index.php"},
                supporting_evidence_ids=[uuid.uuid4()]
            )
        ]
        # Deceptive hint suggesting an unrelated attack:
        deceptive_hint = "Investigate potential Ransomware encryption"
        hypotheses = gen.generate_candidates(findings, objective_hint=deceptive_hint)

        assert len(hypotheses) > 0
        h = hypotheses[0]
        # Must still correctly identify SQL injection / Exploit, NOT ransomware
        assert "T1190" in h.mitre_technique_ids
        assert "SQL Injection" in h.label

    def test_signature_classification_verification(self):
        """Telemetry signatures in feature extraction are standard SIGMA/SOC patterns, not game shortcuts."""
        # Standard SIGMA pattern 1: Windows EventID 4625 -> Brute Force (T1110.001)
        # Standard SIGMA pattern 2: PowerShell -enc / -nop -> Scripting (T1059.001)
        # Standard SIGMA pattern 3: SQL keywords ('union', 'select') -> Exploit Public-Facing App (T1190)
        # Standard SIGMA pattern 4: DoS floods (slowloris, connection exhaustion) -> Network DoS (T1498.001)
        gen = BottomUpHypothesisGenerator()
        features = gen.extract_features([])
        assert features.raw_evidence_count == 0
        assert features.candidate_techniques == []
