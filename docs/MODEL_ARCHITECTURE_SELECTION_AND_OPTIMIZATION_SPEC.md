# Project Sentinel
# Model Architecture, Selection & Optimization Specification

**Document Type:** Technical Design Specification  
**Version:** 1.0  
**Status:** Proposed Architecture  
**Primary Focus:** LLMs, model routing, structured generation, embeddings, optimization, and evaluation

---

## 1. Purpose

This document defines the model architecture for Project Sentinel.

The objective is to select, integrate, evaluate, and optimize AI models for the system's core capabilities without allowing model behavior to compromise orchestration reliability, security, or reproducibility.

Project Sentinel uses a Planner + Specialized Workers architecture. Models provide reasoning and task-specific intelligence, while the orchestration runtime controls execution.

The model layer must support:

- Dynamic investigation planning.
- Specialist agent reasoning.
- Security event interpretation.
- Evidence analysis and correlation.
- Threat intelligence and knowledge retrieval.
- Incident reporting.
- Response recommendations.
- Structured outputs suitable for deterministic processing.

The system must remain model-provider-independent wherever practical.

## 2. Architectural Principles

### 2.1 Planner-controlled orchestration

The Planner is the central decision-making component for investigation coordination.

However, the LLM powering the Planner does not directly execute arbitrary actions.

Its responsibility is to propose a structured plan based on:

- Current investigation state.
- Available evidence.
- Unresolved questions.
- Previous task results.
- Available specialist capabilities.
- Execution constraints.
- Investigation objectives.

The orchestration runtime validates the proposed plan before execution.

**Control boundary:**

```text
Investigation State
       |
       v
Planner LLM
       |
       v
Structured Plan Proposal
       |
       v
Plan Validator
       |
       v
Policy and Permission Checks
       |
       v
LangGraph Orchestration Runtime
       |
       v
Authorized Specialist Capability
       |
       v
Structured Task Result
       |
       v
Investigation State Update
       |
       v
Planner Re-evaluation
```

The LLM proposes. The runtime validates and executes.

### 2.2 Model-provider independence

Model integration must use an abstraction layer.

The application should not depend directly on Ollama-specific request formats throughout the codebase.

Initially, Ollama will provide local model execution. The architecture should allow alternative local or hosted providers later.

### 2.3 Structured outputs over free-form responses

Agent outputs must be machine-readable wherever they affect system behavior.

Free-form natural language is appropriate for explanations and reports, but not as the primary interface between orchestration components.

### 2.4 Evidence-grounded reasoning

Models must distinguish between:

- Observed facts.
- Derived conclusions.
- Hypotheses.
- Missing information.
- Uncertainty.

A model must not invent security events, evidence, timestamps, or indicators.

### 2.5 Measured model selection

No model should be selected solely because it is popular or performs well on general benchmarks.

Selection must consider actual Project Sentinel workloads, including:

- Structured output reliability.
- Security reasoning quality.
- Tool-selection quality.
- Context handling.
- Latency.
- Memory consumption.
- Hardware requirements.
- Reproducibility.

---

## 3. Model Architecture Overview

The architecture separates models by responsibility rather than requiring a unique model for every agent.

```text
                  MODEL ADAPTER LAYER
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
      Planner LLM    Specialist LLM    Retrieval Models
          |               |               |
          v               v               v
    Plan Proposal    Task Reasoning    Embeddings
          |               |               |
          v               v               v
    Plan Validator   Output Validator   Vector Search
          |               |               |
          +---------------+---------------+
                          |
                          v
                 ORCHESTRATION RUNTIME
                          |
                          v
                Investigation State
```

### 3.1 Logical model roles

| Model role | Responsibility |
|---|---|
| Planner model | Selects the next investigation objective and proposes task plans |
| Specialist model | Performs task-specific security reasoning |
| Embedding model | Converts text and knowledge chunks into vectors |
| Reranker model | Reorders retrieved documents by relevance |
| Optional lightweight classifier | Supports narrow classification tasks where beneficial |

These are logical roles, not necessarily separate deployed models.

For the MVP, a single LLM may serve both Planner and specialist roles, with different prompts, schemas, and permissions.

Embedding and reranking models are separate components because they perform different computational tasks.

## 4. Planner Model Specification

### 4.1 Responsibilities

The Planner model receives a structured investigation snapshot and determines what should happen next.

Its responsibilities include:

1. Assessing investigation completeness.
2. Identifying unresolved questions.
3. Selecting appropriate specialist capabilities.
4. Defining task objectives.
5. Specifying required inputs.
6. Defining expected outputs.
7. Identifying task dependencies.
8. Recommending whether more evidence is required.
9. Recommending whether investigation can be completed.
10. Recommending replanning when previous work is insufficient.

### 4.2 Planner input contract

Example:

```json
{
  "investigation_id": "INV-2026-001",
  "objective": "Investigate suspected credential compromise",
  "current_status": "investigating",
  "alert": {
    "alert_id": "ALT-1001",
    "severity": "high",
    "classification": "suspicious_authentication"
  },
  "evidence_summary": {
    "event_count": 42,
    "source_count": 3,
    "confirmed_facts": [
      "Multiple failed authentication attempts",
      "Successful login after repeated failures"
    ]
  },
  "unresolved_questions": [
    "Was the successful login associated with the same source?",
    "Was the account used for subsequent suspicious activity?"
  ],
  "completed_tasks": [
    {
      "task_type": "event_search",
      "status": "completed"
    }
  ],
  "available_capabilities": [
    "correlation",
    "investigation",
    "knowledge_retrieval",
    "event_search",
    "reporting"
  ],
  "constraints": {
    "max_parallel_tasks": 3,
    "response_actions_enabled": false,
    "require_evidence_for_conclusions": true
  }
}
```

The Planner should receive relevant summaries rather than the entire raw dataset.

### 4.3 Planner output contract

Example:

```json
{
  "decision": "continue_investigation",
  "reasoning_summary": "The available evidence establishes suspicious authentication activity, but subsequent account activity remains unknown.",
  "tasks": [
    {
      "task_id": "TASK-2001",
      "capability": "correlation",
      "objective": "Correlate authentication events by account, source, and time",
      "priority": 1,
      "depends_on": [],
      "required_inputs": [
        "authentication_events"
      ],
      "expected_output": "correlation_result"
    },
    {
      "task_id": "TASK-2002",
      "capability": "event_search",
      "objective": "Identify subsequent activity associated with the account",
      "priority": 2,
      "depends_on": [],
      "required_inputs": [
        "account_identifier",
        "time_window"
      ],
      "expected_output": "event_search_result"
    }
  ],
  "completion_criteria": [
    "Authentication activity is correlated",
    "Subsequent account activity is assessed"
  ],
  "confidence": 0.86
}
```

The output must be validated against a predefined schema.

The confidence value is a model-reported estimate, not a statistically calibrated probability. It must not independently authorize actions.

### 4.4 Planner decision types

The Planner should support a finite set of decisions:

| Decision | Meaning |
|---|---|
| `continue_investigation` | Additional work is required |
| `replan` | Existing plan must be modified |
| `request_human_review` | Analyst input or approval is required |
| `complete_investigation` | Completion criteria are satisfied |
| `escalate` | Investigation requires escalation |
| `blocked` | Required capabilities or evidence are unavailable |

The runtime must reject unsupported decision values.

### 4.5 Planner safeguards

- The Planner cannot directly access the database.
- The Planner cannot execute shell commands.
- The Planner cannot create arbitrary tools.
- The Planner cannot bypass capability permissions.
- The Planner cannot approve its own response recommendations.
- The Planner cannot mark an investigation complete without runtime validation.
- The Planner cannot silently discard contradictory evidence.

The runtime remains responsible for enforcing task limits, dependency rules, authorization, and termination conditions.

---

## 5. Specialist Model Specification

Specialist agents use models to perform narrowly scoped reasoning.

Each specialist must have a defined task contract.

### 5.1 Detection Agent

Primary responsibility:

- Interpret detection outputs.
- Explain suspicious activity.
- Assess rule or classifier results.
- Identify potentially relevant indicators.

Detection itself should not rely exclusively on an LLM.

The preferred architecture is hybrid:

```text
Network / Log Events
        |
        v
Rule-based and ML Detection
        |
        v
Detection Findings
        |
        v
Optional LLM Interpretation
        |
        v
Structured Detection Result
```

The deterministic or statistical detection engine provides measurable classification outputs. The LLM adds contextual interpretation.

### 5.2 Correlation Agent

Responsibilities:

- Interpret relationships between events.
- Identify shared entities.
- Assess temporal sequences.
- Explain possible attack chains.
- Identify missing links.

The correlation engine should perform deterministic entity and temporal operations wherever possible.

