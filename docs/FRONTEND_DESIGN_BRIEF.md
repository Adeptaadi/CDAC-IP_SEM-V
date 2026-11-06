# Project Sentinel — Official Frontend Design Brief
**Document Version:** 1.0.0  
**Status:** Approved Product & UX Architecture Specification  
**Author:** Frontend Product & UX Architect  
**Target Audience:** Frontend Engineers, UI/UX Designers, Product Evaluators, SOC Architects  

---

## Executive Summary

Project Sentinel is an **autonomous, state-driven, multi-agent cybersecurity investigation platform**. Unlike conventional Security Information and Event Management (SIEM) tools or static Security Orchestration, Automation, and Response (SOAR) dashboards, Sentinel features an **adaptive Planner** that continuously assesses the operational state of an investigation, scores worker capabilities based on dynamic utility heuristics, incorporates discovered evidence, and reassesses subsequent actions until it produces a grounded recommendation for human authorization.

This document serves as the **official Frontend Design Brief**. It defines the core product philosophy, information architecture, visual hierarchy, non-negotiable principles, dynamic orchestration visualization rules, progressive disclosure levels, and the formal evaluation framework that will govern all future interface development.

> **CRITICAL DIRECTIVE:** No application code or UI components may be written until the three Agentic Investigation Workspace concepts are developed and evaluated against the criteria established in this brief.

---

# 1. Product Vision

### 1.1 The Defining Product Experience
> **"An investigation-first interface where the security threat is immediately understandable to human operators, while the non-linear depth and intelligence of the agentic system are progressively and truthfully revealed."**

Project Sentinel rejects the false dichotomy of modern security interfaces:
1. **The Telemetry Firehose (Traditional SIEM):** Dense grids of unranked logs and disjointed alert widgets that force the analyst to mentally construct the attack chain.
2. **The Black-Box Magic Chat (Generic AI Wrappers):** Unverifiable conversational interfaces that simulate human chatter, hallucinate chain-of-thought reasoning, and output ungrounded advice.

Sentinel establishes an **evidence-grounded cognitive workspace**. The interface translates complex autonomous agent orchestration into a calm, structured, and auditable investigation narrative.

### 1.2 The Seven Core Analyst Questions
Upon opening an investigation, the interface must answer seven sequential questions in decreasing order of urgency:
1. **What is happening?** (Attack category, threat description, severity)
2. **How serious is it?** (Critical / High / Medium / Low blast radius)
3. **What is affected?** (Target endpoints, users, credentials, services)
4. **What does the system currently know vs. suspect?** (Empirical facts vs. working hypotheses)
5. **What is the system doing right now?** (Active Planner capability, execution status)
6. **Why was this capability selected?** (Observable state trigger, utility ranking)
7. **What action is recommended, and what evidence proves it?** (Containment playbook, supporting evidence IDs, human approval gate)

---

# 2. Primary User & Evaluator Goals

