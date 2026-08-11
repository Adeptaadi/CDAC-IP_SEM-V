# Agent Architecture Document (AAD)

**Project Name:** Agentic AI-powered Autonomous Cyber Threat Hunting Platform

**Version:** 1.0

**Status:** Draft

**Prepared By:** Solution Architecture Team

**Document Type:** Agent Architecture Document (AAD)

---

# Table of Contents

1. Executive Summary
2. Purpose
3. Agentic AI Philosophy
4. Architectural Principles
5. Agent Ecosystem
6. High-Level Architecture
7. Planning Agent
8. Planner Internal Components
9. Planner State Machine
10. Planner Responsibilities

---

# 1. Executive Summary

## 1.1 Purpose

This document specifies the autonomous intelligence architecture of the Agentic AI-powered Autonomous Cyber Threat Hunting Platform.

Unlike the Product Requirements Document (PRD), which defines product behavior from a user perspective, this document defines:

- autonomous reasoning
- agent collaboration
- decision making
- planning
- memory
- communication
- investigation lifecycle

This document acts as the architectural blueprint for implementing the Agentic AI platform.

---

## 1.2 Scope

The document defines

- Planning Agent
- Specialized Worker Agents
- Shared Investigation State
- Decision Policies
- Agent Communication
- Memory
- Knowledge Usage
- Investigation Lifecycle
- Explainability
- Human Oversight

Implementation technologies are intentionally excluded.

---

# 2. Purpose of the Agentic System

The purpose of the autonomous system is to transform isolated security telemetry into complete investigations through dynamic reasoning rather than fixed automation.

Traditional cybersecurity systems answer

"What alert occurred?"

Project Sentinel attempts to answer

"What happened?"

"Why did it happen?"

"What evidence supports this?"

"What should happen next?"

This requires reasoning instead of automation.

---

# 3. Agentic AI Philosophy

---

## 3.1 Traditional Automation

Traditional automation systems execute predefined workflows.

Example

```
Alert

↓

Rule A

↓

Rule B

↓

Rule C

↓

Done
```

Advantages

- predictable

Disadvantages

- rigid
- cannot adapt
- poor reasoning
- difficult to extend

---

## 3.2 Agentic Intelligence

Project Sentinel intentionally avoids predefined workflows.

Instead

every investigation begins with a goal.

The Planning Agent continuously determines

"What should happen next?"

This decision depends upon

- investigation state
- evidence
- confidence
- current hypothesis
- available knowledge
- previous agent outputs

Therefore

execution emerges dynamically.

---

## 3.3 Core Philosophy

The system is

Goal Driven

NOT

Workflow Driven

The planner continuously evaluates

```
Current Goal

↓

Current State

↓

Current Evidence

↓

Current Confidence

↓

Current Knowledge

↓

Next Best Action
```

This planning cycle repeats until the investigation completes.

---

## 3.4 Why Planner + Workers

Instead of creating one large AI model responsible for everything,

the platform separates responsibilities.

Planner

↓

Decision Making

Workers

↓

Execution

This separation improves

- explainability
- modularity
- maintainability
- extensibility

---

# 4. Architectural Principles

The architecture follows the following principles.

---

## Principle 1

Single Decision Authority

Only the Planning Agent decides

- what happens next
- which worker executes
- when investigation ends

Workers never control workflow.

---

## Principle 2

Specialized Intelligence

Each worker performs exactly one responsibility.

Examples

Detection

Correlation

Investigation

Reporting

Response

No overlapping responsibilities.

---

## Principle 3

Shared Investigation State

All agents collaborate through shared memory.

Agents do not communicate directly.

---

## Principle 4

Continuous Planning

Planning occurs after every meaningful investigation update.

Planning is not a one-time event.

---

## Principle 5

Explainability

Every planner decision must include

- reason
- evidence
- confidence
- selected agents

---

## Principle 6

Human Oversight

Human analysts may interrupt

pause

resume

override

or terminate

investigations.

---

## Principle 7

Knowledge-Grounded Reasoning

LLM reasoning shall be supported through retrieved cybersecurity knowledge.

The planner shall not depend solely upon model memory.

---

# 5. Agent Ecosystem

