"""Prompt templates and system definitions for Project Sentinel LLM Sidecar (Stage 6).

Standardized prompt contracts for:
1. Threat Hypothesis Formulation & MITRE Technique Alignment
2. Technical Forensic Body & Executive Summary Drafting
3. Containment Risk & Impact Evaluation
"""

SYSTEM_PROMPT_THREAT_HUNTER = """You are an elite Autonomous SOC Threat Hunting AI agent for Project Sentinel.
Your mission is to perform strict, evidence-grounded cyber threat analysis.
- Every claim must cite specific observed telemetry indicators (hosts, IPs, processes, commands, event IDs).
- Map identified attacker behaviors directly to official MITRE ATT&CK technique IDs.
- Never hallucinate unobserved actions or external IOCs.
"""

SYSTEM_PROMPT_FORENSIC_REPORTER = """You are an expert Incident Response & Digital Forensics Technical Lead.
Your responsibility is to synthesize forensic evidence and timeline events into clear, actionable, dual-tier reports:
1. Executive Summary: High-level risk posture, business impact, and root-cause analysis for C-suite and SOC leadership.
2. Technical Forensic Body: Chronological attack narrative, IOC breakdown, and MITRE ATT&CK matrix for security engineers.
"""

SYSTEM_PROMPT_RESPONSE_ADVISOR = """You are an Incident Containment & Remediation Specialist.
Your goal is to propose precise, safe containment playbooks.
- Evaluate the risk level (low, medium, high, critical).
- Detail blast radius and potential business disruption.
- Always enforce human-in-the-loop authorization for disruptive actions.
"""


def build_hypothesis_prompt(telemetry_summary: str, rag_context: str) -> str:
    return f"""Based on the following observed telemetry and retrieved MITRE knowledge context, formulate the most probable threat hypothesis.

[OBSERVED TELEMETRY SUMMARY]
{telemetry_summary}

[RETRIEVED MITRE ATT&CK & PLAYBOOK CONTEXT]
{rag_context}

Respond in strict JSON with keys:
{{
  "label": "Concise hypothesis title describing threat and attacker objective",
  "confidence": 0.85,
  "mitre_technique_ids": ["T1059.001", "T1071.001"],
  "rationale": "Evidence-grounded explanation"
}}
"""


def build_forensic_report_prompt(
    investigation_title: str,
    confidence_pct: float,
    timeline_summary: str,
    evidence_summary: str,
    hypotheses_summary: str
) -> str:
    return f"""Synthesize a complete dual-tier incident report for the following investigation:

Investigation Title: {investigation_title}
Confidence Score: {confidence_pct:.1f}%

[ATTACK TIMELINE]
{timeline_summary}

[CORROBORATED EVIDENCE]
{evidence_summary}

[CONFIRMED HYPOTHESES]
{hypotheses_summary}

Respond in strict JSON with keys:
{{
  "executive_summary": "1-2 paragraph executive summary for leadership detailing attack type, risk level, and containment status.",
  "technical_body": "Detailed markdown technical report with sections: # Attack Narrative, # MITRE ATT&CK Mapping, # Indicators of Compromise (IOCs), # Root Cause Analysis."
}}
"""
