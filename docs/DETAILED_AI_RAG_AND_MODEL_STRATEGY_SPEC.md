# Project Sentinel — Detailed AI, RAG and Model Strategy Specification (AIRMSS)

**Document Type:** AI Intelligence and Retrieval Architecture Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** LLM strategy, AI Planner design, model routing, RAG pipeline, context management, grounded reasoning, fallback behavior, and AI evaluation  
**Related Components:** AI Planner, Context Builder, Model Router, ChromaDB Knowledge Base, Policy Controller, Result Validator

---

# 1. Purpose

Artificial Intelligence is a core component of Project Sentinel, but it must operate within clearly defined boundaries. The system does not use an LLM as an uncontrolled replacement for deterministic software logic.

Instead, Project Sentinel follows a **hybrid intelligence architecture**:

```text
DETERMINISTIC SYSTEM + AI REASONING = CONTROLLED INTELLIGENCE
```

The AI layer provides capabilities that traditional rule-based systems perform poorly:
- Interpreting complex multi-event investigation context.
- Identifying evidence gaps.
- Prioritizing investigation actions.
- Explaining relationships between findings.
- Generating structured investigation assessments.
- Using retrieved domain knowledge to provide contextual interpretation.

The AI layer must not become the sole authority for system truth.

---

# 2. AI Architecture Principles

## 2.1 AI Reasons; Software Controls
```text
AI MODEL ──► Suggest / Assess / Prioritize ──► DETERMINISTIC CONTROL ──► Validate / Authorize / Execute
```
The LLM may recommend an action; the policy layer determines whether that action can be executed.

## 2.2 Evidence Before Interpretation
```text
OBSERVED EVENTS ──► EVIDENCE ──► AI INTERPRETATION ──► CLAIM
```
The AI must never generate a claim first and then search selectively for supporting evidence.

## 2.3 Structured Output
```text
PROMPT ──► LLM ──► STRUCTURED RESPONSE ──► SCHEMA VALIDATION ──► SYSTEM DECISION
```
All autonomous decisions require machine-readable, schema-validated JSON.

---

# 3. AI Responsibility Boundaries

| Function | AI Usage | Reason |
|---|---|---|
| Telemetry normalization | No | Deterministic field mapping |
| Event validation | No | Schema-based Pydantic validation |
| Alert storage | No | Database transaction |
| State versioning | No | Deterministic consistency & optimistic locking |
| Policy enforcement | No | Must be predictable & mathematically verifiable |
| Evidence interpretation | Yes | Requires contextual reasoning |
| Evidence-gap analysis | Yes | Requires semantic prioritization |
| Investigation planning | Yes | Adaptive decision-making |
| Knowledge interpretation | Yes | Semantic reasoning over MITRE ATT&CK |
| Final narrative generation | Yes | Natural-language synthesis |
| Final evidence validation | Hybrid | AI assessment plus deterministic checks |

---

# 4. AI Intelligence Layer

```text
                    ┌───────────────────────┐
                    │    MODEL ROUTER       │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
        PLANNING MODEL     REASONING MODEL    SUMMARY MODEL
              │                 │                  │
              └─────────────────┼──────────────────┘
                                ▼
                       STRUCTURED OUTPUT
```

For the MVP, these functions use the same underlying local model (e.g. Qwen2.5 / Llama3 via Ollama) while preserving logical routing boundaries.

---

# 5. Model Selection Strategy

| Criterion | Importance | Target Specification |
|---|---|---|
| Structured output reliability | Critical | Strict JSON schema compliance without markdown drift |
| Reasoning quality | Critical | High multi-hop causality tracking |
| Local deployment compatibility | High | Air-gapped Ollama runtime |
| Latency | High | < 2.5s for action planning decisions |
| Memory requirements | High | Fits in 8GB–16GB VRAM (e.g. 7B/8B Q4_K_M) |
| Context window | Medium | 8k–32k tokens |
| Cost | Medium | Zero API cost via local open weights |

---

# 6. Model Routing Architecture

```text
AI REQUEST ──► TASK CLASSIFICATION ──┬──► Planning
                                     ├──► Analysis
                                     ├──► Summarization
                                     └──► Retrieval Interpretation
                                                │
                                                ▼
                                         MODEL SELECTION ──► EXECUTION
```

```text
ModelRequest
│
├── task_type
├── priority
├── context_size
├── required_output_schema
└── timeout
```

---

# 7. Primary Planner Model

The Planner analyzes the current state and selects the next action. It operates strictly over controlled context:

```text
PLANNER CONTEXT
│
├── Alert Summary
├── Important Evidence
├── Active Hypotheses
├── Evidence Gaps
├── Previous Actions
├── Available Capabilities
└── Investigation Budget
```

---

# 8. Planner Reasoning Model

1. **What is currently known?** (Observed evidence summary)
2. **What is uncertain?** (Active hypotheses and conflicting claims)
3. **What evidence is missing?** (Unresolved evidence gaps)
4. **Which capability can reduce that uncertainty?** (Candidate action ranking)
5. **Is the action worth its cost?** (Budget vs. information gain)
6. **Produce a structured recommendation.** (Pydantic `PlannerDecision`)

---

# 9. Planner Output Schema