The frontend interface must simultaneously serve three distinct operational personas without compromising clarity:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PROJECT SENTINEL PERSONAS                       │
├────────────────────┬────────────────────┬──────────────────────────────┤
│  TIER 1/2 SOC      │  SOC LEAD &        │  TECHNICAL EVALUATOR &       │
│  ANALYST           │  INCIDENT COMMANDER│  AI AUDITOR                  │
├────────────────────┼────────────────────┼──────────────────────────────┤
│ • 5-sec triage     │ • Blast radius     │ • Verify genuine orchestration│
│ • Clear hypothesis │ • Calibrated conf. │ • Inspect utility scoring    │
│ • Rapid action     │ • Timeline audit   │ • Trace state replans        │
│ • One-click HITL   │ • Legal provenance │ • Replay execution steps     │
└────────────────────┴────────────────────┴──────────────────────────────┘
```

### 2.1 Tier-1 / Tier-2 SOC Analyst (Operational Speed)
* **Goal:** Triage alerts rapidly, understand the scope of the compromise within seconds, review the agent's verified findings, and authorize or reject containment actions.
* **UX Expectation:** Minimalist typography, zero screen clutter, unambiguous severity indicators, and clear distinction between automated findings and required human approvals.

### 2.2 SOC Lead & Incident Commander (Strategic Context & Governance)
* **Goal:** Understand enterprise risk, review timeline evolution, verify that agent confidence is statistically calibrated, and export defensible forensic reports.
* **UX Expectation:** High-level summary views, entity blast-radius mapping, evidence chain of custody, and human sign-off audit logs.

### 2.3 Technical Evaluator & AI Auditor (Observability & Verification)
* **Goal:** Validate that Project Sentinel is a genuine state-driven multi-agent system rather than a smoke-and-mirrors script or hardcoded pipeline.
* **UX Expectation:** Transparent access to Planner decision traces, utility score factor breakdowns, replanning signals, confidence deltas ($\Delta C$), and step-by-step investigation replay.

---

# 3. Non-Negotiable Design Principles

Every component, interaction, and layout proposed for Project Sentinel must comply with the following six principles:

### Principle 1: One Primary Question Per Screen
* Eliminate "IDE Syndrome" (multiple competing panels, four simultaneous toolbars, split horizontal and vertical docks).
* Each viewport must focus on one dominant cognitive task. Secondary diagnostics must live in slide-over drawers or dedicated sub-views.

### Principle 2: Threat Before Telemetry
* Explain the incident before presenting raw technical artifacts.
* Never show an analyst raw packet payloads, JSON blobs, or syslog dumps until the threat summary, affected assets, and working hypothesis are clearly established.

### Principle 3: Planner Visibility Without Reasoning Overload
* Expose observable operational state:
  * Current cycle number
  * Selected worker capability (`investigation.execute`, `correlation.execute`, etc.)
  * Heuristic state trigger (e.g., *Stagnation counter = 2*, *Untriaged evidence > 5*)
  * Empirical confidence shift ($\Delta C = +0.142$)
  * Explicit replanning flags (`[REPLAN] Contradictory egress IP detected`)
* **Prohibited:** Never render fabricated LLM "inner monologue", fake stream-of-consciousness text, or speculative mental dialogue.

### Principle 4: Progressive Disclosure
* The interface must operate on a 3-tier depth model:
  * **Level 0 (Surface — 5-second scan):** Threat title, severity pill, target host, current hypothesis, top recommended containment action, high-level confidence bar.
  * **Level 1 (Operational — 30-second inspection):** Dynamic capability execution trace, evidence ledger with entity tags, active open questions, Planner decision rationale.
  * **Level 2 (Diagnostic — Deep dive):** Raw event JSON, MITRE ATT&CK technique breakdown, utility factor weights, ChromaDB RAG chunk references, database entity graph.

### Principle 5: Dynamic Orchestration Must Be Real
* The backend does **NOT** run a linear waterfall (`Detection → Correlation → Investigation → Response → Report`).
* The interface must never draw a static pipeline with misleading checkmarks.
* The UI must faithfully render the actual execution history: arbitrary order, repeated capabilities, skipped workers, and replanning branches.

### Principle 6: Action Is the Outcome
* Every investigation must converge toward a grounded recommendation.
* Containment recommendations must visually connect to the exact evidence items justifying the action.
* Destructive actions require explicit Human-in-the-Loop (HITL) authorization.

---

# 4. Product Information Architecture

The top-level navigation structure is deliberately constrained to four functional areas:

```text
PROJECT SENTINEL
│
├── 1. Threats
│   ├── Active Ingest Queue (Raw security alerts & anomalies)
│   ├── Prioritized Triage Matrix (Ranked by severity & confidence)
│   └── Threat Ingestion Sources (CIC-IDS2018 scenarios, live sensors)
│
├── 2. Investigations [PRIMARY PRODUCT CENTER]
│   ├── Agentic Investigation Workspace (Live active case)
│   ├── Evidence & Entity Graph Canvas
│   ├── Planner Cognitive Trace
│   └── Grounded Action & HITL Governance
│
├── 3. History
│   ├── Completed Investigations Archive
│   ├── Step-by-Step Investigation Replay Controller
│   └── Forensic Case Reports
│
└── 4. System
    ├── Agent Capability Registry & Health (5 Worker status)
    ├── Knowledge Base & RAG Index Status (ChromaDB)
    └── Empirical Benchmark Observability (P1 Validation Metrics)