The platform consists of one intelligent orchestrator and multiple specialized workers.

```
                    Investigation Goal
                            │
                            ▼
                    Planning Agent
                            │
     ┌──────────────┬────────┼─────────┬────────────┐
     ▼              ▼        ▼         ▼            ▼
 Detection     Correlation Investigation Reporting Response
   Agent          Agent        Agent      Agent      Agent
                            │
                            ▼
                Shared Investigation State
                            │
                            ▼
                  Knowledge & Historical Memory
```

The planner continuously evaluates the investigation state.

Workers execute specialized tasks.

Workers never decide workflow.

---

# 6. High-Level Architecture

```
Continuous Security Events
            │
            ▼
 Event Normalization Layer
            │
            ▼
 Investigation Created
            │
            ▼
     Planning Agent
            │
    Selects Worker
            │
            ▼
 Specialized Worker
            │
 Updates Investigation State
            │
            ▼
     Planning Agent
            │
      Goal Complete?
      │            │
     No           Yes
      │            │
      ▼            ▼
 Continue      Report & Response
```

Notice

There is no predefined worker order.

The planner dynamically selects workers.

---

# 7. Planning Agent

---

## 7.1 Purpose

The Planning Agent represents the intelligence of the platform.

It is responsible for

- planning
- reasoning
- coordination
- decision making

The planner does not perform

- detection
- reporting
- investigation
- response

Instead

it delegates these responsibilities.

---

## 7.2 Responsibilities

Primary responsibilities include

- maintain investigation goals
- maintain investigation state
- assign tasks
- evaluate evidence
- update confidence
- revise hypotheses
- determine next actions
- escalate when necessary
- terminate investigations

---

## 7.3 Planner Inputs

The planner receives

- normalized events
- worker outputs
- investigation state
- historical investigations
- cybersecurity knowledge
- analyst actions

---

## 7.4 Planner Outputs

Planner decisions include

- selected worker
- investigation updates
- new goals
- revised confidence
- planner reasoning
- escalation requests
- report requests
- response requests

---

## 7.5 Planner Goals

The planner always maintains one or more investigation goals.

Examples

Determine whether attack exists.

Collect missing evidence.

Validate hypothesis.

Generate report.

Recommend containment.

Close investigation.

Goals change dynamically.

---

# 8. Planner Internal Components

The planner consists of several logical components.

```
                 Planning Agent
                       │
    ┌──────────────────┼────────────────────┐
    ▼                  ▼                    ▼
 Goal Manager     State Manager      Decision Engine
    │                  │                    │
    ├──────────────────┼────────────────────┤
    ▼                  ▼                    ▼
 Task Manager    Confidence Manager   Memory Manager
                       │
                       ▼
                Explainability Engine
```

---

## Goal Manager

Maintains

- current goals
- completed goals
- pending goals
- goal priorities

---

## State Manager

Maintains

- investigation state
- timeline
- active workers
- completed tasks
- pending tasks

---

## Decision Engine

Determines

- next worker
- next objective
- planner actions
- stopping conditions

---

## Confidence Manager

Maintains

overall investigation confidence.

Updates confidence whenever

- evidence changes
- hypotheses change
- workers complete

---

## Task Manager

Responsible for

creating

assigning

tracking

and completing worker tasks.

---

## Memory Manager

Provides planner access to

working memory

historical investigations

knowledge

planner history

---

## Explainability Engine

Generates explanations for

planner decisions

worker selection

confidence updates

investigation changes

---

# 9. Planner State Machine

```
Idle

↓

Receive Event

↓

Evaluate Investigation

↓

Select Goal

↓

Assign Worker

↓

Wait

↓

Receive Output

↓

Update State

↓

Goal Complete?

      │

No ─────────► Repeat Planning

      │

Yes

↓

Generate Report

↓

Recommend Response

↓

Waiting for Analyst

↓

Closed
```

Planner may return to

Evaluate Investigation

whenever new evidence arrives.

---

# 10. Planner Responsibilities

The planner is responsible for

✓ Investigation ownership

✓ Task scheduling

✓ Goal management

✓ Evidence evaluation

✓ Worker selection

✓ Memory management

✓ Hypothesis revision

