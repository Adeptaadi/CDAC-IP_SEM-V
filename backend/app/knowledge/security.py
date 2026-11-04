import re
from typing import List, Set


class UntrustedSourceError(Exception):
    """Raised when an unapproved knowledge source attempts ingestion or retrieval."""
    pass


class PromptInjectionDetectedError(Exception):
    """Raised when malicious prompt injection or override instructions are found in knowledge content."""
    pass


class RAGSecurityFilter:
    """Security boundaries, approved source enforcement, and prompt-injection defenses (Phase 10)."""

    APPROVED_SOURCES: Set[str] = {
        "mitre_attack",
        "mitre",
        "incident_playbooks",
        "playbook",
        "historical_cases",
        "historical",
        "sigma_rules",
        "sigma",
        "cve_nvd",
        "cve",
        "capec",
        "threat_intel",
    }

    # Common LLM jailbreak, prompt override, and boundary escape regex patterns
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|directives)", re.IGNORECASE),
        re.compile(r"(disregard|forget)\s+everything\s+(above|before)", re.IGNORECASE),
        re.compile(r"you\s+are\s+now\s+(in\s+developer\s+mode|unrestricted)", re.IGNORECASE),
        re.compile(r"system\s*prompt\s*override", re.IGNORECASE),
        re.compile(r"<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]", re.IGNORECASE),
        re.compile(r"execute_action\s*\(\s*authorized\s*=\s*true\s*\)", re.IGNORECASE),
    ]

    @classmethod
    def validate_source(cls, source_name: str) -> None:
        """Verifies that the knowledge source is registered in the approved whitelist."""
        clean_name = source_name.strip().lower()
        if clean_name not in cls.APPROVED_SOURCES:
            raise UntrustedSourceError(
                f"Source '{source_name}' is not in approved knowledge sources list: {sorted(cls.APPROVED_SOURCES)}"
            )

    @classmethod
    def sanitize_content(cls, content: str, strict: bool = False) -> str:
        """Sanitizes text content to prevent prompt injection and instruction smuggling."""
        if not content:
            return ""

        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(content):
                if strict:
                    raise PromptInjectionDetectedError(f"Potential prompt injection detected: {pattern.pattern}")
                # Neutralize matching tokens safely
                content = pattern.sub("[FILTERED_POTENTIAL_INJECTION]", content)

        return content


rag_security_filter = RAGSecurityFilter()