```

> **ARCHITECTURAL RULE:** The **Investigation Workspace is the center of the product**. All other views exist solely to feed threats into the workspace, audit past workspace executions, or monitor the capabilities powering the workspace.

---

# 5. Core Investigation Experience

The core signature experience of Project Sentinel is the **State-Driven Autonomous Loop**. The UI must make this dynamic cycle transparent:

```text
               ┌───────────────────────────────┐
               │    SECURITY THREAT DETECTED   │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │  ESTABLISH INVESTIGATION STATE│
               │  (Seed initial telemetry/ev)  │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
         ┌────►│   PLANNER STATE EVALUATION    │
         │     │ (Evaluate knowns vs unknowns) │
         │     └───────────────┬───────────────┘
         │                     │
         │                     ▼
         │     ┌───────────────────────────────┐
         │     │  CAPABILITY UTILITY SCORING   │
         │     │ (Dynamic rank of 5 capabilities)
         │     └───────────────┬───────────────┘
         │                     │
         │                     ▼
         │     ┌───────────────────────────────┐
         │     │   SELECT HIGHEST CAPABILITY   │
         │     └───────────────┬───────────────┘
         │                     │
         │                     ▼
         │     ┌───────────────────────────────┐
         │     │      WORKER EXECUTES          │
         │     │  (Extracts evidence & links)  │
         │     └───────────────┬───────────────┘
         │                     │
         │                     ▼
         │     ┌───────────────────────────────┐
         │     │    INVESTIGATION STATE SHIFT  │
         │     │ (Confidence delta, new facts) │
         │     └───────────────┬───────────────┘
         │                     │
         └── [Not Terminal] ───┴─── [Terminal Condition Met]
                                         │
                                         ▼
                               ┌───────────────────┐
                               │ GROUNDED ACTION & │
                               │   HUMAN REVIEW    │
                               └───────────────────┘
```

### Deterministic State Triggers (Backend Ground Truth)
The Planner's non-linear behavior is governed by verifiable backend conditions:
* **Untriaged raw alerts exist:** `detection.execute` receives high utility.
* **Multiple disconnected entities exist without links:** `correlation.execute` is selected.
* **Low hypothesis confidence with unexplored host details:** `investigation.execute` is selected.
* **Confidence stagnates across cycles ($\Delta C < 0.02$) or contradictions emerge:** Planner triggers `[REPLAN]` and penalizes recent workers.
* **Confidence exceeds 0.80 or maximum cycles reached:** `response.execute` generates containment recommendations.

---

# 6. Required Workspace Information Hierarchy

The Investigation Workspace must structure and prioritize seven core data categories:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ A. THREAT SUMMARY                                                                      │
│ Threat Type · Severity Pill · Target Entity · Blast Radius · Status                    │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ B. CURRENT INVESTIGATION INSIGHT         │ C. PLANNER DECISION & ORCHESTRATION         │
│ • What is known (Verified Facts)         │ • Current Cycle Number (e.g. Cycle 4/6)     │
│ • What is unknown (Active Gaps)          │ • Selected Capability (e.g. correlation)    │
│ • Working Hypothesis                     │ • State Trigger / Decision Rationale        │
│ • Confidence Gauge (0.00 -> 1.00)        │ • Empirical Confidence Delta (+0.142)       │
│                                          │ • Dynamic Execution Trace (Non-linear list) │
├──────────────────────────────────────────┴─────────────────────────────────────────────┤
│ D. EVIDENCE & FINDINGS                   │ E. GROUNDED RECOMMENDATION & HITL           │
│ • Discovered Evidence Cards              │ • Specific Containment Action               │
│ • Entity Tags (Host, IP, User, Process)  │ • Direct Evidence Citations (EV-01, EV-04)  │
│ • Contradiction / Conflict Warnings      │ • Human Action Buttons [APPROVE] [REJECT]   │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

### Information Category Specifications:
* **A. Threat Summary:** Must be readable in under 3 seconds. Uses high-contrast semantic severity tokens (`rose-400` for Critical, `amber-400` for High).
* **B. Current Investigation Insight:** Synthesizes verified findings into a plain-English situation assessment. Shows the statistical confidence score backed by the 6-factor ConfidenceEngine.
* **C. Planner Decision:** Exposes the exact worker chosen, the mathematical confidence before and after execution, and the observable heuristic trigger.
* **D. Agent Orchestration:** Displays the actual chronological execution steps, showing capability transitions, repeated executions, and replanning events.
* **E. Evidence and Findings:** Ranked list of forensic artifacts. Each artifact displays its title, evidentiary confidence, MITRE ATT&CK technique tags, and affected entities.
* **F. Investigation Timeline:** Chronological timeline tracking every state change, alert, decision, and evidence yield from `t=0` to conclusion.
* **G. Recommendation:** Action-oriented card defining the containment protocol (e.g. *Network Isolation*, *Process Termination*), explicitly citing the supporting evidence records.

---

# 7. Dynamic Orchestration Visualization Rules

The interface must faithfully represent the non-linear execution of Project Sentinel without resorting to deceptive or simplified visual models.

### Rule 1: The Zero-Pipeline Mandate
* **Prohibited:** Never render a static horizontal pipeline such as:
  `Detection ➔ Correlation ➔ Investigation ➔ Response ➔ Reporting`
* **Permitted:** Render an **append-only, chronological execution stream** or an **adaptive state-transition graph** populated directly from `workspace.planner_trace`.

### Rule 2: Explicit Capability Revisit Badging
When the Planner re-selects a previously executed capability (e.g., calling `investigation.execute` at Cycle 1 and again at Cycle 4), the UI must explicitly badge the second occurrence:
$$\text{Investigation (Cycle 4)} \quad \longrightarrow \quad \text{\texttt{[REVISIT: 2nd Execution]}}$$
The card must state the state-driven trigger for the revisit (e.g., *"Re-investigating host following parent process linkage"*).

### Rule 3: Visual Signaling for Replanning & Contradiction Events
When the Planner detects stagnation or an evidence contradiction:
* The decision card must render an amber warning border (`border-amber-500/50`).
* A prominent badge `[REPLAN EVENT]` must appear.
* The state trigger must explicitly declare the root cause (e.g., *"Confidence stagnation: 3 cycles with delta < 0.02. Worker diversification enforced."*).

### Rule 4: Real Capability Utility Breakdown
When an evaluator expands a Planner decision step, the UI must reveal the comparative utility scores of all available workers at that cycle:
```text
Utility Scores at Cycle 3:
  • correlation.execute     0.94  [SELECTED - High entity unlinked ratio]
  • investigation.execute   0.42  [Deprioritized - Recent worker history]
  • response.execute        0.18  [Suppressed - Confidence < 0.80]
  • detection.execute       0.05  [Suppressed - Zero untriaged events]
