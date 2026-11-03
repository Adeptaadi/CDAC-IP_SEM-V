# Project Sentinel
# Testing, Validation & Evaluation Strategy

**Document Type:** Quality Assurance and Evaluation Specification  
**Version:** 1.0  
**Status:** Architecture Baseline  
**Primary Focus:** Functional testing, integration testing, end-to-end validation, detection evaluation, agent evaluation, orchestration evaluation, reliability testing, performance testing, and baseline comparison.

---

# 1. Purpose

Project Sentinel is not a conventional application with only frontend and backend functionality. Its core workflow includes:

- Security telemetry ingestion.
- Data validation and normalization.
- Detection logic.
- Alert generation.
- Investigation orchestration.
- AI agent collaboration.
- Capability execution.
- Evidence collection.
- Analyst review.

Therefore, the project must be tested at multiple levels.

The objective of this strategy is to answer five fundamental questions:

1. **Does each component work correctly?**
2. **Do the components work correctly together?**
3. **Does the complete investigation workflow produce the expected outcome?**
4. **Are the AI agents and orchestration system effective and reliable?**
5. **Can the project's improvement over a baseline be measured?**

The testing philosophy is:

```text
BUILD
  │
  ▼
TEST COMPONENTS
  │
  ▼
TEST INTEGRATION
  │
  ▼
TEST COMPLETE WORKFLOWS
  │
  ▼
MEASURE RESULTS
  │
  ▼
COMPARE WITH BASELINE
```

---

# 2. Quality Assurance Architecture

The complete validation hierarchy is:

```text
                 ┌──────────────────────┐
                 │   PROJECT EVALUATION │
                 └──────────┬───────────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
       FUNCTIONAL      AI/AGENT       PERFORMANCE
        VALIDATION     EVALUATION      VALIDATION
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                    END-TO-END TESTING
                            │
                            ▼
                    INTEGRATION TESTING
                            │
                            ▼
                       UNIT TESTING
```

Each layer has a different purpose.

---

# 3. Testing Levels

| Testing Level | Primary Question |
|---|---|
| Unit Testing | Does an individual component work? |
| Integration Testing | Do connected components work together? |
| End-to-End Testing | Does the complete workflow work? |
| Failure Testing | Does the system fail safely? |
| Performance Testing | Does the system perform within acceptable limits? |
| Evaluation Testing | Is the proposed approach effective? |

---

# 4. Unit Testing Strategy

Unit tests validate isolated components.

The following areas should have unit tests.

## 4.1 Telemetry Processing

Test:

- Schema validation.
- Field extraction.
- Timestamp parsing.
- Event normalization.
- Invalid event handling.

Example:

```text
INPUT EVENT
     │
     ▼
NORMALIZER
     │
     ▼
EXPECTED NORMALIZED EVENT
```

The test should verify both valid and invalid inputs.

---

## 4.2 Detection Logic

Each detection rule or detector should be tested independently.

Test cases should include:

| Test Type | Expected Result |
|---|---|
| Known attack pattern | Alert generated |
| Normal activity | No alert |
| Incomplete event | Safe handling |
| Invalid data | Rejection or controlled failure |

Detection tests must use known expected outcomes.

---

## 4.3 Investigation State Machine

State transitions should be tested explicitly.

Example:

```text
CREATED → ACTIVE
ACTIVE → WAITING_FOR_REVIEW
ACTIVE → COMPLETED
ACTIVE → FAILED
```

Invalid transitions should also be tested.

Example:

```text
FAILED → COMPLETED
```

should not be allowed unless explicitly defined by the workflow.

---

## 4.4 Capability Tests

Every capability should be tested for:

- Valid input.
- Invalid input.
- Expected output.
- Failure handling.
- Timeout behavior.

The capability interface should behave predictably regardless of which agent requested it.

---

# 5. Integration Testing

Integration testing verifies that components communicate correctly.

Important integration boundaries include:

```text
INGESTION → NORMALIZATION

NORMALIZATION → DETECTION

DETECTION → ALERT STORAGE

ALERT → INVESTIGATION

ORCHESTRATOR → AGENT

AGENT → CAPABILITY
```

Each boundary should have at least one successful and one failure-oriented test.

---

# 6. Database Integration Tests

The persistence layer should be tested with realistic data.

Verify:

- Records can be created.
- Records can be retrieved.
- State changes are persisted.
- Relationships remain valid.
- Invalid operations are rejected.

Example workflow:

```text
CREATE ALERT
     │
     ▼
CREATE INVESTIGATION
     │
     ▼
UPDATE STATE
     │
     ▼
RETRIEVE FINAL RECORD
```

The retrieved state should match the expected workflow result.

---

# 7. API Integration Tests

