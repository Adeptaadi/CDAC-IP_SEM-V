# Project Sentinel — Frontend Workflow & Information Architecture Specification

**Document Version:** 1.0.0  
**Status:** Authoritative Architectural Blueprint  
**Author:** Principal Frontend Designer & UX Architect (`frontend-designer`)  
**Target Codebase Integration:** P0 Unified Workspace API (`GET /api/investigations/{id}/workspace`), P1 Evaluation API (`GET /api/evaluation/*`), Dataset & Replayer Endpoints (`/api/dataset/*`)  
**Binding Directives:** [`docs/FRONTEND_DESIGN_BRIEF.md`](file:///c:/Users/Aaditya%20Rana/OneDrive/Desktop/SEM5/CDAC-IP/docs/FRONTEND_DESIGN_BRIEF.md), [`docs/FRONTEND_WORKSPACE_CONCEPTS.md`](file:///c:/Users/Aaditya%20Rana/OneDrive/Desktop/SEM5/CDAC-IP/docs/FRONTEND_WORKSPACE_CONCEPTS.md)  

---

## Executive Decision

Following the B3 Backend Solidification and Autonomous Agent Audit, the backend of Project Sentinel is verified as a **state-driven, non-linear, multi-agent cybersecurity investigation system**. 

To transition from conceptual design to production engineering, this document establishes the **official product-level information architecture and end-to-end user workflow**.

### Key Architectural Rulings:
1. **Global Navigation Model:** Adopt a persistent, compact left-side activity bar (`Simulate`, `Investigate`, `History`, `Knowledge`, `System`) paired with a wide, focused main content viewport.
2. **Workspace Structure Decision (Tabs vs. Fixed Columns):** We **reject** the rigid, permanently visible three-column layout as the default screen partition. Forcing three equal columns simultaneously creates cramped cards on standard 1080p displays and induces visual fatigue. Instead, we adopt the **Anchored Command Canvas**:
   - A **persistent Level-0 Command Header & Action Anchor** (Threat Context, Calibrated Confidence, and Grounded Human Action Card) remains permanently visible.
   - The primary stage utilizes focused, synchronized views:
     `[ Storyline (Narrative Stream) ]` (Default operational view — Concept A)  
     `[ Agent Activity (Dynamic Trace & Utility Map) ]` (Observability & Revisit view — Concept B)  
     `[ Evidence Ledger (Ranked Findings & Provenance) ]`  
     `[ Details (Diagnostic Telemetry & Entity Blast Graph) ]`
3. **Investigation Replay Location:** Replay is implemented as an **in-context mode of the Investigation Workspace** (accessible via a "Replay Mode" toggle), while the `History` section serves as the searchable archive and compliance audit catalog.
4. **Knowledge Architecture:** We reject an isolated, disconnected wiki. Knowledge is engineered primarily as **in-context forensic drill-down drawers** directly accessible from MITRE tags and evidence findings, supported by a global knowledge index search.
5. **Simulation Grounding:** The `Simulate` page is strictly bounded by genuine backend capabilities (the 5 CSE-CIC-IDS2018 benchmark scenario profiles and streaming event replayer). All fictional sliders (e.g. arbitrary packet payload synthesizers or live malware detonation controls) are prohibited.

---

# 1. Finalized Application Navigation

The application uses an ultra-clean, 64px persistent left-hand navigation rail with high-contrast active state indicators:

```text
┌────┬──────────────────────────────────────────────────────────────────────────────────┐
│ [S]│ [INVESTIGATE]  INV-2026-0892: Ares Botnet C2 Beaconing      [CRITICAL] [ACTIVE]  │
│    ├──────────────────────────────────────────────────────────────────────────────────┤
│ ⚡ │ LEVEL 0 ANCHOR: Target: WORKSTATION-04 · Confidence: 84.5% · [APPROVE CONTAINMENT]│
│ Sim├──────────────────────────────────────────────────────────────────────────────────┤
│    │ VIEW TABS: [ Storyline (Default) ]  [ Agent Activity ]  [ Evidence ]  [ Details ] │
│ 🔍 │                                                                                  │
│ Inv│                                                                                  │
│    │                                                                                  │
│ 📜 │                               MAIN CONTENT AREA                                  │
│ His│                         (Driven by active navigation)                            │
│    │                                                                                  │
│ 📚 │                                                                                  │
│ Kno│                                                                                  │
│    │                                                                                  │
│ ⚙️ │                                                                                  │
│ Sys│                                                                                  │
└────┴──────────────────────────────────────────────────────────────────────────────────┘
```

### Navigation Route Specifications:

| Route | Label | Icon | Primary User Question Answered | Primary User Action |
|---|---|---|---|---|
| `/simulate` | **Simulate** | `Zap` | "What threat scenario do I want to inject into the system?" | Select a scenario and launch an investigation |
| `/investigate` | **Investigate** | `ShieldAlert` | "What is the threat, what is the AI doing, and what should I approve?" | Review live investigation, inspect evidence, authorize containment |
| `/history` | **History** | `History` | "What past investigations exist and what were their outcomes?" | Browse historical cases, filter by threat type, open past runs |
| `/knowledge` | **Knowledge** | `BookOpen` | "What TTPs, MITRE techniques, and playbooks does Sentinel know?" | Search threat definitions and view RAG vector index health |
| `/system` | **System** | `Cpu` | "Are the backend services, workers, and models operational?" | Monitor service health (DB, Redis, ChromaDB, Ollama) and P1 metrics |

---

# 2. Primary User Journey: End-to-End Workflow

The core product journey bridges user triggers, autonomous agent execution, human observation, and human-in-the-loop authorization:

```text
               ┌───────────────────────────────────────────────────┐
               │  1. SELECT OR SIMULATE THREAT                     │
               │  • User chooses scenario (e.g. Ares Botnet C2)    │
               │  • Selects mode: Instant Run vs Interactive Replay│
               │  • Clicks [Launch Investigation]                  │
               └─────────────────────────┬─────────────────────────┘
                                         │  (User Initiates)
                                         ▼
               ┌───────────────────────────────────────────────────┐
               │  2. INGESTION & INVESTIGATION SEEDING             │
               │  • Backend creates durable Investigation row      │
               │  • Seeds 5 initial telemetry events as Evidence   │
               │  • Transitions route to /investigate/{id}         │
               └─────────────────────────┬─────────────────────────┘
                                         │  (Autonomous)
                                         ▼
               ┌───────────────────────────────────────────────────┐
         ┌────►│  3. PLANNER EVALUATION & CAPABILITY SELECTION     │◄────┐
         │     │  • Planner assesses knowns vs. unknowns           │     │
         │     │  • Scores candidate worker utility (0.0 to 1.0)   │     │
         │     │  • Detects stagnation/contradictions -> REPLAN    │     │
         │     │  • Selects highest utility capability             │     │
         │     └─────────────────────────┬─────────────────────────┘     │
         │                               │  (Autonomous)                 │
         │                               ▼                               │
         │     ┌───────────────────────────────────────────────────┐     │
         │     │  4. WORKER EXECUTION & STATE SHIFT                │     │
         │     │  • Worker executes (Latency: 10-50ms)             │     │
         │     │  • Produces new findings, links, or playbooks     │     │
         │     │  • ConfidenceEngine computes new confidence (+ΔC) │     │
         │     │  • Persists PlannerDecision & WorkerExecution     │     │
         │     └─────────────────────────┬─────────────────────────┘     │
         │                               │  (Autonomous)                 │
         │                               ▼                               │
         │     ┌───────────────────────────────────────────────────┐     │
         │     │  5. ANALYST OBSERVATION (LIVE MONITORING)         │     │
         │     │  • Analyst observes Storyline & Agent Activity    │     │
         │     │  • Inspects state triggers and confidence delta   │     │
         │     │  • Drills into Evidence Drawer for raw telemetry  │     │
         │     └─────────────────────────┬─────────────────────────┘     │
         │                               │                               │
         └─── [Terminal Condition NOT Met]──┴─── [Terminal Met: Conf ≥ 0.80 or Max Cycles]
                                         │
                                         ▼
               ┌───────────────────────────────────────────────────┐
               │  6. GROUNDED RECOMMENDATION & HUMAN REVIEW        │
               │  • Planner produces Response recommendation       │
               │  • Grounded Action Card renders with citations    │
               │  • Analyst clicks [APPROVE] or [REJECT]           │
               │  • Backend processes POST /api/reviews/{id}/dec   │
               └─────────────────────────┬─────────────────────────┘
                                         │  (Human Authority Gate)
                                         ▼
               ┌───────────────────────────────────────────────────┐
               │  7. TRANSITION TO ARCHIVE & REPLAY                │
               │  • Investigation status: "Contained / Closed"     │
               │  • Appears in /history catalog                    │
               │  • Analyst can launch deterministic Replay Mode   │
               └───────────────────────────────────────────────────┘
```

---

# 3. Page-by-Page Architecture

## 3.1 Simulate Page (`/simulate`)

### Purpose & Reality Check
The Simulate page is the primary injection mechanism for evaluating Project Sentinel. We explicitly audit what the backend currently supports versus what is speculative:
* **Genuinely Supported Now:**
  * Listing all 5 verified CSE-CIC-IDS2018 scenarios (`botnet_c2`, `brute_force`, `dos_goldeneye`, `infiltration`, `web_attacks`) via `GET /api/dataset/scenarios`.
  * Pre-configured scenario metadata: attack description, MITRE techniques, gold hypothesis, and source capture day.
  * Streaming replay parameters: replay speed multiplier (`1.0x`, `2.0x`, `5.0x`) and batch dispatch size (`batch_size=50`) via `POST /api/dataset/replay/load/{id}`.
  * Launching autonomous investigation: initializing investigation with synthetic seed events and running `PlannerEngine.run_autonomous(max_steps=10)`.
* **Prohibited / Fabricated Controls (NOT supported):**
  * Slider for "Attack Intensity" or "Malware Evasion Rate" (no backend model supports this).
  * Custom target IP modification on the fly (scenarios have static network captures).
  * Manual adversary payload upload.

### Layout & Information Architecture:
```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ SIMULATE CYBERSECURITY THREAT SCENARIO                                                 │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. SELECT BENCHMARK ATTACK SCENARIO                                                    │
│                                                                                        │
│ ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐           │
│ │ Botnet Ares C2       │  │ Infiltration Lateral │  │ Brute Force SSH/FTP  │  [+ 2]    │
│ │ Category: Botnet C2  │  │ Category: Infiltrate │  │ Category: BruteForce │           │
│ │ Severity: CRITICAL   │  │ Severity: HIGH       │  │ Severity: HIGH       │           │
│ │ MITRE: T1071.001     │  │ MITRE: T1059, T1021  │  │ MITRE: T1110.001     │           │
│ │ Target: WORKSTATION4 │  │ Target: WS-04, SRV-01│  │ Target: UBUNTU-SRV-01│           │
│ │ [ SELECTED ]         │  │ [ SELECT SCENARIO ]  │  │ [ SELECT SCENARIO ]  │           │
│ └──────────────────────┘  └──────────────────────┘  └──────────────────────┘           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. EXECUTION & INGESTION PARAMETERS                                                    │
│                                                                                        │
│ Execution Mode:                                                                        │
│ (•) Instant Autonomous Investigation (Runs Planner autonomous loop to completion)      │
│ ( ) Interactive Event Streaming Replay (Dispatches events via streaming replayer)     │
│                                                                                        │
│ Autonomous Planning Constraints:                                                       │
│ Max Planning Cycles: [ 10 ] (Default: 10, Range: 1-20)                                 │
│ Confidence Termination Threshold: [ 0.80 ]                                             │
│                                                                                        │
│ Replayer Parameters (Only active if Interactive Streaming selected):                   │
│ Streaming Speed: [ 1.0x ▼ ] (1x, 2x, 5x, Instant)   Batch Size: [ 50 events ]          │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [ LAUNCH INVESTIGATION ] ──► (Creates investigation & navigates to /investigate/{id})  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3.2 Investigate Page (`/investigate/{id}`)

### Purpose & Architecture
The Investigate page is the **centerpiece of Project Sentinel**. It tells the complete story of the threat, the system's evolving understanding, the dynamic Planner decisions, and the grounded recommended action.

### Structural Ruling: The Anchored Command Canvas
Rather than a crowded three-column grid, the workspace employs an **Anchored Command Canvas**:
1. **Persistent Top Command Header (Level 0):**
   * Threat Title, Severity Pill, Impacted Asset, Current Confidence Meter.
   * Grounded Action Card with explicit `[ APPROVE ]` and `[ REJECT ]` buttons.
2. **Sub-Navigation View Switcher:**
   `[ Storyline ]` | `[ Agent Activity ]` | `[ Evidence ]` | `[ Details ]`
3. **Primary Stage:** 100% of the viewport width is dedicated to the selected view, providing optimal reading width and zero visual competition.
4. **Diagnostic Slide-Over Drawer (Level 2):** Clicking any finding ID, entity tag, or utility score slides over a 40% drawer from the right.

---

### View 1: `[ Storyline ]` (Default Operational View)
* **Inspiration:** Concept A (The Linear Narrative Stream).
* **Content:** Calm, vertical chronological stream of state transitions.
* **Structure per Card:**
  * Step header: Cycle number, timestamp, capability tag, and confidence delta ($\Delta C$).
  * State trigger: Why the Planner chose this worker (e.g. *"Untriaged NetFlow anomaly detected"*).
  * Worker outcome: Summary of findings produced.
  * Evidence gained: Clickable evidence chips (`EV-01`, `EV-11`).
  * Replan indicator: Amber callout if the step was triggered by stagnation or contradiction.
* **Side Rail (or Collapsible Accordion):** Tri-Part Investigation State:
  * `WHAT WE KNOW` (Verified factual entities & IOCs).
  * `WHAT WE SUSPECT` (Active working hypothesis).
  * `WHAT REMAINS UNRESOLVED` (Open operational gaps).

---

### View 2: `[ Agent Activity ]` (Dynamic Orchestration & Observability)
* **Inspiration:** Concept B (The Adaptive Map) and Concept C (Planner Observability).
* **Content:** Deep visibility into the autonomous engine's decision-making.
* **Dual Visualization Toggle:**
  * **Option 1 (Dynamic Trace List):** Tabular/card breakdown showing candidate utility scores for all 5 capabilities at every cycle, revealing exactly why the winning worker won.
  * **Option 2 (Spatial State DAG):** 2D node-graph rendering states, capability nodes, revisit loop-backs, and replan branches.
* **Observability Metrics Card:**
  * Planning cycles elapsed.
  * Revisit count (e.g. `Investigation revisited 1 time`).
  * Replanning events count (`1 replan triggered by contradiction`).
  * Execution latency per worker.

---

### View 3: `[ Evidence ]` (Forensic Findings & Provenance)
* **Content:** Comprehensive evidence ledger ranked by evidentiary weight and confidence.
* **Columns / Cards:**
  * Evidence ID (`EV-14`).
  * Summary & Artifact Type (Network Socket, Process Tree, Dropped File).
  * Associated Entity (Host, IP, User, Process PID).
  * MITRE ATT&CK Technique (e.g. `T1071.001: Web Protocols`).
  * Evidentiary Status (`DIRECT_SYSTEM_OBSERVATION`, `CORRELATED_FINDING`).
  * Provenance Link (Source worker ID, Planner decision ID).

---

### View 4: `[ Details ]` (Technical Telemetry & Entity Blast Graph)
* **Content:** Full forensic diagnostics.
* **Sections:**
  * Entity Blast Radius Graph (Host, Account, IP, Socket topology).
  * Raw Telemetry Event Inspector (Syntax-highlighted JSON, Sysmon Event ID 1 / Event ID 3).
  * MITRE ATT&CK Matrix Navigator (Highlights observed vs. suspected techniques).
  * Investigation Audit Trail (State version transitions, timestamps, user modifications).

---

## 3.3 History Page (`/history`)

### Purpose
The History page provides an audit catalog of all completed, contained, or archived investigations. It allows incident commanders and evaluators to review past cases, inspect final reports, and launch deterministic investigation replay.

### Layout & Architecture:
```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ INVESTIGATION ARCHIVE & AUDIT CATALOG                                                  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ Search & Filters: [ Search by Host, Threat, or ID... ]  Status: [ All ▼ ]  Severity: [ All ▼ ] │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ CASE ID        THREAT CATEGORY       TARGET HOST     CYCLES  CONFIDENCE  STATUS  ACTION│
├────────────────────────────────────────────────────────────────────────────────────────┤
│ INV-2026-0892  Ares Botnet C2        WORKSTATION-04    6     84.5% [H]   CONTAINED [REPLAY]│
│ INV-2026-0871  SSH Brute Force       UBUNTU-SRV-01     6     88.2% [H]   RESOLVED  [REPLAY]│
│ INV-2026-0840  Web SQL Injection     WEB-PROD-01       6     79.1% [M]   DISMISSED [REPLAY]│
│ INV-2026-0799  Infiltration Lateral  WORKSTATION-04    6     85.0% [H]   CONTAINED [REPLAY]│
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Architectural Decision on Investigation Replay:
> **RULING:** Replay is implemented as an **in-context mode of the Investigation Workspace** (`/investigate/{id}?mode=replay`), rather than a separate isolated page. 
> 
> When an analyst clicks `[ REPLAY ]` from the History table or from an active investigation, the Investigation Workspace switches its sub-header to render the **Replay Scrubber Controller**. This preserves the exact same visual components (Storyline, Agent Activity, Evidence) and drives them through the historical snapshots.

---

## 3.4 Knowledge Page (`/knowledge`)

### Purpose & Architecture
The Knowledge page provides visibility into Project Sentinel's RAG knowledge layer (powered by ChromaDB). 

### Contextual vs. Standalone Rulings:
1. **Primary Contextual Experience (In-Workspace):** Whenever an analyst clicks a MITRE technique tag (e.g. `T1059.001`) or a knowledge citation in the Investigation Workspace, an unobtrusive **Knowledge Slide-Over Drawer** opens, displaying technique descriptions, detection logic, and playbook countermeasures without leaving the investigation.
2. **Global Reference Experience (`/knowledge`):** The standalone Knowledge page serves as a reference catalog:
   * **MITRE ATT&CK Technique Browser:** Searchable index of techniques loaded into ChromaDB.
   * **Containment Playbook Directory:** Approved remediation scripts and rollback protocols.
   * **Vector Store Telemetry:** Vector count across collections (`mitre_techniques`, `playbooks`, `historical_cases`) via `GET /api/knowledge/stats`.

---

## 3.5 System Page (`/system`)

### Purpose
The System page provides low-cognitive-overhead operational diagnostics for SOC engineers and project evaluators. It is strictly separated from the operational investigation flow.

### Content:
* **Service Dependency Health:** Live status cards for PostgreSQL, Redis, ChromaDB, and Ollama (backed by `GET /health/dependencies`).
* **Agent Capability Registry:** Status of the 5 worker capabilities (`detection`, `correlation`, `investigation`, `response`, `reporting`).
* **P1 Empirical Evaluation Observability:**
  * Summary metrics from `GET /api/evaluation/summary` (Scenario Accuracy, Evidence Coverage, Calibration Error).
  * Direct trigger button to run standalone benchmark evaluation suite (`POST /api/evaluation/run`).

---

# 4. Reassessment of Previous Frontend Concepts

We evaluate Concepts A, B, and C against the finalized navigation and workflow:

| Previous Concept | Original Role | Reassessed Role in Final Architecture | Architectural Rationale |
|---|---|---|---|
| **Concept A: Chronological Narrative** | Standalone Workspace | **Primary `[ Storyline ]` View in Investigate** | Unmatched reading clarity. Placing this as the default tab guarantees that any operator understands the incident in under 10 seconds. |
| **Concept B: Adaptive Investigation Map** | Standalone Workspace | **Secondary `[ Agent Activity ]` Graph Mode** | Too cognitively heavy for rapid frontline triage, but exceptional for technical evaluation and executive briefings. Integrated as an optional toggle within Agent Activity. |
| **Concept C: Three-Column Triad** | Standalone Workspace | **Level-0 Command Anchor & Action Header** | Modified: instead of three rigid full-height columns that crowd 1080p screens, the threat context and action card become a sticky command header, while the main stage uses focused view tabs. |

---

# 5. Dynamic Agent Visualization Rules

To protect architectural integrity, all frontend views must obey four binding visualization rules:

### Rule 1: The Zero-Pipeline Mandate
* **Prohibited:** Never render a static horizontal pipeline such as:
  `Detection ➔ Correlation ➔ Investigation ➔ Response ➔ Reporting`
* **Enforced:** Render an append-only sequence or DAG generated purely from `workspace.orchestration_history`.

### Rule 2: Explicit Capability Revisit Badging
* When `investigation.execute` is selected at Cycle 2 and re-selected at Cycle 4, the second occurrence must render an explicit badge:
  `[REVISIT: 2nd Execution]`
* The card must display the new state trigger that prompted re-inspection.

### Rule 3: Visual Signaling for Replans & Contradictions
* When the Planner encounters stagnation or evidence contradiction, the decision card must render an amber warning border (`border-amber-500/50`) and a prominent badge:
  `[!] REPLAN EVENT`
* The trigger text must state the root cause (e.g. *"Stagnation detected: worker diversification enforced"*).

### Rule 4: Prohibition of Fabricated Chain-of-Thought
* The UI must **never** render simulated AI "thinking aloud" or conversational monologues.
* Display observable inputs: candidate utility scores, factor weights, and state changes.

---

# 6. Investigation Replay Specification

Replay is implemented via the **Investigation Replay Controller**:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ REPLAY CONTROLLER: INV-2026-0892  ·  State Version: 4 / 6  ·  Playback: [► PLAY]       │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ [◄ Step Back]   [► Play / Pause]   [Step Fwd ►]   Speed: [1x ▼]   Scrubber: 66%        │
│ ══════════════════════════════════════════════════○══════════════════════════════════  │
│ Cycle 1 (t=0s)     Cycle 2 (t=12s)     Cycle 3 (t=25s)     Cycle 4 (t=42s) [ACTIVE]    │
│ Detection          Investigation       Correlation [REPLAN] Investigation [REVISIT]    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Replay Data Source:
Backed by `GET /api/investigations/{id}/snapshots` which already provides immutable `InvestigationStateVersion` records including `version_number`, `cycle_number`, `confidence`, and `state_snapshot`.

### Interactive Behavior:
1. Scrubbing to Cycle $N$ restores the entire workspace state (confidence, findings count, working hypothesis) to that exact moment.
2. Newly unearthed evidence items flash with a soft emerald highlight.
3. Pausing on a Replan step opens an explanatory tooltip detailing the contradiction.

---

# 7. Frontend Data Readiness Matrix

Audit of all proposed frontend features against existing backend reality:

| Frontend Feature / Page | Required Data Fields | Existing Backend Support | Status | Gap / Required Action |
|---|---|---|:---:|---|
| **Simulate: Scenario Catalog** | Name, description, MITRE techniques, gold hypothesis | `GET /api/dataset/scenarios` | **`[A]`** | Fully supported out of the box. |
| **Simulate: Streaming Replayer** | Speed, batch size, load, start, step controls | `POST /api/dataset/replay/*` | **`[A]`** | Fully supported out of the box. |
| **Investigate: Threat Profile** | Title, attack type, severity, target entity | `workspace.threat` (`GET /api/investigations/{id}/workspace`) | **`[A]`** | Fully supported via P0 projection. |
| **Investigate: Calibrated Confidence** | Confidence float, state enum (`high`, etc.) | `workspace.threat.confidence` | **`[A]`** | Fully supported via P0 projection. |
| **Investigate: Confidence Factors** | 6-factor decomposition weights | *Not exposed in projection* | **`[C-2]`** | **GAP:** Backend must expose `threat.confidence_factors: Dict[str, float]`. |
| **Investigate: Grounded Action** | Action name, risk level, approval status | `workspace.recommendation` | **`[A]`** | Fully supported via P0 projection. |
| **Investigate: Action Citations** | List of supporting finding IDs and summaries | `workspace.recommendation.supporting_findings` | **`[A]`** | Fully supported via P0 projection. |
| **Investigate: Storyline Feed** | Chronological cycle steps, latencies, $\Delta C$ | `workspace.orchestration_history` | **`[A]`** | Fully supported via P0 projection. |
| **Investigate: Utility Scores** | Comparative candidate scores per cycle | *Only summary rationale exposed* | **`[C-1]`** | **GAP:** Backend must expose `candidate_utilities: Dict[str, float]` in history. |
| **Investigate: Tri-Part State** | `WHAT WE KNOW / SUSPECT / UNRESOLVED` | `unresolved_questions` (`[A]`); facts/hypo derivable (`[B]`) | **`[A/B]`** | Fully realizable on client from existing fields. |
| **Investigate: Evidence Ledger** | Findings, source worker, MITRE tags, entities | `workspace.key_findings` | **`[A]`** | Fully supported via P0 projection. |
| **Investigate: Raw Telemetry** | Raw Sysmon JSON / packet flows | `Evidence.raw_data` in DB | **`[B]`** | Exposed in finding details popover. |
| **History: Investigation Archive** | List of past cases, cycles, status, confidence | `GET /api/investigations` | **`[A]`** | Fully supported out of the box. |
| **History: Replay Snapshots** | State snapshots per version/cycle | `GET /api/investigations/{id}/snapshots` | **`[A]`** | Fully supported out of the box. |
| **Knowledge: Semantic Query** | RAG search query, top-k, citations | `POST /api/knowledge/query` | **`[A]`** | Fully supported out of the box. |
| **Knowledge: Collection Stats** | Technique counts, playbook counts | `GET /api/knowledge/stats` | **`[A]`** | Fully supported out of the box. |
| **System: Service Dependencies** | Status of DB, Redis, ChromaDB, Ollama | `GET /health/dependencies` | **`[A]`** | Fully supported out of the box. |
| **System: Evaluation Metrics** | Aggregate accuracy, ECE, coverage | `GET /api/evaluation/summary` | **`[A]`** | Fully supported via P1 evaluation API. |

---

# 8. Version 1 Scope & Prioritization

To ensure a disciplined, realistic delivery, features are divided into strict release tiers:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                 VERSION 1 FEATURE SCOPE                                 │
├──────────────────────────┬─────────────────────────────┬────────────────────────────────┤
│ MUST HAVE (V1 CORE)      │ SHOULD HAVE (NEXT ITERATION)│ FUTURE / DEFERRED              │
├──────────────────────────┼─────────────────────────────┼────────────────────────────────┤
│ • Left Nav Rail (5 tabs) │ • Spatial DAG view in       │ • Custom adversary payload     │
│ • Simulate Page:         │   Agent Activity            │   upload in Simulate           │
│   - 5 Benchmark Scenarios│ • Confidence Factor         │ • Live multi-analyst chat      │
│   - Instant Autonomous   │   breakdown popover (needs  │ • Automated SIEM ingestion     │
│     Execution Trigger    │   [C-2] backend contract)   │   webhook integrations         │
│ • Investigate Page:      │ • Comparative utility score │ • PDF forensic report export   │
│   - Anchored Command Bar │   matrix (needs [C-1])      │ • Dark/Light theme toggle      │
│   - Grounded Action Card │ • Interactive Replay        │   (V1 dark theme only)         │
│     with HITL Approval   │   Scrubber in Investigate   │                                │
│   - Storyline Narrative  │ • MITRE Technique Matrix    │                                │
│   - Evidence Ledger      │   navigator in Details      │                                │
│   - Tri-Part State Box   │                             │                                │
│ • History Page:          │                             │                                │
│   - Investigation Archive│                             │                                │
│ • System Page:           │                             │                                │
│   - Dependency Health    │                             │                                │
│   - Evaluation Summary   │                             │                                │
└──────────────────────────┴─────────────────────────────┴────────────────────────────────┘
```

---

# 9. Decisions Made and Decisions Intentionally Left Open

### Decisions Made:
1. **Navigation:** Compact persistent left rail (`Simulate`, `Investigate`, `History`, `Knowledge`, `System`).
2. **Investigation Layout:** Anchored Command Canvas (Level-0 top anchor + 4 synchronized view tabs).
3. **Primary View:** `[ Storyline ]` is the default operational view for investigations.
4. **Pipeline Representation:** Strictly banned. All agent activity is rendered from `workspace.orchestration_history`.
5. **Human Authority:** Containment actions require explicit analyst approval via `POST /api/reviews/{id}/decision`.
6. **V1 Theme:** Refined dark SOC theme (`zinc-950` canvas, `zinc-900` cards, semantic accents).

### Decisions Intentionally Left Open (For Frontend Sprint 3):
1. **Spatial Graph Engine Choice:** Whether to use `@xyflow/react` (React Flow) or lightweight SVG/D3 for the optional Agent Activity DAG.
2. **State Management Library:** Whether `zustand` or React Query (`@tanstack/react-query`) alone is sufficient for polling `/workspace` updates.
3. **Replay Step Animation Mechanics:** Whether state transitions animate automatically at 1.5-second intervals or require explicit operator clicks.

---

## Conclusion & Readiness

This specification finalizes the frontend product workflow and information architecture. Every view is grounded in existing backend data contracts, the non-linear multi-agent Planner is truthfully exposed, and the scope for Version 1 is strictly prioritized.

**We are officially ready to proceed to Frontend Implementation Sprint 3 (React Component Foundation & Application Shell).**