The LLM should interpret candidate relationships and explain their significance rather than independently inventing correlations.

### 5.3 Investigation Agent

Responsibilities:

- Analyze collected evidence.
- Evaluate hypotheses.
- Identify contradictions.
- Identify missing evidence.
- Produce investigation findings.
- Recommend additional investigation tasks.

Investigation output must separate facts from hypotheses.

### 5.4 Reporting Agent

Responsibilities:

- Produce analyst-readable incident reports.
- Summarize timelines.
- Explain evidence.
- Describe impact and confidence.
- Present unresolved questions.
- Recommend next steps.

Reports must be generated from persisted investigation state and evidence references.

The Reporting Agent must not introduce unsupported claims.

### 5.5 Response Agent

Responsibilities:

- Recommend response actions.
- Map findings to approved playbooks.
- Explain action rationale.
- Identify risks and prerequisites.

For the MVP, response actions should be simulated.

Any future real-world execution must be protected by a separate authorization and approval layer.

---

## 6. Model Selection Strategy

### 6.1 Selection dimensions

Evaluate candidate models against the following dimensions:

| Dimension | Evaluation question |
|---|---|
| Reasoning quality | Can it analyze security evidence accurately? |
| Structured output | Does it reliably produce valid JSON? |
| Instruction adherence | Does it follow narrow agent contracts? |
| Context capacity | Can it handle investigation summaries and evidence? |
| Tool selection | Can it choose appropriate available capabilities? |
| Latency | Is response time acceptable? |
| Resource usage | Can it run on available hardware? |
| Stability | Does it produce consistent outputs? |
| Security | Can it resist untrusted prompt instructions? |
| Maintainability | Can the model be deployed and versioned reliably? |

### 6.2 Candidate architecture options

| Option | Architecture | Advantages | Limitations |
|---|---|---|---|
| A | One shared LLM | Lowest complexity and resource usage | Shared weaknesses across roles |
| B | Planner LLM + shared specialist LLM | Clear orchestration separation | Two model configurations to maintain |
| C | Planner + task-specific specialist models | More specialization | Higher resource and operational complexity |
| D | Planner + shared specialist + fallback | Balanced reliability and complexity | Requires routing and fallback logic |

**Recommended MVP:** Option B, with a fallback strategy added only where testing demonstrates a need.

Do not deploy a separate model for every agent without evidence that specialization improves measurable outcomes.

### 6.3 Model evaluation matrix

Every candidate model should be tested using the same evaluation dataset and task suite.

| Evaluation category | Example test |
|---|---|
| Planner routing | Select the appropriate capability for a scenario |
| Replanning | Recover after an incomplete task result |
| Investigation | Analyze evidence and identify unresolved questions |
| Structured output | Produce valid schema-conforming output |
| Groundedness | Avoid unsupported security claims |
| Reporting | Generate a report consistent with stored evidence |
| Prompt injection | Ignore malicious instructions inside retrieved content |
| Latency | Complete a representative task within the target budget |
| Resource usage | Operate within available CPU/GPU memory |

No candidate should be declared superior until these tests are run.

---

## 7. Model Adapter and Provider Abstraction

### 7.1 Purpose

All model calls should pass through a common adapter.

This prevents provider-specific code from spreading into agents and orchestration logic.

### 7.2 Proposed interface

```python
from typing import Any, Protocol

class ModelAdapter(Protocol):

    async def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        response_schema: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        ...
```

The actual implementation should also support:

- Model identifier.
- Request timeout.
- Retry policy.
- Token usage metadata where available.
- Provider errors.
- Correlation identifiers.
- Cancellation.
- Model configuration version.

### 7.3 Suggested package structure

```text
backend/
└── app/
    └── models/
        ├── base.py
        ├── registry.py
        ├── router.py
        ├── config.py
        ├── schemas.py
        ├── providers/
        │   ├── ollama.py
        │   └── hosted.py
        ├── evaluation/
        │   ├── benchmark.py
        │   ├── metrics.py
        │   └── test_cases.py
        └── prompts/
            ├── planner.py
            ├── detection.py
            ├── correlation.py
            ├── investigation.py
            ├── reporting.py
            └── response.py
```

The hosted provider is an extension point, not a requirement for the MVP.

### 7.4 Error handling

The adapter should normalize provider errors into application-level categories:

- `MODEL_UNAVAILABLE`
- `MODEL_TIMEOUT`
- `MODEL_RATE_LIMITED`
- `MODEL_INVALID_OUTPUT`
- `MODEL_CONTEXT_OVERFLOW`
- `MODEL_PROVIDER_ERROR`
- `MODEL_RESOURCE_EXHAUSTED`

The orchestrator should decide whether to retry, use a fallback, request human review, or mark the task as blocked.

---

## 8. Model Routing and Selection

### 8.1 Routing responsibility

The model router selects a configured model for a task.

The Planner selects a capability. The model router selects the model configuration used by that capability.

These responsibilities must remain separate.

```text
Planner
   |
   | Selects investigation capability
   v
Capability Registry
   |
   v
Model Router
   |
   | Selects configured model
   v
Model Adapter
   |
   v
Provider
```

### 8.2 Routing policy

Routing should consider:

- Task type.
- Task complexity.
- Required context.
- Structured output requirements.
- Risk level.
- Model availability.
- Resource budget.
- Measured task performance.

Example policy:

| Task | Routing policy |
|---|---|
| Simple classification explanation | Lightweight configured model |
| Investigation reasoning | Primary specialist model |
| Complex multi-evidence analysis | Higher-capability configured model |
| JSON repair | Small constrained repair attempt |
| Report generation | Reporting configuration |
| Planner decisions | Dedicated Planner configuration |

The initial implementation may use the same underlying model for several rows.

### 8.3 Deterministic routing

Routing rules must be configuration-driven and reproducible.

Do not allow a model to choose an arbitrary model identifier or endpoint.

A routing decision should record:

```json
{
  "task_id": "TASK-2001",
  "task_type": "investigation",
  "selected_model": "sentinel-specialist",
  "model_version": "configured-version",
  "routing_policy_version": "1.0",
  "reason": "Primary model assigned to investigation reasoning"
}
```

---

## 9. Structured Generation and Validation

### 9.1 Requirement

All model outputs that affect system state must follow explicit schemas.

A response that is syntactically valid JSON may still be semantically invalid.

Validation must therefore occur at multiple levels:

1. JSON parsing.
2. Schema validation.
3. Enum validation.
4. Reference validation.
5. Permission validation.
6. Business-rule validation.

### 9.2 Example Pydantic contract

```python
from enum import Enum
from pydantic import BaseModel, Field

class PlannerDecision(str, Enum):
    CONTINUE = "continue_investigation"
    REPLAN = "replan"
    HUMAN_REVIEW = "request_human_review"
    COMPLETE = "complete_investigation"
    ESCALATE = "escalate"
    BLOCKED = "blocked"

class PlannedTask(BaseModel):
    task_id: str
    capability: str
    objective: str
    priority: int = Field(ge=1, le=5)
    depends_on: list[str] = Field(default_factory=list)
    required_inputs: list[str] = Field(default_factory=list)
    expected_output: str

class PlannerOutput(BaseModel):
    decision: PlannerDecision
    reasoning_summary: str
    tasks: list[PlannedTask]
    completion_criteria: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
```

### 9.3 Invalid output handling

```text
Model Response
     |
     v
JSON Parsing
     |
     v
Schema Validation
     |
     +---- Valid ----> Semantic Validation
     |
     +---- Invalid
              |
              v
       Limited Repair Attempt
              |
              v
       Validate Again
              |
       +------+------+
       |             |
     Valid         Invalid
       |             |
       v             v
    Continue       Task Failure
```

Repair attempts must be bounded.

A model must not be allowed to repeatedly regenerate output without a task or token limit.

### 9.4 Semantic validation examples

A valid Planner response must also satisfy rules such as:

- Every selected capability exists in the registry.
- Every dependency refers to a valid task.
- No task depends on itself.
- The dependency graph contains no cycles.
- Task count is within the configured maximum.
- Required inputs are available or can be obtained.
- The decision is compatible with the investigation state.
- Completion criteria are supported by evidence.

---

## 10. Prompt Engineering and Version Control

### 10.1 Prompt structure

Each agent prompt should contain:

1. Role and objective.
2. Task-specific responsibilities.
3. Available context.
4. Input schema.
5. Output schema.
6. Reasoning constraints.
7. Evidence requirements.
8. Security restrictions.
9. Explicit prohibited behavior.

### 10.2 Prompt versioning

Prompts must be version-controlled independently of model weights.

Suggested metadata:

```json
{
  "prompt_id": "planner-v1",
  "agent_type": "planner",
  "version": "1.0.0",
  "model_role": "planner",
  "created_at": "2026-08-01",
  "schema_version": "1.0",
  "status": "active"
}
```

Every model invocation should be traceable to:

- Model identifier.
- Model version or artifact digest.
- Prompt version.
- Schema version.
- Routing policy version.
- Generation parameters.
- Input and output references.

Sensitive data should not be copied into ordinary logs.

### 10.3 Prompt testing

Prompt changes require regression tests.

A prompt update must be evaluated against a fixed test suite covering:

- Normal investigation.
- Incomplete evidence.
- Conflicting evidence.
- Missing capabilities.
- Invalid model output.
- Prompt injection.
- Premature completion.
- Excessive task generation.

---

## 11. Embedding Model Architecture

### 11.1 Purpose

The embedding model converts knowledge documents and queries into vector representations for semantic retrieval.

It supports retrieval over:

- MITRE ATT&CK knowledge.
- Sigma rules.
- CVE descriptions.
- CAPEC attack patterns.
- Response playbooks.
- Internal investigation knowledge.
- Historical incident summaries.

The embedding model does not determine whether a retrieved document is authoritative or applicable.

That assessment remains part of retrieval filtering and agent reasoning.

### 11.2 Embedding workflow

```text
Knowledge Source
      |
      v
Document Parsing
      |
      v
Chunking
      |
      v
Metadata Attachment
      |
      v
Embedding Model
      |
      v
Vector Storage
      |
      v
Query Embedding
      |
      v
Similarity Search
      |
      v
Metadata Filtering
      |
      v
Optional Reranking
      |
      v
Retrieved Evidence
```

### 11.3 Embedding requirements

Evaluate candidates on:

- Semantic retrieval quality.
- Security-domain terminology handling.
- Multilingual requirements, if applicable.
- Embedding dimension.
- Throughput.
- Memory footprint.
- Compatibility with ChromaDB.
- Licensing and deployment constraints.

### 11.4 Embedding consistency

The same embedding model and compatible preprocessing configuration must be used for document ingestion and query encoding.

If the embedding model changes, existing vectors must not be silently mixed with vectors from the new model.

Use versioned collections or a controlled re-embedding migration.

Suggested metadata:

```json
{
  "embedding_model": "configured-embedding-model",
  "embedding_version": "1.0",
  "chunking_version": "1.0",
  "collection_version": "knowledge-v1"
}
```

---

## 12. Reranking Architecture

Vector similarity is a candidate retrieval mechanism, not proof of relevance.

A reranker can improve retrieval by evaluating the relevance of each candidate against the query.

Proposed workflow:

```text
User / Agent Query
        |
        v
Embedding Retrieval
        |
        v
Top-K Candidate Documents
        |
        v
Reranker
        |
        v
Top-N Relevant Documents
        |
        v
Evidence Filtering
        |
        v
Agent Context
```

Reranking should be introduced only after measuring baseline retrieval quality.

Evaluate it using:

- Precision@K.
- Recall@K.
- Mean Reciprocal Rank.
- nDCG@K.
- Retrieval latency.

The system should retain source metadata and document references through reranking.

---

## 13. Fine-Tuning vs Prompt Engineering

### 13.1 Initial recommendation

Use prompt engineering and structured contracts first.

Fine-tuning should not be part of the initial MVP unless evaluation demonstrates a specific and recurring deficiency that cannot be addressed adequately through:

- Better prompts.
- Better schemas.
- Better retrieval.
- Better context construction.
- Deterministic post-processing.
- Capability-specific logic.

### 13.2 When fine-tuning may be justified

Potential use cases:

- Consistent security-event classification.
- Domain-specific terminology interpretation.
- Standardized incident report generation.
- Reliable structured extraction from recurring log formats.

### 13.3 Fine-tuning prerequisites

Before fine-tuning:

1. Define the exact target behavior.
2. Build a labeled dataset.
3. Remove duplicates and leakage.
4. Separate training, validation, and test data.
5. Define a baseline model.
6. Measure the current failure rate.
7. Train a candidate.
8. Compare on a held-out test set.
9. Evaluate regression and safety behavior.
10. Document the resulting model artifact.

Fine-tuning must not be used to compensate for poor data quality or missing system controls.

---

## 14. Model Optimization

### 14.1 Quantization

Quantization reduces model memory requirements by representing model weights with lower numerical precision.

