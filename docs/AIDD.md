# AI Design Document (AIDD)

**Project Name:** Agentic AI-powered Autonomous Cyber Threat Hunting Platform

**Version:** 1.0

**Status:** Draft

**Document Type:** AI Design Document (AIDD)

---

# Table of Contents

1. Executive Summary
2. AI Objectives
3. AI Architecture
4. LLM Selection
5. Agent Intelligence Model
6. Planning Model
7. Worker Intelligence
8. RAG Architecture
9. Embedding Strategy
10. Memory Design
11. Prompt Engineering
12. Confidence Model
13. Reasoning Strategy
14. Evaluation Strategy
15. Safety
16. Future Improvements
```

---

# 1 Executive Summary

## Purpose

This document defines the Artificial Intelligence implementation strategy for the platform.

Unlike the SDD, which defines software engineering, this document specifies how intelligence is achieved through Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), embeddings, planning algorithms, and autonomous reasoning.

It defines:

- AI architecture
- reasoning methodology
- memory
- prompts
- retrieval
- confidence estimation
- evaluation

---

# 2 AI Objectives

The AI subsystem shall enable autonomous cybersecurity investigations while remaining explainable, auditable, and human-supervised.

The AI objectives are:

- understand security events
- formulate investigation goals
- coordinate worker agents
- retrieve cybersecurity knowledge
- generate evidence-backed conclusions
- recommend responses
- explain every decision

---

# 3 AI Architecture

## High-Level View

```
                    Security Events
                           │
                           ▼
                 Planning Agent (LLM)
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
 Detection Agent    Investigation Agent  Correlation Agent
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                     Shared Memory
                           │
                           ▼
                    RAG Knowledge Layer
                           │
                           ▼
                  Reporting / Response
```

---

## AI Components

| Component | Purpose |
|-----------|---------|
| Planner LLM | Decision making |
| Worker Agents | Specialized reasoning |
| Embedding Model | Semantic retrieval |
| Vector Store | Knowledge search |
| Confidence Engine | Investigation confidence |
| Memory Manager | Investigation context |

---

# 4 LLM Selection

## Primary Model

Recommended

Qwen 3 Instruct (local via Ollama)

Reasons

- Strong reasoning
- Good instruction following
- Efficient local inference
- Open weights

---

## Alternative Models

- Llama 3.x
- Gemma 3
- Mistral

The architecture remains model-independent.

---

## Model Responsibilities

The LLM is responsible for

- planning
- reasoning
- hypothesis generation
- explanation
- report drafting

The LLM is **not** responsible for

- persistent storage
- workflow execution
- database access
- event streaming

These remain software responsibilities.

---

# 5 Agent Intelligence Model

## Planner Intelligence

The planner operates as a stateful reasoning agent.

Inputs

- investigation state
- current goals
- evidence
- retrieved knowledge
- worker outputs

Outputs

- next task
- selected worker
- updated goal
- confidence adjustment
- explanation

---

## Worker Intelligence

Each worker receives

- task
- investigation context
- relevant knowledge
- planner objective

Workers return structured outputs rather than free-form text.

---

# 6 Planning Model

The planner follows a goal-oriented planning loop.

```
Observe

↓

Understand

↓

Retrieve Knowledge

↓

Evaluate Goal

↓

Select Worker

↓

Assign Task

↓

Receive Result

↓

Update State

↓

Repeat
```

Unlike chain-of-thought prompting, the planner exposes only explainable summaries suitable for analysts while internal reasoning remains encapsulated.

---

# 7 Worker Intelligence

Each worker uses a specialized reasoning strategy.

| Worker | Primary Capability |
|---------|-------------------|
| Detection | Threat identification |
| Correlation | Relationship discovery |
| Investigation | Evidence reasoning |
| Reporting | Structured summarization |
| Response | Containment recommendation |

Workers share a common execution contract but differ in prompts, tools, and retrieved context.

---

# End of AIDD Part 1


---

# 8 Retrieval-Augmented Generation (RAG) Architecture

## 8.1 Purpose

Large Language Models possess strong reasoning capabilities but lack access to continuously evolving cybersecurity knowledge.

To ensure factual, explainable, and up-to-date reasoning, the platform uses Retrieval-Augmented Generation (RAG).

The LLM never relies solely on its internal parameters.

Instead, relevant cybersecurity knowledge is retrieved dynamically before reasoning.

---

## 8.2 Objectives

The RAG subsystem provides

- Grounded reasoning
- Reduced hallucinations
- Explainable decisions
- Updated cybersecurity knowledge
- Historical investigation context

---

## 8.3 Knowledge Sources

The knowledge base consists of multiple collections.

```
Knowledge Repository