Protected APIs should be tested for:

- Valid authentication.
- Missing authentication.
- Invalid authorization.
- Invalid requests.
- Valid requests.
- Invalid state changes.

Example:

```text
CLIENT
  │
  ▼
API REQUEST
  │
  ├── AUTHENTICATION
  ├── AUTHORIZATION
  └── VALIDATION
         │
         ▼
      RESPONSE
```

The tests should verify both HTTP status behavior and application state.

---

# 8. End-to-End Workflow Testing

End-to-end testing validates the complete Project Sentinel workflow.

The baseline scenario is:

```text
DATASET
   │
   ▼
INGESTION
   │
   ▼
NORMALIZATION
   │
   ▼
DETECTION
   │
   ▼
ALERT
   │
   ▼
INVESTIGATION
   │
   ▼
AGENT ORCHESTRATION
   │
   ▼
EVIDENCE ANALYSIS
   │
   ▼
FINAL OUTCOME
```

An end-to-end test should verify the complete chain rather than isolated components.

---

# 9. Attack Scenario Test Set

The project should define a controlled evaluation set of realistic scenarios.

For a 3–4 month implementation timeline, the recommended baseline is **3 primary attack scenarios**, with a fourth scenario added only if the core system is stable.

The scenarios should:

- Be supported by the selected dataset.
- Have identifiable evidence.
- Have expected outcomes.
- Exercise multiple parts of the investigation workflow.

A test scenario template is:

| Field | Description |
|---|---|
| Scenario ID | Unique identifier |
| Scenario Name | Attack or suspicious behavior |
| Dataset Source | Source of telemetry |
| Expected Alert | Expected detection result |
| Expected Evidence | Key supporting artifacts |
| Expected Conclusion | Expected investigation outcome |

---

# 10. Detection Evaluation

The detection layer should be evaluated using measurable metrics.

The standard classification terms are:

| Actual / Predicted | Attack | Normal |
|---|---|---|
| Attack | True Positive | False Negative |
| Normal | False Positive | True Negative |

The primary metrics are defined below.

---

# 11. Precision

Precision measures how many generated alerts were actually relevant.

\[
Precision =
\frac{TP}{TP + FP}
\]

Where:

- \(TP\) = True Positives.
- \(FP\) = False Positives.

High precision means the system generates fewer unnecessary alerts.

---

# 12. Recall

Recall measures how many relevant attacks were successfully identified.

\[
Recall =
\frac{TP}{TP + FN}
\]

Where:

- \(FN\) = False Negatives.

High recall means fewer attacks are missed.

---

# 13. F1 Score

The F1 score balances precision and recall.

\[
F1 =
2 \times
\frac{Precision \times Recall}
{Precision + Recall}
\]

This is useful when both missed attacks and false alerts are important.

---

# 14. Detection Evaluation Record

Each evaluation run should record:

```text
evaluation_id
dataset_version
scenario_id
detection_method
true_positives
false_positives
false_negatives
precision
recall
f1_score
```

This allows results to be reproduced and compared.

---

# 15. Agent Evaluation

AI agent evaluation must be separated into different dimensions.

A single metric called "agent accuracy" is insufficient.

The recommended dimensions are:

```text
TASK COMPLETION
      +
EVIDENCE QUALITY
      +
CONCLUSION QUALITY
      +
OPERATIONAL RELIABILITY
```

---

# 16. Agent Task Completion

Task completion measures whether an agent completed its assigned operation successfully.

\[
TaskCompletionRate =
\frac{SuccessfullyCompletedTasks}
{TotalAssignedTasks}
\]

Examples of successful tasks:

- Relevant evidence was retrieved.
- A required capability executed successfully.
- The result passed schema validation.

This does not automatically measure whether the conclusion was correct.

---

# 17. Evidence Quality Evaluation

Evidence quality evaluates whether the agent identified relevant supporting information.

For each scenario, define a reference evidence set:

```text
Expected Evidence:
- Suspicious process
- Parent-child relationship
- Network connection
```

The agent result can then be compared against the reference set.

A simple evidence recall metric is:

\[
EvidenceRecall =
\frac{RelevantEvidenceRetrieved}
{TotalExpectedRelevantEvidence}
\]

A precision-style metric can also be used:

\[
EvidencePrecision =
\frac{RelevantEvidenceRetrieved}
{TotalEvidenceRetrieved}
\]

---

# 18. Investigation Conclusion Accuracy

The final investigation conclusion should be evaluated against a known expected outcome.

\[
ConclusionAccuracy =
\frac{CorrectConclusions}
{TotalEvaluatedInvestigations}
\]

The expected conclusion must be defined before evaluation.

Example:

