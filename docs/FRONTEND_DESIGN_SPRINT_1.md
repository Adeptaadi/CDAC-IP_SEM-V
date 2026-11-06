# Project Sentinel — Frontend Design Sprint 1
## Product Direction, Architectural Principles & Three Workspace Concepts

**Version:** 1.0.0  
**Date:** 2026-11-06  
**Status:** Approved Architectural Blueprint  
**Primary Objective:** Establish the frontend product direction and UX architecture centered around Project Sentinel's core differentiator: **an adaptive, state-driven, multi-agent investigation system guided by a dynamic Planner.**

---

# 1. Deliverable 1 — Frontend Design Direction

## 1.1 Product Philosophy

Current Security Operations Center (SOC) tooling suffers from two extremes:
1. **The Telemetry Dump:** Dense grids of raw logs, disconnected widgets, and alert firehoses where analysts must mentally reconstruct what happened (traditional SIEMs).
2. **The Black-Box Magic Chat:** Conversational LLM interfaces that hide execution history, fabricate reasoning, and output ungrounded advice with zero verifiable provenance.

**Project Sentinel establishes a third paradigm:**
> **An investigation-first cognitive workspace where the security threat is immediately understandable to human operators, while the non-linear depth and adaptive intelligence of the multi-agent system are progressively and truthfully revealed.**

Sentinel does not simulate an analyst through idle conversation; it is an **autonomous forensic engine** whose state transitions, capability selections, evidence discoveries, and decision rationales are observable, auditable, and grounded in cryptographic/database truth.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                             PROJECT SENTINEL                             │
│       "Threat Simple to Understand — Agentic Depth Progressively Exposed" │
└──────────────────────────────────────────────────────────────────────────┘
           ▲                                             ▲
           │                                             │
   LINEAR INSPIRATION                           CROWDSTRIKE INSPIRATION
   • Radical visual minimalism                  • Unambiguous threat urgency
   • Generous whitespace & low cognitive load   • Impacted blast radius & assets
   • Progressive disclosure on demand           • Action-oriented containment
           │                                             │
           ▼                                             ▼
   LANGSMITH INSPIRATION                        MICROSOFT SENTINEL INSPIRATION
   • Observable execution traces                • Entity relationship graphs
   • Decision rationale & utility scores        • Correlated forensic evidence
   • Step-by-step state transition replay       • Auditable chain of custody
