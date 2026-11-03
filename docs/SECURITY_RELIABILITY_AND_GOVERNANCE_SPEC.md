# Project Sentinel — Security, Reliability & Governance Specification (SRGS)

**Document Type:** Architecture and Operational Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Security, Reliability, Governance, Failure Handling, Auditability, and Human Oversight  
**Related Components:** Orchestration Core, Action Validator, PostgreSQL Audit Log, FastAPI Auth, Human-in-the-Loop Cockpit

---

# 1. Purpose & Governance Architecture

While Project Sentinel employs an adaptive, non-linear multi-agent orchestration model, **adaptive intelligence must never mean unrestricted autonomy**.

This specification formalizes the deterministic guardrails, security boundaries, failure recovery protocols, audit trails, and human-in-the-loop (HITL) policies governing the platform:

```text
                    ┌──────────────────┐
                    │   ORCHESTRATOR   │
                    │  Plans an Action │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  POLICY LAYER    │
                    │  (Deterministic) │
                    └────────┬─────────┘
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
              [Allowed]              [Blocked]
                  │                     │
                  ▼                     ▼
          ┌──────────────┐        Record Audit Decision
          │ CAPABILITY   │              │
          │ EXECUTION    │              ▼
          └──────┬───────┘            Re-plan
                 │
                 ▼
          ┌──────────────┐
          │ RESULT       │
          │ VALIDATION   │
          └──────┬───────┘
                 │
                 ▼
           UPDATE STATE
```

---

# 2. Core Governance Principles

1. **Bounded Autonomy:** The LLM can propose actions, but execution is restricted to a strictly registered capability set and bounded budgets.
2. **Evidence Before Conclusion:** Claims must trace back to concrete empirical events; unsupported inferences remain flagged as `UNVERIFIED`.
3. **Explicit Uncertainty:** The platform natively outputs `SUPPORTED`, `INCONCLUSIVE`, `CONTRADICTED`, or `REQUIRES_REVIEW` rather than manufacturing false certainty.
4. **Human Authority:** Human analysts retain absolute veto power and final approval authority for high-impact actions (containment, account revocation).
5. **Least Privilege:** Capabilities execute with narrow read-only access to relevant event scopes; only the State Manager writes to canonical state.
6. **Immutable Auditability:** Every action, decision rationale, capability output, and human override is append-logged in the audit bus.
7. **Graceful Degradation:** External dependency failures (Ollama, ChromaDB) degrade into fallback modes rather than crashing the investigation.

---

# 3. Authentication & Role-Based Access Control (RBAC)

FastAPI enforces JWT-based authentication with 4 hierarchical roles:

| Role | Permissions & Operational Scope |
| :--- | :--- |
| **Analyst (Tier 1)** | View telemetry, inspect active investigations, view forensic reports. |
| **Senior Threat Hunter (Tier 2)** | Launch autonomous hunts, trigger manual cycles, resolve hypothesis contradictions. |
| **Incident Commander (HITL)** | Authorize destructive containment actions (isolate host, terminate PID, block IP). |
| **Administrator / Auditor** | Configure system policies, inspect cryptographic audit trails, run benchmarks. |

---

# 4. Human-in-the-Loop (HITL) Governance Protocol

When an investigation triggers a high-impact condition, the runtime enters `WAITING_REVIEW`:

```text
Investigation Running ──► Condition Met (e.g. Destructive Containment / Contradiction)
                                      │
                                      ▼
                        Status = WAITING_REVIEW
                                      │
                         Analyst Review Cockpit
                                      │
                      ┌───────────────┴───────────────┐
                      ▼                               ▼
                 [Approve]                        [Reject]
                      │                               │
                      ▼                               ▼
          Action Marked "approved"         Action Marked "rejected"
          Audit Log Created                Audit Log Created
          Execution Dispatched             Planner Backtracks / Re-plans
```

### Mandatory Review Triggers
- Destructive containment actions (Network isolation, firewall egress blocks, session token revocation).
- Unresolvable high-severity contradiction between host logs and network flow data.
- Step budget exhaustion with posterior confidence in ambiguous zone ($0.50 \le \text{Conf} \le 0.79$).