✓ Confidence updates

✓ Investigation completion

✓ Escalation

The planner is NOT responsible for

✗ Detecting attacks

✗ Correlating events

✗ Writing reports

✗ Simulating containment

Those remain worker responsibilities.

---

# End of AAD Part 1

Next Part

11. Specialized Worker Agents

12. Shared Investigation State

13. Memory Architecture

14. Knowledge Architecture

15. Domain Objects

16. Agent Contracts

---

# 11. Specialized Worker Agents

## 11.1 Overview

Specialized Worker Agents execute domain-specific cybersecurity tasks delegated by the Planning Agent.

Worker agents are **execution units**, not decision-makers.

They perform well-defined responsibilities and return structured outputs to the Planning Agent.

Worker agents shall never:

- determine investigation workflow
- terminate investigations
- invoke other worker agents directly
- modify planner goals

Instead, every worker completes its assigned task and reports findings back to the planner.

---

# 11.2 Worker Design Principles

Every worker agent shall satisfy the following principles.

### Single Responsibility

Each worker owns one domain capability.

Examples

- Detection
- Correlation
- Investigation
- Reporting
- Response

---

### Stateless Execution

Workers should not permanently own investigation data.

Instead they receive

Investigation State

↓

Execute Task

↓

Return Results

↓

Release Resources

Persistent state belongs to the planner.

---

### Deterministic Outputs

Every worker returns a structured output.

Workers never return free-form responses.

---

### Explainability

Every conclusion produced by a worker shall include

- evidence
- confidence
- reasoning
- references

---

# 12. Detection Agent

---

## Purpose

Detect suspicious security activity from normalized telemetry.

The Detection Agent is responsible for identifying potential threats.

It does not determine whether an attack occurred.

It produces observations.

---

## Responsibilities

- Analyze incoming events
- Execute detection models
- Execute detection rules
- Calculate confidence
- Generate alerts

---

## Inputs

- Normalized Events
- Detection Models
- Detection Rules
- Historical Thresholds

---

## Outputs

```json
{
  "task":"Threat Detection",
  "status":"Completed",
  "confidence":0.87,
  "alerts":[...],
  "reason":"Multiple failed login attempts detected",
  "next_tasks":[
      "Correlation"
  ]
}
```

---

## Internal Components

```
Incoming Events

↓

Feature Extraction

↓

ML Detection

↓

Rule Evaluation

↓

Confidence Calculation

↓

Alert Generation

```

---

# 13. Correlation Agent

---

## Purpose

Determine relationships among alerts.

Transform isolated alerts into investigations.

---

## Responsibilities

- Merge related alerts
- Build attack chains
- Update timeline
- Maintain relationships
- Estimate incident severity

---

## Correlation Inputs

- Alerts
- Timeline
- Existing Investigations
- Historical Events

---

## Correlation Factors

Examples

- Source IP
- Destination IP
- Host
- Username
- Process
- Port
- Protocol
- Time Window
- Attack Category

---

## Output

```json
{
  "task":"Correlation",
  "merged_alerts":4,
  "confidence":0.91,
  "reason":"Same source IP within correlation window",
  "timeline_updated":true
}
```

---

# 14. Investigation Agent

---

## Purpose

Autonomously investigate suspicious activity.

This worker performs reasoning rather than detection.

---

## Responsibilities

- Collect evidence
- Retrieve historical context
- Build hypotheses
- Validate hypotheses
- Enrich investigation

---

## Inputs

Investigation State

Knowledge Base

Historical Incidents

Threat Intelligence

Planner Goal

---

## Evidence Sources

- Timeline
- Alerts
- MITRE ATT&CK
- Previous Incidents
- Playbooks
- Threat Intelligence

---

## Investigation Output

```json
{
 "task":"Investigation",
 "confidence":0.82,
 "hypothesis":"Credential compromise",
 "evidence":[...],
 "knowledge":[...],
 "recommendation":"Gather authentication logs"
}
```

---

# 15. Reporting Agent

---

## Purpose

Transform investigation state into explainable reports.

---

## Responsibilities

Generate

- Technical Report
- Executive Summary
- Timeline
- Evidence Summary
- MITRE Mapping
- Recommendations