Potential configurations include:

- FP16.
- BF16.
- 8-bit quantization.
- 4-bit quantization.

The appropriate configuration depends on model architecture, runtime support, and available hardware.

Quantization may affect reasoning quality and structured output reliability.

It must therefore be evaluated, not assumed harmless.

### 14.2 Context management

Do not send the entire investigation history to every model call.

Construct context using:

- Current investigation objective.
- Relevant event summaries.
- Selected evidence references.
- Previous task results.
- Outstanding hypotheses.
- Relevant retrieved knowledge.
- Execution constraints.

Use evidence references to retrieve detailed records when needed.

### 14.3 Generation parameters

Generation settings should be task-specific and configuration-controlled.

| Task | Temperature policy |
|---|---|
| Planner decisions | Low or deterministic |
| Structured extraction | Low or deterministic |
| Investigation reasoning | Low |
| Report generation | Low |
| Creative analyst explanation | Slightly higher, if needed |

The initial baseline should use conservative settings.

Record temperature, token limits, stop sequences, and other generation settings for every invocation.

### 14.4 Token budgeting

Define separate budgets for:

- Planner input.
- Planner output.
- Specialist input.
- Specialist output.
- RAG context.
- Reporting context.

If context exceeds the configured budget, prioritize evidence according to relevance and importance.

Do not silently truncate critical evidence.

---

## 15. Hardware and Resource Planning

### 15.1 Initial deployment

The MVP should support local inference through Ollama.

The actual model and quantization level must be selected after checking available hardware.

### 15.2 Resource dimensions

Measure:

- Model loading time.
- Resident memory.
- Peak memory.
- GPU memory utilization.
- CPU utilization.
- Tokens per second.
- Request latency.
- Concurrent request capacity.
- Model swapping overhead.

### 15.3 Resource-aware concurrency

The orchestrator should limit concurrent model requests.

A task limit in LangGraph does not automatically guarantee that the inference server can support the same concurrency.

Use a model execution queue or semaphore.

Example:

```python
import asyncio

class ModelConcurrencyLimiter:
    def __init__(self, max_concurrent: int = 2):
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def run(self, operation):
        async with self.semaphore:
            return await operation()
```

The concurrency limit should be configurable and validated through load testing.

### 15.4 Hardware profiling

Before finalizing deployment configuration, benchmark:

1. One representative Planner request.
2. One investigation request.
3. One report generation request.
4. Multiple concurrent specialist requests.
5. A complete investigation replay.

Record the resource profile for each.

---

## 16. Model Fallback and Failure Recovery

### 16.1 Fallback policy

Fallback should be task-aware.

A smaller model may be acceptable for simple extraction but unsuitable for complex investigation reasoning.

Do not automatically substitute any available model for every failed model call.

### 16.2 Failure handling

```text
Primary Model Request
        |
        v
     Response?
        |
   +----+----+
   |         |
  Yes        No
   |         |
   v         v
 Validate   Classify Failure
   |         |
   |         v
   |     Retry Eligible?
   |         |
   |      +--+--+
   |      |     |
   |     Yes    No
   |      |     |
   |      v     v
   |    Retry  Fallback Eligible?
   |             |
   |          +--+--+
   |          |     |
   |         Yes    No
   |          |     |
   |          v     v
   |       Fallback  Block / Human Review
   |          |
   +----------+
        |
        v
   Output Validation
```

### 16.3 Retry rules

Retries should be limited to transient failures.

Examples:

- Temporary provider unavailability.
- Connection timeout.
- Rate limiting.
- Temporary resource exhaustion.

Invalid reasoning or unsupported conclusions should not trigger unlimited retries.

A fallback response must be marked in task metadata.

### 16.4 Safe degradation

If all suitable models are unavailable:

- Preserve the investigation state.
- Mark affected tasks as blocked.
- Retain completed evidence.
- Avoid fabricating findings.
- Allow analyst intervention.
- Resume when a suitable model becomes available.

---

## 17. Model Registry and Lifecycle Management

### 17.1 Registry responsibilities

The registry stores configuration and lifecycle metadata for approved models.

Example:

```json
{
  "model_id": "sentinel-planner",
  "provider": "ollama",
  "provider_model": "configured-model-name",
  "role": "planner",
  "version": "1.0",
  "status": "active",
  "temperature": 0.0,
  "max_output_tokens": 2048,
  "schema_support": true,
  "fallback_model_id": null
}
```

