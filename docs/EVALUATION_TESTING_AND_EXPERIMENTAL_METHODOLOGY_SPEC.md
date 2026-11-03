# Project Sentinel — Evaluation, Testing & Experimental Methodology Specification (ETEMS)

**Document Type:** Evaluation and Quality Assurance Specification  

**Version:** 1.0  

**Status:** Proposed Architecture Upgrade  

**Primary Focus:** System testing, orchestration evaluation, baseline comparison, attack scenario evaluation, metrics, ablation studies, and experimental methodology

---

# 1. Purpose

Project Sentinel is designed as an intelligent investigation system with an adaptive orchestration layer.

Building the system is not sufficient to demonstrate its value.

The project must answer measurable questions:

- Does the system correctly investigate security scenarios?

- Does adaptive orchestration improve investigation quality?

- Does the Planner select useful actions?

- Are capability results reliable?

- Does RAG improve contextual analysis?

- Does the system terminate investigations efficiently?

- Can the system recover from component failures?

- How does the proposed architecture compare with a simpler baseline?

The purpose of this specification is to define a reproducible evaluation framework.

The central principle is:

> **Every major architectural claim should be supported by measurable experimental evidence.**

---

# 2. Evaluation Philosophy

The project should not evaluate the system using only one metric such as accuracy.

Project Sentinel has multiple responsibilities.

Therefore, evaluation must be multi-dimensional.

```text
                  PROJECT SENTINEL
                         │
         ┌───────────────┼────────────────┐
         ▼               ▼                ▼
    DETECTION       ORCHESTRATION      RELIABILITY
         │               │                │
         ▼               ▼                ▼
      Accuracy       Action Quality     Recovery
      Coverage       Efficiency         Availability
         │               │                │
         └───────────────┼────────────────┘
                         ▼
                   FINAL EVALUATION
```

The evaluation framework measures both:

1. **What the system concludes**

2. **How efficiently and reliably it reaches that conclusion**

---

# 3. Evaluation Layers

The system should be tested at five levels.

| Layer | Question |
|---|---|
| Unit | Does an individual component work correctly? |
| Integration | Do connected components exchange data correctly? |
| Workflow | Does an investigation execute correctly end-to-end? |
| Experimental | Does the proposed approach outperform a baseline? |
| Reliability | Does the system behave safely during failures? |
---

# 4. Unit Testing

Every critical module should be independently tested.

Primary targets include:

```text
Event Normalization
Alert Generation
State Management
Evidence Validation
Capability Interfaces
Action Scoring
Budget Enforcement
Confidence Calculation
Policy Validation
```

Example:

```text
Input:
Raw telemetry event
Expected:
Valid NormalizedEvent
```

The test should also verify invalid input.

```text
Input:
Malformed event
Expected:
Validation failure
```

---

# 5. Integration Testing

Integration tests verify communication between components.

Important flows include:

```text
Ingestion
    ↓
Normalization
    ↓
Detection
```

and:

```text
Planner
    ↓
Action Request
    ↓
Policy Validation
    ↓
Capability
    ↓
State Manager
```

The primary objective is to verify that component contracts remain compatible.

---

# 6. End-to-End Workflow Testing

An end-to-end test should simulate a complete investigation.

```text
Telemetry
    ↓
Alert
    ↓
Investigation Created
    ↓
Planner Assessment
    ↓
Capability Execution
    ↓
Evidence Update
    ↓
Reassessment
    ↓
Final Outcome
```

The test is successful only if:

- The workflow completes.

- State remains valid.

- Evidence remains traceable.

- Decisions are recorded.

- A valid final status is produced.

---

# 7. Scenario-Based Evaluation

Project Sentinel should be evaluated using realistic security scenarios.

Each scenario represents a known investigation problem.

A scenario should contain:

```text
Scenario
│
├── Scenario ID
├── Attack / Activity Type
├── Initial Evidence
├── Expected Investigation Path
├── Expected Findings
├── Ground Truth
└── Evaluation Criteria
```