```text
Scenario:
Suspicious credential activity

Expected Result:
Escalate investigation

System Result:
Escalated

Outcome:
Correct
```

---

# 19. Orchestration Evaluation

The orchestration layer is the core differentiator of Project Sentinel.

It should be evaluated independently.

Important questions include:

- Did the orchestrator select appropriate tasks?
- Were unnecessary agent calls avoided?
- Were dependencies respected?
- Did the workflow reach a valid final state?

A useful metric is:

\[
WorkflowSuccessRate =
\frac{SuccessfullyCompletedWorkflows}
{TotalWorkflowRuns}
\]

---

# 20. Orchestration Efficiency

Efficiency should also be measured.

For example:

\[
AverageAgentCalls =
\frac{TotalAgentExecutions}
{TotalInvestigations}
\]

This helps identify unnecessary orchestration overhead.

A system that invokes ten agents to reach the same result as three agents may be operationally less efficient.

The objective is not to maximize the number of AI calls.

The objective is:

```text
MINIMUM NECESSARY AGENT WORK
        +
MAXIMUM INVESTIGATION VALUE
```

---

# 21. Baseline Comparison

The project should define a baseline before evaluating advanced orchestration.

A recommended baseline is:

```text
RULE-BASED DETECTION
        │
        ▼
STATIC INVESTIGATION FLOW
        │
        ▼
FINAL RESULT
```

The proposed system is:

```text
DETECTION
    │
    ▼
DYNAMIC ORCHESTRATION
    │
    ▼
SPECIALIZED AGENTS
    │
    ▼
EVIDENCE-DRIVEN INVESTIGATION
```

The comparison should use the same evaluation scenarios.

---

# 22. Baseline Comparison Metrics

Compare:

| Metric | Baseline | Project Sentinel |
|---|---|---|
| Detection Precision | Measured | Measured |
| Detection Recall | Measured | Measured |
| Evidence Recall | Measured | Measured |
| Conclusion Accuracy | Measured | Measured |
| Investigation Time | Measured | Measured |
| Workflow Success Rate | Measured | Measured |

The project should report measured results rather than assuming the advanced architecture is automatically better.

---

# 23. Investigation Time

Investigation duration can be measured as:

\[
InvestigationTime =
CompletedAt - StartedAt
\]

Average investigation time is:

\[
AverageTime =
\frac{\sum InvestigationTime}{TotalInvestigations}
\]

This metric should be interpreted carefully because AI processing time can vary based on model and hardware.

---

# 24. Failure Testing

The system must be tested under controlled failure conditions.

Important scenarios include:

```text
Database unavailable

AI model timeout

Invalid agent output

Capability failure

Malformed telemetry

Unexpected application exception
```

Each test should verify that the system:

1. Detects the failure.
2. Records the failure.
3. Avoids invalid state transitions.
4. Applies the appropriate retry or fallback policy.

---

# 25. LLM Failure Test

Example:

```text
AGENT REQUEST
     │
     ▼
LLM TIMEOUT
     │
     ▼
RETRY
     │
 ┌───┴────┐
 │        │
SUCCESS  FAILURE
 │        │
 ▼        ▼
CONTINUE  WAIT / ESCALATE
```

The test should verify that the system never silently treats a failed LLM operation as a successful investigation result.

---

# 26. Agent Output Validation Tests

Test invalid outputs such as:

- Missing required fields.
- Invalid confidence values.
- Unsupported actions.
- Incorrect schema structure.

Expected behavior:

```text
AGENT OUTPUT
     │
     ▼
SCHEMA VALIDATION
     │
 ┌───┴─────┐
 │         │
VALID    INVALID
 │         │
 ▼         ▼
CONTINUE  RETRY / FAIL SAFELY
```

---

# 27. Performance Testing

Performance testing should focus on practical MVP workloads.

The project should measure:

```text
API response time

Event processing time

Detection processing time

Investigation duration

Agent execution duration

Capability execution duration
```

The goal is not necessarily to achieve enterprise-scale throughput.

The goal is to establish measurable performance characteristics.

---

# 28. Performance Test Record

Each performance test should record:

```text
test_id
dataset_size
concurrent_requests
start_time
end_time
success_count
failure_count
average_latency
maximum_latency
```

This makes performance tests reproducible.

---

# 29. Dataset Validation

The selected dataset must be validated before it becomes the evaluation source.

Verify:

- Schema consistency.
- Required fields.
- Timestamp availability.
- Scenario labels or ground truth.
- Attack representation.

A dataset problem should not be incorrectly reported as a system failure.

---

# 30. Regression Testing

Whenever a major component changes, previously successful scenarios should be re-tested.

The regression suite should include:

```text
Telemetry normalization tests

Detection tests

API tests

Investigation workflow tests

Agent capability tests

Failure tests
```

