# PROJECT SENTINEL
# Testing, Validation & Evaluation Strategy Specification

**Document ID:** PS-TEST-001  
**Version:** 1.0  
**Document Type:** Quality Assurance, Experimental Evaluation and Validation Specification  
**Status:** Proposed Architecture Baseline  
**Primary Focus:** Agent orchestration evaluation, multi-agent reliability, detection performance, investigation quality, reproducibility, benchmarking, and measurable system improvement.

---

# 1. Purpose

Project Sentinel is designed as an agentic cybersecurity investigation platform built around a Planner and specialized worker agents.

Its architecture is intended to support:

- Dynamic task planning.
- Intelligent agent selection.
- Non-linear investigation workflows.
- Evidence-driven investigation.
- Context-aware agent collaboration.
- Replanning when evidence is insufficient.
- Recovery from agent and capability failures.
- Human intervention.
- Evidence-backed incident reporting.
- Controlled response simulation.

These capabilities must be validated experimentally.

A system that successfully executes multiple agents is not necessarily a better system than a conventional detection pipeline.

The evaluation must establish whether the proposed architecture produces measurable improvements.

The central research question is:

> Does a dynamically orchestrated multi-agent investigation system produce more accurate, complete, reliable, explainable, and efficient cybersecurity investigations than conventional and simpler AI-assisted approaches?

This specification establishes how to answer that question.

---

# 2. Evaluation Objectives

Project Sentinel must be evaluated at five levels.

| Level | Evaluation objective |
|---|---|
| L1: Detection | Does the system correctly identify malicious activity? |
| L2: Agent | Does each specialized agent perform its assigned task correctly? |
| L3: Orchestration | Does the Planner select appropriate agents and manage execution effectively? |
| L4: Investigation | Does the complete investigation produce a correct, evidence-supported conclusion? |
| L5: System | Does the complete platform operate reliably and efficiently? |

The most important level for this project is L3.

The orchestration layer is the architectural differentiator. Therefore, its effectiveness must be measured independently rather than inferred from the final detection score.

---

# 3. Evaluation Philosophy

Evaluation must distinguish between three different things:

1. Whether the system detects an attack.
2. Whether the agents investigate it correctly.
3. Whether the orchestrator coordinates the investigation effectively.

For example:

A detection model might correctly identify a suspicious event, but the Planner might select an irrelevant agent, execute unnecessary tasks, or terminate the investigation before enough evidence is collected.

A single accuracy score would not reveal these problems.

The evaluation philosophy is:

```text
DETECTION PERFORMANCE
        +
AGENT PERFORMANCE
        +
ORCHESTRATION PERFORMANCE
        +
INVESTIGATION QUALITY
        +
OPERATIONAL RELIABILITY
        │
        ▼
COMPLETE SYSTEM EVALUATION
```

---

# 4. Evaluation Architecture

The evaluation framework should be implemented as an independent subsystem.

```text
                  EVALUATION FRAMEWORK
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      DATASET           BASELINES         TEST CASES
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                  EVALUATION RUNNER
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      DETECTION        AGENT TESTS     ORCHESTRATOR
       METRICS                           TESTS
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                  END-TO-END TESTS
                           │
                           ▼
                   METRIC ENGINE
                           │
                           ▼
                  RESULTS STORAGE
                           │
                           ▼
                 COMPARISON DASHBOARD
```

The evaluation subsystem should not be tightly coupled to the production investigation execution logic.

It should be able to execute repeatable experiments using controlled inputs and configurations.

---

# 5. Evaluation Dataset Strategy

The primary evaluation source should be the selected CSE-CIC-IDS2018 dataset, subject to verification of the actual available files, labels, and telemetry fields.

The evaluation system should maintain separate data categories.

| Data | Purpose |
|---|---|
| Training data | Train eligible detection models |
| Validation data | Select models and tune parameters |
| Test data | Measure final performance |
| Scenario data | Exercise investigation workflows |
| Ground truth | Establish expected outcomes |

The test dataset must not be used to tune the model or investigation logic.

## 5.1 Scenario Coverage

The initial scenario suite should cover representative attack categories.

| Scenario | Primary evaluation objective |
|---|---|
| Brute Force | Authentication-related detection and investigation |
| Web Attack | Network and application activity analysis |
| Botnet | Behavioral and communication pattern investigation |
| Infiltration | Multi-stage investigation and event correlation |
| Benign Activity | False-positive control |

These are proposed evaluation scenarios. Their actual availability and completeness must be confirmed against the selected dataset files.

## 5.2 Scenario Definition

Each scenario should have an explicit definition.

Example:

```json
{
  "scenario_id": "SCN-001",
  "scenario_name": "Brute Force Investigation",
  "dataset_id": "CSE-CIC-IDS2018",
  "scenario_version": "1.0",
  "attack_category": "Brute Force",
  "expected_detection": true,
  "expected_outcome": "malicious",
  "expected_evidence_categories": [
    "network",
    "authentication"
  ]
}
```

The expected evidence categories must be adapted to the telemetry actually available.

---

# 6. Ground Truth Specification

Ground truth represents the expected answer against which system output is evaluated.

It must be established independently of the AI-generated conclusion.

A ground-truth record should include:

```text
ground_truth_id
scenario_id
dataset_version

expected_class
expected_attack_category

expected_event_references
expected_evidence_references

expected_investigation_outcome
expected_attack_techniques

ground_truth_source
validation_status
```

Ground truth should distinguish between:

- Dataset-provided labels.
- Independently verified scenario annotations.
- Expected investigation outcomes.
- Expert-reviewed evidence relationships.

A dataset label is not automatically sufficient ground truth for every agent task.

For example, a flow-level attack label can establish whether a flow is malicious, but it does not necessarily establish which attack technique an agent should infer or what evidence relationship should be produced.

---

# 7. Data Splitting and Leakage Prevention

Evaluation must avoid data leakage.

Randomly splitting individual rows may produce overly optimistic results when related traffic from the same attack scenario appears in both training and test sets.

The preferred strategy is scenario-aware or time-aware separation where dataset structure permits it.

```text
AVAILABLE DATA
      │
      ▼
GROUP BY SCENARIO / TIME
      │
      ├─────────────┐
      ▼             ▼
TRAIN / VALIDATION  TEST
      │             │
      ▼             ▼
MODEL DEVELOPMENT  FINAL EVALUATION
```

Requirements:

1. Preserve attack scenario boundaries where possible.
2. Prevent duplicate or near-duplicate records from crossing partitions.
3. Fit preprocessing only on training data.
4. Tune hyperparameters using training and validation data.
5. Freeze the configuration before final test evaluation.
6. Record the split configuration and random seeds.

If the dataset does not support an appropriate independent split, this limitation must be documented rather than concealed.

---

# 8. Baseline Architecture Strategy

A proper evaluation requires multiple baselines.

The proposed system should not be compared only with a weak implementation.

The following baseline hierarchy is recommended.

## Baseline B0: Rule-Based Detection

A conventional rule-based detection implementation.

Purpose:

- Establish a basic non-ML detection baseline.
- Measure false-positive behavior.
- Establish a simple reference for detection performance.

## Baseline B1: Traditional Machine Learning

A supervised classification model trained on labeled network telemetry.

Candidate models:

- Random Forest.
- XGBoost.
- Logistic Regression.

Purpose:

- Establish traditional ML detection performance.
- Measure whether advanced orchestration adds value beyond a competent detector.

## Baseline B2: Single-Agent Investigation

One AI agent receives the alert and relevant evidence and produces an investigation result.

Purpose:

- Measure what can be achieved without multi-agent specialization.
- Establish the single-agent comparison baseline.

## Baseline B3: Fixed Multi-Agent Workflow

Specialized agents execute in a predetermined sequence.

Example:

```text
DETECTION
    │
    ▼
CORRELATION
    │
    ▼
INVESTIGATION
    │
    ▼
REPORTING
```

Purpose:

- Measure the value of multiple specialized agents without dynamic planning.

## Proposed P1: Planner-Based Multi-Agent Orchestration

The Planner dynamically selects workers based on investigation state, available evidence, task dependencies, and investigation objectives.

```text
              PLANNER
                 │
       ┌─────────┼─────────┐
       ▼         ▼         ▼
  CORRELATION INVESTIGATION RETRIEVAL
       │         │         │
       └─────────┼─────────┘
                 ▼
          UPDATED STATE
                 │
                 ▼
             REPLANNING
```

Purpose:

- Measure the benefit of dynamic agent selection.
- Measure the value of iterative investigation.
- Measure whether adaptive execution reduces unnecessary tasks.
- Measure whether evidence completeness improves.

**Important:** All baselines must use equivalent input data, equivalent ground truth, comparable model resources where possible, and the same evaluation conditions.

---

# 9. Primary Research Comparisons

The most important comparisons are:

| Comparison | Question |
|---|---|
| B0 vs B1 | Does ML improve detection over basic rules? |
| B1 vs B2 | Does AI investigation add value beyond detection? |
| B2 vs B3 | Does agent specialization improve investigation? |
| B3 vs P1 | Does dynamic orchestration improve fixed multi-agent execution? |
| P1 vs P1 without memory | Does investigation memory improve performance? |
| P1 vs P1 without RAG | Does retrieval improve investigation quality? |
| P1 vs P1 without replanning | Does iterative planning improve outcomes? |

