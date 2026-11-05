# Project Sentinel — Workspace Projection API & Provenance Specification (P0)

**Document Type:** Core Backend API and Data Provenance Specification  
**Status:** Implemented & Verified Baseline  
**Version:** 1.0  
**Endpoint:** `GET /api/investigations/{investigation_id}/workspace`  
**Primary Consumer:** Agentic Investigation Workspace Frontend

---

## 1. Overview

The Unified Workspace Projection API consolidates the entire investigation lifecycle into a single, strongly-typed, auditable, and provenance-grounded projection contract.

Instead of requiring the frontend to assemble fragmented calls across `/investigations`, `/planner/.../state`, `/planner/.../decisions`, `/orchestration/tasks`, and `/reviews/pending`, this endpoint provides an analyst-oriented projection directly reflecting:

1. **Threat Context**: Severity, attack classification, and affected entities.
2. **Planner Cognitive State**: Current observation, empirical questions, chosen decision, and rationale.
3. **Orchestration History**: Chronological, multi-cycle audit trail with confidence deltas and latency.
4. **Key Findings with Provenance**: Direct linkage to producing worker, decision, and task.
5. **Actionable Recommendation**: Blast-radius simulation and supporting empirical findings.
6. **Human Review Governance**: Direct linkage to the recommendation requiring analyst authorization.

---

## 2. API Contract

### Request
* **HTTP Method**: `GET`
* **Route**: `/api/investigations/{investigation_id}/workspace`
* **Path Parameter**: `investigation_id` (`UUID`)