---

## Output Structure

Executive Summary

↓

Investigation Summary

↓

Timeline

↓

Evidence

↓

Attack Analysis

↓

Recommendations

---

# 16. Response Agent

---

## Purpose

Recommend containment actions.

The Response Agent does not execute containment.

It simulates possible responses.

---

## Responsibilities

Recommend

- Block IP
- Disable Account
- Isolate Host
- Kill Process
- Password Reset

Estimate

- Risk
- Expected Impact
- Recovery Time

---

## Output

```json
{
 "recommended_action":"Block Source IP",
 "confidence":0.94,
 "impact":"Low",
 "requires_approval":true
}
```

---

# 17. Shared Investigation State

---

## Purpose

The Shared Investigation State represents the planner's understanding of an investigation.

Workers never own state.

They update it.

---

## Investigation Object

```
Investigation

├── Metadata

├── Goal

├── Status

├── Severity

├── Confidence

├── Evidence

├── Timeline

├── Hypotheses

├── Planner Decisions

├── Worker Outputs

├── Reports

└── Recommendations

```

---

## Investigation Metadata

Contains

- Investigation ID
- Creation Time
- Last Updated
- Priority
- Status

---

## Evidence Store

Contains

Evidence ID

Type

Source

Confidence

Timestamp

Collector

Validation Status

---

## Timeline Store

Stores

chronological events.

Timeline entries are immutable.

---

## Hypothesis Store

Stores

Current hypothesis

Previous hypotheses

Supporting evidence

Contradicting evidence

Confidence

Status

---

## Planner History

Stores

every planner decision.

Examples

Planner selected Investigation Agent.

Planner revised confidence.

Planner escalated incident.

---

## Worker History

Stores

every worker execution.

Input

Output

Execution Time

Confidence

Completion Status

---

# 18. Memory Architecture

The platform maintains two independent memory systems.

```
                Memory

          ┌─────────────┐

          ▼             ▼

 Working Memory     Long Term Memory

```

---

## Working Memory

Used during active investigations.

Contains

- Current Evidence
- Current Timeline
- Current Goals
- Current Tasks
- Active Workers
- Investigation Confidence

Updated continuously.

---

## Long Term Memory

Stores

Historical Incidents

Playbooks

MITRE ATT&CK

Threat Intelligence

Planner History

Closed Investigations

Used through retrieval.

---

# 19. Knowledge Architecture

Knowledge improves reasoning.

The planner retrieves knowledge rather than relying entirely on LLM memory.

---

## Knowledge Sources

Mandatory

MITRE ATT&CK

Response Playbooks

Historical Investigations

Optional

Threat Intelligence

Sigma Rules

CAPEC

---

## Knowledge Categories

```
Knowledge Base

├── MITRE

├── Historical Incidents

├── Playbooks

├── IOC Database

├── Sigma Rules

└── Threat Intelligence

```

---

## Retrieval Process

Planner

↓

Determine Knowledge Need

↓

Retrieve Relevant Knowledge

↓

Pass Context

↓

Worker Executes

↓

Planner Updates Investigation

---

# 20. Domain Objects

## Investigation

Central entity.

Contains

Everything known about one security incident.

---

## Evidence

Validated observation.

---

## Planner Decision

Represents one planning cycle.

---

## Worker Task

Represents work assigned by planner.

---

## Worker Result

Represents completed work.

---

## Knowledge Item

Represents retrieved cybersecurity knowledge.

---

# 21. Agent Contracts

Every worker must implement the following interface.

## Input Contract

```json
{
 "task_id":"",
 "investigation_id":"",
 "goal":"",
 "state":{},
 "context":{},
 "knowledge":[]
}
```

---

## Output Contract

```json
{
 "task_id":"",
 "status":"",
 "confidence":0.91,
 "observations":[],
 "evidence":[],
 "recommendations":[],
 "next_possible_tasks":[]
}
```

---

## Communication Rules

Workers communicate

ONLY

through

Shared Investigation State.

Workers never invoke other workers.

Planner remains the only orchestration authority.

---

# End of AAD Part 2

Next Part

22. Planning Cycle

23. Decision Policy

24. Goal Management

