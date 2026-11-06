# Project Sentinel — Final Frontend Design Direction & Implementation Blueprint

**Document Version:** 1.0.0  
**Status:** Authoritative Implementation Blueprint (Final Design Sign-off)  
**Author:** Principal Frontend Designer & UX Architect (`frontend-designer`)  
**Target Architecture:** React 18 / TypeScript / Tailwind CSS / Vite  
**Backend Grounding:** P0 Unified Workspace API (`GET /api/investigations/{id}/workspace`), P1 Evaluation API (`/api/evaluation/*`), Dataset & Replayer Endpoints (`/api/dataset/*`)  
**Predecessor Specifications:**  
- [`docs/FRONTEND_DESIGN_BRIEF.md`](file:///c:/Users/Aaditya%20Rana/OneDrive/Desktop/SEM5/CDAC-IP/docs/FRONTEND_DESIGN_BRIEF.md)  
- [`docs/FRONTEND_WORKSPACE_CONCEPTS.md`](file:///c:/Users/Aaditya%20Rana/OneDrive/Desktop/SEM5/CDAC-IP/docs/FRONTEND_WORKSPACE_CONCEPTS.md)  
- [`docs/FRONTEND_INFORMATION_ARCHITECTURE_AND_WORKFLOW.md`](file:///c:/Users/Aaditya%20Rana/OneDrive/Desktop/SEM5/CDAC-IP/docs/FRONTEND_INFORMATION_ARCHITECTURE_AND_WORKFLOW.md)  

---

## Executive Summary

Project Sentinel is an **autonomous, state-driven, multi-agent cybersecurity investigation system**. It does not use a fixed pipeline or an opaque chatbot wrapper. Instead, an adaptive Planner continuously evaluates investigation state, scores five distinct worker capabilities (`detection`, `correlation`, `investigation`, `response`, `reporting`), dispatches workers, incorporates evidence, reassesses uncertainty, and replans when contradictions or stagnation emerge.

This document represents the **final design-direction alignment review**. It synthesizes all prior design sprints into a singular, unambiguous blueprint for production React implementation.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               PROJECT SENTINEL IDENTITY                                │
│                                                                                        │
│     Threat Simulation  ──►  Autonomous Investigation  ──►  Agent Observability         │
│                                                                 │                      │
│                                                                 ▼                      │
│     Deterministic Case Replay  ◄──  Evidence-Grounded Action Approval                   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 1. Product Vision & Five-Page User Journey

Project Sentinel is deliberately designed **NOT to be a generic security dashboard**. The product experience follows a strict, intuitive operational journey:

```text
SIMULATE A THREAT
       ↓
WATCH THE AUTONOMOUS SYSTEM INVESTIGATE IT
       ↓
UNDERSTAND WHAT THE PLANNER AND AGENTS DID
       ↓
REVIEW THE EVIDENCE AND RECOMMENDATION
       ↓
APPROVE OR REJECT ACTION
       ↓
REVIEW OR REPLAY THE INVESTIGATION LATER
```

The application is structured into five dedicated pages anchored by a persistent 64px left-hand activity rail:

```text
┌────┬──────────────────────────────────────────────────────────────────────────────────┐
│ [S]│ [INVESTIGATE]  INV-2026-0892: Ares Botnet C2 Beaconing      [CRITICAL] [ACTIVE]  │
│    ├──────────────────────────────────────────────────────────────────────────────────┤
│ ⚡ │ COMMAND ANCHOR: Target: WORKSTATION-04 · Conf: 84.5% · [APPROVE HOST CONTAINMENT]│
│ Sim├──────────────────────────────────────────────────────────────────────────────────┤
│    │ VIEW TABS: [ Storyline (Default) ]  [ Agent Activity ]  [ Evidence ]  [ Details ] │
│ 🔍 │                                                                                  │
│ Inv│                                                                                  │
│    │                                                                                  │
│ 📜 │                               MAIN CONTENT STAGE                                 │
│ His│                          (Focused single-view canvas)                            │
│    │                                                                                  │
│ 📚 │                                                                                  │
│ Kno│                                                                                  │
│    │                                                                                  │
│ ⚙️ │                                                                                  │
│ Sys│                                                                                  │
└────┴──────────────────────────────────────────────────────────────────────────────────┘
```

### The Five Core Pages:

| Route | Page | Purpose & Scope |
|---|---|---|
| `/simulate` | **Simulate** | Select from the 5 verified CSE-CIC-IDS2018 benchmark scenarios and configure real backend execution parameters (instant autonomous run vs. interactive streaming replayer). |
| `/investigate` | **Investigate** | **The Primary Experience.** Anchored Command Canvas displaying the threat context, live Planner decisions, dynamic agent execution paths, grounded findings, and the human approval gate. |
| `/history` | **History** | Searchable audit archive of past investigations, case outcomes, and the launching pad for deterministic investigation replay. |
| `/knowledge` | **Knowledge** | Searchable reference catalog of MITRE ATT&CK techniques, containment playbooks, and ChromaDB vector store health telemetry. |
| `/system` | **System** | Low-cognitive-overhead operational status for backing services (DB, Redis, ChromaDB, Ollama) and P1 empirical benchmark evaluation metrics. |

---

# 2. Targeted Design Inspiration Synthesis

Sentinel draws specific, disciplined lessons from four industry-leading tools without copying any of their complete interfaces:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             INSPIRATION SYNTHESIS MATRIX                               │
├───────────────────┬──────────────────────────────────┬─────────────────────────────────┤
│ INSPIRATION       │ ADOPTED ATTRIBUTES               │ REJECTED / AVOIDED              │
├───────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ **LINEAR**        │ • Radical visual minimalism      │ • Kanban task board layouts     │
│                   │ • High-contrast typography       │ • Task management mechanics     │
│                   │ • Generous whitespace            │                                 │
│                   │ • Progressive disclosure         │                                 │
├───────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ **LANGSMITH**     │ • Truthful execution traces      │ • Raw developer debug clutter   │
│                   │ • Decision latency & utility     │ • Unfiltered stack traces       │
│                   │ • Replay scrubber concepts       │ • Complex multi-window tiling   │
│                   │ • Observable state transitions   │                                 │
├───────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ **CROWDSTRIKE**   │ • Threat context before data     │ • Dense, 50-widget dashboards   │
│                   │ • Clear severity hierarchy       │ • Obscure vendor-specific icons │
│                   │ • Blast-radius awareness         │ • Unranked alert firehoses      │
│                   │ • Action-oriented containment    │                                 │
├───────────────────┼──────────────────────────────────┼─────────────────────────────────┤
│ **MICROSOFT**     │ • Entity relationship awareness  │ • Decorative 3D hairball graphs │
│ **SENTINEL**      │ • Evidence chain of custody      │ • Nested 6-tab inspection mazes │
│                   │ • Structured investigation state │ • Unresponsive query delays     │
│                   │ • MITRE ATT&CK mapping           │                                 │
└───────────────────┴──────────────────────────────────┴─────────────────────────────────┘
```

---

# 3. Resolution of Prior Concept Contradictions

During earlier design sprints, architectural trade-offs were explored across three distinct workspace concepts. We now formally document why certain approaches were modified or rejected:

### 3.1 Rejection of the Permanent Three-Column Layout (Concept C Modification)
* **Earlier Proposal:** Concept C in `FRONTEND_WORKSPACE_CONCEPTS.md` proposed three permanently visible vertical columns (Col 1: Threat 25%, Col 2: Planner 45%, Col 3: Evidence & Action 30%).
* **Contradiction Identified:** On standard 1920×1080 monitors (accounting for OS scaling and browser chrome), three simultaneous 100vh columns compress cards down to ~350px. This cuts off process command lines, forces horizontal scrolling in decision cards, and creates visual exhaustion.
* **Final Resolution:** We adopt the **Anchored Command Canvas**:
  - The critical Level-0 elements from Column 1 and Column 3 are hoisted into a **sticky, compact Command Header Anchor** (Threat Summary, Severity, Calibrated Confidence, and Grounded Action Card with `[APPROVE]` / `[REJECT]`).
  - The main stage beneath the anchor uses **synchronized, full-width view tabs** (`Storyline`, `Agent Activity`, `Evidence`, `Details`), giving each view 100% reading width.
  - Deep diagnostics slide over in a 40% drawer from the right, preserving situational awareness.

### 3.2 Resolution of Investigation Replay Location
* **Contradiction Identified:** Whether Replay belongs in `History` as an isolated sub-page or inside `Investigate` as a viewing mode.
* **Final Resolution:** Replay is implemented as an **in-context mode of the Investigation Workspace** (`/investigate/{id}?mode=replay`). 
  - `History` acts as the catalog/archive.
  - Clicking `[REPLAY]` in History loads the investigation directly into the familiar workspace layout, swapping the sub-header into the **Replay Scrubber Controller**.
  - This eliminates duplicate code and gives analysts a unified mental model for both active and historical investigations.

### 3.3 Resolution of Knowledge Architecture
* **Contradiction Identified:** Standalone encyclopedia wiki vs. contextual in-line knowledge.
* **Final Resolution:** Hybrid approach:
  - **Contextual In-Line:** Clicking any MITRE tag or knowledge citation in Investigate opens a slide-over **Knowledge Drawer** immediately.
  - **Global Reference:** The `/knowledge` route provides a searchable technique explorer and ChromaDB collection statistics.

---

# 4. The Final Investigate Page Philosophy

The Investigate page is designed around a single psychological imperative:
> **An analyst must grasp the threat and its blast radius within 3 seconds, follow the agent's causal reasoning without reading raw logs, and approve containment grounded in verifiable evidence.**

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [SENTINEL]  Threats / INV-2026-0892: Ares Botnet C2 Beaconing              [SEVERITY: CRITICAL] [LIVE] │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ LEVEL 0 COMMAND ANCHOR BAR (STICKY)                                                                    │
│ Target: WORKSTATION-04 (192.168.1.104)  ·  User: corp\jdoe  ·  Cycles: 6/10                           │
│ Confidence: 84.5% [██████████████░░░░] High                                                           │
│ ┌────────────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │ [!] GROUNDED ACTION: Host Network Isolation (Sever active sockets on WORKSTATION-04)               │ │
│ │ Grounded in: EV-14 (C2 Socket), EV-11 (Encoded PowerShell), EV-08 (Word Macro)   Certainty: 84.5%  │ │
│ │ [ APPROVE CONTAINMENT ACTION ]   [ REJECT / DISMISS ]   [ SIMULATE BLAST RADIUS ]                  │ │
│ └────────────────────────────────────────────────────────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ PRIMARY VIEW SWITCHER:  [ Storyline (Active) ]   [ Agent Activity ]   [ Evidence (18) ]   [ Details ]  │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ STORYLINE VIEW (DEFAULT OPERATIONAL CANVAS)                                                            │
│                                                                                                        │
│ ┌───────────────────────────────────────────────────────────────────────┐ ┌──────────────────────────┐│
│ │ [t=10:00:15] · CYCLE 1: detection.execute                   +0.087 ΔC │ │ INVESTIGATION STATE      ││
│ │ Trigger: Untriaged NetFlow anomaly (Periodic outbound SSL traffic)    │ │                          ││
│ │ Result: Triaged 5 flow records. Destination tagged as suspicious.     │ │ [WHAT WE KNOW] (Facts)   ││
│ │ Evidence Gained: EV-01 (Beacon Interval: 120s, Dst: 13.58.225.34)     │ │ • Active C2 Socket (443) ││
│ └───────────────────────────────────┬───────────────────────────────────┘ │ • Target: WORKSTATION-04 ││
│                                     ▼                                     │ • User: corp\jdoe        ││
│ ┌───────────────────────────────────────────────────────────────────────┐ │                          ││
│ │ [t=10:00:22] · CYCLE 2: investigation.execute               +0.079 ΔC │ │ [WHAT WE SUSPECT] (Hypo) ││
│ │ Trigger: Host process tree verification required for compromised host │ │ • Word macro payload     ││
│ │ Result: Identified hidden PowerShell instance executing Base64 cmd.   │ │   dropped Ares beacon.   ││
│ │ Evidence Gained: EV-11 (PID 4812: powershell.exe -Enc SQ..)           │ │                          ││
│ └───────────────────────────────────┬───────────────────────────────────┘ │ [WHAT REMAINS UNRESOLVED]││
│                                     ▼                                     │ ? Has payload spread via ││
│ ┌───────────────────────────────────────────────────────────────────────┐ │   SMB to UBUNTU-SRV-01?  ││
│ │ [t=10:00:35] · [!] CYCLE 3: correlation.execute (REPLAN)   +0.260 ΔC  │ │ ? Persistence run keys?  ││
│ │ Trigger: Contradiction detected in parent PID of PowerShell process   │ └──────────────────────────┘│
│ │ Planner Decision: Selected Correlation over Investigation (0.94/0.42) │                             │
│ │ Result: Correlated parent process to WINWORD.EXE (PID 4108).          │ ┌──────────────────────────┐│
│ │ Evidence Gained: EV-08 (invoice_august.docm internet macro drop)      │ │ IMPACTED ASSET SCOPE     ││
│ └───────────────────────────────────┬───────────────────────────────────┘ │ • WORKSTATION-04 (Host)  ││
│                                     ▼                                     │ • corp\jdoe (User)       ││
│ ┌───────────────────────────────────────────────────────────────────────┐ │ • 13.58.225.34 (External)││
│ │ [t=10:00:48] · CYCLE 4: investigation.execute [REVISIT]     +0.067 ΔC │ └──────────────────────────┘│
│ │ Trigger: Inspect dropped Word macro artifact & scheduled task registry│                             │
│ │ Result: Extracted scheduled persistence task named 'AdobeUpdateTask'. │                             │
│ └───────────────────────────────────────────────────────────────────────┘                             │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

# 5. Dynamic Orchestration Visualization Rules

The interface must faithfully represent the non-linear, state-driven behavior of Project Sentinel:

```text
               ┌───────────────────────────────┐
               │    INVESTIGATION STATE        │
               │  (Knowns, Unknowns, Gaps)     │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
         ┌────►│   UTILITY HEURISTIC SCORING   │
         │     │  Detection:     0.05          │
         │     │  Correlation:   0.94 [WINNER] │
         │     │  Investigation: 0.42          │
         │     │  Response:      0.18          │
         │     │  Reporting:     0.10          │
         │     └───────────────┬───────────────┘
         │                     │
         │                     ▼
         │     ┌───────────────────────────────┐
         │     │     CAPABILITY EXECUTION      │
         │     │  (correlation.execute)        │
         │     └───────────────┬───────────────┘
         │                     │
         │                     ▼
         │     ┌───────────────────────────────┐
         │     │      NEW EVIDENCE ADDED       │
         │     │ (Confidence updated +0.260 ΔC)│
         │     └───────────────┬───────────────┘
         │                     │
         └── [Re-evaluate] ────┴─── [Terminal Condition Met]
```

### Binding Visualization Rules:
1. **Never Render a Fixed Pipeline:** Strictly ban decorative static sequences (`Detection ➔ Correlation ➔ Investigation ➔ Response ➔ Reporting`). The UI renders solely from `workspace.orchestration_history`.
2. **Explicit Capability Revisit Tagging:** When a capability is re-selected, it renders a violet badge `[REVISIT: 2nd Execution]` and displays the new trigger.
3. **Explicit Replanning Banners:** When stagnation or an evidence contradiction occurs, the cycle card renders an amber border (`border-amber-500/50`) and a badge `[!] REPLAN EVENT` stating the root cause.
4. **No Simulated Inner Monologue:** The UI displays **observable inputs**: utility scores, state triggers, confidence deltas, and execution latencies. Never simulate human conversational text.
5. **Tri-Part State Display:** Maintain the strict cognitive separation of:
   - `WHAT WE KNOW` (Verified factual entities & IOCs).
   - `WHAT WE SUSPECT` (Active working hypothesis with confidence score).
   - `WHAT REMAINS UNRESOLVED` (Open operational gaps from `unresolved_questions`).

---

# 6. Progressive Disclosure Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PROGRESSIVE DISCLOSURE ARCHITECTURE                             │
├────────────────────┬─────────────────────────┬─────────────────────────────────────────┤
│ LEVEL              │ PURPOSE                 │ DATA ELEMENTS                           │
├────────────────────┼─────────────────────────┼─────────────────────────────────────────┤
│ **LEVEL 0: SURFACE**│ 3-Second Situational    │ • Threat Title & Category               │
│ *(Sticky Anchor)*  │ Awareness & Immediate   │ • Semantic Severity Pill (Critical/High)│
│                    │ Containment Action      │ • Target Asset & Compromised User       │
│                    │                         │ • Calibrated Confidence % Meter         │
│                    │                         │ • Grounded Action Card & [APPROVE] Gate │
├────────────────────┼─────────────────────────┼─────────────────────────────────────────┤
│ **LEVEL 1: OPERATE**│ Operational Validation  │ • Storyline Chronological Stream        │
│ *(Main View Tabs)* │ & Agent Observability   │ • Decision Triggers & Confidence Deltas │
│                    │                         │ • Replan & Revisit Badges               │
│                    │                         │ • Tri-Part State Box                    │
│                    │                         │ • Ranked Evidence Ledger with MITRE Tags│
├────────────────────┼─────────────────────────┼─────────────────────────────────────────┤
│ **LEVEL 2: DIAGNOSE**│ Deep Forensic Audit   │ • Raw Telemetry JSON (Sysmon Event ID 1)│
│ *(Slide-Over Drawer│ & Technical Grounding   │ • Candidate Utility Scoring Vector      │
│  or Modal)*        │                         │ • ChromaDB RAG Chunk Citations          │
│                    │                         │ • Entity Blast-Radius SVG Topology      │
└────────────────────┴─────────────────────────┴─────────────────────────────────────────┘
```

---

# 7. Comprehensive Frontend Component Map

The upcoming frontend implementation will be structured into modular, single-responsibility React/TypeScript components:

```text
frontend/src/
├── api/
│   ├── client.ts                   # Axios client with base URL & error interceptor
│   ├── workspaceClient.ts          # GET /api/investigations/{id}/workspace (P0 API)
│   ├── datasetClient.ts            # GET /api/dataset/scenarios & POST /replay/*
│   ├── evaluationClient.ts         # GET /api/evaluation/runs & /summary (P1 API)
│   ├── reviewClient.ts             # POST /api/reviews/{id}/decision (HITL API)
│   └── healthClient.ts             # GET /health/dependencies
│
├── types/
│   ├── workspace.ts                # TypeScript interfaces matching backend Unified Workspace Projection
│   ├── dataset.ts                  # ScenarioMetadata, ReplayStatus interfaces
│   ├── evaluation.ts               # ScenarioEvaluationResult, AggregateMetrics interfaces
│   └── navigation.ts               # AppNavigationRoute enum ('simulate'|'investigate'|...)
│
├── components/
│   ├── shell/                      # Global Application Shell
│   │   ├── AppShell.tsx            # Master layout wrapping ActivityBar and MainCanvas
│   │   ├── ActivityBar.tsx         # Persistent 64px left rail with 5 icons and active indicator
│   │   └── GlobalStatusBar.tsx     # Bottom 28px status strip: backend connection, environment
│   │
│   ├── simulate/                   # /simulate Page
│   │   ├── SimulatePage.tsx        # Container coordinating scenario selection and launch
│   │   ├── ScenarioCardGrid.tsx    # 5 benchmark cards with MITRE technique pills
│   │   ├── ScenarioDetailPanel.tsx # Gold hypothesis, capture description, file metadata
│   │   └── ExecutionConfigBar.tsx  # Mode selector (Instant vs Replayer) & speed slider
│   │
│   ├── investigate/                # /investigate Page (THE CENTERPIECE)
│   │   ├── InvestigatePage.tsx     # Master investigation container fetching workspace API
│   │   │
│   │   ├── anchor/                 # Level-0 Command Header Anchor
│   │   │   ├── CommandHeaderAnchor.tsx # Sticky top anchor card
│   │   │   ├── ThreatProfileBar.tsx    # Attack title, critical pill, target asset
│   │   │   ├── ConfidenceMeter.tsx     # Numerical score, confidence state, sparkline
│   │   │   └── GroundedActionCard.tsx  # Recommended action, evidence citations, [APPROVE]
│   │   │
│   │   ├── views/                  # Primary Synchronized View Tabs
│   │   │   ├── ViewTabSwitcher.tsx     # [Storyline] [Agent Activity] [Evidence] [Details]
│   │   │   ├── StorylineView.tsx       # Concept A narrative stream of cycle transitions
│   │   │   ├── AgentActivityView.tsx   # Decision trace, candidate utility scores, metrics
│   │   │   ├── EvidenceLedgerView.tsx  # Ranked evidence findings, source workers, tags
│   │   │   └── ForensicDetailsView.tsx # Raw telemetry inspector and MITRE matrix
│   │   │
│   │   ├── cards/                  # Operational Cards used in views
│   │   │   ├── PlannerStepCard.tsx     # Single cycle card: trigger, worker, latency, +ΔC
│   │   │   ├── StateTriadBox.tsx       # WHAT WE KNOW, SUSPECT, UNRESOLVED container
│   │   │   ├── ReplanBanner.tsx        # Amber callout for contradiction/stagnation replans
│   │   │   ├── RevisitBadge.tsx        # Violet pill for revisited capability executions
│   │   │   └── EvidenceRowCard.tsx     # Discovered finding with evidentiary weight
│   │   │
│   │   ├── drawers/                # Level-2 Progressive Disclosure Drawers
│   │   │   ├── SlideOverDrawer.tsx     # Universal 40% slide-over drawer shell
│   │   │   ├── RawTelemetryDrawer.tsx  # Highlighted JSON and Sysmon event payload
│   │   │   ├── UtilityVectorDrawer.tsx # Candidate scoring matrix for all 5 capabilities
│   │   │   └── ContextKnowledgeDrawer.tsx # In-line MITRE technique & playbook citations
│   │   │
│   │   └── replay/                 # In-Context Replay Controller
│   │       ├── ReplayControllerBar.tsx # Step Back, Play/Pause, Step Fwd, Speed Selector
│   │       └── SnapshotScrubber.tsx    # Timeline scrubber reflecting version snapshots
│   │
│   ├── history/                    # /history Page
│   │   ├── HistoryPage.tsx         # Catalog container fetching GET /api/investigations
│   │   ├── CaseFilterBar.tsx       # Search by host, severity filter, status dropdown
│   │   └── InvestigationTable.tsx  # Clean table with case ID, target, cycles, confidence, [REPLAY]
│   │
│   ├── knowledge/                  # /knowledge Page
│   │   ├── KnowledgePage.tsx       # Catalog container for MITRE & playbook references
│   │   ├── TechniqueExplorer.tsx   # Searchable technique index
│   │   └── VectorStoreStats.tsx    # ChromaDB collection counts and index telemetry
│   │
│   ├── system/                     # /system Page
│   │   ├── SystemPage.tsx          # Diagnostics container
│   │   ├── DependencyHealthGrid.tsx# Live status cards: PostgreSQL, Redis, ChromaDB, Ollama
│   │   ├── CapabilityStatusCard.tsx# 5 Worker status indicators
│   │   └── EvaluationSummaryCard.tsx # P1 Empirical benchmark accuracy and calibration scores
│   │
│   └── ui/                         # Reusable Design System Primitives
│       ├── Badge.tsx               # Severity, status, and worker tags
│       ├── Button.tsx              # Primary, secondary, danger, ghost buttons
│       ├── Card.tsx                # Border-zinc-800 rounded container
│       ├── Modal.tsx               # Centered dialog for human approval confirmation
│       └── Tabs.tsx                # Styled navigation tabs
```

---

# 8. Frontend Data Readiness Matrix & Backend Contract Audit

Every UI data field is audited and classified:
* **`[A]` Available Now:** Natively provided by existing backend endpoints.
* **`[B]` Derivable on Client:** Computed on the client side from existing backend fields.
* **`[C]` Backend Enhancement Required:** Backend contract addition required.

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND DATA READINESS MATRIX                                  │
├────────────────────────────┬─────────────────────────────┬────────┬────────────────────┤
│ FRONTEND COMPONENT         │ REQUIRED BACKEND FIELD      │ STATUS │ SOURCE / GAP       │
├────────────────────────────┼─────────────────────────────┼────────┼────────────────────┤
│ **Simulate Page**          │                             │        │                    │
│ Scenario Catalog           │ ScenarioMetadata list       │  [A]   │ GET /api/dataset/  │
│                            │                             │        │ scenarios          │
│ Replayer Engine            │ Speed, batch size, step     │  [A]   │ POST /api/dataset/ │
│                            │                             │        │ replay/*           │
│ Launch Autonomous Run      │ Run loop until completion   │  [A]   │ POST /api/planner/ │
│                            │                             │        │ .../run            │
├────────────────────────────┼─────────────────────────────┼────────┼────────────────────┤
│ **Investigate Page**       │                             │        │                    │
│ Threat Summary & Asset     │ Title, severity, entities   │  [A]   │ workspace.threat   │
│ Calibrated Confidence      │ Current confidence float    │  [A]   │ workspace.threat   │
│ Confidence Factor Breakdown│ 6-factor weight vectors     │  [C-2] │ GAP: Backend must  │
│                            │                             │        │ expose factors     │
│ Grounded Action Card       │ Action, risk level, status  │  [A]   │ workspace.recomm.  │
│ Evidence Citations         │ Supporting finding IDs      │  [A]   │ workspace.recomm.  │
│                            │                             │        │ supporting_findings│
│ Human Review Action Gate   │ Submit approval / rejection │  [A]   │ POST /api/reviews/ │
│                            │                             │        │ {id}/decision      │
│ Storyline Cycle Steps      │ Cycle, capability, delta C  │  [A]   │ workspace.orch_hist│
│ State Trigger Rationale    │ Heuristic trigger text      │  [A]   │ workspace.orch_hist│
│ Capability Revisit Badge   │ Count previous occurrences  │  [B]   │ Client counts hist │
│ Replan Alert Callout       │ is_replanning boolean       │  [A]   │ workspace.planner  │
│ Tri-Part: Known Facts      │ Confirmed findings & assets │  [B]   │ Client derives     │
│ Tri-Part: Suspicions       │ Hypothesis & observation    │  [B]   │ Client derives     │
│ Tri-Part: Gaps / Questions │ Unresolved questions list   │  [A]   │ workspace.planner  │
│ Evidence Findings Ledger   │ Finding summaries, MITRE    │  [A]   │ workspace.key_find.│
│ Candidate Utility Scores   │ Comparative utility vector  │  [C-1] │ GAP: Backend must  │
│                            │ for all 5 capabilities      │        │ expose candidate   │
│                            │                             │        │ utilities          │
│ Raw Telemetry Inspector    │ Raw Sysmon / NetFlow JSON   │  [B]   │ finding.provenance │
├────────────────────────────┼─────────────────────────────┼────────┼────────────────────┤
│ **History & Replay**       │                             │        │                    │
│ Case Catalog Archive       │ List of past investigations │  [A]   │ GET /api/investiga.│
│ Replay State Snapshots     │ State snapshot per version  │  [A]   │ GET /api/investiga.│
│                            │                             │        │ {id}/snapshots     │
├────────────────────────────┼─────────────────────────────┼────────┼────────────────────┤
│ **Knowledge Page**         │                             │        │                    │
│ Semantic Query & Citations │ RAG query context & sources │  [A]   │ POST /api/knowledge│
│ Vector Store Telemetry     │ Technique & playbook counts │  [A]   │ GET /api/knowledge/│
│                            │                             │        │ stats              │
├────────────────────────────┼─────────────────────────────┼────────┼────────────────────┤
│ **System Page**            │                             │        │                    │
│ Dependency Health Status   │ DB, Redis, Chroma, Ollama   │  [A]   │ GET /health/deps   │
│ Empirical Benchmark Metrics│ Accuracy, coverage, ECE     │  [A]   │ GET /api/eval/sum. │
└────────────────────────────┴─────────────────────────────┴────────┴────────────────────┘
```

### Graceful Frontend Degradation for `[C]` Gaps:
Until the two minor backend enhancements (`[C-1]` candidate utilities and `[C-2]` confidence factors) are deployed:
1. **Utility Vector Gap (`[C-1]`):** The frontend renders the winning capability with its summary rationale string (fully available in `[A]`), while displaying a clean informational pill: *"Full comparative utility vector will be exposed in backend contract v1.1"*.
2. **Confidence Factor Gap (`[C-2]`):** The frontend renders the calibrated aggregate confidence meter (available in `[A]`) and shows the qualitative state (`high`, `medium`, `low`) without breaking the UI.

---

# 9. Implementation Handoff & Sprint 1 Scope

### 9.1 Finalized Decisions
1. **Application Navigation:** Persistent left rail (`/simulate`, `/investigate`, `/history`, `/knowledge`, `/system`).
2. **Investigation Layout:** Anchored Command Canvas with Level-0 Command Anchor and four focused view tabs (`Storyline`, `Agent Activity`, `Evidence`, `Details`).
3. **Default View:** `[ Storyline ]` is the default operational view.
4. **Agent Representation:** Append-only chronological trace or dynamic DAG; zero fixed pipelines.
5. **Human Authority:** Consequential containment actions are blocked until analyst clicks `[ APPROVE ]`.
6. **Design System Tokens:** Strict Dark SOC palette (`zinc-950` canvas, `zinc-900` cards, semantic accents).

### 9.2 Components to Build First (Frontend Implementation Sprint 1)
```text
PHASE 1: SHELL & PRIMITIVES
  ├── src/types/ (workspace.ts, dataset.ts, navigation.ts)
  ├── src/api/ (client.ts, workspaceClient.ts, datasetClient.ts, healthClient.ts)
  ├── src/components/ui/ (Badge, Button, Card, Tabs, Modal)
  └── src/components/shell/ (AppShell, ActivityBar, GlobalStatusBar)

PHASE 2: SIMULATE PAGE (/simulate)
  ├── ScenarioCardGrid (5 verified benchmark profiles)
  └── ExecutionConfigBar (Launch autonomous run trigger)

PHASE 3: INVESTIGATION WORKSPACE (/investigate)
  ├── CommandHeaderAnchor (Threat profile, confidence, GroundedActionCard)
  ├── ViewTabSwitcher ([Storyline] [Agent Activity] [Evidence] [Details])
  ├── StorylineView (PlannerStepCard, StateTriadBox, ReplanBanner)
  └── EvidenceLedgerView (Ranked findings and MITRE chips)

PHASE 4: SYSTEM & HEALTH (/system)
  └── DependencyHealthGrid & EvaluationSummaryCard
```

### 9.3 Acceptance Criteria for Frontend Implementation Sprint 1
1. **Compilation & Build:** Frontend compiles cleanly with `npm run build` with zero TypeScript (`tsc`) warnings or unused variable errors.
2. **Navigation Operability:** Clicking left rail tabs seamlessly routes between `/simulate`, `/investigate`, `/history`, `/knowledge`, and `/system`.
3. **Simulate Operability:** Selecting a benchmark scenario (e.g. `botnet_c2`) and clicking `[ Launch Investigation ]` triggers the backend, creates an investigation, and transitions to `/investigate/{id}`.
4. **Truthful Dynamic Orchestration:** The Storyline view renders the real sequence of Planner decisions, badging revisits and replans from database records.
5. **Grounded Action Approval:** Clicking `[ APPROVE ACTION ]` dispatches `POST /api/reviews/{id}/decision` and visually shifts status to `[ APPROVED · CONTAINED ]`.
6. **System Health Visibility:** The `/system` view truthfully displays live PostgreSQL, Redis, ChromaDB, and Ollama connectivity from `/health/dependencies`.

---

## Conclusion

This document concludes the frontend design planning phase. The product philosophy is verified, previous concept contradictions are reconciled, every UI element is grounded in audited backend reality, and a disciplined implementation sequence is defined.

**We are officially ready to begin Frontend Implementation Sprint 1.**