The system should initially use a manageable number of scenarios.

For a 3–4 month academic implementation, the recommended scope is:

```text
3 Primary Scenarios
+ Optional Extension Scenarios
```

This provides enough variation for evaluation without reducing implementation quality.

---

# 8. Recommended Scenario Structure

Each scenario should test different orchestration requirements.

Example categories:

| Scenario | Primary Evaluation Focus |
|---|---|
| Suspicious authentication | Timeline and event correlation |
| Process or execution activity | Evidence linking |
| Network anomaly | Cross-event analysis |
| Multi-stage attack | Adaptive investigation planning |
The final scenarios should be selected according to the dataset fields that are actually available.

The evaluation must not claim capabilities unsupported by the selected telemetry.

---

# 9. Ground Truth

Every evaluation scenario should define expected facts.

```text
Ground Truth
│
├── Relevant Events
├── Attack Timeline
├── Expected Relationships
├── Known Attack Label
└── Expected Conclusion
```

Ground truth is required to distinguish:

```text
Correct Investigation
        from
Plausible-Sounding Investigation
```

This is particularly important when LLM-generated reasoning is involved.

---

# 10. Baseline Architecture

The strongest academic comparison is between:

```text
BASELINE
    vs.
PROPOSED SYSTEM
```

The baseline should be simpler but functionally comparable.

Example:

```text
Baseline:
Fixed investigation sequence
Step 1 → Correlation
Step 2 → Knowledge Retrieval
Step 3 → Final Summary
```

The proposed architecture:

```text
Assess State
    ↓
Identify Evidence Gaps
    ↓
Select Best Capability
    ↓
Execute
    ↓
Reassess
    ↓
Continue or Terminate
```

The purpose is to determine whether adaptive orchestration provides measurable benefits.

---

# 11. Baseline Comparison Questions

The experiments should answer:

- Does adaptive orchestration find more relevant evidence?

- Does it perform fewer unnecessary operations?

- Does it improve final investigation quality?

- Does it handle incomplete evidence better?

- Does it terminate earlier when sufficient evidence exists?

---

# 12. Investigation Accuracy

Final investigation accuracy can be measured against ground truth.

Conceptually:

```text
Investigation Accuracy =
Correct Conclusions
────────────────────
Total Scenarios
```

However, accuracy alone is insufficient.

A system may reach a correct answer inefficiently or without reliable evidence.

Therefore, additional metrics are required.

---

# 13. Evidence Coverage

Evidence coverage measures how much relevant information was identified.

```text
Evidence Coverage =
Relevant Evidence Identified
────────────────────────────
Total Relevant Evidence
```

Example:

```text
Ground Truth:
10 relevant events
System identified:
8 relevant events
Coverage:
80%
```

This metric evaluates investigation completeness.

---

# 14. Evidence Precision

Evidence precision measures whether collected evidence is relevant.

```text
Evidence Precision =
Relevant Evidence Collected
───────────────────────────
Total Evidence Collected
```

A system that retrieves every possible event may have high coverage but poor precision.

Therefore:

```text
Coverage + Precision
```

provide a more meaningful evaluation.

---

# 15. Action Selection Quality

The Planner should be evaluated based on the usefulness of its selected actions.

For each decision:

```text
Selected Action
        │
        ▼
Did it reduce an evidence gap?
        │
   ┌────┴────┐
   │         │
  Yes        No
   │         │
Useful    Low Value
```

A conceptual metric is:

```text
Action Utility =
Useful Actions
──────────────
Total Actions
```

This measures whether orchestration decisions contribute to the investigation.

---

# 16. Information Gain Evaluation

Each capability execution should be evaluated for its contribution.

Information gain may be estimated using:

- New relevant evidence discovered.

- Evidence gaps resolved.

- Hypotheses strengthened or rejected.

- Reduction in investigation uncertainty.

Example:

```text
Before Action:
3 unresolved gaps
After Action:
1 unresolved gap
Information Improvement:
2 gaps resolved
```