```text
PlannerDecision
│
├── assessment
├── evidence_gaps
├── candidate_actions
├── selected_action
├── parameters
├── rationale
├── expected_information_gain
└── stop_recommendation
```

---

# 10. Planner Prompt Architecture

```text
SYSTEM ROLE ──► INVESTIGATION OBJECTIVE ──► CURRENT STATE ──► AVAILABLE CAPABILITIES ──► DECISION RULES ──► OUTPUT SCHEMA
```

Prompt directives:
- Do not invent telemetry.
- Distinguish empirical evidence from assumptions.
- Prefer actions that reduce critical uncertainty.
- Never request unregistered capabilities.
- Respect investigation step and time budgets.
- Return raw JSON conforming to the output schema.

---

# 11. Context Construction & Token Budgeting

```text
INVESTIGATION STATE ──► CONTEXT BUILDER ──┬──► Select Important Evidence
                                         ├──► Summarize History
                                         ├──► Include Active Gaps
                                         └──► Apply Token Budget ──► PLANNER
```

### Context Priority When Budget is Exceeded:
1. Critical Alert Context
2. Recent Validated Evidence
3. Active Evidence Gaps
4. Active Hypotheses
5. Relevant Action History
6. Historical Summaries

---

# 12. Retrieval-Augmented Generation (RAG) Architecture

```text
KNOWLEDGE SOURCES (MITRE ATT&CK / Docs)
        │
        ▼
DOCUMENT INGESTION & CLEANING
        │
        ▼
CHUNKING (Heading-Preserving Semantic Chunks)
        │
        ▼
EMBEDDING GENERATION (all-MiniLM-L6-v2)
        │
        ▼
CHROMADB VECTOR STORE
        │
        ▼
SEMANTIC RETRIEVAL + METADATA FILTERING
        │
        ▼
RERANKING
        │
        ▼
CONTEXT CONSTRUCTOR ──► LLM
```

---

# 13. Grounded Knowledge Usage Axiom

```text
TELEMETRY EVENT ──► Observed Fact: "Host X sent 500 failed POST requests to /login"
RETRIEVED MITRE  ──► Domain Context: "T1110.001 (Password Spraying) involves automated authentication attempts"
VALID INFERENCE ──► "Activity is consistent with Technique T1110.001"
INVALID DRIFT   ──► "Telemetry proves APT28 initiated this attack" (Prohibited without direct attribution evidence)
```

---

# 14. Hallucination Safeguards

1. **Evidence-Grounded Prompts**: Explicit negative constraints forbidding fabricated telemetry.
2. **Schema Enforcement**: Deterministic JSON decoding with strict Pydantic parsing.
3. **Source References**: Mandatory citations of `event_id` and document `chunk_id`.
4. **Claim Validation Loop**: Independent verification check separating supported, unsupported, and contradictory claims.

---

# 15. AI Failure Handling & Fallback Hierarchy

```text
PRIMARY MODEL (Ollama)
        │
        ▼ (Timeout / Malformed JSON)
RETRY WITH TEMPERATURE 0.0 & CORRECTION PROMPT
        │
        ▼ (Failed Retry)
DETERMINISTIC FALLBACK PLANNER
        │
        ▼ (Critical Gaps Remain)
HUMAN ESCALATION
```

### Deterministic Fallback Policy:
1. Validate existing unconfirmed evidence.
2. Run standard time-window correlation on seed entities.
3. If uncertainty remains high, request human review (`WAITING_REVIEW`).

---

# 16. Prompt Versioning

Every prompt template is immutably tracked:
- `prompt_id`
- `version`
- `purpose`
- `model_compatibility`
- `created_at`

Decision records link directly to the prompt version that produced them.

---

# 17. AI Evaluation Framework

- **Planner Evaluation**:
  - `Valid Action Rate`: $\frac{\text{Valid Schema \& Policy Actions}}{\text{Total Planner Actions}}$
  - `Action Utility Rate`: $\frac{\text{Actions Resolving Evidence Gaps}}{\text{Total Actions}}$
  - `Redundant Action Rate`: $\frac{\text{Repeated Low-Value Actions}}{\text{Total Actions}}$
- **RAG Evaluation**:
  - `Retrieval Precision@K`: Relevant chunks within top-$K$ returned.
  - `Grounded Claim Rate`: $\frac{\text{Supported Claims}}{\text{Total Generated Claims}}$
- **Latency Observability**: Track prompt token count, output token count, inference latency, and retry rate.

---

# 18. Complete AI Decision Flow

```text
                    ┌────────────────────┐
                    │ INVESTIGATION STATE│
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │  CONTEXT BUILDER   │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼────────────────┐
              ▼                                ▼
     ┌─────────────────┐             ┌─────────────────┐
     │   AI PLANNER    │             │   RAG SYSTEM    │
     │                 │◄────────────│                 │
     │ Reason & Decide │             │ Retrieve Context│
     └────────┬────────┘             └─────────────────┘
              │
              ▼
     ┌─────────────────┐
     │ STRUCTURED      │
     │ DECISION        │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ VALIDATION &    │
     │ POLICY CONTROL  │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ CAPABILITIES    │
     └─────────────────┘
```

---

# 19. Final Principle

> **AI should increase the system's ability to understand, prioritize, and adapt, while deterministic architecture preserves reliability, traceability, and control.**