These comparisons form the experimental foundation of the project.

---

# 10. Detection Evaluation

Detection performance should be measured using standard classification metrics.

The confusion matrix is:

| | Predicted Malicious | Predicted Benign |
|---|---:|---:|
| Actually Malicious | TP | FN |
| Actually Benign | FP | TN |

Where:

- TP: True Positive.
- FP: False Positive.
- TN: True Negative.
- FN: False Negative.

## 10.1 Accuracy

\[
Accuracy = \frac{TP+TN}{TP+TN+FP+FN}
\]

Measures the proportion of correctly classified observations.

## 10.2 Precision

\[
Precision = \frac{TP}{TP+FP}
\]

Measures how many predicted malicious observations are actually malicious.

## 10.3 Recall

\[
Recall = \frac{TP}{TP+FN}
\]

Measures how many actual malicious observations were detected.

## 10.4 F1 Score

\[
F1 = 2 \times
\frac{Precision \times Recall}
{Precision+Recall}
\]

Balances precision and recall.

## 10.5 False Positive Rate

\[
FPR = \frac{FP}{FP+TN}
\]

Measures the proportion of benign observations incorrectly flagged.

## 10.6 False Negative Rate

\[
FNR = \frac{FN}{FN+TP}
\]

Measures the proportion of malicious observations missed.

## 10.7 Example

Suppose:

```text
TP = 180
FP = 20
TN = 790
FN = 10
```

Then:

- Precision = 90%.
- Recall ≈ 94.74%.
- F1 ≈ 92.31%.
- Accuracy = 97%.
- FPR ≈ 2.47%.

These numbers are illustrative, not measured Project Sentinel results.

---

# 11. Class Imbalance Evaluation

Cybersecurity datasets commonly contain unequal proportions of benign and malicious observations.

Accuracy alone can therefore be misleading.

The evaluation should include:

- Macro F1.
- Weighted F1.
- Per-class precision.
- Per-class recall.
- Balanced accuracy.
- Confusion matrices.

Balanced accuracy is:

\[
BalancedAccuracy =
\frac{Sensitivity+Specificity}{2}
\]

where:

\[
Sensitivity = Recall
\]

\[
Specificity = \frac{TN}{TN+FP}
\]

For multi-class classification:

\[
MacroF1 = \frac{1}{K}\sum_{i=1}^{K}F1_i
\]

where \(K\) is the number of classes.

Macro F1 gives each class equal weight, which helps reveal poor performance on less frequent attack categories.

---

# 12. Correlation Agent Evaluation

The Correlation Agent should be evaluated on whether it correctly identifies relationships between security events.

Define:

- Correctly identified event relationships.
- Incorrectly identified event relationships.
- Missed expected relationships.

Then:

\[
CorrelationPrecision =
\frac{CorrectLinks}{CorrectLinks+IncorrectLinks}
\]

\[
CorrelationRecall =
\frac{CorrectLinks}{CorrectLinks+MissedLinks}
\]

\[
CorrelationF1 =
2 \times
\frac{CorrelationPrecision \times CorrelationRecall}
{CorrelationPrecision+CorrelationRecall}
\]

Additional metrics:

| Metric | Purpose |
|---|---|
| Event-link precision | Avoid false relationships |
| Event-link recall | Avoid missing real relationships |
| Timeline accuracy | Correct event ordering |
| Entity resolution accuracy | Correctly associate hosts, IPs, and users |
| Correlation latency | Measure execution time |

A relationship must be defined precisely before scoring it. For example, two events sharing an IP address are not automatically part of the same attack.

---

# 13. Investigation Agent Evaluation

The Investigation Agent should be evaluated on the correctness and completeness of its findings.

Recommended dimensions:

1. Hypothesis correctness.
2. Evidence selection quality.
3. Evidence coverage.
4. Contradiction recognition.
5. Conclusion correctness.
6. Uncertainty calibration.

## 13.1 Evidence Precision

\[
EvidencePrecision =
\frac{RelevantRetrievedEvidence}
{TotalRetrievedEvidence}
\]

## 13.2 Evidence Recall

\[
EvidenceRecall =
\frac{RelevantRetrievedEvidence}
{TotalExpectedRelevantEvidence}
\]

## 13.3 Evidence F1

\[
EvidenceF1 =
2 \times
\frac{EvidencePrecision \times EvidenceRecall}
{EvidencePrecision+EvidenceRecall}
\]

These metrics require a reviewed set of expected relevant evidence items.

## 13.4 Conclusion Accuracy

\[
ConclusionAccuracy =
\frac{CorrectConclusions}
{TotalEvaluatedConclusions}
\]

