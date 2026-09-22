import re
from typing import List, Dict, Any, Optional
from uuid import uuid4
from app.workers.base import BaseWorker
from app.schemas.contracts import WorkerTask, WorkerResult, Finding, WorkerType


class DetectionWorker(BaseWorker):
    worker_type: WorkerType = "detection"

    # Known malicious indicators and heuristics
    HEURISTICS = [
        {
            "name": "Encoded PowerShell Command Execution",
            "technique_id": "T1059.001",
            "regex": re.compile(r"powershell.*(-enc|-encodedcommand|-w hidden|-nop)", re.IGNORECASE),
            "severity": "high",
            "confidence": 0.88,
            "description": "Suspicious PowerShell command execution with encoded payload or hidden window parameters."
        },
        {
            "name": "Office Application Spawning Command Interpreter",
            "technique_id": "T1566.001",
            "check": lambda ev: (ev.get("raw_log", {}).get("ParentProcess") or "").lower().endswith("winword.exe") and "powershell" in (ev.get("process_name") or "").lower(),
            "severity": "critical",
            "confidence": 0.95,
            "description": "Microsoft Word spawned PowerShell interpreter, strongly indicating a malicious macro payload."
        },
        {
            "name": "Automated Credential Brute Force",
            "technique_id": "T1110.001",
            "check": lambda ev: ev.get("event_type") == "auth_failure" or ev.get("raw_log", {}).get("EventID") == 4625,
            "severity": "high",
            "confidence": 0.82,
            "description": "Repeated authentication failure indicating potential dictionary attack or password spray."
        },
        {
            "name": "Web Application SQL Injection Query",
            "technique_id": "T1190",
            "regex": re.compile(r"(\'|%27)\s*(or|union|select|--|#|1=1)", re.IGNORECASE),
            "severity": "high",
            "confidence": 0.85,
            "description": "Inbound HTTP request containing SQL injection syntax."
        },
        {
            "name": "Botnet C2 Beaconing",
            "technique_id": "T1071.001",
            "check": lambda ev: ev.get("event_type") == "c2_beacon" or "ares" in (ev.get("process_name") or "").lower(),
            "severity": "high",
            "confidence": 0.80,
            "description": "Periodic outbound network beaconing characteristic of Botnet C2 agent."
        },
        {
            "name": "Denial of Service HTTP Resource Exhaustion",
            "technique_id": "T1498.001",
            "check": lambda ev: ev.get("event_type") == "dos_flood" or "goldeneye" in str(ev.get("raw_log", {})).lower(),
            "severity": "medium",
            "confidence": 0.78,
            "description": "High-volume connection flood aimed at application resource exhaustion."
        }
    ]

    def execute(self, task: WorkerTask) -> WorkerResult:
        """Evaluates telemetry in scope, detecting anomalies and generating structured findings."""
        findings: List[Finding] = []
        max_confidence_signal = 0.5
        suggested_next = "correlation"

        # If specific events or context are provided in task, triage them
        events = getattr(task, "events", [])
        if not events and task.context:
            # Fallback evaluation based on objective
            objective_lower = task.objective.lower()
            for h in self.HEURISTICS:
                if "regex" in h and h["regex"].search(task.objective):
                    findings.append(
                        Finding(
                            description=h["description"],
                            entity_refs={"hosts": ["TARGET-HOST"]},
                            mitre_technique_id=h["technique_id"]
                        )
                    )
                    max_confidence_signal = max(max_confidence_signal, h["confidence"])

        for ev in events:
            ev_dict = ev if isinstance(ev, dict) else ev.model_dump()
            cmd = ev_dict.get("command_line") or ""
            proc = ev_dict.get("process_name") or ""
            host = ev_dict.get("host")
            user = ev_dict.get("user")
            src_ip = ev_dict.get("src_ip")
            dest_ip = ev_dict.get("dest_ip")

            entity_refs = {
                "hosts": [host] if host else [],
                "users": [user] if user else [],
                "ips": [ip for ip in [src_ip, dest_ip] if ip],
                "processes": [proc] if proc else []
            }

            for h in self.HEURISTICS:
                matched = False
                if "regex" in h and (h["regex"].search(cmd) or h["regex"].search(proc)):
                    matched = True
                elif "check" in h and h["check"](ev_dict):
                    matched = True

                if matched:
                    findings.append(
                        Finding(
                            description=f"{h['description']} (Event: {ev_dict.get('event_type')})",
                            entity_refs=entity_refs,
                            mitre_technique_id=h["technique_id"]
                        )
                    )
                    max_confidence_signal = max(max_confidence_signal, h["confidence"])

        # Default fallback finding if none matched explicitly
        if not findings:
            findings.append(
                Finding(
                    description=f"Triaged telemetry according to objective: {task.objective}",
                    entity_refs={"hosts": [], "users": [], "ips": []},
                    mitre_technique_id=None
                )
            )
            max_confidence_signal = 0.45
            suggested_next = "investigation"

        return WorkerResult(
            task_id=task.task_id,
            worker_type=self.worker_type,
            status="success",
            findings=findings,
            confidence_signal=max_confidence_signal,
            new_evidence=findings,
            reasoning_summary=f"Detection worker evaluated telemetry and flagged {len(findings)} anomaly signatures with confidence {max_confidence_signal:.2f}.",
            next_task_suggestion=suggested_next
        )
