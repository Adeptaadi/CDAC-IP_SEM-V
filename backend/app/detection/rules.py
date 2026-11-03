import re
import uuid
import urllib.parse
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from sqlalchemy.orm import Session

from app.detection.contracts import DetectionFindingPayload
from app.models.detection import DetectionRule


class RuleDefinition:
    def __init__(
        self,
        rule_key: str,
        name: str,
        description: str,
        severity: str,
        confidence: float,
        mitre_tactics: List[str],
        mitre_techniques: List[str],
        condition_fn: Callable[[Dict[str, Any]], bool],
        version: str = "1.0.0",
    ):
        self.rule_key = rule_key
        self.name = name
        self.description = description
        self.severity = severity
        self.confidence = confidence
        self.mitre_tactics = mitre_tactics
        self.mitre_techniques = mitre_techniques
        self.condition_fn = condition_fn
        self.version = version


DetectionRuleDefinition = RuleDefinition


class RuleEngine:
    """Configurable Rule-Based Detection Engine evaluating security events against expert threat signatures (Phase 5)."""

    def __init__(self):
        self._rules: Dict[str, RuleDefinition] = {}
        self._init_default_rules()

    def _init_default_rules(self):
        # 1. Encoded PowerShell (T1059.001)
        ps_regex = re.compile(r"powershell.*(-enc|-encodedcommand|-w hidden|-nop)", re.IGNORECASE)
        self.register_rule(
            RuleDefinition(
                rule_key="RULE_POWERSHELL_OBFUSCATION",
                name="Suspicious Encoded PowerShell Execution",
                description="PowerShell process execution with encoded parameters or hidden window attributes.",
                severity="high",
                confidence=0.90,
                mitre_tactics=["Execution"],
                mitre_techniques=["T1059.001"],
                condition_fn=lambda ev: bool(
                    ps_regex.search(str(ev.get("command_line") or ""))
                    or ps_regex.search(str(ev.get("normalized_data", {}).get("command_line") or ""))
                ),
            )
        )

        # 2. Office Spawning Interpreter (T1566.001)
        self.register_rule(
            RuleDefinition(
                rule_key="RULE_MACRO_SPAWN_SHELL",
                name="Office Document Spawning Shell",
                description="Microsoft Office document spawned cmd.exe or powershell.exe interpreter.",
                severity="critical",
                confidence=0.95,
                mitre_tactics=["Initial Access", "Execution"],
                mitre_techniques=["T1566.001", "T1059.001"],
                condition_fn=lambda ev: (
                    ("winword" in str(ev.get("normalized_data", {}).get("raw_log", {}).get("ParentProcess") or "").lower()
                     or "excel" in str(ev.get("normalized_data", {}).get("raw_log", {}).get("ParentProcess") or "").lower())
                    and ("powershell" in str(ev.get("process_name") or "").lower() or "cmd.exe" in str(ev.get("process_name") or "").lower())
                ),
            )
        )

        # 3. Automated Credential Brute Force (T1110.001)
        self.register_rule(
            RuleDefinition(
                rule_key="RULE_AUTH_BRUTE_FORCE",
                name="Automated Authentication Brute Force",
                description="Repeated authentication failure indicating automated dictionary attack or password guessing.",
                severity="high",
                confidence=0.85,
                mitre_tactics=["Credential Access"],
                mitre_techniques=["T1110.001"],
                condition_fn=lambda ev: (
                    ev.get("event_type") == "auth_failure"
                    or ev.get("destination_port") == 22 and "fail" in str(ev.get("normalized_data", {})).lower()
                    or ev.get("normalized_data", {}).get("raw_log", {}).get("EventID") == 4625
                ),
            )
        )

        # 4. Web Application SQL Injection (T1190)
        sqli_regex = re.compile(r"(\'|%27)\s*(or|union|select|--|#|1=1)", re.IGNORECASE)
        self.register_rule(
            RuleDefinition(
                rule_key="RULE_WEB_SQLI",
                name="SQL Injection Attack Payload",
                description="Inbound HTTP request payload matches SQL syntax injection patterns.",
                severity="high",
                confidence=0.88,
                mitre_tactics=["Initial Access"],
                mitre_techniques=["T1190"],
                condition_fn=lambda ev: bool(
                    sqli_regex.search(urllib.parse.unquote(str(ev.get("command_line") or "")))
                    or sqli_regex.search(urllib.parse.unquote(str(ev.get("normalized_data") or "")))
                    or sqli_regex.search(urllib.parse.unquote(str(ev.get("raw_log") or "")))
                ),
            )
        )

        # 5. Botnet Command & Control Beaconing (T1071.001)
        self.register_rule(
            RuleDefinition(
                rule_key="RULE_BOTNET_C2_BEACON",
                name="Botnet Command & Control Beaconing",
                description="Periodic outbound connection characteristic of Botnet C2 agent.",
                severity="high",
                confidence=0.82,
                mitre_tactics=["Command and Control"],
                mitre_techniques=["T1071.001"],
                condition_fn=lambda ev: (
                    ev.get("event_type") == "c2_beacon"
                    or "ares" in str(ev.get("process_name") or "").lower()
                    or "botnet" in str(ev.get("event_type") or "").lower()
                ),
            )
        )

        # 6. Lateral Network Port Scanning (T1046)
        self.register_rule(
            RuleDefinition(
                rule_key="RULE_PORT_SCAN_DISCOVERY",
                name="Network Service Scanning",
                description="Host conducting horizontal or vertical TCP SYN port scan.",
                severity="medium",
                confidence=0.80,
                mitre_tactics=["Discovery"],
                mitre_techniques=["T1046"],
                condition_fn=lambda ev: (
                    "scan" in str(ev.get("event_type") or "").lower()
                    or "portscan" in str(ev.get("normalized_data") or "").lower()
                    or ev.get("destination_port") in [445, 139, 135, 3389] and "discovery" in str(ev.get("normalized_data") or "").lower()
                ),
            )
        )

    def register_rule(self, rule: RuleDefinition):
        self._rules[rule.rule_key] = rule

    def evaluate_event(self, event: Dict[str, Any]) -> List[DetectionFindingPayload]:
        """Evaluates all registered rules against a single normalized security event."""
        findings: List[DetectionFindingPayload] = []
        event_id = event.get("id") or event.get("event_id") or uuid.uuid4()
        if isinstance(event_id, str):
            try:
                event_id = uuid.UUID(event_id)
            except ValueError:
                event_id = uuid.uuid4()

        host = event.get("source_identifier") or event.get("host")
        user = event.get("user")
        src_ip = event.get("source_ip") or event.get("src_ip")
        dest_ip = event.get("destination_ip") or event.get("dest_ip")

        entity_refs = {
            "hosts": [host] if host else [],
            "users": [user] if user else [],
            "ips": [ip for ip in [src_ip, dest_ip] if ip],
        }

        for rule in self._rules.values():
            try:
                if rule.condition_fn(event):
                    finding = DetectionFindingPayload(
                        finding_id=uuid.uuid4(),
                        event_id=event_id,
                        detection_method="rule",
                        rule_key=rule.rule_key,
                        predicted_class=rule.name,
                        severity=rule.severity,
                        confidence=rule.confidence,
                        mitre_tactics=rule.mitre_tactics,
                        mitre_techniques=rule.mitre_techniques,
                        explanation=rule.description,
                        details={
                            "rule_key": rule.rule_key,
                            "rule_version": rule.version,
                            "event_type": event.get("event_type"),
                        },
                        entity_refs=entity_refs,
                        detected_at=datetime.utcnow(),
                    )
                    findings.append(finding)
            except Exception:
                continue

        return findings

    def sync_rules_to_db(self, db: Session):
        """Synchronizes in-memory rule definitions with detection_rules database table."""
        for rule in self._rules.values():
            existing = db.query(DetectionRule).filter(DetectionRule.rule_key == rule.rule_key).first()
            if not existing:
                db_rule = DetectionRule(
                    rule_key=rule.rule_key,
                    name=rule.name,
                    description=rule.description,
                    rule_type="signature",
                    severity=rule.severity,
                    confidence=rule.confidence,
                    mitre_tactics=rule.mitre_tactics,
                    mitre_techniques=rule.mitre_techniques,
                    rule_logic={"key": rule.rule_key, "version": rule.version},
                    version=rule.version,
                    is_active=True,
                )
                db.add(db_rule)
            else:
                existing.severity = rule.severity
                existing.confidence = rule.confidence
                existing.mitre_tactics = rule.mitre_tactics
                existing.mitre_techniques = rule.mitre_techniques
        db.commit()


rule_engine_instance = RuleEngine()
