# Project Sentinel — Agentic Investigation Workspace: Three Design Concepts & Workflow Architecture

**Document Version:** 2.0.0  
**Status:** Authoritative Architectural Design Specification  
**Author:** Principal Frontend Designer & UX Architect (`frontend-designer`)  
**Binding Constraints:** [`docs/FRONTEND_DESIGN_BRIEF.md`](file:///c:/Users/Aaditya%20Rana/OneDrive/Desktop/SEM5/CDAC-IP/docs/FRONTEND_DESIGN_BRIEF.md)  
**Target Codebase Integration:** P0 Unified Workspace API (`GET /api/investigations/{id}/workspace`) & P1 Evaluation Service  

---

## Executive Summary

Project Sentinel is an **autonomous, state-driven, multi-agent cybersecurity investigation platform**. Unlike legacy SIEM interfaces or static SOAR playbooks, Sentinel's core differentiator is its **dynamic Planner**:
1. It continuously assesses the operational investigation state.
2. It scores all five worker capabilities (`detection`, `correlation`, `investigation`, `response`, `reporting`) using dynamic utility heuristics.
3. It selects and dispatches the most valuable capability.
4. The worker executes and incorporates new findings, entities, or actions.
5. The investigation state shifts (updating confidence $\Delta C$).
6. The Planner reassesses the new state, frequently looping back to prior capabilities, diversifying upon stagnation, or executing explicit replans.
7. The cycle terminates only when confidence exceeds threshold ($\ge 0.80$), max cycles are reached, or a grounded containment recommendation is ready for human authorization.

Because the system **does NOT execute a fixed linear pipeline** (`Detection → Correlation → Investigation → Response → Reporting`), the frontend must faithfully represent this non-linear reality without imposing artificial linear constraints or overwhelming the operator with raw diagnostic clutter.

This document explores **three distinct architectural concepts** for the **Agentic Investigation Workspace**:
* **Concept A — Chronological Investigation Narrative:** A Linear-inspired, sequential forensic stream modeling cause-and-effect state transitions vertically.
* **Concept B — Adaptive Investigation Map:** A spatial state-transition DAG canvas inspired by LangSmith that visualizes dynamic branches, capability revisits, and loops without creating an unreadable "hairball".
* **Concept C — Hybrid Operational Workspace (Threat-Centric Triad):** A balanced SOC command triad inspired by CrowdStrike and Microsoft Sentinel that prioritizes 5-second operational triage while keeping dynamic agent orchestration immediately observable.

---

# 1. Concept A — Chronological Investigation Narrative

## 1.1 Concept Name & Philosophy
* **Name:** *The Chronological Investigation Narrative* (The Forensic Journal)
* **Design Philosophy:** Inspired by **Linear**, **GitHub Pull Requests**, and modern developer chronicles. An investigation is treated as an **evolving, append-only forensic story**. Rather than forcing the analyst into complex 2D geometric navigation, the workspace presents a calm, focused, vertical stream where time flows downward. Every event represents an empirical state transition:
  $$\text{Investigation State}_t \xrightarrow{\text{Planner Trigger}} \text{Worker Execution} \xrightarrow{\text{Evidence Gained}} \text{State Shift}_{t+1} \quad (\Delta C)$$

## 1.2 Primary User Question the Layout Answers
> **"What happened from the start of the attack until now, what is the Planner doing at this exact moment, and what containment action is currently justified?"**

## 1.3 Information Hierarchy
1. **Level 0 Anchor (Top Right Sticky):** Threat Type, Severity Pill, Impacted Endpoint, Current Confidence Bar, and Grounded Containment Action Card.
2. **Level 1 Narrative (Center Column):** Chronological card stream of Planner decisions, execution latencies, state triggers, confidence deltas ($\Delta C$), and discovered evidence summaries.
3. **Level 1 State Status (Right Column Sub-panel):** Explicit tri-part investigation state:
   - `WHAT WE KNOW` (Verified factual entities & IOCs)
   - `WHAT WE SUSPECT` (Active working hypothesis)
   - `WHAT REMAINS UNRESOLVED` (Open operational gaps)
4. **Level 2 Diagnostic (Slide-Over Drawer):** Deep JSON telemetry, Sysmon process command-lines, and capability utility scoring vectors.

## 1.4 Detailed Workspace Layout
* **Header Bar (56px):** Global breadcrumb (`Threats / INV-2026-0892`), live socket status badge (`ACTIVE POLLING / LIVE`), cycle counter pill (`Cycle 6/10`), and quick-export report button.
* **Main Canvas (Two-Column Asymmetric Split):**
  * **Left/Center Narrative Stream (65% width):** Scrollable vertical ledger. Top card anchors the initial alert. Subsequent cards detail each Planner cycle in chronological sequence.
  * **Right Context & Action Rail (35% width):** Sticky 100vh panel. Top contains the Grounded Action Card with prominent approval buttons. Middle displays the Tri-Part State breakdown. Bottom displays the Asset Blast Radius.

## 1.5 ASCII Wireframe (Concept A)

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [SENTINEL]  Threats / INV-2026-0892: Ares Botnet C2 Beaconing              [SEVERITY: CRITICAL] [LIVE]  │
├────────────────────────────────────────────────────────────────┬────────────────────────────────────────┤
│ LEFT / CENTER CANVAS: CHRONOLOGICAL INVESTIGATION STREAM (65%) │ RIGHT PANEL: CONTEXT & ACTION (35%)    │
│                                                                │                                        │
│ ┌────────────────────────────────────────────────────────────┐ │ ┌────────────────────────────────────┐ │
│ │ [ANCHOR BAR] Target: WORKSTATION-04 (192.168.1.104)        │ │ │ [LEVEL 0] GROUNDED ACTION CARD     │ │
│ │ Category: Botnet Command & Control (Ares)                  │ │ │ [!] ACTION: Host Network Sever     │ │
│ │ Confidence: 84.5% [██████████████░░░░]  ·  Cycle: 6/10     │ │ │ Target: WORKSTATION-04             │ │
│ └────────────────────────────────────────────────────────────┘ │ │ Certainty: HIGH (84.5% Calibrated) │ │
│                                                                │ │ Rationale: Active Ares C2 beacon   │ │
│ [t=10:00:15] · INITIAL THREAT DETECTION                        │ │ verified over port 443 socket.     │ │
│ ┌────────────────────────────────────────────────────────────┐ │ │                                    │ │
│ │ CYCLE 1 · detection.execute                     +0.087 ΔC  │ │ │ Supporting Evidence Citations:     │ │
│ │ State Trigger: Untriaged NetFlow anomaly (Periodic SSL)    │ │ │ • EV-14: Outbound Socket 49210     │ │
│ │ Outcome: 5 flow events triaged. Destination flagged.       │ │ │ • EV-11: Encoded PowerShell cmd    │ │
│ │ Evidence Gained: EV-01 (Beacon Interval: 120s)             │ │ │ • EV-08: Dropped invoice_august    │ │
│ └────────────────────────────────────────────────────────────┘ │ │                                    │ │
│                               │                                │ │ [ APPROVE CONTAINMENT ]            │ │
│                               ▼                                │ │ [ REJECT / MODIFY PLAN ]           │ │
│ [t=10:00:22] · STATE EVALUATION: LOW CONFIDENCE HOST ENTITY    │ └────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────────┐ │                                        │
│ │ CYCLE 2 · investigation.execute                 +0.079 ΔC  │ │ ┌────────────────────────────────────┐ │
│ │ State Trigger: Host process tree inspection required.      │ │ │ INVESTIGATION STATE TRI-PART       │ │
│ │ Outcome: Inspected WORKSTATION-04 process table.           │ │ │                                    │ │
│ │ Evidence Gained: EV-11 (PID 4812: powershell.exe -Enc SQ..)│ │ │ [WHAT WE KNOW] (Verified Facts)    │ │
│ └────────────────────────────────────────────────────────────┘ │ │ • Outbound C2 IP: 13.58.225.34      │ │
│                               │                                │ │ • Target Host: WORKSTATION-04      │ │
│                               ▼                                │ │ • Compromised User: corp\jdoe      │ │
│ [t=10:00:35] · [!] REPLAN EVENT: CONTRADICTION DETECTED        │ │                                    │ │
│ ┌────────────────────────────────────────────────────────────┐ │ │ [WHAT WE SUSPECT] (Hypothesis)    │ │
│ │ CYCLE 3 · correlation.execute (REPLAN)          +0.260 ΔC  │ │ │ • Ares botnet payload dropped via  │ │
│ │ State Trigger: Conflicting parent PID of PowerShell detected│ │ │   Word macro; beaconing to C2.     │ │
│ │ Selected Over: Investigation (Utility: 0.94 vs 0.42)       │ │ │                                    │ │
│ │ Outcome: Linked powershell.exe to parent WINWORD.EXE.      │ │ │ [WHAT REMAINS UNRESOLVED] (Gaps)   │ │
│ │ Evidence Gained: EV-08 (invoice_august.docm macro drop)    │ │ │ ? Has payload spread laterally to   │ │
│ └────────────────────────────────────────────────────────────┘ │ │   UBUNTU-SRV-01 via SMB?           │ │
│                               │                                │ │ ? Persistence run keys verified?   │ │
│                               ▼                                │ └────────────────────────────────────┘ │
│ [t=10:00:48] · CAPABILITY REVISIT: HOST RE-INSPECTION          │                                        │
│ ┌────────────────────────────────────────────────────────────┐ │ ┌────────────────────────────────────┐ │
│ │ CYCLE 4 · investigation.execute [REVISIT]       +0.067 ΔC  │ │ │ BLAST RADIUS / IMPACTED ASSETS     │ │
│ │ State Trigger: Analyze dropped docm macro & persistence.   │ │ │ • WORKSTATION-04 (Endpoint - High) │ │
│ │ Outcome: Extracted scheduled task persistence artifact.    │ │ │ • corp\jdoe (User - Medium)        │ │
│ └────────────────────────────────────────────────────────────┘ │ │ • 13.58.225.34 (External - Mal)    │ │
│                               │                                │ └────────────────────────────────────┘ │
│                               ▼                                │                                        │
│ [t=10:01:05] · RESPONSE FORMULATION (TERMINAL CONFIDENCE)      │ [ ◄ PREV CYCLE ]   [ NEXT CYCLE ► ]   │
└────────────────────────────────────────────────────────────────┴────────────────────────────────────────┘
```

## 1.6 Component Inventory (Concept A)
1. `ThreatAnchorBar`: Displays primary target, severity badge, and overall confidence meter.
2. `NarrativeStreamContainer`: Virtualized vertical feed handling chronological cycle step cards.
3. `PlannerDecisionCard`: Structured event card showing cycle number, capability tag, state trigger, execution latency, and $\Delta C$.
4. `ReplanCalloutBanner`: Prominent amber badge highlighting contradiction or stagnation replans.
5. `EvidenceYieldPill`: Compact inline badges displaying evidence IDs discovered during that cycle.
6. `GroundedActionCard`: High-urgency containment panel citing exact supporting evidence.
7. `InvestigationStateTriadBox`: Structured container rendering `WHAT WE KNOW`, `WHAT WE SUSPECT`, and `WHAT REMAINS UNRESOLVED`.
8. `DiagnosticDrawer`: Slide-over drawer for Level-2 telemetry and candidate utility matrices.

## 1.7 Primary User Interaction Flow
1. **Entry & Orientation (0-5s):** Analyst opens incident; immediately reads right-hand rail for threat category (*Botnet C2*), impacted host (*WORKSTATION-04*), and recommended containment action (*Host Network Sever*).
2. **Reviewing the Narrative (5-20s):** Analyst scrolls downward through the central feed, observing how the Planner transitioned from *Detection* to *Investigation*, hit a contradiction, replanned to *Correlation*, and looped back to *Investigation*.
3. **Inspecting Evidence (20-35s):** Clicking `EV-11` on Cycle 2 opens the right slide-over drawer showing decoded Base64 PowerShell execution and parent PID.
4. **Authorizing Containment (35-45s):** Analyst reviews the direct citations (`EV-14`, `EV-11`, `EV-08`) under the Action Card and clicks `[ APPROVE CONTAINMENT ]`.
5. **Completion State:** Action card confirms dispatch; bottom of stream appends `Cycle 6 · response.execute [EXECUTED & HUMAN APPROVED]`.

## 1.8 Representation of Dynamic Orchestration
* **Arbitrary Execution Order:** No fixed slots. Cycles are strictly appended to the ledger as they occur ($C_1, C_2, C_3, \dots, C_n$).
* **Revisited Capabilities:** When `investigation.execute` is selected again at Cycle 4, it receives a distinct violet tag: `[REVISIT: 2nd Execution]` and displays the new trigger.
* **Replanning Events:** Cycle 3 renders an amber border (`border-amber-500/50`) with an explicit trigger explanation: *"Selected over Investigation (Utility: 0.94 vs 0.42) due to parent PID contradiction"*.
* **Available Capabilities:** Hovering over the active cycle header displays a tooltip listing all five capabilities and their active utility scores.

## 1.9 Progressive Disclosure Model
* **Level 0 (Surface):** Threat anchor, confidence gauge, recommended action, and primary approval button.
* **Level 1 (Operational):** Cycle decision cards, state triggers, $\Delta C$, evidence yield pills, and tri-part state breakdown.
* **Level 2 (Diagnostic):** Clicking any card or evidence pill opens the slide-over drawer displaying raw Sysmon logs, decoded command strings, and the complete utility score matrix.

## 1.10 Strengths
* Lowest cognitive friction; natural top-to-bottom reading flow familiar to developers and analysts.
* Superb causal storytelling: cause-and-effect transitions are immediately obvious.
* Perfectly handles arbitrary non-linear execution paths without layout breakage.

## 1.11 Risks & Weaknesses
* In extended investigations (15+ cycles), the feed becomes very long, requiring extensive scrolling.
* Multi-host blast radius and network topologies are represented textually rather than geometrically.

---

# 2. Concept B — Adaptive Investigation Map

## 2.1 Concept Name & Philosophy
* **Name:** *The Adaptive Investigation Map* (Spatial State Machine)
* **Design Philosophy:** Inspired by **LangSmith**, **n8n**, and **Figma**. An investigation is modeled as a **living state-machine DAG (Directed Acyclic Graph)**. The mental model is spatial: the investigation state is a central node that evaluates conditions and emits directional execution nodes across iterations.
  $$\text{State Node } S_k \xrightarrow{\text{Utility Evaluation}} \text{Capability Node } W_k \xrightarrow{\text{Yield}} \text{Evidence Cluster } E_k \xrightarrow{\text{Update}} \text{State Node } S_{k+1}$$

Branching, capability loops, and replanning diversions are rendered in two dimensions. If the Planner revisits `investigation`, the canvas routes a visible loop-back edge or instantiates a connected secondary execution node with directional provenance arrows.

## 2.2 Primary User Question the Layout Answers
> **"How did the system navigate the investigation space, what capability branches were explored, and how did evidence discoveries alter the Planner's trajectory?"**

## 2.3 Information Hierarchy
1. **Level 0 Anchor (Top Threat Bar):** Threat category, severity pill, target asset, overall confidence %, and active cycle indicator.
2. **Level 1 Canvas (Central Spatial Graph):** Interactive 2D graph with pan/zoom. Nodes represent Planner decisions, worker executions, evidence clusters, and human approval gates.
3. **Level 1 Node Inspector (Bottom Dock):** Expands upon node selection, detailing the input state, utility scoring breakdown, latency, and findings.
4. **Level 2 Diagnostic (Modal / Popover):** Raw event JSON, MITRE ATT&CK matrix view, and full entity connection graph.

## 2.4 Detailed Workspace Layout
* **Top Threat Bar (48px):** Minimalist horizontal strip with threat title, critical severity badge, target host, and terminal status.
* **Central Canvas Viewport (100% width, flexible height):** Interactive infinite canvas supporting pan, zoom, auto-layout centering, and node selection.
* **Bottom Inspector Dock (240px, collapsible):** Displays structured diagnostics for whatever node is currently selected on the canvas.
* **Floating Action HUD (Bottom Right):** Persistent floating card showing the terminal recommended action with an `[ APPROVE ]` button.

## 2.5 ASCII Wireframe (Concept B)

```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [SENTINEL]  Investigation Canvas / INV-2026-0892: Ares Botnet C2 Beaconing  ·  Confidence: 84.5%        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ TOP THREAT BAR: [CRITICAL] Ares Botnet C2  ·  Target: WORKSTATION-04  ·  Cycle 6/10  ·  Status: Triage  │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ SPATIAL AGENT STATE & EXECUTION MAP (INTERACTIVE CANVAS — PAN / ZOOM / SELECT)                          │
│                                                                                                         │
│   ┌──────────────┐        ┌───────────────────────┐        ┌───────────────────────┐                    │
│   │ INITIAL SEED │───────►│ CYCLE 1: DETECTION    │───────►│ EVIDENCE CLUSTER 1    │                    │
│   │ 5 NetFlow Ev │        │ Trigger: Untriaged > 0│        │ • EV-01: HTTPS Beacon │                    │
│   └──────────────┘        └───────────────────────┘        └───────────┬───────────┘                    │
│                                                                        │                                │
│                                  ┌─────────────────────────────────────┘                                │
│                                  ▼                                                                      │
│                       ┌───────────────────────┐        ┌───────────────────────┐                        │
│                       │ CYCLE 2: INVESTIGATION│───────►│ EVIDENCE CLUSTER 2    │                        │
│                       │ Trigger: Verify Host  │        │ • EV-11: Encoded PS   │                        │
│                       └───────────────────────┘        └───────────┬───────────┘                        │
│                                                                    │                                    │
│             ┌──────────────────────────────────────────────────────┘                                    │
│             ▼                                                                                           │
│   ┌───────────────────────────┐      (Replan Divergence)   ┌───────────────────────┐                    │
│   │ CYCLE 3: CORRELATION      │───────────────────────────►│ EVIDENCE CLUSTER 3    │                    │
│   │ [!] REPLAN: Contradiction │                            │ • EV-08: Word Macro   │                    │
│   │ Utility Score: 0.94       │                            └───────────┬───────────┘                    │
│   └───────────────────────────┘                                        │                                │
│             │                                                          │                                │
│             │ (Loop-back revisit to inspect dropped docm)              │                                │
│             ▼                                                          ▼                                │
│   ┌───────────────────────────┐                            ┌───────────────────────┐                    │
│   │ CYCLE 4: INVESTIGATION    │◄───────────────────────────┤ CYCLE 5: RESPONSE     │                    │
│   │ [REVISIT: 2nd Execution]  │                            │ Terminal Conf > 0.80  │                    │
│   │ Utility Score: 0.88       │                            │ Grounded Action Plan  │                    │
│   └───────────────────────────┘                            └───────────┬───────────┘                    │
│                                                                        │                                │
│                                                                        ▼                                │
│                                                            ╔═══════════════════════╗                    │
│                                                            ║ [!] HUMAN REVIEW NODE ║                    │
│                                                            ║ ACTION: Sever Socket  ║                    │
│                                                            ╚═══════════════════════╝                    │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ BOTTOM INSPECTOR DOCK (EXPANDS ON NODE CLICK — SELECTED: CYCLE 3: CORRELATION)                          │
│ • State Trigger: Contradiction in process hierarchy (Parent PID of powershell.exe unresolved).          │
│ • Utility Comparison: correlation: 0.94 | investigation: 0.42 | response: 0.18 | detection: 0.05       │
│ • Confidence Delta: +0.260 (0.320 ──> 0.580)  ·  Latency: 38ms  ·  Status: SUCCESS                     │
│ • Discovered Finding: Linked invoice_august.docm execution to spawned hidden PowerShell beacon.         │
│ • State Impact: Updated WHAT WE SUSPECT with macro delivery vector.                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 2.6 Component Inventory (Concept B)
1. `TopThreatBar`: Compact bar with attack type, severity, target asset, and status.
2. `SpatialCanvas`: WebGL/SVG pan-and-zoom viewport with dynamic dagre/elk layout.
3. `PlannerStateNode`: Circular or rounded rectangular node representing investigation state $S_k$.
4. `CapabilityExecutionNode`: Distinctively colored node representing worker execution (`detection` cyan, `investigation` violet, `correlation` blue, `response` emerald).
5. `ReplanBranchEdge`: Dashed amber curved edge indicating an adaptive diversion due to contradiction or stagnation.
6. `LoopbackRevisitEdge`: Directional vector showing a capability revisit.
7. `EvidenceClusterNode`: Clustered pill grouping evidence artifacts yielded by a worker.
8. `TerminalActionNode`: Glowing emerald node representing the pending human containment gate.
9. `BottomInspectorDock`: Collapsible 3-column drawer detailing inputs, utility scores, and outputs of the selected node.

## 2.7 Primary User Interaction Flow
1. **Entry & Orientation (0-5s):** Analyst opens canvas; reads top bar for threat severity and scans canvas to locate the glowing `[!] HUMAN REVIEW NODE`.
2. **Exploring the Topology (5-20s):** Analyst traces edges: notices the linear start, the downward branch at Cycle 3 (`[!] REPLAN`), and the loop-back to Cycle 4 (`INVESTIGATION REVISIT`).
3. **Inspecting Decision Depth (20-35s):** Clicking the `CYCLE 3: CORRELATION` node populates the bottom dock, revealing why `correlation` scored 0.94 while `investigation` dropped to 0.42.
4. **Authorizing Action (35-45s):** Analyst clicks the `HUMAN REVIEW NODE` on the canvas; a popover displays the containment script and evidence links; analyst clicks `[ AUTHORIZE ISOLATION ]`.
5. **Completion State:** Terminal node turns solid emerald with a verified checkmark (`CONTAINED`).

## 2.8 Representation of Dynamic Orchestration
* **Arbitrary Execution Order:** Rendered purely as directional vectors between nodes.
* **Revisited Capabilities:** Rendered either as a visible looping backward edge or as a discrete second node labeled `Capability (Revisit)`.
* **Replanning Events:** Rendered with an amber halo and a dashed branching edge labeled `(Replan Divergence)`.
* **Available Capabilities:** The bottom dock displays a bar chart of all five capabilities and their utility scores at that node's timestamp.

## 2.9 Progressive Disclosure Model
* **Level 0 (Surface):** Top threat bar, node icons, execution labels, and glowing terminal action node.
* **Level 1 (Operational):** Bottom inspector dock showing trigger text, utility rankings, latency, and findings.
* **Level 2 (Diagnostic):** Double-clicking an evidence cluster opens a full-screen forensic modal with raw event JSON, packet payload, and entity graphs.

## 2.10 Strengths
* Unmatched demonstration value; visual proof of non-linear, branching agentic behavior.
* Geometric clarity for capability loops, revisits, and replans.

## 2.11 Risks & Weaknesses
* High cognitive load; operators must pan and zoom to read labels.
* "Canvas Fatigue": lengthy investigations with 25+ nodes can turn into an unreadable graph.
* Threat context and action buttons are separated, slowing down rapid frontline response.

---

# 3. Concept C — Hybrid Operational Workspace (Threat-Centric Triad)

## 3.1 Concept Name & Philosophy
* **Name:** *The Threat-Centric Triad* (Operator-First Command Center)
* **Design Philosophy:** Inspired by **CrowdStrike Falcon**, **Microsoft Sentinel**, and modern developer observability suites. It prioritizes the **operational velocity of a frontline SOC analyst** who has 60 seconds to triage an incident, understand what the autonomous engine has verified, and take decisive containment action.

The workspace is organized into **three purposeful, synchronized vertical columns** answering the three fundamental human questions:
$$\begin{aligned}
\text{Column 1 (25%): } & \textbf{What is the threat?} \quad \text{(Context, Entity Blast Radius, Confidence, Hypothesis)} \\
\text{Column 2 (45%): } & \textbf{What is the AI doing?} \quad \text{(Planner Status, Chronological Decision Trace, Replan Alerts)} \\
\text{Column 3 (30%): } & \textbf{What action is justified?} \quad \text{(Grounded Action Card, Human Approval, Evidence Ledger)}
\end{aligned}$$

## 3.2 Primary User Question the Layout Answers
> **"What is the threat and blast radius, how did the Planner deduce it, and what containment action should I approve right now based on verified evidence?"**

## 3.3 Information Hierarchy
1. **Level 0 Command Surface (Always Visible across the 3 Columns):**
   - *Col 1 Top:* Threat Type (*Ares Botnet C2*), Severity Pill (*CRITICAL*), Impacted Host (*WORKSTATION-04*).
   - *Col 2 Top:* Active Planner Status (*Cycle 6/10: Awaiting Action*), Last Selection (*response.execute*).
   - *Col 3 Top:* Grounded Action Card (*Host Network Sever*), Certainty (*84.5%*), Approval Gate (*[ APPROVE ]*).
2. **Level 1 Operational Detail (Lower Sections of the 3 Columns):**
   - *Col 1 Lower:* Confidence Trajectory Gauge, Impacted Asset Scope, and Tri-Part Investigation State (`WHAT WE KNOW`, `WHAT WE SUSPECT`, `WHAT REMAINS UNRESOLVED`).
   - *Col 2 Lower:* Scrollable chronological feed of Planner decision cards with state triggers, utility scores, and $\Delta C$.
   - *Col 3 Lower:* Supporting Evidence Ledger ranked by evidentiary weight, with MITRE technique tags and entity links.
3. **Level 2 Diagnostic (Slide-Over Drawer):** Slide-over panel for raw Sysmon telemetry, entity connection topology, and ChromaDB RAG chunk inspect.

## 3.4 Detailed Workspace Layout
* **Global Header (48px):** System logo, breadcrumb, active investigation ID, global platform status, and a central View Mode Toggle: `[ Timeline Feed ] <──> [ Spatial Graph ]`.
* **Three-Column Command Grid (Synchronized 100vh):**
  * **Column 1: Threat & State (25% width / 320px min):** Sticky left rail. Top has threat profile; middle has calibrated confidence gauge; bottom has tri-part state box and entity impact scope.
  * **Column 2: Planner & Orchestration (45% width / flexible):** Scrollable center stage. Top has active Planner goal and status. Below is the reverse-chronological or forward-chronological stream of structured Planner decision cards.
  * **Column 3: Evidence & Action (30% width / 380px min):** Action-first right rail. Top has Grounded Action Card with prominent approval buttons. Bottom has ranked evidence cards directly substantiating the action.

## 3.5 ASCII Wireframe (Concept C)

```text
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [SENTINEL]  Threats / INV-2026-0892: Ares Botnet C2  ·  Target: WORKSTATION-04  ·  [SEVERITY: CRITICAL]  ·  [LIVE]    │
├───────────────────────────────┬───────────────────────────────────────────────┬───────────────────────────────────────┤
│ COL 1: THREAT & STATE (25%)   │ COL 2: PLANNER DECISION FEED (45%)            │ COL 3: EVIDENCE & ACTION (30%)        │
│                               │                                               │                                       │
│ ┌───────────────────────────┐ │ ┌───────────────────────────────────────────┐ │ ┌───────────────────────────────────┐ │
│ │ [LEVEL 0] THREAT PROFILE  │ │ │ [LEVEL 0] ACTIVE PLANNER STATUS           │ │ │ [LEVEL 0] GROUNDED ACTION CARD    │ │
│ │ Type: Botnet C2 (Ares)    │ │ │ Current Goal: Verify C2 Persistence       │ │ │ Action: Host Network Isolation    │ │
│ │ Severity: CRITICAL        │ │ │ Cycle: 6 / 10  ·  Status: Awaiting Action │ │ │ Target: WORKSTATION-04 (IP .104)  │ │
│ │ Target: WORKSTATION-04    │ │ │ Active Capability: response.execute       │ │ │ Confidence: 84.5% (Calibrated)    │ │
│ │ User: corp\jdoe           │ │ └───────────────────────────────────────────┘ │ │ Status: PENDING HUMAN APPROVAL    │ │
│ └───────────────────────────┘ │                                               │ │                                   │ │
│                               │ ┌───────────────────────────────────────────┐ │ │ [ APPROVE ACTION ] [ REJECT ]      │ │
│ ┌───────────────────────────┐ │ │ CHRONOLOGICAL DECISION TRACE (SCROLLABLE) │ │ └───────────────────────────────────┘ │
│ │ CONFIDENCE TRAJECTORY     │ │ │                                           │ │                                       │
│ │ Current: 84.5% [HIGH]     │ │ │ ┌───────────────────────────────────────┐ │ │ ┌───────────────────────────────────┐ │
│ │ 0.150 ═══════════► 0.845  │ │ │ │ Cycle 5 · response.execute  +0.093 ΔC │ │ │ │ SUPPORTING EVIDENCE LEDGER (18)   │ │
│ │ Factors:                  │ │ │ │ Trigger: Confidence > 0.80 reached.   │ │ │ │ Ranked by Evidentiary Weight      │ │
│ │ • Anomaly Score: 0.92     │ │ │ │ Rationale: Generate host containment. │ │ │ │                                   │ │
│ │ • Correlation Conf: 0.88  │ │ │ └───────────────────────────────────────┘ │ │ │ • EV-14 [Network Socket]    0.95 │ │
│ │ • Graph Completeness: 0.74│ │ │                    ▲                      │ │ │   192.168.1.104:49210 ->          │ │
│ └───────────────────────────┘ │ │                    │                      │ │ │   13.58.225.34:443 (Periodic C2)  │ │
│                               │ │ ┌───────────────────────────────────────┐ │ │ │   Source: cic_network_flow        │ │
│ ┌───────────────────────────┐ │ │ │ Cycle 4 · investigation.exec +0.067 ΔC│ │ │ │                                   │ │
│ │ INVESTIGATION STATE       │ │ │ │ [REVISIT: 2nd Execution]              │ │ │ │ • EV-11 [Process Command]   0.91 │ │
│ │                           │ │ │ │ Trigger: Word macro artifact analysis │ │ │ │   powershell.exe -Enc SQ.. (4812) │ │
│ │ [WHAT WE KNOW] (Facts)    │ │ │ └───────────────────────────────────────┘ │ │ │   Parent: WINWORD.EXE (PID 4108)  │ │
│ │ • Active C2 Socket (Port) │ │ │                    ▲                      │ │ │                                   │ │
│ │ • Encoded PowerShell PID  │ │ │                    │                      │ │ │ • EV-08 [Dropped File]      0.84 │ │
│ │ • Target: WORKSTATION-04  │ │ │ ┌───────────────────────────────────────┐ │ │ │   invoice_august.docm             │ │
│ │                           │ │ │ │ Cycle 3 · correlation.exec   +0.260 ΔC│ │ │ │   Zone.Identifier: Internet       │ │
│ │ [WHAT WE SUSPECT] (Hypo)  │ │ │ │ [!] REPLAN: Contradictory Parent PID  │ │ │ │                                   │ │
│ │ • Word macro dropped Ares │ │ │ │ Selected over Investigation (0.94/0.4)│ │ │ │ • EV-01 [Initial Anomaly]   0.72 │ │
│ │   beacon payload.         │ │ │ └───────────────────────────────────────┘ │ │ │   SSL Beaconing Cluster           │ │
│ │                           │ │ │                    ▲                      │ │ └───────────────────────────────────┘ │
│ │ [WHAT REMAINS UNRESOLVED] │ │ │ [ + View Cycles 1-2 (Detection/Invest) ] │ │                                       │
│ │ ? Lateral SMB spread?     │ │ └───────────────────────────────────────────┘ │ [ + Open Forensic Drawer (L2) ]     │
└───────────────────────────────┴───────────────────────────────────────────────┴───────────────────────────────────────┘
```

## 3.6 Component Inventory (Concept C)
1. `ThreatProfileCard`: Attack category, severity badge, target endpoint, and user ID.
2. `ConfidenceTrajectoryGauge`: Graphical progress gauge displaying calibrated score and 6-factor breakdown popup.
3. `InvestigationStateBox`: Explicit tri-part display of `WHAT WE KNOW`, `WHAT WE SUSPECT`, and `WHAT REMAINS UNRESOLVED`.
4. `ImpactedAssetScope`: Structured entity pills (hosts, IPs, accounts) with compromise indicators.
5. `ActivePlannerHeader`: Real-time banner showing current cycle, goal, active worker, and replan status.
6. `PlannerDecisionFeed`: Scrollable feed of structured decision cards with utility rankings and $\Delta C$.
7. `DecisionCard`: Individual cycle card showing capability, trigger rationale, latency, and status.
8. `GroundedActionCard`: High-urgency action container with direct evidence citations and approval buttons.
9. `EvidenceLedger`: Filterable, ranked list of evidence items displaying confidence and source tags.
10. `ForensicTelemetryDrawer`: Slide-over drawer for Level-2 raw logs, command lines, and entity graphs.

## 3.7 Primary User Interaction Flow
1. **Entry & Orientation (0-3s):**
   - **Gaze 1 (Col 1):** Reads Threat (*Ares Botnet C2*), Target (*WORKSTATION-04*), and Confidence (*84.5%*).
   - **Gaze 2 (Col 3):** Reads Action (*Host Network Isolation*) and verifies it requires approval.
2. **Observing Agent Logic (3-15s):** Analyst reviews Column 2, spotting the amber `[!] REPLAN` badge at Cycle 3 and understanding that the Planner switched to `correlation` to resolve a parent PID conflict.
3. **Evaluating Supporting Evidence (15-25s):** In Column 3, directly beneath the action button, the analyst inspects `EV-14` (Outbound C2 socket) and `EV-11` (Encoded PowerShell execution).
4. **Authorizing Action (25-35s):** Analyst clicks `[ APPROVE ACTION ]`. A modal records the authorization.
5. **Completion State:** Action button shifts to an emerald verified badge: `[APPROVED · ISOLATION DISPATCHED]`.

## 3.8 Representation of Dynamic Orchestration
* **Arbitrary Execution Order:** Decision cards in Column 2 reflect real database records.
* **Revisited Capabilities:** Second execution of a worker receives an explicit purple tag: `[REVISIT: 2nd Execution]`.
* **Replanning Events:** Amber border and banner explaining the contradiction or stagnation trigger.
* **Comparative Utility Scores:** Clicking `Utility` expands a bar chart showing scores of all 5 workers at that cycle.

## 3.9 Progressive Disclosure Model
* **Level 0 (Surface):** Threat profile, confidence gauge, recommended action, and approval buttons.
* **Level 1 (Operational):** Tri-part state box, decision feed with triggers and $\Delta C$, and ranked evidence cards.
* **Level 2 (Diagnostic):** Clicking an evidence card or utility badge slides over the Level-2 forensic drawer.

## 3.10 Strengths
* **Fastest time-to-action (under 3 seconds)** of all three concepts.
* Perfect proximity: action recommendation is immediately adjacent to the evidence justifying it.
* Zero panning, zooming, or cognitive disorientation.

## 3.11 Risks & Weaknesses
* Requires minimum 1280px screen width for three columns (requires responsive collapse on smaller screens).
* Less visually novel than the full node graph of Concept B.

---

# 4. Mandatory Feature Handling Across All Three Concepts

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        HOW ALL CONCEPTS HANDLE THE 7 MANDATORY CAPABILITIES                            │
├──────────────────────────┬───────────────────────────┬───────────────────────────┬─────────────────────┤
│ MANDATORY REQUIREMENT    │ CONCEPT A: STREAM         │ CONCEPT B: MAP            │ CONCEPT C: TRIAD    │
├──────────────────────────┼───────────────────────────┼───────────────────────────┼─────────────────────┤
│ 1. Threat Context        │ Header anchor + Col 2     │ Top threat bar            │ Col 1 dedicated box │
│ 2. Planner Visibility    │ Inline step cards + ΔC    │ Node inspector drawer     │ Col 2 decision feed │
│ 3. Dynamic Orchestration │ Append-only cycle cards   │ Spatial DAG vectors       │ Col 2 badged trace  │
│ 4. Investigation State   │ Right-rail tri-part box   │ State nodes in graph      │ Col 1 tri-part box  │
│ 5. Evidence & Provenance │ Inline yield pills + L2   │ Evidence cluster nodes    │ Col 3 ranked ledger │
│ 6. Recommended Action    │ Sticky right action card  │ Terminal glowing node     │ Col 3 top card      │
│ 7. Replay Compatibility  │ Downward step scrubber    │ Graph traversal animator  │ Scrubbable feed bar │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Investigation State Breakdown (`WHAT WE KNOW / SUSPECT / UNRESOLVED`)
Every concept incorporates the formal tri-part state structure:
* **`WHAT WE KNOW` (Verified Facts):** Grounded in immutable evidence records (e.g., target host IP, confirmed outbound socket, authenticated user identity).
* **`WHAT WE SUSPECT` (Active Hypotheses):** Grounded in hypothesis records with assigned confidence scores (e.g., Ares payload delivered via Word macro).
* **`WHAT REMAINS UNRESOLVED` (Open Questions):** Derived from `PlannerWorkspaceState.unresolved_questions` (e.g., lateral movement via SMB, registry run key persistence).

---

# 5. Investigation Replay Compatibility

All three concepts support **Deterministic Investigation Replay** for completed cases:

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ INVESTIGATION REPLAY CONTROLLER (PERSISTENT SUB-HEADER DOCK)                                           │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ [◄ Previous]  [► Play / Pause]  [Next ►]   Cycle: 3 / 6   Speed: [1x] [2x] [Instant]  ·  Progress: 50% │
│ ═══════════════════════════════════════════════════════○════════════════════════════════════════════  │
│ Step 1 (t=0s)       Step 2 (t=12s)       Step 3 (t=25s)       Step 4 (t=42s)       Step 5 (t=60s)      │
│ Ingestion           Investigation        Correlation [REPLAN] Inv [REVISIT]        Response Ready      │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

* **Concept A Replay:** As the user steps from Cycle $N-1$ to $N$, the journal scrolls to the newly appended card and pulses its border in emerald.
* **Concept B Replay:** The graph illuminates node-by-node; newly traversed edges glow with directional particle animations.
* **Concept C Replay:** Column 2 highlights the active decision card; Column 1 updates the confidence trajectory gauge in real time; Column 3 populates newly unearthed evidence items.

---

# 6. Evaluation Against the Official 35-Point Rubric

Scored strictly against the seven weighted criteria defined in `docs/FRONTEND_DESIGN_BRIEF.md`:

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              OFFICIAL 35-POINT EVALUATION SCORING                                      │
├──────────────────────────┬───────┬───────────────────┬───────────────────┬─────────────────────────────┤
│ EVALUATION CRITERION     │ MAX   │ CONCEPT A: STREAM │ CONCEPT B: MAP    │ CONCEPT C: TRIAD            │
├──────────────────────────┼───────┼───────────────────┼───────────────────┼─────────────────────────────┤
│ 1. Investigation Clarity │ 5 pts │ 4.2 / 5           │ 3.0 / 5           │ 4.9 / 5 (Immediate triage)  │
│ 2. Cognitive Load        │ 5 pts │ 4.8 / 5 (Calm)    │ 2.5 / 5 (Complex) │ 4.4 / 5 (Structured)        │
│ 3. Agent Visibility      │ 5 pts │ 4.1 / 5           │ 4.9 / 5 (Visible) │ 4.7 / 5 (Visible & clear)   │
│ 4. Dynamic Truthfulness  │ 5 pts │ 4.8 / 5           │ 5.0 / 5 (Perfect) │ 4.8 / 5 (Truthful trace)    │
│ 5. Evidence Grounding    │ 5 pts │ 4.0 / 5           │ 3.2 / 5           │ 4.9 / 5 (Direct citations)  │
│ 6. Actionability         │ 5 pts │ 4.2 / 5           │ 3.1 / 5           │ 4.9 / 5 (HITL front & center)│
│ 7. Demonstration Value   │ 5 pts │ 4.0 / 5           │ 4.9 / 5 (Stunning)│ 4.6 / 5 (Enterprise ready)  │
├──────────────────────────┼───────┼───────────────────┼───────────────────┼─────────────────────────────┤
│ TOTAL SCORE              │ 35 pts│ 30.1 / 35         │ 26.6 / 35         │ 33.2 / 35 (WINNER)          │
└──────────────────────────┴───────┴───────────────────┴───────────────────┴─────────────────────────────┘
```

### Detailed Evaluation Commentary:
1. **Investigation Clarity:** Concept C scores 4.9/5 because an analyst absorbs the threat, target, and severity in under 3 seconds without moving their eyes across panels. Concept B scores 3.0/5 because spatial labels get lost in the graph canvas.
2. **Cognitive Load:** Concept A scores highest (4.8/5) for calm narrative reading. Concept B scores 2.5/5 due to canvas pan/zoom overhead. Concept C scores 4.4/5 by maintaining strict 3-panel boundaries.
3. **Agent Visibility:** Concept B (4.9/5) and Concept C (4.7/5) both excel in exposing Planner utility scores, cycle progression, and state triggers.
4. **Dynamic Truthfulness:** All three concepts score $\ge 4.8/5$ because all render directly from database records without fixed pipeline waterfalls. Concept B gets 5.0/5 for spatial loop representation.
5. **Evidence Grounding:** Concept C scores 4.9/5 because the Grounded Action Card sits directly above the Supporting Evidence Ledger in the same visual column.
6. **Actionability:** Concept C scores 4.9/5; the `[ APPROVE ACTION ]` button is always visible on the command surface. Concept B scores 3.1/5 because the action is hidden in a terminal node or modal.
7. **Demonstration Value:** Concept B scores 4.9/5 for conference-level visual impact. Concept C scores 4.6/5 as a battle-tested, credible enterprise SOC tool.

---

# 7. Final Recommendation & Hybrid Synthesis

### The Core Decision:
**Concept C (The Operator-First Triad) is the definitively recommended workspace direction (33.2 / 35).**

It provides the fastest frontline operational triage, perfectly adheres to the "Threat Before Telemetry" principle, co-locates recommended actions with evidence, and preserves low cognitive load.

### Strategic Hybrid Synthesis:
To capture the unique strengths of Concepts A and B without compromising Concept C's operational speed, the production architecture incorporates two high-value syntheses:
1. **The Linear Decision Card Pattern (from Concept A):** Column 2 of Concept C utilizes the clean, narrative card design from Concept A for each cycle step, displaying the cycle number, capability tag, state trigger, and $\Delta C$ without visual clutter.
2. **Interactive Graph Replay Mode (from Concept B):** A view toggle in the sub-header:
   `[ Timeline Feed ] <──> [ Spatial Graph ]`
   allows analysts or evaluators to toggle Column 2 into Concept B's node graph on demand for architectural audits and technical briefings.
3. **Slide-Over Forensic Drawer:** Deep Level-2 telemetry (raw JSON, Sysmon logs, MITRE technique matrices, ChromaDB RAG chunk inspect) opens in an unobtrusive 40% slide-over drawer from the right.

---

# 8. Preliminary End-to-End Frontend Workflow

```text
[1. Threat Ingestion Queue] ➔ Analyst selects prioritized incident (e.g. Ares Botnet C2)
         │
         ▼
[2. Workspace Initialization] ➔ GET /api/investigations/{id}/workspace populates Level-0 Triad
    • Left: Threat context, affected host, living hypothesis
    • Right: Grounded Action Card with pending approval status and 84.5% confidence
         │
         ▼
[3. Planner Observation] ➔ Analyst inspects Column 2 decision feed
    • Tracks non-linear path: Detection -> Investigation -> Replan to Correlation -> Investigation Revisit
    • Reviews explicit triggers, capability revisits, and empirical confidence shifts (+ΔC)
    • (Optional) Toggles to [Spatial Graph] mode for topological inspection
         │
         ▼
[4. Evidence Drill-Down] ➔ Analyst clicks evidence in Column 3 (e.g. EV-11: Encoded PowerShell)
    • Level-2 slide-over drawer displays raw Sysmon Event ID 1 telemetry and MITRE T1059.001
         │
         ▼
[5. Human-in-the-Loop Action] ➔ Analyst reviews containment action and supporting citations
    • Clicks [APPROVE ACTION] (dispatches POST /api/investigations/{id}/review)
         │
         ▼
[6. Replay & Governance] ➔ Status shifts to "Contained"; analyst can scrub historical replay
```

---

# 9. Backend Contract Requirements for the Selected Frontend Direction

To ensure implementation honesty, every data field in the recommended Synthesized Hybrid was audited:
* **`[A]` Already available:** Field is natively exposed by `InvestigationWorkspaceProjection` (`GET /api/investigations/{id}/workspace`).
* **`[B]` Derivable on client:** Can be computed purely on the frontend from existing backend fields.
* **`[C]` Requires new backend projection field:** Backend API enhancement required.

### Data Field Classification Audit:

| Workspace UI Field | Status | Source in Backend |
|---|:---:|---|
| Threat Title, Attack Type, Severity | **`[A]`** | `workspace.threat.title`, `attack_type`, `severity` |
| Affected Entities (Host, IP, User) | **`[A]`** | `workspace.threat.affected_entities` |
| Confidence Score & Confidence State | **`[A]`** | `workspace.threat.confidence`, `confidence_state` |
| Current Planning Cycle & Max Cycles | **`[A]`** | `workspace.threat.current_cycle`, `max_cycles` |
| Active Capability Name & Status | **`[A]`** | `workspace.planner.active_capability` |
| Decision Rationale & Trigger Text | **`[A]`** | `workspace.planner.decision_rationale` |
| Replanning Flag (`is_replanning`) | **`[A]`** | `workspace.planner.is_replanning` |
| Chronological Trace (`selected_worker`) | **`[A]`** | `workspace.orchestration_history[].selected_worker` |
| Confidence Delta per Step ($\Delta C$) | **`[A]`** | `workspace.orchestration_history[].confidence_delta` |
| Step Latency & Gained Evidence Count | **`[A]`** | `workspace.orchestration_history[].latency_ms`, `evidence_count_gained` |
| Discovered Findings & MITRE Tags | **`[A]`** | `workspace.key_findings[].summary`, `mitre_technique_id` |
| Recommended Action & Risk Level | **`[A]`** | `workspace.recommendation.action`, `risk_level` |
| Supporting Evidence Citations | **`[A]`** | `workspace.recommendation.supporting_findings` |
| Human Review Status & Approver | **`[A]`** | `workspace.human_review.status`, `analyst_id` |
| Tri-Part `WHAT WE KNOW` (Facts) | **`[B]`** | Derived from confirmed `key_findings` and `affected_entities`. |
| Tri-Part `WHAT WE SUSPECT` (Hypo) | **`[B]`** | Derived from `planner.current_observation` and `threat.attack_type`. |
| Tri-Part `WHAT REMAINS UNRESOLVED` | **`[A]`** | Exposed directly in `planner.unresolved_questions`. |
| Revisit Detection Badge (`[REVISIT]`) | **`[B]`** | Client counts previous occurrences of `selected_worker` in `orchestration_history`. |
| Confidence Trajectory Sparkline | **`[B]`** | Client plots `confidence_before` and `confidence_after` across `orchestration_history`. |
| Entity Blast Radius Count | **`[B]`** | Client calculates `affected_entities.length`. |
| Evidentiary Weight Sort Rank | **`[B]`** | Client sorts `key_findings` by `confidence_score`. |

---

### Backend Contract Requirements for the Selected Frontend Direction (`[C]` Fields)

1. **Full Capability Utility Score Vector (`[C-1]`):** `orchestration_history[].candidate_utilities: Dict[str, float]` — to allow Level-2 utility breakdowns showing why a worker won over other candidates.
2. **Confidence Factor Decomposition (`[C-2]`):** `threat.confidence_factors: Dict[str, float]` — exposing the 6 factors computed by `ConfidenceEngine` (anomaly, correlation, graph density, etc.).
3. **Replay Delta Snapshot Endpoint (`[C-3]`):** `GET /api/investigations/{id}/replay?cycle={N}` — providing deterministic server-side state snapshots for historical scrubbing.

---

## Conclusion

With **Concept C (The Operator-First Triad)** selected and enhanced via the narrative simplicity of Concept A and the spatial graph replay of Concept B, Project Sentinel has an authoritative, validated product architecture ready for component implementation.