The objective is to prevent improvements in one area from breaking another.

---

# 31. Test Environment

Testing should be separated conceptually from normal development.

Recommended environments:

```text
DEVELOPMENT
    │
    ▼
TEST / EVALUATION
    │
    ▼
DEMONSTRATION
```

The evaluation dataset and configuration should be versioned where practical.

This improves reproducibility.

---

# 32. Evaluation Experiment Design

Every major evaluation experiment should define:

### Input

What data or scenarios are used?

### Baseline

What conventional approach is being compared?

### Proposed Method

What Project Sentinel feature is being evaluated?

### Metrics

How is effectiveness measured?

### Result

What was observed?

The structure is:

```text
BASELINE
    │
    ▼
EVALUATION SCENARIOS
    │
    ▼
PROPOSED SYSTEM
    │
    ▼
METRICS
    │
    ▼
RESULT COMPARISON
```

---

# 33. Evaluation Report Template

Each final experiment should contain:

| Section | Content |
|---|---|
| Objective | What is being tested? |
| Dataset | What data was used? |
| Scenarios | Which cases were evaluated? |
| Baseline | What is the comparison method? |
| Proposed Method | What changed? |
| Metrics | What was measured? |
| Results | Measured outcomes |
| Analysis | Interpretation |
| Limitations | Known constraints |

This structure is suitable for the final project report and presentation.

---

# 34. MVP Testing Priority

The recommended testing sequence is:

## Phase 1 — Component Validation

```text
Telemetry normalization
Detection logic
Database operations
API validation
State transitions
```

## Phase 2 — Integration

```text
Ingestion → Detection
Detection → Alert
Alert → Investigation
Agent → Capability
```

## Phase 3 — End-to-End Workflows

```text
Attack scenario
     ↓
Detection
     ↓
Investigation
     ↓
Agent workflow
     ↓
Outcome
```

## Phase 4 — Evaluation

```text
Baseline run
     ↓
Project Sentinel run
     ↓
Metric calculation
     ↓
Result comparison
```

## Phase 5 — Reliability

```text
Dependency failures
Timeouts
Invalid output
Malformed input
Recovery behavior
```

---

# 35. Testing Acceptance Criteria

The project testing baseline is complete when:

### Functional Validation

- Core components pass defined tests.
- Detection scenarios produce expected outcomes.
- Investigation states behave correctly.

### Integration

- Major component boundaries are tested.
- Data moves correctly through the pipeline.

### End-to-End

- At least three realistic scenarios complete through the full workflow.
- Expected outcomes can be verified.

### Agent Evaluation

- Task completion is measured.
- Evidence quality is evaluated.
- Conclusion accuracy is evaluated separately.

### Orchestration

- Workflow success rate is measured.
- Agent usage is observable.
- Unnecessary workflow complexity can be identified.

### Reliability

- Major failure modes are tested.
- The system enters safe states when dependencies fail.

### Academic Evaluation

- A baseline is defined.
- The proposed system is evaluated using the same scenarios.
- Results are presented using measurable metrics.

---

# 36. Complete Validation Model

The complete Project Sentinel evaluation framework is:

```text
                         DATASET
                            │
                            ▼
                    TEST SCENARIOS
                            │
             ┌──────────────┴──────────────┐
             │                             │
             ▼                             ▼
         BASELINE                    PROJECT SENTINEL
             │                             │
             ▼                             ▼
        STATIC FLOW                AGENT ORCHESTRATION
             │                             │
             └──────────────┬──────────────┘
                            │
                            ▼
                       EVALUATION
                            │
          ┌─────────────────┼──────────────────┐
          │                 │                  │
          ▼                 ▼                  ▼
      DETECTION         INVESTIGATION       RELIABILITY
       METRICS           QUALITY             METRICS
                            │
                            ▼
                     FINAL COMPARISON
```

---

# 37. Final Design Principle

The strongest technical demonstration of Project Sentinel will not be:

> "The system uses multiple AI agents."

The stronger demonstration is:

> **"The system was evaluated against defined security scenarios and a baseline. Its detection, investigation quality, orchestration reliability, and operational performance were measured using reproducible metrics."**

The final evaluation philosophy is:

```text
IMPLEMENTATION
      +
TESTING
      +
MEASUREMENT
      +
BASELINE COMPARISON
      =
TECHNICALLY DEFENSIBLE RESULTS
```

---

# Next Document

The next recommended document is:

## Deployment, Environment & DevOps Specification

It will define the complete environment strategy for Project Sentinel, including Docker architecture, Docker Compose services, environment configuration, local development workflow, service dependencies, database migrations, startup sequencing, health checks, CI/CD readiness, and development-to-demonstration deployment procedures.