├── MITRE ATT&CK

├── Response Playbooks

├── Historical Investigations

├── Incident Reports

├── IOC Repository

├── Sigma Rules

├── CAPEC

└── Threat Intelligence
```

---

## 8.4 Retrieval Flow

```
Planner

↓

Determine Knowledge Need

↓

Generate Embedding

↓

Vector Search

↓

Rank Results

↓

Context Assembly

↓

Worker Agent

↓

Reasoning
```

---

## 8.5 Retrieval Strategy

Retrieval follows semantic similarity rather than keyword matching.

Example

Query

```
Multiple failed logins followed by PowerShell execution.
```

Retrieved Context

- MITRE T1110
- MITRE T1059
- Credential Access Playbook
- Previous Similar Incident

---

## 8.6 Context Assembly

Retrieved documents are ranked according to

Semantic Similarity

↓

Source Reliability

↓

Recency

↓

Relevance

Only the highest quality context is passed to the LLM.

---

# 9 Embedding Strategy

## Purpose

Embeddings transform cybersecurity knowledge into high-dimensional vectors suitable for semantic retrieval.

---

## Embedding Sources

MITRE

Historical Incidents

Playbooks

Threat Intelligence

Reports

---

## Embedding Pipeline

```
Document

↓

Chunking

↓

Cleaning

↓

Embedding Model

↓

Vector

↓

ChromaDB
```

---

## Chunking Strategy

Knowledge documents are divided into logical chunks.

Example

MITRE

Technique

↓

Procedure

↓

Mitigation

↓

Detection

rather than fixed-size chunks.

---

## Metadata

Each embedding stores

Document ID

Category

Source

Version

Tags

Reference

Confidence

---

## Embedding Refresh

Knowledge updates trigger

Re-Embedding

↓

Vector Update

↓

Index Refresh

---

# 10 Memory Design

## Overview

The AI architecture maintains multiple forms of memory.

```
Memory

├── Working Memory

├── Episodic Memory

├── Semantic Memory

└── Long-Term Memory
```

---

## 10.1 Working Memory

Stores

Current Investigation

Evidence

Current Goal

Current Tasks

Timeline

Hypothesis

Confidence

Worker Results

Planner Decisions

Working memory is updated after every planning cycle.

---

## 10.2 Episodic Memory

Represents completed investigations.

Stores

Investigation Summary

Outcome

Lessons Learned

MITRE Mapping

Final Confidence

Reports

Recommendations

---

## 10.3 Semantic Memory

Contains cybersecurity knowledge.

Examples

MITRE

Playbooks

Attack Patterns

Detection Rules

Threat Intelligence

---

## 10.4 Long-Term Memory

Persistent storage of

Historical investigations

Planner history

Worker history

Reports

Knowledge

---

## Memory Relationships

```
Working Memory

↓

Completed Investigation

↓

Episodic Memory

↓

Future Retrieval

↓

Planner
```

---

# 11 Prompt Engineering

## Philosophy

Every agent uses a role-specific system prompt.

Generic prompts are prohibited.

---

## Planner Prompt

Planner receives

Current Investigation

Current Goal

Evidence

Confidence

Knowledge

Worker Results

Task

Determine the next best action while minimizing investigation uncertainty.

Output only structured JSON.

---

## Detection Prompt

Objective

Determine whether observed events represent suspicious behavior.

Output

Alerts

Confidence

Explanation

Suggested Next Task

---

## Correlation Prompt

Objective

Determine relationships among alerts.

Output

Merged Events

Reason

Confidence

Timeline Updates

---

## Investigation Prompt

Objective

Develop and validate attack hypotheses.

Output

Evidence

Hypotheses

Knowledge References

Confidence

Missing Information

---

## Reporting Prompt

Objective

Generate

Technical Report

Executive Summary

Timeline

MITRE Mapping

Recommendations

---

## Response Prompt

Objective

Recommend containment actions.

Never execute containment.

Return

Action

Risk

Impact

Reason

Approval Requirement

---

## Prompt Constraints

Agents must

- remain factual
- reference evidence
- avoid unsupported assumptions
- produce structured output
- remain concise

---

# 12 Confidence Model

## Overview

Confidence represents the planner's trust in the current investigation.

Confidence is calculated using multiple independent factors.

---

## Confidence Factors

```
Detection Quality

+

Evidence Quality

+

Correlation Quality

+

Knowledge Match

+

Worker Agreement

+

Historical Similarity

↓

Overall Confidence
```

---

## Confidence Update Formula

Conceptually

```
Previous Confidence

