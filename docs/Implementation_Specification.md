# Implementation Specification (IS)

**Project:** Project Sentinel — Agentic AI-powered Autonomous Cyber Threat Hunting Platform
**Companion to:** TDD v1.0, AIDD v1.0
**Purpose:** This document is not a new layer of architecture — it fills five specific holes in the TDD/AIDD where those documents describe *what* exists but not *how it computes*. Everything below is written so a developer could implement it directly: exact formulas, DDL, pseudocode, and type contracts.

**Scope of this document**
1. Confidence Scoring Algorithm (replaces the placeholder formula in AIDD §12)
2. Database Schema (replaces the field-name-only tables in SDD's data model section)
3. Planner Decision Algorithm (replaces the flowchart in AIDD §6)
4. Interface Contracts — Planner↔Worker, RAG, Confidence Engine (new; TDD referenced these without signatures)
5. Evaluation Methodology (replaces the metric *names* in AIDD §14 with measurement protocols)

---

# 1. Confidence Scoring Algorithm

## 1.1 Why the original formula doesn't work

AIDD §12 proposed:

```
Updated Confidence = Previous Confidence + Supporting Evidence − Contradictory Evidence + Knowledge Strength
```

This is additive and unbounded — nothing stops it from exceeding 1.0 or going negative, and there's no defined unit for "Supporting Evidence." It cannot be implemented as written. Below is a bounded, composable replacement.

## 1.2 Design: weighted logistic (log-odds) update

Confidence is tracked as a probability `C ∈ [0, 1]`. Instead of updating `C` additively (which breaks at the boundaries), we update it in **log-odds space**, where sums are safe, then convert back:

```
logit(C) = ln( C / (1 − C) )
sigmoid(x) = 1 / (1 + e^-x)
```

Each planning cycle produces a **confidence delta** from six independently-scored factors, and the delta is applied in log-odds space:

```
logit(C_t) = logit(C_{t-1}) + Σ_i  w_i · δ_i(cycle_t)
C_t = sigmoid( logit(C_t) )
```

This guarantees `C_t` always stays in `(0, 1)`, lets each factor contribute an unbounded raw signal (`δ_i` can be any real number) without breaking the final score, and is the same mechanism used for calibrated classifier ensembling — so it's auditable against a known technique rather than a bespoke heuristic.

## 1.3 Factor definitions

| Factor `i` | Weight `w_i` | Computed from |
|---|---|---|
| Detection Quality | 0.15 | Detector's own confidence × rule severity tier |
| Evidence Quality | 0.20 | Evidence count, source diversity, corroboration |
| Correlation Quality | 0.15 | Density of the entity/timeline correlation graph |
| Knowledge Match | 0.15 | RAG top-k similarity, weighted by source reliability |
| Worker Agreement | 0.15 | Inverse variance across independent worker confidence estimates |
| Historical Similarity | 0.20 | Similarity to nearest episodic-memory cases, weighted by their known outcome accuracy |

Weights sum to 1.0 and are stored in config (not hardcoded) so they can be tuned per the calibration process in §5.5.

### Detection Quality
```
δ_detection = mean(detector_raw_scores) × severity_multiplier − baseline
severity_multiplier ∈ {0.8 (low), 1.0 (medium), 1.2 (high), 1.4 (critical)}
baseline = 0.5   # score of 0.5 = no information gained
```

### Evidence Quality
```
δ_evidence = min(1.0, evidence_count_this_cycle / 5) 
             × source_diversity_ratio
             × corroboration_bonus
source_diversity_ratio = distinct_sources / total_evidence   (0–1)
corroboration_bonus = 1.2 if ≥2 sources agree on same fact else 1.0
```

### Correlation Quality
```
δ_correlation = edges_added_this_cycle / max(1, nodes_in_graph)
# graph = entities (hosts, users, IPs, processes) as nodes,
# temporal/causal links found by the Correlation Worker as edges
```

### Knowledge Match
```
δ_knowledge = mean(cosine_similarity of top_k retrieved chunks)
              × reliability_weight(source)
reliability_weight: MITRE=1.0, internal_playbook=0.9,
                     historical_investigation=0.8, open_threat_intel=0.6
```

### Worker Agreement
```
δ_agreement = 1 − stddev(worker_confidence_estimates) / 0.5
# stddev near 0 (workers agree) → δ near 1 (strong positive signal)
# stddev near 0.5+ (workers disagree) → δ near 0 or negative
```

### Historical Similarity
```
δ_historical = Σ (sim(current_case, past_case_k) × past_case_k.outcome_accuracy)
               for top-5 nearest episodic memory cases, then normalized to [-1,1]
```

## 1.4 Worked example

Starting confidence after cycle 1: `C_0 = 0.30` → `logit(0.30) = -0.847`

Cycle 2 factor deltas (illustrative):

| Factor | δ_i | w_i | w_i·δ_i |
|---|---|---|---|
| Detection | +0.35 | 0.15 | +0.0525 |
| Evidence | +0.60 | 0.20 | +0.1200 |
| Correlation | +0.20 | 0.15 | +0.0300 |
| Knowledge | +0.45 | 0.15 | +0.0675 |
| Agreement | +0.10 | 0.15 | +0.0150 |
| Historical | +0.25 | 0.20 | +0.0500 |
| **Sum** | | | **+0.3350** |

```
logit(C_1) = -0.847 + 0.335 = -0.512
C_1 = sigmoid(-0.512) = 0.375
```

Confidence rose from 0.30 → 0.375 in one cycle — a meaningful but not runaway jump, which is the intended behavior (no single cycle should be able to swing confidence from "Low" straight to "Very High").

## 1.5 Confidence states (thresholds, configurable)

| State | Range |
|---|---|
| Very Low | 0.00 – 0.20 |
| Low | 0.20 – 0.40 |
| Moderate | 0.40 – 0.65 |
| High | 0.65 – 0.85 |
| Very High | 0.85 – 1.00 |

Investigation auto-completion requires `C ≥ 0.85` **and** at least 3 planning cycles **and** zero unresolved contradictions (see §3.3 termination logic).

---

# 2. Database Schema

Target: PostgreSQL 15+. Vector data (embeddings) stays in ChromaDB per AIDD §9 — Postgres stores only relational/investigation state and *references* to vector IDs, not the vectors themselves.

```sql
-- Extension for UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- USERS & RBAC
-- ============================================================

CREATE TABLE roles (
    role_id        SMALLINT PRIMARY KEY,
    name           VARCHAR(50) UNIQUE NOT NULL,   -- 'analyst','senior_analyst','admin'
    description    TEXT
);

CREATE TABLE users (
    user_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email          VARCHAR(255) UNIQUE NOT NULL,
    display_name   VARCHAR(255) NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at  TIMESTAMPTZ
);

CREATE TABLE user_roles (
    user_id        UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role_id        SMALLINT NOT NULL REFERENCES roles(role_id),
    PRIMARY KEY (user_id, role_id)
);

-- ============================================================
-- INVESTIGATIONS
-- ============================================================

CREATE TABLE investigations (
    investigation_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title               VARCHAR(255) NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'active'
                         CHECK (status IN ('active','paused','completed','escalated','closed_no_threat')),
    current_confidence  NUMERIC(5,4) NOT NULL DEFAULT 0.0
                         CHECK (current_confidence BETWEEN 0 AND 1),
    confidence_state    VARCHAR(20) NOT NULL DEFAULT 'very_low',
    current_goal        TEXT,
    planning_cycle_count SMALLINT NOT NULL DEFAULT 0,
    triggering_event_id  UUID,               -- FK to source SIEM event, external system
    assigned_analyst_id UUID REFERENCES users(user_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at           TIMESTAMPTZ
);

CREATE INDEX idx_investigations_status ON investigations(status);
CREATE INDEX idx_investigations_confidence ON investigations(current_confidence);

-- ============================================================
-- EVIDENCE
-- ============================================================

CREATE TABLE evidence (
    evidence_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id   UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    source_type        VARCHAR(50) NOT NULL,   -- 'log','alert','worker_output','analyst_input'
    source_ref          TEXT,                  -- pointer to raw log/alert in source system
    description         TEXT NOT NULL,
    entity_refs          JSONB,                 -- {"hosts":[...], "users":[...], "ips":[...]}
    produced_by_worker  VARCHAR(30),            -- nullable if analyst-submitted
    corroborated_by     UUID[] DEFAULT '{}',    -- array of evidence_id this supports/is supported by
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_evidence_investigation ON evidence(investigation_id);
CREATE INDEX idx_evidence_entity_refs ON evidence USING GIN (entity_refs);

-- ============================================================
-- TIMELINE EVENTS
-- ============================================================

CREATE TABLE timeline_events (
    event_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id    UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    evidence_id         UUID REFERENCES evidence(evidence_id),
    occurred_at          TIMESTAMPTZ NOT NULL,
    event_summary         TEXT NOT NULL,
    mitre_technique_id    VARCHAR(20),          -- e.g. 'T1110'
    sequence_position      INT                  -- ordering when timestamps tie
);

CREATE INDEX idx_timeline_investigation_time ON timeline_events(investigation_id, occurred_at);

-- ============================================================
-- HYPOTHESES
-- ============================================================

CREATE TABLE hypotheses (
    hypothesis_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id     UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    label                 VARCHAR(255) NOT NULL,     -- 'Credential Theft'
    status                VARCHAR(20) NOT NULL DEFAULT 'active'
                          CHECK (status IN ('active','strengthened','weakened','rejected','confirmed')),
    confidence            NUMERIC(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    mitre_technique_ids   TEXT[],
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE hypothesis_evidence (        -- many-to-many join
    hypothesis_id   UUID NOT NULL REFERENCES hypotheses(hypothesis_id) ON DELETE CASCADE,
    evidence_id     UUID NOT NULL REFERENCES evidence(evidence_id) ON DELETE CASCADE,
    stance          VARCHAR(10) NOT NULL CHECK (stance IN ('supports','contradicts')),
    weight          NUMERIC(4,3) NOT NULL DEFAULT 1.0,
    PRIMARY KEY (hypothesis_id, evidence_id)
);

-- ============================================================
-- PLANNER DECISIONS (audit trail of every planning cycle)
-- ============================================================

CREATE TABLE planner_decisions (
    decision_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id      UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    cycle_number           SMALLINT NOT NULL,
    selected_worker         VARCHAR(30) NOT NULL,
    selection_score          NUMERIC(6,4),         -- utility score that won (see §3.2)
    knowledge_need           TEXT,
    confidence_before         NUMERIC(5,4) NOT NULL,
    confidence_after           NUMERIC(5,4) NOT NULL,
    explanation_summary          TEXT NOT NULL,     -- analyst-facing, not raw chain-of-thought
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (investigation_id, cycle_number)
);

-- ============================================================
-- WORKER EXECUTIONS
-- ============================================================

CREATE TABLE worker_executions (
    execution_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id            UUID NOT NULL REFERENCES planner_decisions(decision_id) ON DELETE CASCADE,
    worker_type              VARCHAR(30) NOT NULL
                            CHECK (worker_type IN ('detection','correlation','investigation','reporting','response')),
    status                    VARCHAR(15) NOT NULL CHECK (status IN ('success','partial','failed')),
    input_context_ref          TEXT,               -- pointer to assembled RAG context, logged separately
    raw_output                  JSONB NOT NULL,
    latency_ms                   INT,
    llm_token_usage                INT,
    created_at                     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_worker_exec_decision ON worker_executions(decision_id);

-- ============================================================
-- REPORTS & RECOMMENDATIONS
-- ============================================================

CREATE TABLE reports (
    report_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id       UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    executive_summary        TEXT NOT NULL,
    technical_body            TEXT NOT NULL,
    final_confidence           NUMERIC(5,4) NOT NULL,
    generated_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_by_user_id          UUID REFERENCES users(user_id),
    approved_at                   TIMESTAMPTZ
);

CREATE TABLE recommendations (
    recommendation_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id              UUID NOT NULL REFERENCES reports(report_id) ON DELETE CASCADE,
    action                  TEXT NOT NULL,
    risk_level                VARCHAR(10) NOT NULL CHECK (risk_level IN ('low','medium','high','critical')),
    impact_summary              TEXT,
    requires_approval             BOOLEAN NOT NULL DEFAULT TRUE,
    approval_status                VARCHAR(15) NOT NULL DEFAULT 'pending'
                                  CHECK (approval_status IN ('pending','approved','rejected','executed')),
    approved_by_user_id             UUID REFERENCES users(user_id)
);

-- ============================================================
-- AUDIT LOG (append-only)
-- ============================================================

CREATE TABLE audit_log (
    audit_id             BIGSERIAL PRIMARY KEY,
    investigation_id       UUID REFERENCES investigations(investigation_id),
    actor_type               VARCHAR(10) NOT NULL CHECK (actor_type IN ('system','planner','worker','analyst')),
    actor_id                   VARCHAR(100),
    action                       VARCHAR(100) NOT NULL,
    details                       JSONB,
    occurred_at                    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_investigation ON audit_log(investigation_id, occurred_at);

-- ============================================================
-- KNOWLEDGE DOCUMENT METADATA (vectors live in ChromaDB; this is the relational mirror)
-- ============================================================

CREATE TABLE knowledge_documents (
    doc_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chroma_vector_id         VARCHAR(100) NOT NULL UNIQUE,
    category                   VARCHAR(30) NOT NULL,   -- 'mitre','playbook','historical','ioc','sigma','capec','intel'
    title                        VARCHAR(255) NOT NULL,
    source                         VARCHAR(255),
    version                          VARCHAR(20),
    reliability_weight                 NUMERIC(3,2) NOT NULL DEFAULT 0.80,
    last_embedded_at                    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_knowledge_category ON knowledge_documents(category);
```

### Notes on schema decisions
- All primary keys are `UUID` (not serial ints) so worker/planner services can generate IDs client-side before insert, avoiding a round trip — needed because the planner creates a `decision_id` before it knows if the worker call will succeed.
- `planner_decisions` has a `UNIQUE(investigation_id, cycle_number)` constraint — this is what makes the planning loop's cycle count auditable and prevents a retry bug from silently duplicating a cycle.
- `hypothesis_evidence` is a genuine many-to-many join with a `stance` column, because AIDD's contradiction-handling logic (§13) needs to know *which* evidence contradicts *which* hypothesis, not just that a hypothesis has "confidence."
- `worker_executions.raw_output` is `JSONB` rather than typed columns because each worker type returns a different result shape (see interface contracts in §4) — Postgres JSONB lets you index into it (`raw_output->>'field'`) without a table-per-worker-type explosion.

---

# 3. Planner Decision Algorithm

## 3.1 Main loop

```python
def run_investigation(investigation_id: UUID) -> None:
    state = load_investigation_state(investigation_id)

    while True:
        if should_terminate(state):
            finalize_investigation(state)
            return

        knowledge_need = determine_knowledge_need(state)
        context = rag_retrieve(knowledge_need, top_k=8)

        worker_type, utility_score = select_worker(state, context)
        task = build_worker_task(state, worker_type, context)

        result = execute_worker(worker_type, task)          # §4 contract
        state = apply_worker_result(state, result)           # updates evidence, hypotheses, timeline

        confidence_delta = compute_confidence_delta(state, result)   # §1
        state.confidence = update_confidence(state.confidence, confidence_delta)
        state.confidence_state = classify_confidence(state.confidence)

        persist_planner_decision(state, worker_type, utility_score, knowledge_need)
        state.cycle_number += 1
```

## 3.2 Worker selection — utility function, not just "pick the obvious one"

The planner scores each of the 5 worker types against the current investigation gap and picks the argmax. This replaces AIDD's undefined "Select Worker" box with an actual decision rule:

```python
def select_worker(state: InvestigationState, context: RetrievedContext) -> tuple[str, float]:
    scores = {}

    # Detection: high value when raw signals haven't been triaged yet
    scores['detection'] = (
        1.0 if state.untriaged_event_count > 0 else 0.0
    ) * state.untriaged_event_count / max(1, state.total_event_count)

    # Correlation: high value when evidence exists but the entity graph is sparse
    scores['correlation'] = (
        state.evidence_count * (1 - state.graph_density)
    ) if state.evidence_count >= 2 else 0.0

    # Investigation: high value when hypotheses are weak/contradicted
    scores['investigation'] = (
        1.0 - max((h.confidence for h in state.hypotheses), default=0.0)
    ) if state.hypotheses else 0.8   # no hypothesis yet -> strongly favor this worker

    # Reporting: only becomes viable once confidence is high and stable
    scores['reporting'] = (
        1.0 if state.confidence >= 0.65 and state.cycles_since_confidence_gain >= 1 else 0.0
    )

    # Response: only viable once a hypothesis is confirmed
    scores['response'] = (
        1.0 if any(h.status == 'confirmed' for h in state.hypotheses) else 0.0
    )

    best_worker = max(scores, key=scores.get)
    return best_worker, scores[best_worker]
```

This is a greedy one-step utility maximization (not a full lookahead planner) — appropriate for an MVP, and explicitly noted as a documented simplification rather than a silent one. A future version could replace this with expected-information-gain estimation (see AIDD §16, "Adaptive Planning").

## 3.3 Termination logic

```python
def should_terminate(state: InvestigationState) -> bool:
    if state.analyst_requested_stop:
        return True
    if state.cycle_number >= MAX_CYCLES:            # hard ceiling, default 15
        state.termination_reason = 'max_cycles_reached'
        return True
    if state.confidence >= 0.85 and state.cycle_number >= 3 and not state.has_unresolved_contradictions:
        state.termination_reason = 'confidence_threshold_met'
        return True
    if state.cycles_since_confidence_gain >= 3:      # stagnation guard
        state.termination_reason = 'stagnation'
        state.requires_analyst_review = True
        return True
    return False
```

The stagnation guard is the concrete implementation of AIDD §15's safety principle "if evidence is insufficient, continue investigating OR request analyst review" — three cycles with no meaningful confidence movement routes to a human rather than looping forever or fabricating a conclusion.

---

# 4. Interface Contracts

These are the exact data contracts referenced but never specified in TDD/AIDD. Written as Pydantic models — directly usable as FastAPI/Python types.

```python
from pydantic import BaseModel
from typing import Literal
from uuid import UUID
from datetime import datetime

WorkerType = Literal["detection", "correlation", "investigation", "reporting", "response"]

class RetrievedChunk(BaseModel):
    doc_id: UUID
    category: str
    text: str
    similarity_score: float
    reliability_weight: float

class RetrievedContext(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
    assembled_at: datetime

class WorkerTask(BaseModel):
    task_id: UUID
    investigation_id: UUID
    worker_type: WorkerType
    objective: str                     # planner's instruction, e.g. "assess PowerShell events for T1059"
    evidence_refs: list[UUID]          # evidence already in scope
    context: RetrievedContext
    priority: int = 1

class Finding(BaseModel):
    description: str
    entity_refs: dict[str, list[str]]  # {"hosts": [...], "users": [...]}
    mitre_technique_id: str | None = None
    supporting_evidence_ids: list[UUID] = []

class WorkerResult(BaseModel):
    task_id: UUID
    worker_type: WorkerType
    status: Literal["success", "partial", "failed"]
    findings: list[Finding]
    confidence_signal: float           # this worker's own confidence, 0-1 — feeds Worker Agreement factor
    new_evidence: list[Finding] = []
    hypothesis_updates: list[dict] = []  # [{hypothesis_id, stance, evidence_id, weight}]
    reasoning_summary: str             # 1-3 sentences, analyst-facing — NOT full chain-of-thought
    next_task_suggestion: str | None = None

# --- Base worker contract every worker type must implement ---
class BaseWorker:
    worker_type: WorkerType

    def execute(self, task: WorkerTask) -> WorkerResult:
        """Every concrete worker (DetectionWorker, CorrelationWorker, etc.)
        implements this. Enforces the 'structured output, not free text'
        requirement from AIDD §5."""
        raise NotImplementedError

# --- RAG retrieval contract ---
class RAGRetriever:
    def retrieve(self, query: str, top_k: int = 8,
                 category_filter: list[str] | None = None) -> RetrievedContext:
        """1. embed(query) -> vector
           2. ChromaDB similarity search, optionally filtered by category
           3. rank by: similarity_score * reliability_weight * recency_decay
           4. return top_k chunks assembled into RetrievedContext"""
        raise NotImplementedError

# --- Confidence engine contract ---
class ConfidenceEngine:
    weights: dict[str, float]   # the w_i from §1.3, loaded from config

    def compute_delta(self, state: "InvestigationState", result: WorkerResult) -> float:
        """Computes Σ w_i * δ_i for this cycle (§1.3)."""
        raise NotImplementedError

    def update(self, current_confidence: float, delta: float) -> float:
        """logit-space update, §1.2. Always returns a value in (0,1)."""
        raise NotImplementedError
```

This gives every downstream implementer (or evaluator reading the code) a single source of truth for what a "Worker" actually returns — closing the exact ambiguity that made the AAD/SDD worker diagrams non-implementable as written.

---

# 5. Evaluation Methodology

AIDD §14 named eight metrics with no measurement protocol. Below is how each is actually computed, including the dataset you need to build first.

## 5.1 Eval dataset (build this before any metric means anything)

Construct **N ≥ 30** labeled cases, each with:
- Raw input events (real or synthetic SOC alerts)
- Gold hypothesis (the correct attack scenario, or "benign")
- Gold evidence set (the minimal evidence an analyst would need to conclude gold hypothesis)
- Gold MITRE technique mapping
- A reference report (human-written or human-approved)

Mix of sources: replay a public dataset (e.g., a subset of a MITRE ATT&CK evaluation dataset or a SOC log dataset) for realism, plus a handful of hand-crafted synthetic cases to cover edge cases (benign-but-suspicious, multi-stage attacks).

## 5.2 Planner Accuracy
```
For each cycle in a completed investigation, compare selected_worker
against the "necessary worker" label (assigned by a human reviewer
looking at investigation state at that point).

planner_accuracy = correct_worker_selections / total_cycles
```
Run this across all eval cases; report mean ± stddev.

## 5.3 Investigation Quality (evidence coverage)
```
evidence_coverage = |evidence_collected ∩ gold_evidence_set| / |gold_evidence_set|
```
Computed per case, averaged. A case with coverage < 0.5 is flagged for manual review regardless of what confidence the system reported — this is your check against confidence/quality drifting apart.

## 5.4 Hallucination Rate — actual protocol
This is the metric most likely to be handwaved, so it needs the most explicit protocol:
1. **Claim extraction**: split the generated report into atomic factual claims (one verifiable statement per claim) using a claim-decomposition prompt.
2. **Evidence matching**: for each claim, check whether it is entailed by the investigation's `evidence` + `timeline_events` + retrieved `knowledge_documents` — either via a lightweight NLI (natural language inference) model or an LLM-as-judge prompt that outputs `supported | unsupported | contradicted`.
3. ```
   hallucination_rate = unsupported_or_contradicted_claims / total_claims
   ```
4. Report this per-report and as a corpus-wide average. Spot-check a random 10% sample by hand each eval run — LLM-judge agreement with humans should itself be measured (treat it as a classifier and report its own precision/recall against human labels).

## 5.5 Retrieval Precision
```
precision@k = |retrieved_top_k ∩ gold_relevant_docs| / k
```
Requires gold-relevant-document labels per query — label these when building the eval set in §5.1 (a human marks which of the top-15 retrieved candidates are actually relevant, once, and that becomes ground truth).

## 5.6 Planner Efficiency
```
mean_cycles_per_investigation = Σ cycle_count / N
```
Track this alongside evidence_coverage — a system that "cheats" by terminating early will show low cycles but also low coverage, which is why these two metrics must always be reported together, never separately.

## 5.7 Worker Utilization
```
utilization[worker_type] = executions_of_type / total_executions
```
Flag if any worker type is never selected across the eval set — indicates a bug in `select_worker` (§3.2), not necessarily that the worker is unneeded.

## 5.8 Confidence Calibration
Bucket predicted confidence into 10 bins (0.0–0.1, 0.1–0.2, ... 0.9–1.0). For each bin, compute the actual fraction of investigations in that bin whose final hypothesis matched gold.
```
ECE = Σ_bins (|bin_size| / N) * |bin_mean_confidence − bin_actual_accuracy|
```
This is the standard **Expected Calibration Error**. A well-calibrated system has ECE close to 0 — e.g. investigations the system reports at "80% confidence" should be correct about 80% of the time. This is the single most important number for a security tool, since analysts will act on the confidence score directly.

## 5.9 Running the eval suite
All of the above should be one offline script (`eval_harness.py`) that takes a list of `investigation_id`s, re-runs or reads stored results, and outputs a single scorecard — not something computed ad hoc per demo. This is what you'd actually show a panel: "here is our eval harness, here's this week's scorecard," rather than a claimed target with no measurement behind it.

---

# 6. Visual Explainability & Cognitive Observability Subsystem

## 6.1 Cognitive Transparency Architecture

To eliminate the "black-box" nature of autonomous planning, the platform exposes real-time cognitive state transitions over WebSockets and renders them via dedicated observability components.

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Telemetry Ticker (Live Redis Packet Stream)              │
│    Highlights anomalous ports (4444), flags, protocols      │
├─────────────────────────────────────────────────────────────┤
│ 2. Multi-Agent Orbital Map (SVG Dynamic Topology)           │
│    Central Planner + 5 Orbiting Workers with live beams     │
├─────────────────────────────────────────────────────────────┤
│ 3. Agent Thought Stream (Real-Time SOC Command Console)     │
│    [PLANNER] [UTILITY] [RAG] [WORKER] [BAYESIAN] logs       │
├─────────────────────────────────────────────────────────────┤
│ 4. Mathematical Explainability Cards                        │
│    - Worker Utility Competition: Argmax(U_w) comparison     │
│    - 6-Factor Bayesian Decomposition: Σ (w_i · δ_i)         │
├─────────────────────────────────────────────────────────────┤
│ 5. Paced Simulation Engine                                  │
│    Configurable playback interval (0.8s, 1.5s, 2.5s)        │
└─────────────────────────────────────────────────────────────┘
```

## 6.2 Granular Telemetry WebSocket Schema

Every planning cycle emits a rich `PLANNER_DECISION` event:

```json
{
  "type": "PLANNER_DECISION",
  "investigation_id": "uuid",
  "cycle_number": 2,
  "selected_worker": "correlation",
  "utility_score": 0.8200,
  "utility_scores": {
    "detection": 0.0,
    "correlation": 0.82,
    "investigation": 0.35,
    "reporting": 0.0,
    "response": 0.0
  },
  "factor_contributions": {
    "detection": { "raw_delta": 0.35, "weight": 0.15, "weighted_contribution": 0.0525 },
    "evidence": { "raw_delta": 0.60, "weight": 0.20, "weighted_contribution": 0.1200 },
    "correlation": { "raw_delta": 0.20, "weight": 0.15, "weighted_contribution": 0.0300 },
    "knowledge": { "raw_delta": 0.45, "weight": 0.15, "weighted_contribution": 0.0675 },
    "agreement": { "raw_delta": 0.10, "weight": 0.15, "weighted_contribution": 0.0150 },
    "historical": { "raw_delta": 0.25, "weight": 0.20, "weighted_contribution": 0.0500 }
  },
  "rag_citations": [
    { "category": "mitre", "text": "T1059.001 PowerShell execution", "similarity_score": 0.912, "reliability_weight": 1.0 }
  ],
  "confidence_before": 0.3000,
  "confidence_after": 0.5850,
  "confidence_delta": 0.2850,
  "confidence_state": "moderate",
  "explanation": "CorrelationWorker identified 3 pivot IP nodes.",
  "latency_ms": 78,
  "status": "active"
}
```

---

# Summary of what changed vs. TDD/AIDD

| Gap identified | Resolved by |
|---|---|
| Confidence formula was additive/unbounded | §1: bounded logit-space weighted update with defined per-factor formulas |
| DB schema had field names only | §2: full DDL with types, PKs, FKs, constraints, indexes |
| Planner "Select Worker" step was undefined | §3.2: explicit utility-scoring function per worker type |
| No termination condition | §3.3: three concrete stop conditions including a stagnation guard |
| Worker I/O shape unspecified | §4: Pydantic contracts for Task/Result/Finding |
| Metrics were names with no protocol | §5: dataset requirements + exact computation for all 8 metrics |
| Cognitive reasoning was invisible to users | §6: Agent Thought Stream, Orbital Topology, and Mathematical Factor Decomposition |

This document should sit alongside the TDD as the thing you'd actually hand to someone implementing the system — or defend to a technical panel asking "how does this actually work."