The initial MVP can use transparent rule-based information gain measurements.

---

# 17. Investigation Efficiency

Efficiency measures how many resources are required.

Important measurements include:

```text
Number of Steps
Number of Capability Calls
Total Investigation Time
Repeated Actions
```

Example:

```text
Efficiency Improvement =
Baseline Steps - Proposed Steps
──────────────────────────────
Baseline Steps
```

The proposed system does not need to be faster in every case.

It should demonstrate a justified trade-off between:

```text
Investigation Quality
        vs.
Execution Cost
```

---

# 18. Redundant Action Rate

Adaptive systems must avoid repeatedly performing low-value operations.

Measure:

```text
Redundant Action Rate =
Repeated Low-Value Actions
──────────────────────────
Total Actions
```

A lower rate indicates better planning efficiency.

---

# 19. Termination Quality

The system should stop for the correct reason.

Termination outcomes should be classified.

```text
SUFFICIENT_EVIDENCE
BUDGET_EXHAUSTED
INCONCLUSIVE
HUMAN_REVIEW_REQUIRED
SYSTEM_FAILURE
```

Evaluation should determine whether the termination was appropriate.

Example:

```text
Termination Precision =
Correct Terminations
────────────────────
Total Terminations
```

---

# 20. Confidence Calibration

The system's confidence should correspond reasonably to actual correctness.

Example:

```text
High Confidence Cases
        │
        ▼
How Often Were They Correct?
```

If the system frequently gives high confidence to incorrect conclusions, its confidence model is poorly calibrated.

Evaluation can group results into:

```text
High Confidence
Medium Confidence
Low Confidence
```

and compare:

```text
Reported Confidence
        vs.
Actual Correctness
```

---

# 21. Capability Evaluation

Each capability should be evaluated separately.

| Capability | Example Metric |
|---|---|
| Correlation | Relevant event linkage |
| Knowledge Retrieval | Context relevance |
| Evidence Validator | Correct validation decisions |
| Reporting | Traceability and completeness |
This identifies whether poor overall performance is caused by:

```text
Planner
    or
Specific Capability
```

---

# 22. RAG Evaluation

The knowledge retrieval component should be evaluated separately from incident detection.

Key questions:

- Were retrieved documents relevant?

- Did retrieved context improve interpretation?

- Were sources traceable?

A basic retrieval metric is:

```text
Retrieval Precision@K =
Relevant Documents Retrieved
────────────────────────────
K Documents Returned
```

For the MVP, manual relevance assessment can supplement automated evaluation.

---

# 23. RAG Ablation Test

Compare:

```text
Investigation Without Knowledge Retrieval
                 vs.
Investigation With Knowledge Retrieval
```

Measure:

- Investigation completeness.

- Interpretation quality.

- Action selection quality.

- Final conclusion quality.

This demonstrates whether RAG provides measurable value.

---

# 24. Orchestration Ablation Tests

Ablation testing removes one component to determine its contribution.

Recommended experiments:

```text
Experiment A:
Full System
Experiment B:
Without Adaptive Planning
Experiment C:
Without Knowledge Retrieval
Experiment D:
Without Evidence Validation
```

Example comparison:

| Configuration | Accuracy | Steps | Evidence Coverage |
|---|---:|---:|---:|
| Full System | TBD | TBD | TBD |
| No Adaptive Planning | TBD | TBD | TBD |
| No RAG | TBD | TBD | TBD |
| No Validation | TBD | TBD | TBD |
The results should be filled using actual experiments.

---

# 25. Failure Testing

The system must be tested under controlled failures.

Important cases include:

```text
LLM Timeout
Capability Failure
Database Unavailable
ChromaDB Unavailable
Invalid Capability Output
Malformed Input
```

For each failure:

```text
Failure
   ↓
Expected System Behavior
   ↓
Observed Behavior
   ↓
Pass / Fail
```

---

# 26. LLM Failure Test

Example:

```text
Planner Call
    ↓
Timeout
    ↓
Fallback Strategy
    ↓
Retry or Deterministic Fallback
    ↓
Continue / Escalate
```

Evaluation criteria:

- No corrupted state.

- No uncontrolled retries.

- Failure recorded.

- Investigation follows defined fallback behavior.

---

# 27. Degraded Mode Testing

Example:

```text
ChromaDB Disabled
```

Expected:

```text
Knowledge Capability Unavailable
        ↓
Other Capabilities Continue
        ↓
Limitation Recorded
        ↓
Final Report Indicates Degraded Mode
```

The investigation should not silently pretend that unavailable services were used.

---

# 28. State Integrity Testing

State integrity tests verify that invalid transitions cannot occur.

Example:

```text
State Version 5
      │
      ▼
Invalid Update Attempt
      │
      ▼
Rejected
      │
      ▼
State Version Remains 5
```

Tests should cover:

- Invalid schemas.

- Version conflicts.

- Missing evidence references.

- Invalid status transitions.

---

# 29. Reproducibility

Experimental results must be reproducible.

Each experiment should record:

```text
Experiment ID
Scenario ID
Dataset Version
System Version
Configuration
Model Used
Parameters
Timestamp
Results
```

This prevents results from becoming untraceable.

---

# 30. LLM Configuration Recording

LLM behavior may vary depending on configuration.

Experiments should record:

```text
Model Name
Temperature
Prompt Version
Timeout
Retry Policy
```

For evaluation, deterministic or low-variability settings are preferred where possible.

---

# 31. Experiment Matrix

A practical experiment matrix is:

| Experiment | Purpose |
|---|---|
| E1 | Baseline workflow |
| E2 | Full adaptive orchestration |
| E3 | Full system without RAG |
| E4 | Full system without evidence validation |
| E5 | LLM failure recovery |
| E6 | Capability failure recovery |
| E7 | State integrity validation |
This is a manageable academic evaluation scope.

---

# 32. Testing Architecture

```text
                  TEST DATA
                      │
                      ▼
              SCENARIO RUNNER
                      │
             ┌────────┼────────┐
             ▼        ▼        ▼
         BASELINE   PROPOSED   ABLATION
             │        │        │
             └────────┼────────┘
                      ▼
                METRIC ENGINE
                      │
                      ▼
               RESULT STORAGE
                      │
                      ▼
              EXPERIMENT REPORT
```

The scenario runner should execute configurations consistently.

---

# 33. Evaluation Dataset Split

If the selected dataset supports it, scenarios should be separated into:

```text
Development Scenarios
        │
        ▼
Used to build and debug
Evaluation Scenarios
        │
        ▼
Used for final measurement
```

The final evaluation should not rely exclusively on scenarios repeatedly used during development.

---

# 34. Human Evaluation

Some qualities require structured human assessment.

Examples:

- Report clarity.

- Investigation explanation.

- RAG context relevance.

A simple rubric can use:

```text
1 = Poor
2 = Limited
3 = Acceptable
4 = Good
5 = Excellent
```

Human evaluation criteria should be defined before reviewing results.

---

# 35. Investigation Report Evaluation

A final report can be evaluated against a checklist.

| Criterion | Question |
|---|---|
| Evidence Traceability | Are claims linked to evidence? |
| Completeness | Are major findings included? |
| Limitations | Are unresolved gaps stated? |
| Clarity | Can an analyst understand the result? |
| Consistency | Does the report match investigation state? |
---

# 36. Result Visualization

The final project should visualize results clearly.

Recommended charts include:

```text
Investigation Accuracy
    Baseline vs Proposed
Evidence Coverage
    Baseline vs Proposed
Average Investigation Steps
    Baseline vs Proposed
Action Utility
    Baseline vs Proposed
Failure Recovery Rate
```

Results should be based on actual experiment output.

No artificial performance values should be used.

---

# 37. Statistical Caution

Because the project may use a limited number of scenarios, results should not make exaggerated claims.

For example, prefer:

> "The proposed architecture demonstrated improved evidence coverage across the evaluated scenarios."

Avoid:

> "The proposed architecture is universally superior."

The scope of conclusions should match the evaluation scope.

---

# 38. Performance Evaluation

The system should also record basic performance metrics.

```text
API Response Time
Capability Execution Time
LLM Latency
Database Query Time
Investigation Duration
```

The purpose is not necessarily to achieve enterprise-scale throughput.

The purpose is to identify architectural bottlenecks and demonstrate controlled execution.

---

# 39. Evaluation Output Schema

Each scenario run should produce structured results.

```text
EvaluationResult
│
├── experiment_id
├── scenario_id
├── configuration
│
├── final_status
├── correctness
│
├── evidence_precision
├── evidence_coverage
│
├── action_utility
├── total_steps
├── execution_time
│
├── failures
└── notes
```

This allows automated comparison.

---

# 40. Complete Experimental Workflow

```text
SELECT SCENARIO
       │
       ▼
LOAD GROUND TRUTH
       │
       ▼
SELECT CONFIGURATION
       │
       ├── Baseline
       ├── Full System
       └── Ablation
       │
       ▼
RUN INVESTIGATION
       │
       ▼
COLLECT DECISIONS
       │
       ▼
COLLECT EVIDENCE
       │
       ▼
CALCULATE METRICS
       │
       ▼
STORE RESULTS
       │
       ▼
COMPARE CONFIGURATIONS
       │
       ▼
GENERATE EVALUATION REPORT
```

---

# 41. Recommended Success Criteria

The project should define success criteria before final experiments.

Examples:

### Functional

- All selected scenarios execute successfully.

- Investigation state remains valid.

- Evidence remains traceable.

### Orchestration

- Adaptive action selection demonstrates useful action choices.

- Redundant actions remain controlled.

- Investigation budgets prevent uncontrolled loops.

### Reliability

- Defined failure scenarios do not corrupt state.

- Fallback behavior is observable.

### Experimental

- The proposed architecture can be compared against a baseline.

- Results are reproducible.

The exact numerical targets should be determined after initial baseline measurements.

---

# 42. Evaluation of the Central Innovation

The project's central innovation is not simply:

```text
"Using an LLM"
```

The central evaluation target is:

```text
STATE-AWARE
ADAPTIVE
EVIDENCE-DRIVEN
CAPABILITY ORCHESTRATION
```

Therefore, the strongest experiment is:

```text
Fixed Investigation Workflow
             vs.
Adaptive State-Aware Workflow
```

Measure:

```text
Investigation Quality
Evidence Coverage
Action Utility
Execution Efficiency
Termination Quality
```

This directly evaluates the architectural contribution.

---

# 43. Final Evaluation Framework

```text
                    PROJECT SENTINEL
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
     CORRECTNESS       ORCHESTRATION      RELIABILITY
        │                  │                  │
        ▼                  ▼                  ▼
     Accuracy          Action Utility     Recovery
     Coverage          Efficiency         Integrity
     Precision         Termination        Degraded Mode
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                   BASELINE COMPARISON
                           │
                           ▼
                    ABLATION STUDIES
                           │
                           ▼
                    EXPERIMENTAL RESULTS
```

---

# 44. Final Principles

Project Sentinel should be evaluated as a system rather than as a collection of technologies.

The evaluation should demonstrate:

```text
INPUT
  ↓
ADAPTIVE INVESTIGATION
  ↓
TRACEABLE DECISIONS
  ↓
EVIDENCE-BASED CONCLUSION
  ↓
MEASURABLE RESULT
```

The strongest final project demonstration will therefore include:

1. A realistic scenario.

2. A complete investigation trace.

3. A baseline comparison.

4. Measurable metrics.

5. A failure-handling demonstration.

6. An explanation of why the orchestration selected its actions.

> **The goal is not to prove that Project Sentinel uses more technologies than a conventional system. The goal is to demonstrate, through controlled evaluation, that its orchestration architecture provides measurable investigative value.**