### 17.2 Model lifecycle

```text
Candidate
   |
   v
Benchmarking
   |
   v
Security and Reliability Testing
   |
   v
Approval
   |
   v
Staging
   |
   v
Production
   |
   v
Monitoring
   |
   v
Retirement / Replacement
```

### 17.3 Version changes

Every model replacement must trigger regression testing.

Do not update a model alias silently and assume behavior remains unchanged.

Persist model identifiers and version information with investigation task records.

---

## 18. Model Evaluation Framework

Model selection must use the evaluation strategy defined in the Testing, Validation & Evaluation Strategy Specification.

### 18.1 Planner evaluation

| Metric | Purpose |
|---|---|
| Task selection accuracy | Measures whether appropriate capabilities are selected |
| Routing precision | Measures how often selected capabilities are appropriate |
| Routing recall | Measures whether required capabilities are selected |
| Replanning effectiveness | Measures recovery after incomplete results |
| Termination accuracy | Measures appropriate completion decisions |
| Plan validity rate | Measures schema and semantic validity |
| Planning latency | Measures planning overhead |

### 18.2 Specialist evaluation

| Metric | Purpose |
|---|---|
| Task correctness | Correctness of specialist result |
| Evidence groundedness | Support for conclusions from evidence |
| Unsupported claim rate | Frequency of unsupported claims |
| Structured output validity | Schema compliance |
| Task completion rate | Successful task completion |
| Latency | Execution time |

### 18.3 Retrieval evaluation

Use:

- Precision@K.
- Recall@K.
- MRR.
- nDCG@K.
- Retrieval latency.

### 18.4 Model comparison protocol

To compare two models:

1. Use the same evaluation scenarios.
2. Use the same input evidence.
3. Use the same output schemas.
4. Keep generation settings controlled.
5. Record model and prompt versions.
6. Run sufficient repetitions where outputs are stochastic.
7. Compare quality, latency, and resource use.
8. Analyze failure categories.
9. Report uncertainty and sample size.
10. Avoid selecting a model based on one successful demonstration.

### 18.5 Ablation studies

Recommended experiments:

| Experiment | Comparison |
|---|---|
| Planner separation | Shared LLM vs dedicated Planner configuration |
| Structured output | Free-form vs schema-constrained generation |
| Context management | Full history vs selected investigation context |
| Reranking | Vector retrieval vs vector retrieval plus reranking |
| Quantization | Full precision vs lower precision |
| Fallback | Primary-only vs task-aware fallback |
| Prompt revision | Baseline prompt vs revised prompt |

---

## 19. Integration with LangGraph

LangGraph controls the investigation execution graph.

The model layer provides reasoning within graph nodes.

Suggested logical graph:

```text
START
  |
  v
Load Investigation State
  |
  v
Planner Node
  |
  v
Plan Validation Node
  |
  v
Task Dispatch Node
  |
  +------> Specialist Node
  |             |
  |             v
  |       Result Validation
  |             |
  +-------------+
        |
        v
State Update
        |
        v
Planner Re-evaluation
        |
        +------> More Investigation
        |
        +------> Human Review
        |
        +------> Completion
        |
        v
       END
```

The graph is a control structure, not a fixed incident workflow.

The Planner can select different specialist nodes, revisit capabilities, or request additional evidence based on current state.

### 19.1 State ownership

The orchestration runtime owns the authoritative investigation state.

Models receive snapshots and return proposals or results.

Models do not directly mutate persistent state.

### 19.2 Persistence

Persist:

- Model invocation metadata.
- Prompt version.
- Model version.
- Input references.
- Output references.
- Validation result.
- Retry and fallback history.
- Token usage, where available.
- Latency.
- Associated task and investigation IDs.

This supports debugging, evaluation, and reproducibility.

---

## 20. Security Requirements for Model Usage

Model inputs may contain untrusted data, including attacker-controlled log fields and retrieved documents.

The model layer must assume that input content can contain malicious instructions.

Required controls:

1. Clearly distinguish system instructions from evidence.
2. Treat logs and retrieved documents as untrusted content.
3. Do not allow retrieved content to override agent instructions.
4. Restrict model tool access to registered capabilities.
5. Validate every model-generated action.
6. Enforce permissions outside the LLM.
7. Redact sensitive information where required.
8. Avoid logging secrets or unnecessary personal data.
9. Bound context, tokens, retries, and execution time.
10. Record suspicious prompt-injection attempts where appropriate.