---

# 5. Prompt Safety & Data Boundary Isolation

To prevent prompt injection from attacker-controlled payload strings (e.g., suspicious HTTP URLs, malicious PowerShell command lines):

```text
External Content / Telemetry ──► Bound as Quoted Untrusted Data ──► LLM Parser
                                              │
                                   NEVER Intermingled With
                                              │
                                 SYSTEM INSTRUCTIONS
```

- **Strict Invariant:** System prompts and security policies are immutable and isolated from incoming telemetry text and retrieved RAG context.
- **Structured Parsing:** LLM completions are accepted strictly via Pydantic schema validation; invalid JSON triggers an automated deterministic fallback.

---

# 6. Failure Classification & Circuit-Breaker Architecture

Failures are categorized into five distinct severity classes:

```text
FAILURE TAXONOMY:
├── TRANSIENT   : Brief network hiccup or query timeout (triggers bounded exponential backoff)
├── CAPABILITY  : Worker returned invalid schema or exception (handled by worker fallback)
├── DEPENDENCY  : External sidecar down (Ollama down -> rule-based selector; ChromaDB down -> empirical mode)
├── VALIDATION  : Claim lacked raw evidence citations (flagged UNVERIFIED; blocked from final report)
└── CRITICAL    : PostgreSQL unreachable (investigation safely paused; state frozen)
```

### Circuit Breaker Defaults
- Max consecutive LLM timeouts: $3 \to$ trips circuit $\to$ activates deterministic rule-based Planner fallback.
- Max worker retries per action: $2 \to$ if exhausted, marks gap `UNRESOLVABLE` and forces alternative capability selection.

---

# 7. Resource Budgets & Infinite Loop Prevention

Every investigation runs inside a bounded sandbox:

```python
MAX_STEPS = 10                  # Maximum orchestration decision cycles
MAX_DURATION_SECONDS = 600      # 10 minutes wall-clock timeout
MAX_CAPABILITY_CALLS = 15       # Total worker invocations
MAX_DUPLICATE_ACTIONS = 0       # Zero tolerance for identical action signatures
```

### Loop Prevention Mechanics
Every candidate action computes an execution signature:
$$\text{Sig} = \text{SHA256}(\text{Capability} \,\|\, \text{Target Entity} \,\|\, \text{Time Window} \,\|\, \text{Parameters})$$
If $\text{Sig} \in \text{RecentSignatures}$ without a material state change (new evidence or $\ge 20\%$ time window expansion), the Action Validator rejects the proposal with `REDUNDANCY_PENALTY`.

---

# 8. Cryptographic Audit Logging & Decision Tracing

Every decision cycle creates an immutable record in PostgreSQL:

```text
AuditEntry:
├── timestamp: ISO8601
├── investigation_id: UUID
├── state_version: int
├── event_type: "ACTION_PROPOSED" | "POLICY_VALIDATED" | "CONTAINMENT_APPROVED" | ...
├── actor_type: "orchestrator" | "analyst" | "capability_worker"
├── actor_id: str
├── decision_payload: {
│     evidence_gap: str,
│     candidate_actions: List[str],
│     selected_action: str,
│     rationale: str,
│     policy_verdict: "ALLOWED" | "BLOCKED"
│   }
└── previous_entry_hash: SHA256 (Hash-chained for tamper-evidence)
```

---

# 9. Final Incident Report Governance

Generated reports maintain strict structural isolation between observed facts and AI interpretations:

```text
Incident Report Sections:
1. Executive Briefing (High-level business risk & severity)
2. Empirical Observed Evidence (Raw timestamps, event IDs, host names)
3. Derived Analytical Findings (Correlated event links, graph centrality)
4. Contextual Knowledge (ATT&CK technique guidance from RAG)
5. Claim-by-Claim Confidence Ledger (Posterior score with evidence citations)
6. Unresolved Gaps & System Limitations (Degraded modes, missing logs)
7. Audit Trail & Human Approvals (Timestamps of analyst sign-offs)
```