+

Supporting Evidence

-

Contradictory Evidence

+

Knowledge Strength

↓

Updated Confidence
```

Actual implementation may use weighted scoring.

---

## Confidence Sources

Detection

Correlation

Investigation

Knowledge

Planner

Analyst Feedback

---

## Confidence States

Very Low

Low

Moderate

High

Very High

---

# 13 Reasoning Strategy

## Purpose

Reasoning transforms observations into explainable conclusions.

---

## Reasoning Cycle

```
Observe

↓

Collect Evidence

↓

Retrieve Knowledge

↓

Generate Hypothesis

↓

Validate Hypothesis

↓

Update Confidence

↓

Planner Decision
```

---

## Hypothesis-Based Reasoning

Instead of concluding immediately,

the platform generates one or more attack hypotheses.

Example

Hypothesis A

Credential Theft

Confidence

52%

Hypothesis B

Brute Force

Confidence

41%

Planner continues collecting evidence until one hypothesis dominates.

---

## Contradiction Handling

New evidence may

Strengthen

Weaken

Replace

Current hypotheses.

Planner continuously revises its understanding.

---

## Multi-Step Reasoning

Planner reasoning may involve multiple planning cycles.

Example

```
Cycle 1

Collect Logs

↓

Cycle 2

Retrieve MITRE

↓

Cycle 3

Validate Evidence

↓

Cycle 4

Generate Report
```

Each cycle improves investigation quality.

---

# 14 AI Evaluation Strategy

## Purpose

Evaluate AI quality rather than software correctness.

---

## Evaluation Metrics

### Planner Accuracy

Did the planner choose appropriate workers?

---

### Investigation Quality

Did the investigation collect sufficient evidence?

---

### Report Quality

Did reports contain

Evidence

Timeline

MITRE

Recommendations

---

### Hallucination Rate

Percentage of unsupported AI statements.

Target

Near Zero

---

### Retrieval Precision

Percentage of retrieved knowledge relevant to the investigation.

---

### Planner Efficiency

Average planning cycles per investigation.

---

### Worker Utilization

Distribution of worker executions.

---

### Confidence Calibration

Relationship between confidence and investigation correctness.

---

# 15 AI Safety

## Objectives

Prevent

Hallucinations

Unsafe recommendations

Unsupported conclusions

Unverifiable reports

---

## Safety Principles

Evidence before conclusions

Human approval

Knowledge grounding

Confidence reporting

Explainability

---

## Unsafe Response Handling

If evidence is insufficient

Planner shall

Continue Investigation

OR

Request Analyst Review

The planner shall never fabricate conclusions.

---

# 15.5 6-Factor Bayesian Explainability & Cognitive Streaming

To guarantee complete cognitive transparency, the AI subsystem decomposes every posterior confidence shift into 6 weighted factor deltas ($\sum_{i=1}^6 w_i \cdot \delta_i$) and streams real-time execution tokens:

1. **Detection Quality ($w_1 = 0.15$):** Reflects detector raw confidence $\times$ severity tier ($0.8 - 1.4$).
2. **Evidence Corroboration ($w_2 = 0.20$):** Multi-source diversity ratio and corroboration bonus ($1.2\times$).
3. **Correlation Graph Density ($w_3 = 0.15$):** Entity graph expansion ratio ($\text{edges} / \max(1, \text{nodes})$).
4. **Knowledge Retrieval Match ($w_4 = 0.15$):** RAG cosine similarity $\times$ source reliability weight (MITRE ATT&CK = $1.0$).
5. **Worker Agreement ($w_5 = 0.15$):** Inverse variance across independent worker confidence estimates.
6. **Historical Similarity ($w_6 = 0.20$):** Semantic proximity to validated historical cases in episodic memory.

Every cycle emits structured telemetry over WebSockets, updating the visual `FactorDecompositionView` and `AgentThoughtStream` in real time.

---

# 16 Future AI Improvements

Future versions may include

Graph Neural Networks

Knowledge Graphs

Multi-modal LLMs

Adaptive Planning

Self-Improving Planner

Automatic Prompt Optimization

Multi-Agent Debate

Continual Learning

Online Threat Intelligence

Federated Knowledge Sharing

---

# AI Design Summary

The AI subsystem combines

- Large Language Models
- Retrieval-Augmented Generation
- Shared Investigation Memory
- Planner-based reasoning
- Specialized worker agents
- Structured prompting
- Confidence estimation
- Explainability

to create an autonomous cybersecurity investigation platform capable of dynamic, evidence-driven decision making while remaining transparent and human-supervised.

---

# End of AI Design Document (AIDD)