25. Task Lifecycle

26. Agent Communication Protocol

27. Planning Algorithms

28. Investigation Lifecycle

29. Sequence Diagrams


---

# 22. Planning Cycle

## 22.1 Overview

The Planning Cycle is the continuous reasoning loop executed by the Planning Agent.

Unlike traditional workflow systems where execution follows a predefined sequence, the Planning Agent continuously evaluates the investigation state and dynamically determines the next best action.

Every investigation is therefore adaptive.

---

## 22.2 Planning Objectives

The Planning Agent continuously attempts to satisfy one or more investigation goals.

Examples

- Determine if an attack exists.
- Collect sufficient evidence.
- Reduce uncertainty.
- Validate hypotheses.
- Recommend containment.
- Generate report.
- Close investigation.

Goals evolve throughout the investigation.

---

## 22.3 Planning Loop

```

Receive Update

↓

Read Investigation State

↓

Evaluate Goal Progress

↓

Evaluate Confidence

↓

Evaluate Missing Evidence

↓

Select Next Objective

↓

Select Worker

↓

Assign Task

↓

Wait

↓

Receive Result

↓

Update Investigation

↓

Goal Complete?

↓

No → Repeat

↓

Yes

↓

Generate Report

↓

Recommend Response

↓

Wait for Analyst

```

Planning continues until termination conditions are satisfied.

---

## 22.4 Planner Inputs

The planner evaluates

Current Investigation

Current Goal

Worker Outputs

Evidence

Confidence

Historical Knowledge

Analyst Feedback

Incoming Events

---

## 22.5 Planner Outputs

The planner may

Assign Worker

Update Goal

Revise Hypothesis

Increase Priority

Decrease Priority

Generate Report

Escalate Investigation

Recommend Response

Close Investigation

---

# 23 Decision Policy

---

## Purpose

The Decision Policy defines how the Planning Agent determines the next action.

The planner never follows hardcoded workflows.

Instead it continuously minimizes investigation uncertainty.

---

## Decision Inputs

Planner considers

Current Goal

Current Confidence

Evidence Completeness

Investigation Status

Knowledge Availability

Worker Recommendations

Analyst Actions

---

## Decision Priorities

Priority 1

Protect investigation integrity.

---

Priority 2

Reduce uncertainty.

---

Priority 3

Collect missing evidence.

---

Priority 4

Validate hypotheses.

---

Priority 5

Complete investigation efficiently.

---

## Example

Current State

```
Confidence

42%

↓

Missing Authentication Logs

↓

Hypothesis Weak
```

Decision

```
Assign Investigation Agent

↓

Collect Authentication Evidence
```

Another Example

```
Confidence

91%

↓

Evidence Complete

↓

Hypothesis Validated
```

Decision

```
Generate Report

↓

Recommend Response
```

---

# 24 Goal Management

---

## Purpose

Every investigation maintains one or more active goals.

Goals guide planner decisions.

Workers never create goals.

---

## Goal Lifecycle

```
Created

↓

Active

↓

Satisfied

↓

Archived
```

---

## Goal Types

Evidence Collection

Hypothesis Validation

Threat Confirmation

Attack Classification

Report Generation

Response Planning

Investigation Closure

---

## Goal Priority

Planner continuously reprioritizes goals.

Example

```
Collect Logs

Priority

Medium

↓

Credential Theft Detected

↓

Collect Authentication Logs

Priority

Critical
```

---

## Goal Completion

Planner evaluates

Evidence Available?

Confidence High?

Hypothesis Valid?

Knowledge Retrieved?

If yes

Goal complete.

---

# 25 Task Lifecycle

---

## Overview

Tasks represent work assigned to specialized worker agents.

Tasks are created only by the planner.

---

## Task Lifecycle

```
Created

↓

Queued

↓

Assigned

↓

Executing

↓

Completed

↓

Verified

↓

Archived
```

---

## Task Structure

Task ID

Task Type

Assigned Worker

Investigation ID

Goal

Priority

Deadline

Status

Dependencies

---

## Example

```
Task

↓

Collect Authentication Logs

↓

Worker

Investigation Agent

↓

Priority

High
```

---

# 26 Agent Communication Protocol