The model must never be the sole security boundary.

---

## 21. Configuration Management

Model configuration should be externalized.

Example:

```yaml
models:
  planner:
    provider: ollama
    model: configured-planner-model
    temperature: 0.0
    max_output_tokens: 2048
    timeout_seconds: 60

  specialist:
    provider: ollama
    model: configured-specialist-model
    temperature: 0.1
    max_output_tokens: 4096
    timeout_seconds: 90

  embeddings:
    provider: ollama
    model: configured-embedding-model
    batch_size: 32

  routing:
    max_concurrent_requests: 2
    enable_fallback: false
    max_retries: 2
```

The model names above are configuration placeholders, not recommendations for particular releases.

Configuration must be validated during application startup.

---

## 22. Implementation Roadmap

### Phase 1 — Model abstraction

- Define ModelAdapter interface.
- Implement Ollama provider.
- Create model registry.
- Externalize model configuration.
- Add invocation logging and error normalization.

### Phase 2 — Planner integration

- Define Planner input and output schemas.
- Implement Planner prompt.
- Add schema and semantic validation.
- Integrate with LangGraph.
- Add bounded retries and failure handling.

### Phase 3 — Specialist integration

- Define specialist contracts.
- Implement shared specialist model configuration.
- Add evidence-grounding rules.
- Add structured output validation.
- Integrate task results with investigation state.

### Phase 4 — Retrieval models

- Select embedding candidates.
- Benchmark retrieval quality.
- Integrate embeddings with ChromaDB.
- Add metadata filtering.
- Evaluate reranking.

### Phase 5 — Optimization

- Profile inference performance.
- Test quantization options.
- Tune concurrency.
- Implement context management.
- Evaluate fallback strategies.

### Phase 6 — Evaluation and release

- Build fixed model evaluation datasets.
- Run model comparisons.
- Conduct prompt-injection tests.
- Run regression tests.
- Approve model configurations.
- Document deployment requirements.

---

## 23. Acceptance Criteria

The model architecture is ready for MVP integration when:

| ID | Acceptance criterion |
|---|---|
| MOD-01 | All model calls use the model adapter |
| MOD-02 | Model configuration is externalized |
| MOD-03 | Planner output conforms to a defined schema |
| MOD-04 | Invalid plans are rejected before execution |
| MOD-05 | Planner cannot execute arbitrary tools |
| MOD-06 | Specialist outputs use defined contracts |
| MOD-07 | Evidence references are preserved |
| MOD-08 | Model and prompt versions are recorded |
| MOD-09 | Model failures are normalized and handled |
| MOD-10 | Retry behavior is bounded |
| MOD-11 | Investigation state remains persistent after model failure |
| MOD-12 | Embedding model version is tracked |
| MOD-13 | Model latency and resource usage are measurable |
| MOD-14 | Prompt-injection tests are included |
| MOD-15 | Model comparisons use a repeatable evaluation suite |

## 24. Key Architectural Decisions

| Decision | MVP position |
|---|---|
| Primary inference | Local Ollama |
| Orchestration | LangGraph |
| Planner | Dedicated Planner configuration |
| Specialist agents | Shared specialist configuration initially |
| Detection | Rules and ML, with optional LLM interpretation |
| Embeddings | Separate embedding model |
| Reranking | Optional, introduced after baseline evaluation |
| Fine-tuning | Deferred until evidence justifies it |
| Quantization | Selected through hardware and quality benchmarks |
| Fallback | Designed into the architecture; initially optional |
| Model access | Through a provider abstraction |
| State management | Owned by orchestration runtime |
| Tool execution | Registered capabilities with external validation |

## 25. Final Architectural Position

Project Sentinel should not be designed as a collection of autonomous LLMs that independently control the investigation.

It should be designed as a controlled multi-agent system in which:

- The Planner determines what investigation work is needed.
- Specialist agents perform bounded tasks.
- Models provide reasoning and structured recommendations.
- The model router selects approved model configurations.
- The model adapter handles provider integration.
- The orchestration runtime validates and executes plans.
- Persistent investigation state remains authoritative.
- Evidence and provenance constrain conclusions.
- Human approval governs sensitive response actions.

The central differentiator remains dynamic, goal-driven orchestration—not the number of models deployed.

A small number of well-evaluated models, combined with reliable orchestration and evidence management, is preferable to a large collection of unvalidated specialist models.