Conclusion correctness should be assessed against the scenario ground truth, with expert review for outcomes that are not directly represented by dataset labels.

---

# 14. Reporting Agent Evaluation

The Reporting Agent should produce structured, evidence-backed incident reports.

Evaluate the report at field level.

Recommended fields:

- Incident classification.
- Severity.
- Timeline.
- Affected entities.
- Supporting evidence.
- Attack technique mapping.
- Recommended actions.
- Limitations.

Define:

\[
FieldAccuracy =
\frac{CorrectRequiredFields}
{TotalRequiredFields}
\]

Also evaluate:

| Metric | Description |
|---|---|
| Evidence citation coverage | Proportion of material claims linked to evidence |
| Unsupported claim rate | Proportion of material claims without adequate support |
| Required field completeness | Proportion of required fields populated |
| Report consistency | Agreement between report and investigation state |

A grammatically polished report must not receive a high quality score if its conclusions are factually unsupported.

---

# 15. Response Agent Evaluation

For the MVP, response operations should be simulated.

Evaluation should focus on:

- Correct action recommendation.
- Policy compliance.
- Correct target identification.
- Appropriate approval requirement.
- Correct simulation result.

Define:

\[
ActionAccuracy =
\frac{CorrectRecommendedActions}
{TotalEvaluatedActions}
\]

Define policy compliance:

\[
PolicyCompliance =
\frac{PolicyCompliantActions}
{TotalAttemptedActions}
\]

Unauthorized or prohibited action attempts should be separately counted.

The system must never receive credit for executing an action merely because the action was attempted.

---

# 16. Planner Evaluation — Core Project Metric

The Planner is the central architectural component.

Its job is not simply to produce text or select an agent.

It must manage the investigation objective, state, task dependencies, available capabilities, execution outcomes, and termination conditions.

Planner evaluation must therefore cover multiple dimensions.

## 16.1 Task Selection Accuracy

Measures whether the Planner selected an appropriate next task.

\[
TaskSelectionAccuracy =
\frac{CorrectTaskSelections}
{TotalEvaluatedSelections}
\]

The expected task should be established using scenario-specific evaluation criteria and expert-reviewed acceptable alternatives.

## 16.2 Agent Routing Precision

\[
RoutingPrecision =
\frac{AppropriateAssignments}
{TotalAssignments}
\]

## 16.3 Agent Routing Recall

\[
RoutingRecall =
\frac{AppropriateAssignments}
{ExpectedAssignments}
\]

## 16.4 Planning Efficiency

Measures the proportion of executed tasks that contribute to the investigation objective.

\[
PlanningEfficiency =
\frac{UsefulCompletedTasks}
{TotalCompletedTasks}
\]

A useful task must be defined through evaluation annotations, not merely assumed from its successful execution.

## 16.5 Replanning Effectiveness

Measures whether replanning improves an incomplete or incorrect investigation state.

\[
ReplanningEffectiveness =
\frac{SuccessfulRecoveryEvents}
{EligibleReplanningEvents}
\]

## 16.6 Termination Accuracy

Measures whether the Planner terminates only when investigation conditions are satisfied.

\[
TerminationAccuracy =
\frac{CorrectTerminationDecisions}
{TotalTerminationDecisions}
\]

Premature termination and unnecessary continuation should be separately reported.

---

# 17. Orchestration Quality Score

A composite score may summarize multiple orchestration dimensions.

Define:

- \(R\): Routing quality.
- \(P\): Planning efficiency.
- \(C\): Completion correctness.
- \(F\): Failure recovery effectiveness.
- \(T\): Termination correctness.

Each metric is normalized to the interval \([0,1]\).

A proposed weighted score is:

\[
OQS = 0.25R + 0.20P + 0.25C + 0.15F + 0.15T
\]

Where:

\[
OQS \in [0,1]
\]

This is a proposed evaluation index, not an industry-standard metric.

The component scores must always be reported alongside OQS.

A high composite score must not conceal a severe weakness in routing or termination.

---

# 18. Investigation-Level Evaluation

The complete investigation should be evaluated independently of individual agents.

Recommended dimensions:

| Dimension | Evaluation question |
|---|---|
| Outcome correctness | Was the final incident classification correct? |
| Evidence completeness | Was sufficient evidence collected? |
| Investigation completeness | Were required investigation objectives satisfied? |
| Explainability | Can conclusions be traced to evidence? |
| Efficiency | Were unnecessary tasks avoided? |
| Reliability | Did the investigation complete without unrecovered failures? |

## 18.1 Investigation Success Rate

\[
ISR =
\frac{SuccessfulInvestigations}
{TotalInvestigations}
\times 100
\]

A successful investigation must satisfy predefined correctness and completeness criteria.