---

## Communication Philosophy

Workers never communicate directly.

Planner remains the central coordinator.

```
Worker

↓

Planner

↓

Worker
```

NOT

```
Worker

↓

Worker
```

---

## Why

Advantages

Simpler architecture

Explainability

Auditability

Centralized reasoning

Avoid conflicting decisions

---

## Message Types

Planner →

Worker

Task Assignment

---

Worker →

Planner

Task Result

---

Planner →

Dashboard

Investigation Update

---

Analyst →

Planner

Approval

Pause

Resume

Override

---

## Task Assignment Message

```
{
 task_id

 investigation_id

 goal

 priority

 context

 evidence

 knowledge

}
```

---

## Worker Result

```
{
 task_id

 status

 confidence

 evidence

 observations

 recommendation

 next_possible_tasks
}
```

---

# 27 Investigation Lifecycle

---

Unlike traditional incident management systems,

Project Sentinel maintains evolving investigations.

---

## Investigation States

```
NEW

↓

ACTIVE

↓

EVIDENCE COLLECTION

↓

CORRELATION

↓

REASONING

↓

REPORTING

↓

RESPONSE PLANNING

↓

WAITING FOR ANALYST

↓

CLOSED
```

---

New evidence

↓

Planner

↓

Reopen Investigation

---

## State Transitions

Planner exclusively controls transitions.

Workers never change investigation state.

---

## Example

```
ACTIVE

↓

Evidence Complete

↓

Planner

↓

REPORTING
```

---

Another Example

```
WAITING FOR ANALYST

↓

New Critical Evidence

↓

Planner

↓

ACTIVE
```

---

# 28 Planning Algorithms

---

The Planning Agent follows a reasoning cycle rather than an execution pipeline.

High-level algorithm

```
while investigation.active

    observe()

    update_state()

    evaluate_goal()

    evaluate_confidence()

    choose_worker()

    assign_task()

    wait()

    receive_result()

    update_memory()

end
```

---

## Worker Selection Strategy

Planner evaluates

Goal

↓

Missing Evidence

↓

Confidence

↓

Knowledge

↓

Worker Capability

↓

Best Worker

---

Example

```
Need

Timeline

↓

Investigation Agent
```

---

Need

Related Alerts

↓

Correlation Agent

---

Need

Executive Summary

↓

Reporting Agent

---

# 29 Investigation Memory Updates

Planner updates memory whenever

Worker completes task

↓

Evidence changes

↓

Hypothesis changes

↓

Confidence changes

↓

Timeline changes

↓

Knowledge retrieved

---

Memory update triggers

another planning cycle.

---

# 30 Sequence Diagram

```
Event

↓

Planner

↓

Detection Agent

↓

Planner

↓

Correlation Agent

↓

Planner

↓

Investigation Agent

↓

Planner

↓

Reporting Agent

↓

Planner

↓

Response Agent

↓

Dashboard
```

This is

NOT

a required sequence.

Planner chooses dynamically.

---

# 31 State Synchronization

Every planner cycle synchronizes

Current Investigation

Current Tasks

Evidence

Timeline

Confidence

Hypotheses

Reports

Recommendations

Historical Memory

Knowledge

Synchronization guarantees

all workers receive

the latest investigation context.

---

# 32 Planner Stopping Conditions

Planner terminates investigation only if

✓ Goal achieved

✓ Confidence exceeds threshold

✓ Evidence complete

✓ Report generated

✓ Response recommended

OR

Analyst terminates.

---

Planner does NOT stop because

one worker completed.

Planning continues until

investigation objective

is satisfied.

---

# End of AAD Part 3

Next Part

33. Confidence Model

34. Reasoning Model

35. Prompt Architecture

36. Tool Architecture

37. Knowledge Retrieval (RAG)

38. Explainability

39. Human Oversight

40. Failure Recovery

41. Future Agents

42. Architecture Summary


---

# 33. Confidence Model

## 33.1 Overview

The Confidence Model represents the planner's quantitative assessment of the reliability of the current investigation.

Confidence is not static.

It evolves continuously as new evidence is collected, hypotheses are validated, and specialized worker agents contribute additional observations.

