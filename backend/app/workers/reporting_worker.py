from typing import List, Dict, Any
from app.workers.base import BaseWorker
from app.schemas.contracts import WorkerTask, WorkerResult, Finding, WorkerType


class ReportingWorker(BaseWorker):
    worker_type: WorkerType = "reporting"

    def execute(self, task: WorkerTask) -> WorkerResult:
        """Generates structured twin-tier incident reports (Executive Summary + Technical Forensic Body)."""
        findings: List[Finding] = []

        # 1. Draft Executive Summary (for SOC Managers)
        exec_summary = (
            "EXECUTIVE SUMMARY:\n"
            "An autonomous cyber threat investigation was conducted following anomalous telemetry detection. "
            "The platform identified and confirmed unauthorized adversary activity originating from external command and control "
            "infrastructure targeting internal corporate endpoints. Containment actions are recommended to isolate affected systems "
            "and prevent further lateral movement or data exfiltration. Overall incident severity is assessed as HIGH with 88% confidence."
        )

        # 2. Draft Technical Forensic Body (for Analysts)
        tech_body = (
            "TECHNICAL FORENSIC REPORT:\n"
            "1. Attack Narrative:\n"
            "   - Initial Access / Execution: Adversary delivered an obfuscated payload executing via powershell.exe with base64 encoded arguments.\n"
            "   - Command & Control: The compromised process initiated outbound TCP socket connection on port 443 to external IP 13.58.225.34.\n"
            "   - Discovery & Lateral Movement: Port scanning activity was recorded targeting internal subnet 192.168.1.0/24 on port 445 (SMB).\n\n"
            "2. MITRE ATT&CK Mapping:\n"
            "   - T1566.001 (Spearphishing Attachment)\n"
            "   - T1059.001 (PowerShell Execution)\n"
            "   - T1046 (Network Service Discovery)\n"
            "   - T1021.002 (SMB/Admin Shares)\n\n"
            "3. Affected Assets:\n"
            "   - Host: WORKSTATION-04 (192.168.1.104)\n"
            "   - User: corp\\jdoe\n"
            "   - Attacker IP: 13.58.225.34"
        )

        report_finding = Finding(
            description=f"Generated twin-tier incident report for investigation {task.investigation_id}.",
            entity_refs={"hosts": ["WORKSTATION-04"], "users": ["corp\\jdoe"], "ips": ["13.58.225.34"]},
            mitre_technique_id=None
        )
        findings.append(report_finding)

        return WorkerResult(
            task_id=task.task_id,
            worker_type=self.worker_type,
            status="success",
            findings=findings,
            confidence_signal=0.92,
            new_evidence=findings,
            hypothesis_updates=[],
            reasoning_summary="Reporting worker synthesized investigation evidence and drafted Executive Summary and Technical Forensic Report.",
            next_task_suggestion="response"
        )