Merely reaching a `completed` state does not constitute success.

## 18.2 End-to-End Accuracy

\[
E2EAccuracy =
\frac{CorrectFinalOutcomes}
{TotalEvaluatedInvestigations}
\]

## 18.3 Evidence Completeness

\[
EvidenceCompleteness =
\frac{ExpectedEvidenceItemsFound}
{TotalExpectedEvidenceItems}
\]

## 18.4 Investigation Efficiency

\[
InvestigationEfficiency =
\frac{RequiredObjectivesCompleted}
{TotalExecutedTasks}
\]

This is a proposed efficiency indicator. It should be interpreted alongside task complexity and task cost.

---

# 19. Agent Reliability Evaluation

The evaluation should distinguish task quality from execution reliability.

## Task Success Rate

\[
TaskSuccessRate =
\frac{SuccessfullyCompletedTasks}
{TotalAttemptedTasks}
\times 100
\]

## Task Failure Rate

\[
TaskFailureRate =
\frac{FailedTasks}
{TotalAttemptedTasks}
\times 100
\]

## Retry Rate

\[
RetryRate =
\frac{TasksWithRetries}
{TotalTasks}
\times 100
\]

## Recovery Rate

\[
RecoveryRate =
\frac{RecoveredFailedTasks}
{EligibleFailedTasks}
\times 100
\]

These metrics should be reported separately for each agent type.

---

# 20. Latency and Resource Evaluation

Agentic architectures can introduce additional execution overhead.

Therefore, the evaluation must measure both performance and investigation quality.

Important measurements:

- Total investigation duration.
- Agent task duration.
- Planner decision duration.
- LLM response duration.
- Retrieval duration.
- Capability execution duration.
- Number of model calls.
- Number of agent tasks.
- Token consumption where available.

## 20.1 Mean Latency

\[
MeanLatency =
\frac{\sum_{i=1}^{N}Latency_i}{N}
\]

## 20.2 Median Latency

The middle value of sorted latency measurements.

This reduces the influence of extreme observations.

## 20.3 Percentile Latency

Report:

- P50.
- P90.
- P95.
- P99 where sample size supports it.

## 20.4 Model Calls per Investigation

\[
CallsPerInvestigation =
\frac{TotalModelCalls}
{TotalInvestigations}
\]

## 20.5 Tasks per Investigation

\[
TasksPerInvestigation =
\frac{TotalExecutedTasks}
{TotalInvestigations}
\]

These metrics help establish whether dynamic orchestration uses resources efficiently.

---

# 21. RAG Evaluation

RAG should be evaluated independently from the agent that consumes its results.

Recommended metrics:

| Metric | Purpose |
|---|---|
| Recall@K | Relevant documents found within top K |
| Precision@K | Relevant proportion of top K results |
| MRR | Rank of the first relevant result |
| nDCG@K | Ranking quality with graded relevance |
| Retrieval latency | Execution efficiency |
| Citation correctness | Whether claims are supported by retrieved sources |

## 21.1 Recall@K

\[
Recall@K =
\frac{RelevantDocumentsInTopK}
{TotalRelevantDocuments}
\]

## 21.2 Mean Reciprocal Rank

\[
MRR =
\frac{1}{Q}
\sum_{i=1}^{Q}\frac{1}{rank_i}
\]

Where \(rank_i\) is the rank of the first relevant result for query \(i\).

## 21.3 Retrieval Groundedness

Material claims in an agent response should be checked against the retrieved source material.

A groundedness evaluation should distinguish:

- Supported claims.
- Partially supported claims.
- Unsupported claims.
- Contradicted claims.

Automated LLM judging may be used as a supplementary measure, but important evaluation samples should receive human review.

---

# 22. Memory Evaluation

The system's investigation memory should be tested independently.

Important questions:

1. Can the system retrieve relevant information from previous investigations?
2. Does memory improve investigation performance?
3. Does irrelevant memory negatively affect decisions?
4. Does the system distinguish historical findings from current evidence?
5. Can stale information be identified?

A controlled experiment should compare:

```text
P1: ORCHESTRATION WITH MEMORY

P1-M: ORCHESTRATION WITHOUT MEMORY
```

Compare:

- Investigation accuracy.
- Evidence completeness.
- Investigation duration.
- Retrieval relevance.
- Incorrect reuse of historical information.

Memory should not automatically be considered beneficial simply because it increases the amount of available context.

---

# 23. Ablation Testing

Ablation testing is essential for identifying which architectural components contribute actual value.

The proposed architecture should be evaluated by removing one component at a time.