Confidence influences every major planner decision.

Examples include

- Continue investigation
- Gather additional evidence
- Change hypothesis
- Generate report
- Recommend response
- Escalate to analyst

---

## 33.2 Confidence Philosophy

Confidence represents

> "How certain is the platform that the current understanding of the investigation is correct?"

Confidence is **not**

- probability of attack
- ML model probability
- LLM certainty

Instead it represents

Planner Confidence.

---

## 33.3 Confidence Scale

| Score | Interpretation |
|---------|---------------|
| 0–20 | Very Weak |
| 21–40 | Weak |
| 41–60 | Moderate |
| 61–80 | Strong |
| 81–100 | Very Strong |

---

## 33.4 Confidence Sources

Confidence is influenced by

Evidence Quality

↓

Evidence Quantity

↓

Correlation Strength

↓

Knowledge Match

↓

Worker Agreement

↓

Historical Similarity

↓

Planner Consistency

---

## 33.5 Confidence Updates

Planner recalculates confidence after

- Detection completed
- Correlation completed
- Evidence added
- Hypothesis updated
- Knowledge retrieved
- Analyst feedback
- New event received

---

## 33.6 Confidence Rules

Increase confidence when

- evidence supports hypothesis
- multiple workers agree
- MITRE mapping exists
- correlation succeeds

Decrease confidence when

- contradictory evidence appears
- evidence missing
- worker disagreement
- uncertain reasoning

---

## 33.7 Confidence Thresholds

Planner Behavior

| Confidence | Action |
|------------|--------|
| <40 | Continue investigation |
| 40–70 | Gather evidence |
| 70–85 | Validate hypothesis |
| >85 | Report & Recommend Response |

Thresholds remain configurable.

---

# 34. Reasoning Model

## 34.1 Purpose

The Reasoning Model defines how the platform transforms observations into conclusions.

Reasoning is evidence-driven.

The platform never jumps directly from

Alert

↓

Response

Instead

Alert

↓

Evidence

↓

Hypothesis

↓

Validation

↓

Conclusion

↓

Recommendation

---

## 34.2 Reasoning Pipeline

```
Observation

↓

Evidence Collection

↓

Knowledge Retrieval

↓

Hypothesis Generation

↓

Hypothesis Validation

↓

Confidence Update

↓

Decision

```

Although the reasoning pipeline is described sequentially, the planner may revisit any step based on new evidence.

---

## 34.3 Observation

Observations originate from

- Detection Agent
- Correlation Agent
- Investigation Agent
- Human Analyst

Observations do not imply attacks.

---

## 34.4 Evidence

Evidence is

validated

timestamped

traceable

Evidence supports reasoning.

---

## 34.5 Hypothesis

A hypothesis explains

"What attack most likely explains the evidence?"

Example

Credential Theft

Privilege Escalation

Lateral Movement

Data Exfiltration

Multiple hypotheses may coexist.

---

## 34.6 Validation

Validation asks

Does collected evidence support this hypothesis?

If no

Planner revises hypothesis.

---

## 34.7 Planner Reasoning Loop

```
Observe

↓

Understand

↓

Retrieve Knowledge

↓

Think

↓

Validate

↓

Decide

↓

Repeat
```

This repeats throughout the investigation.

---

# 35. Prompt Architecture

## 35.1 Philosophy

Each agent shall use a specialized prompt aligned with its responsibility.

Generic prompts are prohibited.

---

## 35.2 Planner Prompt

Planner prompts emphasize

Goal

State

Planning

Decision

Examples

Current Goal

Current Evidence

Current Confidence

Current Tasks

Available Workers

Select the next best worker and explain why.

---

## 35.3 Detection Prompt

Focus

Threat detection

Alert explanation

Confidence

---

## 35.4 Investigation Prompt

Focus

Evidence

Reasoning

Hypotheses

MITRE mapping

---

## 35.5 Reporting Prompt

Focus

Technical explanation

Executive summary

Timeline

Recommendations

---

## 35.6 Response Prompt

Focus

Containment

Impact

Risk

Approval requirement

---

# 36. Tool Architecture

## 36.1 Purpose

Agents extend their capabilities through tools.

LLMs reason.