```

---

## 1.2 Non-Negotiable Design Principles

Every component, view, and interaction in Project Sentinel must adhere to seven foundational rules:

### Principle 1: Threat Before Telemetry
Analysts must never be greeted with raw JSON or packet counts before answering:
- **What is the attack?** (e.g., *Ares Botnet Command & Control Beaconing*)
- **How severe is it?** (Critical / High / Medium / Low)
- **What is affected?** (Target hosts, accounts, services)
- **What does the system currently know?** (Verified facts vs. working hypotheses)
- **What is the current operational bottleneck?** (What is the Planner trying to resolve?)

### Principle 2: One Primary Question Per Screen
Eliminate "IDE Syndrome" (multi-panel split docks, four simultaneous toolbars, competing sidebars). The primary viewport must answer exactly one question at a time:
- *In Investigation Workspace:* "What is the threat, how is the Planner investigating it, and what action is recommended?"
- *In Forensic Drawer:* "What raw telemetry and entity connections support this finding?"
- *In Capability Inspector:* "Why did the Planner select Worker X over Worker Y at Step N?"

### Principle 3: Observable Planner Decisions Without Reasoning Hallucination
The UI must display **observable operational state**:
- Active capability (`investigation.execute`, `correlation.execute`, etc.)
- Capability utility scores (e.g., Correlation: 0.82, Investigation: 0.45)
- State triggers that drove the choice (e.g., *Stagnation counter = 2*, *Untriaged evidence count > 5*)
- Empirical confidence deltas ($\Delta C = +0.142$)
- Explicit replanning events (`[REPLAN] Detected contradictory egress IP`)

The UI must **never** render fabricated LLM "inner monologues" or simulate human thinking in places where deterministic backend rules made the choice.

### Principle 4: Progressive Disclosure
Interface hierarchy must follow a 3-layer depth model:
1. **Level 0 (Surface — 5-second scan):** Threat title, severity pill, current hypothesis, top recommended containment action, high-level confidence bar.
2. **Level 1 (Operational — 30-second inspection):** Dynamic capability execution trace, evidence ledger with entity tags, active open questions, Planner decision rationale.
3. **Level 2 (Diagnostic — Deep dive):** Raw event JSON, MITRE ATT&CK technique breakdown, utility factor weights, ChromaDB RAG chunk references, database entity graph.

### Principle 5: Dynamic Truthfulness (Zero Fake Pipelines)
The backend does **NOT** run a linear waterfall (`Detection → Correlation → Investigation → Response → Report`). 
The interface must **never** draw a static pipeline with misleading checkmarks. If the real execution was:
$$\text{Investigation} \longrightarrow \text{Correlation} \longrightarrow \text{Investigation} \longrightarrow \text{Response} \longrightarrow \text{Investigation}$$
the UI must render that exact sequence, clearly displaying why capabilities were revisited or why replanning occurred.

### Principle 6: Evidence-Grounded Recommendations
Every containment or remediation action must have direct clickable provenance:
$$\text{Recommendation} \xrightarrow{\text{grounded in}} \text{Evidence IDs} \xrightarrow{\text{derived from}} \text{Telemetry Events / Entity Links}$$
If an action cannot be tied to persisted evidence, the UI flags it as an ungrounded draft.

### Principle 7: Human Review as the Definitive Authority
Project Sentinel assists and accelerates; it does not unilaterally execute destructive response actions without authorization.
- System observations are marked `OBSERVED`.
- Agent hypotheses are marked `HYPOTHESIS (Confidence: X%)`.
- Containment recommendations are marked `REQUIRES HUMAN APPROVAL`.

---

## 1.3 Visual & Interaction System Direction

### 1.3.1 Color Palette & Semantic Tokens
Sentinel utilizes an ultra-refined dark theme palette engineered for extended SOC shifts with zero visual fatigue:

| Semantic Role | Token Class | Hex Value | Application |
|---|---|---|---|
| **Canvas Background** | `bg-zinc-950` | `#09090b` | Global root viewport background |
| **Card Surface** | `bg-zinc-900/80` | `#18181b` | Floating workspace cards with subtle 1px border |
| **Card Border** | `border-zinc-800` | `#27272a` | Clean, low-contrast structural dividers |
| **Text Primary** | `text-zinc-100` | `#f4f4f5` | Headings, threat titles, active hypotheses |
| **Text Secondary** | `text-zinc-400` | `#a1a1aa` | Metadata, timestamps, rationale descriptions |
| **Critical / Breach** | `text-rose-400 / bg-rose-950/40 border-rose-800` | `#f43f5e` | Active critical attacks, uncontained threats |
| **High Urgency** | `text-amber-400 / bg-amber-950/40 border-amber-800` | `#fbbf24` | Elevated risk, unresolved contradictions |
| **Medium / Notice** | `text-cyan-400 / bg-cyan-950/40 border-cyan-800` | `#22d3ee` | Triaged anomalies, active investigation step |
| **Verified / Safe** | `text-emerald-400 / bg-emerald-950/40 border-emerald-800` | `#34d399` | Contained threats, verified evidence, approved actions |
| **Planner / Cognitive** | `text-violet-400 / bg-violet-950/40 border-violet-800` | `#a78bfa` | Planner decisions, utility scores, replanning badges |

### 1.3.2 Typography Rules
- **Sans-Serif (`font-sans` — Inter / Geist):** Used for all human-readable content: titles, threat summaries, explanations, button labels, and status badges.
- **Monospace (`font-mono` — JetBrains Mono / Fira Code):** Strictly reserved for machine identifiers: IPs (`18.218.115.60`), hostnames (`UBUNTU-SRV-01`), hashes, UUIDs, process command lines, and MITRE technique codes (`T1059.001`).

### 1.3.3 Motion & Transitions
- Micro-transitions: `150ms ease-out` for hover states and button presses.
- State progressions: `300ms cubic-bezier(0.16, 1, 0.3, 1)` for expanding drawers and adding evidence cards.
- Pulse indicators: Subtle 2-second ease-in-out breathing animation for active running capabilities (`animate-pulse`). Never use frantic blinking.