| Experiment | Removed component | What it measures |
|---|---|---|
| A1 | Dynamic Planner | Value of dynamic orchestration |
| A2 | Specialized agents | Value of role specialization |
| A3 | RAG | Value of external security knowledge |
| A4 | Investigation memory | Value of memory |
| A5 | Replanning | Value of iterative investigation |
| A6 | Event correlation | Value of cross-event reasoning |
| A7 | Structured evidence validation | Value of evidence constraints |

For each experiment, measure:

- Final investigation correctness.
- Evidence completeness.
- Orchestration quality.
- Execution time.
- Model calls.
- Failure rate.

The objective is to identify which components justify their complexity.

---

# 24. Controlled Failure Testing

A robust agentic system must handle failures.

Testing should intentionally introduce controlled failures.

| Failure | Expected behavior |
|---|---|
| LLM timeout | Retry or use an approved fallback |
| Agent failure | Record failure and replan |
| Retrieval unavailable | Mark knowledge retrieval unavailable |
| Database unavailable | Prevent unsafe state transitions |
| Invalid agent output | Reject invalid result |
| Capability denial | Record denial and continue safely where possible |
| Conflicting evidence | Request further investigation or human review |
| Repeated retry failure | Escalate or terminate safely |

The orchestrator should not interpret missing information as evidence that an attack did not occur.

---

# 25. Orchestration Stress Testing

The Planner should be tested under different investigation conditions.

Recommended test categories:

### Simple Investigation

One alert with sufficient evidence.

Expected behavior: minimal task execution.

### Multi-Event Investigation

Multiple related events.

Expected behavior: appropriate correlation and investigation.

### Incomplete Evidence

Insufficient evidence for a conclusion.

Expected behavior: additional task selection or explicit uncertainty.

### Conflicting Evidence

Different sources produce contradictory signals.

Expected behavior: further investigation or analyst escalation.

### Agent Failure

A selected worker cannot complete its task.

Expected behavior: recovery, alternative routing, or safe escalation.

### Complex Investigation

Multiple investigative objectives with dependencies.

Expected behavior: dynamic task scheduling and state-aware replanning.

The Planner should not execute the same number of tasks in every scenario.

---

# 26. Deterministic and Stochastic Testing

AI systems can produce variable results.

Testing must account for this.

Two testing modes should be supported.

## 26.1 Deterministic Tests

Use:

- Fixed inputs.
- Mock model responses.
- Controlled agent outputs.
- Fixed timestamps.
- Fixed execution dependencies.

Purpose:

- Validate state transitions.
- Validate routing rules.
- Validate retries.
- Validate task dependencies.
- Validate error handling.

## 26.2 Stochastic Tests

Use the configured real model and retrieval system.

Run repeated experiments to measure:

- Output variability.
- Routing consistency.
- Investigation consistency.
- Completion variability.
- Latency variability.

A stochastic experiment should record its model configuration and execution parameters.

---

# 27. Statistical Evaluation

A single execution is not sufficient to establish reliable performance for a variable AI system.

Repeated experiments should be used.

For a metric \(X\):

\[
Mean(X) = \frac{1}{N}\sum_{i=1}^{N}X_i
\]

Sample standard deviation:

\[
SD(X) =
\sqrt{
\frac{\sum_{i=1}^{N}(X_i-\bar X)^2}{N-1}
}
\]

A 95% confidence interval for a mean can be estimated as:

\[
\bar X \pm t_{0.975,N-1}
\frac{SD(X)}{\sqrt{N}}
\]

For sufficiently large samples, a normal approximation may be appropriate.

For comparisons between two systems:

- Use paired comparisons when both systems evaluate the same scenarios.
- Report effect sizes.
- Report confidence intervals.
- Use appropriate statistical tests.
- Avoid claiming improvement based only on small numerical differences.

For paired continuous measurements, a paired t-test may be suitable when its assumptions hold. Otherwise, use an appropriate non-parametric alternative.

For paired binary outcomes, consider McNemar's test.

---

# 28. Experimental Fairness

Every baseline comparison must control relevant variables.

The following should remain consistent wherever possible:

```text
Dataset Version
Scenario Selection
Input Events
Ground Truth
Hardware
Model Configuration
Evaluation Criteria
Timeout Limits
```

If a baseline uses a different model or computational budget, document the difference.

A comparison between a small local model and a substantially larger model should not be presented as evidence that orchestration alone caused the improvement.

---

# 29. Test Categories

The complete testing framework should contain the following test layers.

## 29.1 Unit Tests

Test individual functions and components.

Examples:

- Normalization.
- Detection scoring.
- Planner decision validation.
- Task creation.
- Evidence validation.
- State transition validation.

## 29.2 Integration Tests

Test interactions between components.

Examples:

- Planner to worker.
- Agent to capability.
- Agent to retrieval.
- Backend to PostgreSQL.
- Backend to Redis.
- Evidence persistence.