### Success Response (`200 OK`)
Returns JSON conforming to [`InvestigationWorkspaceProjection`](file:///backend/app/schemas/workspace_projection.py):

```json
{
  "threat": {
    "investigation_id": "3b9ba7f9-9fc0-424a-9421-1262f73df36e",
    "title": "Infiltration Scenario: Lateral Movement Hunt",
    "attack_type": "Infiltration & Lateral Movement",
    "severity": "critical",
    "affected_entities": [
      { "id": "host:WS-FINANCE-01", "label": "WS-FINANCE-01", "type": "host" },
      { "id": "ip:10.0.0.50", "label": "10.0.0.50", "type": "ip" },
      { "id": "proc:powershell.exe", "label": "powershell.exe", "type": "process" }
    ],
    "status": "investigating",
    "confidence": 0.94,
    "confidence_state": "confirmed",
    "current_cycle": 3,
    "max_cycles": 10,
    "detected_at": "2026-11-05T09:40:00Z",
    "data_provenance": {
      "source_type": "benchmark_derived_scenario",
      "scenario_name": "Infiltration & Lateral Movement",
      "benchmark_basis": "CSE-CIC-IDS2018 Profile"
    }
  },
  "planner": {
    "current_observation": "Correlation worker linked host WS-FINANCE-01 to external IP 198.51.100.22.",
    "unresolved_questions": [
      "Does the containment recommendation require human operational review before deployment?"
    ],
    "current_decision": "Execute capability for worker 'response' (Cycle 3)",
    "decision_rationale": "Planner prioritized worker 'response' based on confirmed hypothesis.",
    "rationale_source": "persisted",
    "is_replanning": true,
    "active_capability": {
      "name": "response.execute",
      "worker_type": "response",
      "status": "idle",
      "risk_level": "high"
    }
  },
  "key_findings": [
    {
      "finding_id": "e4f8d9b2-...",
      "summary": "Encoded PowerShell execution spawned by WINWORD.EXE",
      "source_type": "worker_output",
      "source_worker": "detection",
      "mitre_technique_id": "T1059.001",
      "entity_refs": { "hosts": ["WS-FINANCE-01"], "processes": ["powershell.exe"] },
      "confidence_score": 0.88,
      "created_at": "2026-11-05T09:40:15Z",
      "provenance": {
        "source_worker": "detection",
        "planner_decision_id": "a1b2c3d4-...",
        "worker_execution_id": "f5e6d7c8-...",
        "agent_task_id": null,
        "produced_at": "2026-11-05T09:40:15Z",
        "provenance_status": "direct"
      }
    }
  ],
  "orchestration_history": [
    {
      "cycle": 1,
      "decision_type": "continue_investigation",
      "selected_worker": "correlation",
      "selected_capability": "correlation.execute",
      "observation": "Correlation worker constructed entity graph.",
      "unresolved_question": "Evaluate network endpoints communicating with external IP",
      "rationale": "Selected worker 'correlation' with selection score 1.10",
      "confidence_before": 0.10,
      "confidence_after": 0.38,
      "confidence_delta": 0.28,
      "latency_ms": 45,
      "evidence_count_gained": 1,
      "status": "success",
      "created_at": "2026-11-05T09:40:10Z"
    }
  ],
  "recommendation": {
    "id": "7b8c9d0e-...",
    "action": "Isolate affected host and block C2 IP at border firewall",
    "rationale": "Prevents lateral movement and active data exfiltration.",
    "risk_level": "medium",
    "requires_approval": true,
    "approval_status": "pending",
    "supporting_findings": [
      {
        "finding_id": "e4f8d9b2-...",
        "summary": "Encoded PowerShell execution spawned by WINWORD.EXE",
        "relevance": "Primary empirical justification"
      }
    ],
    "provenance_status": "direct",
    "simulation": {
      "blast_radius_score": 0.15,
      "disruption_level": "minimal",
      "safety_assessment": "Safe: Preserves remote agent management socket.",
      "rollback_plan": "Automated network un-isolation via agent control."
    }
  },
  "human_review": {
    "review_id": "9a8b7c6d-...",
    "recommendation_id": "7b8c9d0e-...",
    "status": "approved",
    "decision": "approved",
    "analyst_id": "a4b3c2d1-...",
    "analyst_comments": "Validated CobaltStrike beaconing. Approved network containment.",
    "requested_at": "2026-11-05T09:41:00Z",
    "decided_at": "2026-11-05T09:42:15Z",
    "provenance_status": "direct"
  },
  "workspace_metadata": {
    "generated_at": "2026-11-05T09:43:00Z",
    "investigation_state_version": 4
  }
}
```

### Error Responses
* `404 Not Found`: Returned when `investigation_id` does not match an existing record.
* `422 Unprocessable Entity`: Returned if `investigation_id` is not a valid UUID string.

---

## 3. Data Sources Mapping

| Projection Field | Canonical Database Source | Relationship / Join |
|---|---|---|
| `threat.investigation_id` | `investigations.investigation_id` | Primary Key |
| `threat.title` | `investigations.title` | Direct column |
| `threat.status` | `investigations.status` | Direct column |
| `threat.confidence` | `investigations.current_confidence` | Direct column |
| `threat.confidence_state` | `investigations.confidence_state` | Direct column |
| `threat.current_cycle` | `investigations.planning_cycle_count` | Direct column |
| `threat.attack_type` | `incident_candidates.title` / `hypotheses.label` | Resolved via `investigations.incident_candidate_id` or hypotheses |
| `threat.affected_entities`| `evidence.entity_refs` | Aggregated and deduplicated across all investigation evidence |
| `threat.data_provenance` | `investigations.title` / `evidence.source_ref` | Scanned against benchmark registry profiles |
| `planner.current_observation`| `planner_decisions.explanation_summary` | Most recent decision record |
| `planner.unresolved_questions`| Derived gap analysis | Mathematical evaluation of state snapshot |
| `planner.current_decision` | `planner_decisions.selected_worker` | Most recent decision record |
| `planner.decision_rationale` | `planner_decisions.explanation_summary` / scores | Most recent decision record |
| `planner.is_replanning` | `planner_decisions.selected_worker` frequency | Replan flag or repeated capability execution |
| `planner.active_capability` | `agent_tasks` / `planner_decisions` | Running task or most recent decision capability |
| `key_findings` | `evidence` table | Filtered by `investigation_id`, joined with `timeline_events` |
| `key_findings[].provenance` | `evidence.planner_decision_id`, `worker_execution_id` | Direct FKs or derived proximity matching |
| `orchestration_history` | `planner_decisions` + `worker_executions` | Ordered by `cycle_number ASC` |
| `recommendation` | `reports` + `recommendations` | Filtered by `investigation_id` |
| `recommendation.supporting_findings`| `recommendations.supporting_evidence_ids` | Direct UUID array referencing `evidence.evidence_id` |
| `recommendation.simulation`| `response_simulations` | Joined via `recommendations.recommendation_id` or `investigation_id` |
| `human_review` | `human_reviews` | Joined via `human_reviews.recommendation_id` or `investigation_id` |

---

## 4. Derived Fields & Derivation Logic

To ensure 100% frontend truthfulness without fabricating agent thoughts, all non-persisted cognitive fields follow deterministic rules:

| Field | Source Records | Derivation Rule |
|---|---|---|
| `planner.unresolved_questions` | `investigations.current_confidence`, `hypotheses`, `evidence` | 1. If confidence $< 0.65$: *"Is the observed anomalous activity verified adversary behavior or benign baseline noise?"*<br>2. If entity graph has $>1$ entities and evidence $<5$: *"Are the identified endpoints and network connections part of a coordinated multi-stage progression?"*<br>3. If contradictions exist: *"Resolve contradictory evidence on primary attack hypothesis."*<br>4. If no hypothesis confirmed: *"Which MITRE ATT&CK technique accounts for the observed execution signature?"*<br>5. If confidence $\ge 0.85$: *"Does the proposed containment action require operational review before deployment?"* |
| `planner.is_replanning` | `planner_decisions` | Set to `True` if `decision_type == 'replan'`, or if `len(decisions) > len(set(selected_workers))` (capability revisited after new evidence). |
| `planner.rationale_source` | `planner_decisions` | Marked as `"persisted"` if `explanation_summary` is populated by agent worker; marked as `"derived_from_execution_data"` if formatted from utility scores. |
| `orchestration_history.confidence_delta`| `planner_decisions.confidence_before`, `confidence_after` | $\Delta = \text{confidence\_after} - \text{confidence\_before}$. |
| `orchestration_history.evidence_count_gained`| `evidence.planner_decision_id` | Count of evidence records with matching `planner_decision_id`. Falls back to `raw_output.findings` count. |
| `threat.severity` | `incident_candidates.severity` / confidence | If candidate exists, uses `candidate.severity`. Otherwise: $\ge 0.85 \rightarrow \text{critical}$, $\ge 0.65 \rightarrow \text{high}$, $\ge 0.35 \rightarrow \text{medium}$, $< 0.35 \rightarrow \text{low}$. |

---

## 5. Provenance Semantics

### Finding Provenance (`key_findings[].provenance.provenance_status`)
* `"direct"`: The finding has an explicit foreign key (`planner_decision_id`, `worker_execution_id`, or `agent_task_id`) recorded in the database.
* `"derived"`: The finding has a recorded `produced_by_worker` string that matches a planner decision executed during the same cycle.
* `"legacy_unlinked"`: The record predates provenance columns or was manually ingested without execution tracking.

### Recommendation Provenance (`recommendation.provenance_status`)
* `"direct"`: The recommendation contains an explicit list of supporting evidence UUIDs in `recommendations.supporting_evidence_ids`.
* `"derived"`: Evidence exists for the investigation, and top corroborated findings are linked as supporting context.
* `"limited"`: No evidence is linked or present in the investigation.

### Human Review Provenance (`human_review.provenance_status`)
* `"direct"`: The review request contains an explicit `recommendation_id` linking it to the specific containment action.
* `"legacy_unlinked"`: The review request is linked only at the investigation level without an explicit recommendation foreign key.