---

## 1.4 What the Interface Must Avoid (Anti-Patterns)

| Anti-Pattern | Why It Fails | Sentinel Enforcement |
|---|---|---|
| **Fixed Linear Pipeline** | Falsely implies a fixed 5-step sequence; collapses when Planner revisits workers or skips steps. | Render dynamic timeline / state-graph generated strictly from `PlannerDecision` records. |
| **The Raw Telemetry Firehose** | Floods the screen with 1,000 log lines; exhausts the operator before the threat is understood. | Telemetry is hidden behind Evidence summary cards; accessible only via slide-over drawer. |
| **The "AI Magic Chatbot" Box** | Misrepresents deterministic backend rules as conversational LLM chatter; impossible to audit. | Structured cognitive cards with explicit utility scores, factor weights, and trigger rationale. |
| **IDE Dock Clutter (5+ split panes)** | Fragmented screen real estate where no single panel has sufficient reading width. | Single focused workspace canvas with slide-over inspection drawers. |
| **Ungrounded Action Buttons** | "Isolate Host" button without direct visual links to the evidence justifying why the host is malicious. | Action cards display explicit evidence citations and confidence thresholds required for approval. |

---

# 2. Deliverable 2 — Three Distinct Workspace Concepts

To determine the optimal interface architecture, three distinct UX models were developed, each offering a fundamentally different mental model of the investigation.

---

## 2.1 Concept 1: The Linear Investigation Journal (Narrative & Sequential State Flow)

### 2.1.1 Mental Model
Inspired by **Linear** and **Sublime Text**. An investigation is treated as an **evolving forensic chronicle**. The page is structured as a calm, vertical, chronological stream of state-change events. Each entry in the journal documents:
- What state the investigation was in
- What decision the Planner made and why
- What worker executed and what evidence it unearthed
- How the system's confidence shifted

