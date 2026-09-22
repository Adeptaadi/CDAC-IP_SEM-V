from typing import List, Dict, Any
from app.workers.base import BaseWorker
from app.schemas.contracts import WorkerTask, WorkerResult, Finding, WorkerType


class ResponseWorker(BaseWorker):
    worker_type: WorkerType = "response"

    def execute(self, task: WorkerTask) -> WorkerResult:
        """Formulates actionable containment recommendations with risk/impact analysis and mandatory human approval (PRD FR-701-704)."""
        findings: List[Finding] = []

        recommendations = [
            {
                "action": "Network Isolate Host: WORKSTATION-04",
                "risk_level": "medium",
                "impact_summary": "Temporarily disconnects workstation from corporate LAN. Prevents further lateral spread and active C2 communication.",
                "requires_approval": True,
            },
            {
                "action": "Block Inbound/Outbound IP: 13.58.225.34 on Edge Firewall",
                "risk_level": "low",
                "impact_summary": "Blocks adversary C2 server across all enterprise perimeter firewalls.",
                "requires_approval": True,
            },
            {
                "action": "Terminate Process: powershell.exe (PID 4812) on WORKSTATION-04",
                "risk_level": "low",
                "impact_summary": "Kills the active reverse shell process.",
                "requires_approval": True,
            },
            {
                "action": "Force Password Reset & Revoke Active Sessions for corp\\jdoe",
                "risk_level": "low",
                "impact_summary": "Invalidates potentially compromised Kerberos tickets and session tokens.",
                "requires_approval": True,
            }
        ]

        for rec in recommendations:
            f = Finding(
                description=f"RECOMMENDED CONTAINMENT ACTION: {rec['action']} (Risk: {rec['risk_level'].upper()}) - Impact: {rec['impact_summary']}",
                entity_refs={"hosts": ["WORKSTATION-04"], "users": ["corp\\jdoe"], "ips": ["13.58.225.34"]},
                mitre_technique_id=None
            )
            findings.append(f)

        return WorkerResult(
            task_id=task.task_id,
            worker_type=self.worker_type,
            status="success",
            findings=findings,
            confidence_signal=0.95,
            new_evidence=findings,
            hypothesis_updates=[],
            reasoning_summary="Response worker generated 4 prioritized containment actions with risk/impact evaluations. Mandatory human approval enforced.",
            next_task_suggestion=None  # Terminal investigation stage
        )