## 29.3 API Tests

Test:

- Authentication.
- Authorization.
- Request validation.
- Response contracts.
- Error handling.

## 29.4 Agent Tests

Test each specialist independently.

## 29.5 Orchestrator Tests

Test:

- Agent selection.
- Dependency management.
- Replanning.
- Retry limits.
- Termination.
- Human escalation.

## 29.6 End-to-End Tests

Test the complete workflow from dataset replay to final investigation outcome.

---

# 30. Test Case Schema

Every formal test should have a consistent record.

```json
{
  "test_id": "ORCH-001",
  "test_name": "Planner Replanning After Evidence Failure",
  "test_category": "orchestration",
  "scenario_id": "SCN-001",
  "preconditions": [
    "Investigation is active",
    "Initial evidence is insufficient"
  ],
  "input": {
    "investigation_id": "inv-test-001"
  },
  "expected_behavior": [
    "Planner identifies missing evidence",
    "Planner selects an appropriate additional task",
    "Investigation state is updated"
  ],
  "success_criteria": {
    "task_selected": true,
    "replanning_recorded": true,
    "investigation_remains_valid": true
  }
}
```

Test identifiers should remain stable across repeated runs.

---

# 31. Evaluation Run Schema

Every evaluation run should be reproducible.

Recommended schema:

```text
evaluation_run_id
experiment_id

dataset_id
dataset_version
scenario_version

system_version
orchestration_version
agent_versions

model_provider
model_name
model_parameters

rag_configuration
memory_configuration

random_seed
hardware_configuration

started_at
completed_at
run_status
```

The configuration should capture all variables that could materially affect the result.

---

# 32. Evaluation Result Schema

Each metric should be stored as an independently identifiable result.

```text
result_id
evaluation_run_id

metric_name
metric_category

metric_value
metric_unit

sample_count
confidence_interval_lower
confidence_interval_upper

measurement_status
```

Examples:

```json
{
  "metric_name": "planner_routing_precision",
  "metric_category": "orchestration",
  "metric_value": 0.91,
  "sample_count": 100,
  "measurement_status": "measured"
}
```

The value above is illustrative only.

The system should distinguish:

- Measured values.
- Estimated values.
- Manually reviewed values.
- Missing measurements.

---

# 33. Evaluation Results Dashboard

The evaluation interface should present results by architectural layer.

Recommended sections:

### Detection

- Accuracy.
- Precision.
- Recall.
- F1.
- False-positive rate.

### Agent Performance

- Task success.
- Task failure.
- Evidence precision.
- Evidence recall.
- Agent latency.

### Orchestration

- Routing precision.
- Planning efficiency.
- Replanning effectiveness.
- Termination accuracy.
- Orchestration quality score.

### Investigation

- End-to-end correctness.
- Evidence completeness.
- Investigation success rate.
- Average duration.

### Operational Performance

- Model calls.
- Agent tasks.
- Latency percentiles.
- Resource consumption.

---

# 34. Acceptance Thresholds

Thresholds must be established before the final evaluation.

They should not be selected retrospectively to make results appear successful.

A provisional engineering target table is:

| Metric | Initial target |
|---|---:|
| Detection macro F1 | ≥ 0.85 |
| Detection recall | ≥ 0.90 |
| Detection false-positive rate | ≤ 0.05 |
| Planner routing precision | ≥ 0.85 |
| Investigation evidence completeness | ≥ 0.85 |
| Structured agent output validity | ≥ 0.98 |
| Agent task success rate | ≥ 0.95 |
| Successful investigation rate | ≥ 0.90 |

**These are proposed project targets, not established performance claims or universal industry benchmarks.**

They must be refined after inspecting the actual dataset, task difficulty, model capabilities, and evaluation sample sizes.

For high-risk tasks, safety and policy compliance should be treated as hard requirements rather than averaged into a quality score.

---

# 35. Comparative Results Table

The final experimental report should contain a table similar to the following.

| Metric | B0 Rules | B1 ML | B2 Single Agent | B3 Fixed Multi-Agent | P1 Dynamic Planner |
|---|---:|---:|---:|---:|---:|
| Detection F1 | TBD | TBD | TBD | TBD | TBD |
| Investigation accuracy | TBD | TBD | TBD | TBD | TBD |
| Evidence completeness | TBD | TBD | TBD | TBD | TBD |
| Routing precision | N/A | N/A | N/A | Fixed | TBD |
| Task efficiency | TBD | TBD | TBD | TBD | TBD |
| Investigation duration | TBD | TBD | TBD | TBD | TBD |
| Model calls | N/A | N/A | TBD | TBD | TBD |
| Investigation success | TBD | TBD | TBD | TBD | TBD |