```

---

# 8. Progressive Disclosure Strategy

To balance the conflicting demands of executive clarity and forensic auditability, Sentinel enforces three strict levels of progressive disclosure:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PROGRESSIVE DISCLOSURE LEVELS                   │
├────────────────────┬────────────────────┬──────────────────────────────┤
│  LEVEL 0: SURFACE  │  LEVEL 1: OPERATE  │  LEVEL 2: DIAGNOSE           │
│  (Always Visible)  │  (Default Panels)  │  (Slide-Over / Modal)        │
├────────────────────┼────────────────────┼──────────────────────────────┤
│ • Threat Title     │ • Working Hypoth.  │ • Raw Event JSON             │
│ • Severity Badge   │ • Planner Stream   │ • Entity Blast-Radius Graph  │
│ • Impacted Asset   │ • Evidence Ledger  │ • ChromaDB RAG References    │
│ • Top Action Card  │ • Replan Flags     │ • Utility Factor Formulas    │
│ • Confidence %     │ • Entity Tag Pills │ • Audit Log / Full PCAP      │
└────────────────────┴────────────────────┴──────────────────────────────┘
```

### Disclosure Mechanics:
1. **Level 0 (Surface):** Visible instantly without user interaction. Designed for 5-second situational awareness.
2. **Level 1 (Operational):** The main body of the Investigation Workspace. Cards have a compact default state showing 2-line summaries and key badges.
3. **Level 2 (Diagnostic):** Triggered on-demand by clicking an Evidence ID, Entity tag, or Utility badge. Opens an unobtrusive slide-over drawer from the right side of the screen (40% viewport width) without navigating away from the workspace.

---

# 9. Investigation Replay Requirements

A major demonstration differentiator of Project Sentinel is **True Investigation Replay**. Replay must not be a canned marketing video or mock animation; it must be an interactive walkthrough of real database state transitions.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ INVESTIGATION REPLAY CONTROLLER                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [◄ Previous]  [► Play / Pause]  [Next ►]   Cycle: 3 / 6   Speed: [1x] [2x] [Instant]  │
│ ═══════════════════════════════════════════════════════○═════════════════════════════  │
│ Step 1 (t=0)        Step 2 (t=12s)       Step 3 (t=25s)       Step 4 (t=42s)           │
│ Threat Ingestion    Investigation        Correlation [REPLAN] Response Ready           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Core Replay Capabilities:
1. **Deterministic State Reconstruction:** Scrubbing to Step $N$ restores the workspace view to the exact state it had at Step $N$ (confidence gauge, active evidence count, working hypothesis).
2. **State Delta Highlighting:** When advancing from Step $N-1$ to Step $N$, the UI visually flashes newly added evidence items in emerald and pulses the confidence gauge to show the exact delta ($\Delta C$).
3. **Replan Inspection:** Pausing at a replanning step displays a callout explaining:
   * What contradiction or stagnation occurred.
   * How utility scores shifted between Step $N-1$ and Step $N$.
   * Why the Planner altered its trajectory.

---

# 10. Prohibited Design Approaches (Anti-Patterns)

The following design patterns are strictly prohibited across all Project Sentinel interfaces:

| Prohibited Anti-Pattern | Reason for Prohibition | Enforced Sentinel Alternative |
|---|---|---|
| **1. The SIEM Telemetry Dump** | Floods analysts with thousands of unranked log lines. | Telemetry is strictly contained inside Level-2 slide-over drawers. |
| **2. Fixed Linear Pipelines** | Falsely implies a fixed 5-stage waterfall workflow. | Dynamic chronological decision feed or state graph. |
| **3. Fake AI Stream-of-Consciousness** | Fabricates "inner thinking" not grounded in backend code. | Structured decision cards showing explicit utility metrics and triggers. |
| **4. IDE Multi-Dock Overload** | Fragments screen into 5+ tiny panes where nothing is readable. | Single focused primary canvas with progressive slide-over panels. |
| **5. Ungrounded Action Buttons** | Presenting an "Isolate Host" button without evidence backing. | Action card displays direct citations to the evidence proving malice. |
| **6. Arbitrary Vanity Gauges** | Circular gauges without mathematical meaning. | Confidence gauges display values strictly computed by the ConfidenceEngine. |
| **7. Decorative Graph Clutter** | Massive hairball entity graphs with zero investigative utility. | Targeted entity blast-radius views scoped strictly to correlated assets. |
| **8. Disconnected Multi-Tab Mazes** | Forcing analysts to open 6 tabs to piece together one incident. | Unified 3-panel command posture (Threat $\rightarrow$ Planner $\rightarrow$ Evidence/Action). |

---

# 11. Open Design Decisions (For Validation in Concept Exploration)

The following design decisions involve valid architectural trade-offs and are deliberately left open for exploration across the three upcoming workspace concepts:

### OPEN DESIGN DECISION 1: Center Column Visualization Mode
* **Option A (Sequential Stream):** Vertical chronological cards showing decisions and outcomes (Linear / LangSmith style). High readability, low cognitive load, but becomes vertically long on 15+ cycles.
* **Option B (Spatial Node Graph):** Living state-machine canvas showing states as nodes and transitions as edges. High demonstration value and spatial clarity, but introduces panning/zooming cognitive overhead.
* **Option C (Dual-Mode Toggle):** Default to the chronological stream with a one-click header toggle to swap into the spatial graph view for executive briefings.

### OPEN DESIGN DECISION 2: Replay Controller Placement
* **Option A (Persistent Bottom Dock):** A fixed bottom scrubbing bar that remains visible throughout the investigation.
* **Option B (Modal / Dedicated Sub-View):** Replay is accessed via an "Investigation History & Replay" tab to keep the live workspace 100% focused on active triage.

### OPEN DESIGN DECISION 3: Entity Blast Radius Representation
* **Option A (Structured Entity Tag Cloud):** High-density pills with host, IP, and user icons indicating status.
* **Option B (Micro Entity Relationship Graph):** An interactive canvas embedded within the threat summary panel showing radial connections.

---

# 12. Preliminary Design Evaluation Framework

Every candidate workspace concept developed in the next sprint will be scored (1 to 5 points) across these seven standardized criteria:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                CONCEPT EVALUATION RUBRIC (35 POINTS TOTAL)             │
├──────────────────────────┬─────────────────────────────────────────────┤
│ 1. Investigation Clarity │ Can a user understand the threat and status │
│    (Weight: 15%)         │ within 5 seconds?                           │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 2. Cognitive Load        │ Is secondary diagnostic telemetry properly  │
│    (Weight: 15%)         │ deferred behind progressive disclosure?     │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 3. Agent Visibility      │ Can the user understand what the Planner is │
│    (Weight: 15%)         │ doing and why it selected this capability?  │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 4. Dynamic Truthfulness  │ Does the UI faithfully render non-linear,   │
│    (Weight: 20%)         │ repeated, or replanned execution paths?     │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 5. Evidence Grounding    │ Are all recommendations explicitly linked   │
│    (Weight: 15%)         │ to verified evidence records?               │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 6. Actionability         │ Is the next operational action immediately  │
│    (Weight: 10%)         │ clear and governed by human approval?       │
├──────────────────────────┼─────────────────────────────────────────────┤
│ 7. Demonstration Value   │ Does the layout compellingly showcase the   │
│    (Weight: 10%)         │ multi-agent differentiator to an evaluator? │
└──────────────────────────┴─────────────────────────────────────────────┘
```

---

# Conclusion & Next Phase

This Frontend Design Brief provides the authoritative product and UX foundation for Project Sentinel. It establishes clear visual, structural, and behavioral constraints while leaving strategic space for creative concept generation.

### Immediate Next Step
Execute **Sprint 2: Three Workspace Concepts Exploration**, generating three distinct architectural mockups and evaluating them against the 7 criteria in Section 12 to select the production design.
