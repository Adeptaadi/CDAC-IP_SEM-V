import pytest
from app.llm.client import LLMClient
from app.llm.prompts import (
    build_hypothesis_prompt,
    build_forensic_report_prompt,
    SYSTEM_PROMPT_THREAT_HUNTER,
    SYSTEM_PROMPT_FORENSIC_REPORTER
)


def test_prompt_builders():
    hypo_prompt = build_hypothesis_prompt(
        telemetry_summary="powershell.exe -Enc base64 executed on WORKSTATION-04",
        rag_context="T1059.001 PowerShell command execution"
    )
    assert "OBSERVED TELEMETRY SUMMARY" in hypo_prompt
    assert "powershell.exe" in hypo_prompt
    assert "T1059.001" in hypo_prompt

    rep_prompt = build_forensic_report_prompt(
        investigation_title="Infiltration Attack Hunt",
        confidence_pct=92.5,
        timeline_summary="10:00 WINWORD.EXE -> 10:01 powershell.exe",
        evidence_summary="Outbound connection to 13.58.225.34",
        hypotheses_summary="Adversary Infiltration"
    )
    assert "Infiltration Attack Hunt" in rep_prompt
    assert "92.5%" in rep_prompt
    assert "ATTACK TIMELINE" in rep_prompt


def test_llm_client_fallback_mode():
    # Test client pointing to dummy unreachable port
    client = LLMClient(host="http://127.0.0.1:59999", model="test-model")
    assert client.is_available() is False

    # Should fall back cleanly without raising exception
    completion = client.generate_completion(prompt="Analyze PowerShell threat")
    assert "[Offline AI Summary]" in completion or len(completion) > 0

    fallback = {
        "label": "Fallback Threat Hypothesis",
        "confidence": 0.85,
        "mitre_technique_ids": ["T1059.001"]
    }
    structured = client.generate_structured(prompt="Synthesize JSON", fallback_data=fallback)
    assert structured["label"] == "Fallback Threat Hypothesis"
    assert structured["confidence"] == 0.85
    assert "T1059.001" in structured["mitre_technique_ids"]