The final report must contain actual measurements, not assumed values.

---

# 36. Regression Testing

Every major architectural change should trigger regression testing.

Examples:

- Planner prompt changes.
- New agent implementation.
- New model.
- Retrieval configuration changes.
- Memory changes.
- Normalization changes.
- Detection model changes.
- Capability changes.

A previously successful investigation scenario should not silently become unsuccessful after a modification.

A versioned regression suite should be maintained.

---

# 37. Model Evaluation and Selection

Different models may perform differently on different tasks.

Model selection should therefore be task-specific.

Evaluate candidate models using:

- Structured output validity.
- Agent task correctness.
- Routing performance.
- Evidence groundedness.
- Reasoning consistency.
- Latency.
- Resource consumption.

The model that performs best at summarization is not necessarily the best Planner model.

A possible architecture is:

```text
                MODEL ROUTER
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       PLANNER    SPECIALIST   REPORTING
        MODEL       MODEL        MODEL
```

However, multiple models should only be introduced when evaluation demonstrates a measurable benefit over a simpler shared-model baseline.

---

# 38. Final End-to-End Evaluation Procedure

The final evaluation should follow a controlled procedure.

```text
STEP 1
Freeze dataset and scenario versions
        │
        ▼
STEP 2
Freeze system and model configuration
        │
        ▼
STEP 3
Execute baseline experiments
        │
        ▼
STEP 4
Execute dynamic orchestration experiments
        │
        ▼
STEP 5
Run repeated trials
        │
        ▼
STEP 6
Collect agent and orchestration metrics
        │
        ▼
STEP 7
Compare investigation outcomes
        │
        ▼
STEP 8
Perform statistical analysis
        │
        ▼
STEP 9
Perform error and failure analysis
        │
        ▼
STEP 10
Publish reproducible evaluation report
```

---

# 39. Evaluation Deliverables

The implementation should produce the following artifacts:

1. Dataset and scenario registry.
2. Ground-truth definitions.
3. Automated test suite.
4. Baseline implementations.
5. Agent-specific test suites.
6. Orchestrator evaluation suite.
7. Ablation experiment configurations.
8. Evaluation runner.
9. Metrics calculation module.
10. Evaluation results database.
11. Comparative results dashboard.
12. Reproducible experiment reports.

---

# 40. Definition of Success

Project Sentinel should be considered technically successful only when the following can be demonstrated:

### Detection

The detection layer performs reliably against known benign and malicious observations.

### Agent Specialization

Specialized agents perform their defined responsibilities with measurable quality.

### Orchestration

The Planner selects appropriate workers, manages dependencies, responds to failures, and terminates investigations correctly.

### Non-Linear Investigation

The system can revisit earlier investigative stages when new evidence changes the investigation state.

### Evidence

Important conclusions are supported by traceable evidence.

### Reliability

Failures do not silently produce incorrect conclusions.

### Efficiency

The proposed architecture provides a defensible quality-versus-cost improvement over appropriate baselines.

### Reproducibility

The evaluation can be repeated using recorded datasets, configurations, versions, and experiment definitions.

---

# 41. Final Evaluation Principle

The ultimate goal is not to demonstrate that Project Sentinel uses more agents, more models, or more sophisticated infrastructure.

The goal is to demonstrate that its architecture delivers better cybersecurity investigation outcomes.

The central research comparison is:

```text
CONVENTIONAL DETECTION
          │
          ▼
SINGLE-AGENT INVESTIGATION
          │
          ▼
FIXED MULTI-AGENT INVESTIGATION
          │
          ▼
DYNAMIC PLANNER-BASED ORCHESTRATION
          │
          ▼
COMPARATIVE EVALUATION
          │
          ▼
MEASURABLE IMPROVEMENT
```

The most important result should be evidence that dynamic orchestration provides benefits that simpler architectures cannot achieve as effectively.

**Project Sentinel's success must ultimately be demonstrated through measurable investigation quality, not architectural complexity alone.**

---

# Next Recommended Document

## Model Architecture, Selection & Optimization Specification

The next document should define the AI model architecture in greater technical detail.

It should cover:

1. Planner model selection.
2. Specialist agent model selection.
3. Local versus hosted models.
4. Model routing and selection policies.
5. Structured generation.
6. Function and tool calling.
7. Embedding model selection.
8. Reranking models.
9. Fine-tuning versus prompt engineering.
10. Model quantization.
11. GPU and CPU resource planning.
12. Model benchmarking.
13. Fallback models.
14. Model version management.
15. Model evaluation and replacement criteria.

This document will directly support the core orchestration architecture by defining which models should power which decisions and how their performance should be measured.