### 2.1.2 Layout Structure
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  SENTINEL  /  INV-2026-0892: Ares Botnet C2 Beaconing              [CRITICAL]  [LIVE]  │
├───────────────────────────────────────────────────────────────┬────────────────────────┤
│                                                               │  INVESTIGATION SUMMARY │
│  CHRONOLOGICAL INVESTIGATION JOURNAL                          │  Target: 192.168.1.104 │
│                                                               │  Attacker: 13.58.225.34│
│  ┌─────────────────────────────────────────────────────────┐  │  Confidence: 84.5%     │
│  │ STEP 1 · THREAT DETECTED                     10:00:15   │  │  Status: Triaged       │
│  │ Initial trigger: 12 periodic outbound SSL handshakes    │  │                        │
│  │ Evidence seeded: 5 network flow records                 │  ├────────────────────────┤
│  └─────────────────────────────────────────────────────────┘  │  GROUNDED ACTION CARD  │
│                               │                               │  [!] Host Containment  │
│                               ▼                               │  Sever active sockets  │
│  ┌─────────────────────────────────────────────────────────┐  │  on WORKSTATION-04     │
│  │ STEP 2 · PLANNER DECISION: INVESTIGATION     10:00:18   │  │                        │
│  │ Rationale: Untriaged host entity with low confidence.   │  │  Evidence Grounding:   │
│  │ Selected: investigation.execute (Utility: 0.88)         │  │  • EV-01: C2 Beacon    │
│  │ Result: Identified process powershell.exe (PID 4812)    │  │  • EV-04: Encoded cmd  │
│  │ Confidence: 0.150 ──> 0.320 (+0.170)                    │  │                        │
│  └─────────────────────────────────────────────────────────┘  │  [ APPROVE ACTION ]   │
│                               │                               │  [ REJECT / DISMISS ]  │
│                               ▼                               │                        │
│  ┌─────────────────────────────────────────────────────────┐  │                        │
│  │ STEP 3 · REPLAN EVENT · CONTRADICTION        10:00:24   │  │                        │
│  │ Egress destination resolved to legitimate CDN ASN.      │  │                        │
│  │ Planner Trigger: Contradiction penalty applied.         │  │                        │
│  │ Selected: correlation.execute (Utility: 0.94)           │  │                        │
│  │ Result: Correlated parent process WINWORD.EXE (Macro)   │  │                        │
│  │ Confidence: 0.320 ──> 0.580 (+0.260)                    │  │                        │
│  └─────────────────────────────────────────────────────────┘  │                        │
│                               │                               │                        │
│                               ▼                               │                        │
│  [+ 3 Subsequent Autonomous Planning Steps Collapsed]         │                        │
│                                                               │                        │
└───────────────────────────────────────────────────────────────┴────────────────────────┘
```

### 2.1.3 Primary User Journey
1. **At-a-Glance Orientation:** The user lands on the page and reads the sticky right column: Threat Severity, Target Host, Current Hypothesis, and the Grounded Action Card.
2. **Reviewing the Narrative:** The user scrolls the central journal. Each card explains the cause-and-effect loop: *Planner assessed state $\rightarrow$ selected worker $\rightarrow$ worker returned finding $\rightarrow$ confidence updated*.
3. **Inspecting Decision Depth:** Clicking any step expands a drawer detailing the exact utility scores across all 5 capabilities at that moment in time.
4. **Authorizing Action:** The user reviews the evidence linked directly under the action card and clicks `Approve Containment`.

### 2.1.4 Orchestration Visualization
- Rendered as a continuous vertical timeline connected by directional pulse rails.
- Re-selected capabilities appear naturally as subsequent journal entries (e.g., Step 2: Investigation, Step 3: Correlation, Step 4: Investigation again).
- Replanning and contradiction events are highlighted with amber accent tags (`[REPLAN]`).

### 2.1.5 Progressive Disclosure Strategy
- **Collapsed by Default:** Routine worker steps show a 2-line summary (*"Investigation completed in 42ms. 3 new artifacts linked"*).
- **Expanded on Click:** Inline disclosure exposes raw artifacts, process tree snippets, and the utility score table.

---

## 2.2 Concept 2: The Adaptive Cognitive Canvas (Spatial State-Machine & Node Graph)

### 2.2.1 Mental Model
Inspired by **LangSmith**, **Figma**, and **n8n**. The investigation is modeled as a **living state-machine canvas**. The central mental model is spatial: the investigation state is a central node that evaluates conditions and emits directional execution nodes across iterations.

### 2.2.2 Layout Structure
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  SENTINEL CANVAS  /  INV-2026-0892: Ares Botnet C2  ·  Cycle 5/6  ·  Confidence: 84.5% │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  TOP THREAT BANNER: Critical | Target: WORKSTATION-04 (192.168.1.104) | Ares C2 Beacon │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  DYNAMIC AGENT EXECUTION GRAPH                                                         │
│                                                                                        │
│  [ State 0 ] ──> [ Planner: Select ] ──> [ Investigation ] ──> [ 3 Evidence Nodes ]   │
│                         │                                            │                 │
│                         │ (State Update: Conf = 0.32)                │                 │
│                         ▼                                            ▼                 │
│                  [ State 1 ] ──> [ Planner: Replan ] ──> [ Correlation ]               │
│                         │          (Contradiction)                   │                 │
│                         │                                            ▼                 │
│                         │ (State Update: Conf = 0.58)        [ Macro Parent Link ]     │
│                         ▼                                            │                 │
│                  [ State 2 ] ──> [ Planner: Select ] ──> [ Investigation (Revisit) ]   │
│                         │                                            │                 │
│                         ▼                                            ▼                 │
│                  [ State 3 ] ──> [ Planner: Terminal ] ──> [ Response Recommendation ] │
│                                                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│  BOTTOM DRAWER (INSPECTOR)                                                             │
│  [Active Node: Planner Replan (State 1)]                                               │
│  • Trigger: Stagnation = 2, Unresolved Contradiction in Destination IP                │
│  • Utility Scores: Correlation: 0.94 | Investigation: 0.42 | Response: 0.11           │
│  • Decision Outcome: Switched from Host Inspection to Network-Parent Correlation       │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2.3 Primary User Journey
1. **Top Banner Context:** User reads the high-level threat status.
2. **Exploring the Graph:** The user navigates a horizontal/vertical node graph showing every iteration. Loops and revisits are clearly visible as directional edges looping back to capability nodes.
3. **Inspecting Nodes:** Clicking any node in the graph instantly updates the bottom inspector panel, revealing input state, utility weights, execution latency, and output findings.
4. **Action Trigger:** The terminal node in the graph is styled as a glowing emerald action node that opens the human review modal.

### 2.2.4 Orchestration Visualization
- Pure graph topology. Worker capabilities are discrete node types with distinct icons and colors.
- True non-linear journeys are visually obvious: if the Planner calls `investigation`, then `correlation`, then `investigation` again, the canvas draws node $A_1 \rightarrow B_1 \rightarrow A_2$ with clear causal links.

### 2.2.5 Progressive Disclosure Strategy
- Canvas level: High-level nodes with status pills and execution latencies.
- Inspector drawer level: Full JSON payload, ChromaDB similarity chunks, and confidence factor breakdowns.

---

## 2.3 Concept 3: The Threat-Centric Triad (Balanced SOC Command Workspace)

### 2.3.1 Mental Model
Inspired by **CrowdStrike Falcon**, **Microsoft Sentinel**, and modern developer observability tools. The workspace is divided into three purposeful, synchronized vertical columns representing the three fundamental questions of an investigation:
1. **Left: What is happening?** (Threat context, entity scope, confidence trajectory, current hypothesis)
2. **Center: What is the system doing?** (Planner decision feed, active capability, execution history, replanning signals)
3. **Right: What requires action?** (Forensic evidence ledger, grounded recommendations, human review controls)

### 2.3.2 Layout Structure
```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  PROJECT SENTINEL  │  INV-2026-0892: Ares Botnet C2 Beaconing  │  Target: WORKSTATION-04  │  [CRITICAL] │
├───────────────────────────────┬────────────────────────────────────────┬───────────────────────────────┤
│  COLUMN 1: THREAT & STATE     │  COLUMN 2: ADAPTIVE PLANNER STREAM     │  COLUMN 3: EVIDENCE & ACTION  │
│                               │                                        │                               │
│  [ THREAT OVERVIEW ]          │  [ ACTIVE PLANNER STATUS ]             │  [ GROUNDED RECOMMENDATION ]  │
│  Severity: CRITICAL           │  Status: Awaiting Human Action         │  Action: Host Network Sever   │
│  Category: Botnet C2          │  Cycles Elapsed: 6 / 6                 │  Confidence: 84.5% (High)     │
│  MITRE: T1071.001, T1059.001  │  Last Selection: response.execute      │  Status: PENDING APPROVAL     │
│                               │                                        │                               │
│  [ CONFIDENCE TRAJECTORY ]    │  [ DECISION TRACE (CHRONOLOGICAL) ]    │  [ APPROVE ]  [ REJECT ]      │
│  0.15 ──> 0.85 (+0.70)        │                                        │                               │
│  ██████████████░░░░  84.5%    │  ┌──────────────────────────────────┐  │  [ SUPPORTING EVIDENCE (18) ] │
│  State: High Confidence       │  │ Cycle 6 · response.execute       │  │                               │
│                               │  │ Rationale: Confidence > 0.80     │  │  • EV-14 (Network Socket)     │
│  [ ENTITY IMPACT (3) ]        │  │ Generated containment plan       │  │    192.168.1.104:49210 ->      │
│  • Host: WORKSTATION-04       │  └──────────────────────────────────┘  │    13.58.225.34:443 (Periodic)│
│  • User: corp\jdoe            │  ┌──────────────────────────────────┐  │                               │
│  • Process: powershell.exe    │  │ Cycle 5 · investigation.execute  │  │  • EV-11 (Process Command)    │
│                               │  │ [REPLAN] Revisit capability      │  │    powershell.exe -Enc SQ...  │
│  [ WORKING HYPOTHESIS ]       │  │ Extracted C2 beaconing interval  │  │    Parent: WINWORD.EXE (4108) │
│  "Ares botnet payload dropped │  └──────────────────────────────────┘  │                               │
│  via Word macro executing     │  ┌──────────────────────────────────┐  │  • EV-08 (File Dropped)       │
│  hidden PowerShell beacon."   │  │ Cycle 4 · correlation.execute    │  │    invoice_august.docm        │
│                               │  │ Linked WINWORD to powershell     │  │    Zone.Identifier = Internet │
│                               │  └──────────────────────────────────┘  │                               │
│                               │  [ View Earlier Cycles (1-3) ]         │  [ + Open Full Evidence Tab ] │
└───────────────────────────────┴────────────────────────────────────────┴───────────────────────────────┘
```

### 2.3.3 Primary User Journey
1. **Immediate Context (Col 1):** In under 3 seconds, the analyst absorbs the attack classification, affected asset, current hypothesis, and overall confidence.
2. **Observing Agent Logic (Col 2):** The center column shows how the system arrived here. The user inspects the latest decisions, observing the transition from Investigation to Correlation and back to Investigation.
3. **Evaluating Action (Col 3):** The right column presents the recommended response, explicitly linked to the key evidence items directly below it.
4. **Executing Authorization:** The analyst reviews the correlated parent process evidence and hits `Approve`.

### 2.3.4 Orchestration Visualization
- Reverse-chronological or forward-scrubbable vertical card deck in Column 2.
- Each card highlights: Cycle number, Worker badge, Decision trigger, and Confidence shift ($\Delta C$).
- Re-selections and revisits display an explicit badge: `Revisit (2nd Execution)`.

### 2.3.5 Progressive Disclosure Strategy
- Column 1: Clicking any entity (e.g., `WORKSTATION-04`) opens an Entity Blast-Radius popover.
- Column 2: Clicking any decision card opens the Capability Utility Breakdown modal showing why other workers scored lower.
- Column 3: Clicking an evidence row slides over the raw telemetry event viewer.

---

# 3. Deliverable 3 — Comprehensive Evaluation & Recommendation

## 3.1 Systematic Evaluation Matrix

Each concept was evaluated against the 8 architectural criteria defined in the sprint brief:

| Criterion | Evaluation Question | Concept 1: Linear Journal | Concept 2: Cognitive Canvas | Concept 3: Threat-Centric Triad |
|---|---|:---:|:---:|:---:|
| **1. Threat Clarity** | Can the user understand the threat immediately? | Good (4/5) | Fair (3/5) | **Exceptional (5/5)** |
| **2. Cognitive Load** | Is unnecessary information hidden or deferred? | **Exceptional (5/5)** | Fair (2/5) | Good (4/5) |
| **3. Investigation Clarity** | Can the user understand what changed and why? | **Exceptional (5/5)** | Good (4/5) | **Exceptional (5/5)** |
| **4. Planner Visibility** | Are decisions understandable without hidden reasoning? | Good (4/5) | **Exceptional (5/5)** | **Exceptional (5/5)** |
| **5. Dynamic Truthfulness** | Does it accurately support non-linear execution? | **Exceptional (5/5)** | **Exceptional (5/5)** | **Exceptional (5/5)** |
| **6. Evidence Visibility** | Can important claims be traced to evidence? | Good (4/5) | Fair (3/5) | **Exceptional (5/5)** |
| **7. Actionability** | Is the next recommended action clear? | Good (4/5) | Fair (3/5) | **Exceptional (5/5)** |
| **8. Demonstration Value** | Would this effectively showcase Project Sentinel? | Good (4/5) | **Exceptional (5/5)** | **Exceptional (5/5)** |
| **Total Score** | *(Out of 40)* | **35 / 40** | **29 / 40** | **38 / 40** |

---

## 3.2 In-Depth Trade-Off Analysis

### Concept 1: The Linear Investigation Journal
- **Strengths:** 
  - Lowest cognitive load of all concepts; reading a top-to-bottom journal is natural and intuitive.
  - Exemplary progressive disclosure; feels like modern developer tools (Linear / GitHub Issues).
  - Perfectly models cause-and-effect over time.
- **Weaknesses:**
  - In lengthy investigations (15+ cycles), the page becomes very tall and requires excessive vertical scrolling.
  - Threat context and action cards compete for space in a secondary sidebar.
- **Best Use Case:** Post-incident audits, forensic reporting, and historical case review.

### Concept 2: The Adaptive Cognitive Canvas
- **Strengths:**
  - Highest visual impact for technical demonstrations and agentic AI conferences.
  - Graph topology makes branching, loops, and revisits instantly recognizable as spatial paths.
- **Weaknesses:**
  - High cognitive load; graph canvases require panning, zooming, and spatial orientation that slows down rapid incident response.
  - Evidence and recommendations are relegated to a secondary drawer, separating action from context.
- **Best Use Case:** R&D debugging, model developers tuning planner utility formulas, and academic presentations.

### Concept 3: The Threat-Centric Triad
- **Strengths:**
  - Best alignment with real-world SOC operational speed: Threat context on the left, Planner observability in the center, Grounded action on the right.
  - Zero panning or scrolling required to understand the immediate state of the world.
  - Directly binds the recommended action to the evidence supporting it in the same column.
- **Weaknesses:**
  - Requires disciplined screen real-estate allocation across the three columns to avoid feeling crowded on displays below 1280px width.
- **Best Use Case:** Primary operational SOC investigations and live incident response.

---

## 3.3 Recommended Product Direction: The Synthesized Hybrid

Rather than adopting a single concept in isolation, **the recommended direction is a synthesized hybrid that combines the structural power of Concept 3 (The Threat-Centric Triad) with the narrative fidelity of Concept 1 and the spatial replay power of Concept 2.**

### The Synthesized Architecture:
1. **Core Workspace View:** **Concept 3 (The Triad)** serves as the default operational view:
   - **Left Panel (25% width):** Threat Context, Entity Impact Scope, Confidence Gauge, and Working Hypothesis.
   - **Center Panel (45% width):** The Adaptive Planner Stream (from Concept 1's clean journal card pattern) displaying the real, chronological sequence of capability decisions, rationale triggers, and $\Delta C$ updates.
   - **Right Panel (30% width):** Grounded Action Card with explicit 1-click approval, supported by the Evidence & Finding ledger.
2. **Integrated Replay & Graph Mode (from Concept 2):**
   - An interactive toggle in the header (`[ Timeline Stream ] <──> [ Canvas Graph ]`) allows the center panel to swap between the chronological narrative stream and the spatial node graph for executive presentations or deep architectural auditing.
3. **Slide-Over Forensic Drawer:**
   - Clicking any evidence badge or planner utility score slides over an unobtrusive Level 2 diagnostic drawer without navigating away from the workspace.

---

# 4. Deliverable 4 — Preliminary Component Map

To prepare for implementation without creating technical debt or monolithic files, the future frontend will be organized into modular, single-responsibility components adhering to strict TypeScript types.

```
frontend/src/
├── api/
│   ├── workspaceClient.ts          # Consumes GET /api/investigations/{id}/workspace (P0 API)
│   ├── evaluationClient.ts         # Consumes GET /api/evaluation/runs and summary (P1 API)
│   └── reviewClient.ts             # POST /api/investigations/{id}/review (HITL approval)
│
├── types/
│   ├── workspace.ts                # TypeScript interfaces matching backend UnifiedWorkspaceProjection
│   └── evaluation.ts               # TypeScript interfaces matching backend Evaluation schemas
│
├── components/
│   ├── shell/
│   │   ├── SentinelHeader.tsx       # Product logo, global status, breadcrumb, active mode toggle
│   │   ├── NavigationRail.tsx       # High-level sections (Threats, Investigations, Replay, Metrics)
│   │   └── GlobalToastHub.tsx       # Asynchronous operation notifications (approvals, errors)
│   │
│   ├── workspace/
│   │   ├── InvestigationWorkspace.tsx  # Master container coordinating the Triad layout
│   │   │
│   │   ├── threat/                  # Column 1: Threat & State
│   │   │   ├── ThreatHeaderCard.tsx    # Attack classification, severity pill, target identifier
│   │   │   ├── ConfidenceGauge.tsx     # Large numerical confidence + 6-factor mini breakdown
│   │   │   ├── EntityScopeList.tsx     # Affected hosts, IPs, users, and processes
│   │   │   └── HypothesisBox.tsx       # Current working hypothesis + uncertainty notes
│   │   │
│   │   ├── planner/                 # Column 2: Planner & Orchestration
│   │   │   ├── PlannerStream.tsx       # Scrollable/scrubbable chronological feed of decisions
│   │   │   ├── DecisionCard.tsx        # Single step: cycle, capability badge, trigger, delta C
│   │   │   ├── ActiveExecutionCard.tsx # Pulsing card for currently executing worker
│   │   │   ├── ReplanAlertBanner.tsx   # Visual indicator for stagnation/contradiction replans
│   │   │   ├── UtilityScoreBreakdown.tsx # Expandable table showing why worker won selection
│   │   │   └── PlannerGraphCanvas.tsx  # Alternative node-graph view (Concept 2 integration)
│   │   │
│   │   ├── evidence/                # Column 3: Evidence & Action
│   │   │   ├── GroundedActionCard.tsx  # Recommendation, containment action, approval buttons
│   │   │   ├── EvidenceLedger.tsx      # Ranked list of discovered evidence cards
│   │   │   ├── EvidenceItemCard.tsx    # Individual finding: summary, source tag, confidence
│   │   │   └── ContradictionNotice.tsx # Highlights conflicting evidence requiring resolution
│   │   │
│   │   ├── drawers/                 # Progressive Disclosure Drawers (Level 2)
│   │   │   ├── ForensicTelemetryDrawer.tsx # Raw event JSON, timestamps, network payloads
│   │   │   ├── EntityGraphDrawer.tsx   # Interactive visual node graph of connected entities
│   │   │   └── HumanReviewModal.tsx    # Formal sign-off dialog for destructive actions
│   │   │
│   │   └── replay/                  # Investigation Replay Subsystem
│   │       ├── ReplayScrubberBar.tsx   # Play/Pause, step forward/back, speed selector (1x/5x)
│   │       └── StepDeltaInspector.tsx  # Highlights what changed between Step N and Step N-1
│   │
│   └── ui/                          # Reusable Primitive Design System
│       ├── Badge.tsx                # Status, severity, and worker tags
│       ├── Button.tsx               # Primary, secondary, danger, and ghost buttons
│       ├── Card.tsx                 # Standard border-zinc-800 rounded container
│       ├── Drawer.tsx               # Slide-over overlay container
│       └── Progress.tsx             # Animated confidence progress bar
```

---

# 5. Final Architectural Validation

### The Core Test Question:
> **"If the backend dynamically changes from Investigation $\rightarrow$ Detection $\rightarrow$ Correlation $\rightarrow$ Investigation, would the interface truthfully show that actual path without forcing it into a predefined visual workflow?"**

### Verification Against Proposed Architecture:
1. **Data Source Grounding:**
   The frontend renders Column 2 directly from `workspace.planner_trace` (backed by database `PlannerDecision` and `WorkerExecution` records), not a client-side hardcoded enum or mock wizard.
2. **Rendering Dynamic Sequences:**
   - At Cycle 1: The UI instantiates a `DecisionCard` with `selected_worker: "investigation"`.
   - At Cycle 2: If untriaged events enter, the Planner scores Detection highest. The UI instantiates a subsequent `DecisionCard` with `selected_worker: "detection"` and a badge `[TRANSITION] Shifted to raw triage`.
   - At Cycle 3: The Planner links new entities via Correlation. A `DecisionCard` for `"correlation"` is added.
   - At Cycle 4: If an entity requires deeper host inspection, the Planner re-selects Investigation. The UI renders another `"investigation"` card clearly badged `[REVISIT: 2nd Execution]`.
3. **Conclusion:**
   **PASSED.** The interface renders the exact chronological and causal trajectory of the Planner. There is zero structural assumption that capabilities occur in a predetermined sequence.

---

# 6. Conclusion & Next Steps

This design sprint establishes a distinct product identity for Project Sentinel: **calm, evidence-grounded, and relentlessly truthful to its adaptive multi-agent core.**

### Immediate Next Steps for Implementation:
1. **Frontend Foundation Setup:** Configure typography, semantic design tokens, and layout shell in `frontend/`.
2. **P0 API Integration:** Connect `workspaceClient.ts` to `GET /api/investigations/{id}/workspace`.
3. **Build Core Triad Components:** Implement `ThreatHeaderCard`, `PlannerStream`, `DecisionCard`, and `GroundedActionCard`.
4. **Interactive Investigation Replay:** Implement `ReplayScrubberBar` allowing reviewers to scrub through an investigation step-by-step.