Tools perform operations.

---

## 36.2 Planner Tools

Planner may use

Task Manager

Memory Manager

Knowledge Retriever

Worker Dispatcher

Confidence Calculator

---

## 36.3 Detection Tools

Detection Model

Rule Engine

Feature Extractor

---

## 36.4 Investigation Tools

MITRE Retriever

Timeline Builder

Historical Search

Evidence Collector

---

## 36.5 Reporting Tools

Report Generator

Timeline Formatter

PDF Export

Markdown Export

---

## 36.6 Response Tools

Playbook Retriever

Containment Library

Risk Calculator

---

# 37. Knowledge Retrieval (RAG)

## 37.1 Purpose

LLMs should reason using retrieved cybersecurity knowledge instead of relying solely on model parameters.

---

## 37.2 Knowledge Sources

Primary

MITRE ATT&CK

Historical Investigations

Response Playbooks

Secondary

Sigma Rules

Threat Intelligence

CAPEC

Future

CVE Database

---

## 37.3 Retrieval Flow

```
Planner

↓

Determine Knowledge Need

↓

Retriever

↓

Vector Search

↓

Relevant Documents

↓

Worker

↓

Reasoning

```

---

## 37.4 Retrieved Context

Context should include

Relevant Techniques

Previous Incidents

Recommended Playbooks

Supporting Evidence

Related Investigations

---

## 37.5 Context Limits

Only relevant knowledge should be retrieved.

Avoid unnecessary context.

---

# 38. Explainability Model

## 38.1 Goal

Every planner decision shall be explainable.

Analysts must understand

Why

How

Based on What

Confidence

---

## 38.2 Explainable Decision

Every decision includes

Decision

Reason

Supporting Evidence

Confidence

Knowledge References

Selected Worker

Timestamp

---

## 38.3 Explainable Reports

Reports shall include

Timeline

Evidence

Reasoning

MITRE Mapping

Recommendations

Confidence

---

## 38.4 Explainable Worker Outputs

Workers shall never return

"Attack Detected."

Instead

```
Reason

Evidence

Confidence

Suggested Next Task

```

---

# 39. Human Oversight

## 39.1 Philosophy

The platform is autonomous.

Not autonomous authority.

Analysts remain responsible for

approval

override

termination

---

## 39.2 Intervention Points

Analysts may

Pause Investigation

Resume Investigation

Approve Recommendation

Reject Recommendation

Modify Priority

Reopen Investigation

Terminate Investigation

---

## 39.3 Escalation

Planner escalates when

Confidence insufficient

Contradictory evidence

High-risk response

Analyst approval required

---

# 40. Failure Recovery

## Worker Failure

Planner

↓

Detect Failure

↓

Retry

↓

Assign Alternative Worker

↓

Escalate if required

---

## Planner Failure

Current Investigation State remains persisted.

Planner restarts using latest investigation snapshot.

---

## Memory Failure

Historical memory remains persistent.

Working memory reconstructed from latest checkpoint.

---

# 41. Future Agents

Future architecture supports

Threat Intelligence Agent

Malware Analysis Agent

Asset Context Agent

Risk Assessment Agent

Compliance Agent

Forensics Agent

Cloud Security Agent

Identity Analysis Agent

---

Each future agent follows the same architecture.

Input

↓

Task

↓

Output

↓

Planner

---

# 42. Architecture Summary

Project Sentinel adopts a **goal-driven, planner-centric, multi-agent architecture** designed for autonomous cybersecurity investigations.

The architecture intentionally separates

Decision Making

from

Task Execution.

One Planning Agent continuously reasons over an evolving Investigation State.

Specialized Worker Agents execute domain-specific tasks.

Workers never coordinate directly.

All collaboration occurs through Shared Investigation State managed by the planner.

This architecture provides

- Explainability
- Modularity
- Extensibility
- Human Oversight
- Continuous Planning
- Dynamic Investigation
- Evidence-Based Reasoning

Unlike workflow automation systems, Project Sentinel is fundamentally a **state-driven autonomous reasoning platform** capable of adapting its investigation strategy according to changing evidence rather than following predefined execution sequences.

---

# End of Agent Architecture Document (AAD)
