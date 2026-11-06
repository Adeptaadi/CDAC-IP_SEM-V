# Project Sentinel — Backend Decision Logic, Threshold & Investigation Loop Audit

**Document Version:** 1.0.0  
**Audit Date:** 2026-11-05  
**Audit Classification:** Rigorous Technical Architecture & Empirical Execution Audit  
**Target Subsystems:** `PlannerEngine`, `ConfidenceEngine`, `select_worker`, `should_terminate`, `WORKER_REGISTRY`  
**Execution Environment:** Python 3.11.8, SQLite (In-Memory Isolation), Real Database Persistence  

---

## 1. Executive Conclusion: Is the Investigation Loop Functioning Correctly?

**Definitive Finding: NO. The backend investigation loop is NOT functioning correctly as an adaptive decision-making system.**

While Project Sentinel's execution pipeline executes without unhandled runtime exceptions (100% execution success rate), empirical decision traces and source code analysis demonstrate that **the investigation loop is not genuinely adaptive**. 

Instead, the loop exhibits deterministic state locking, pseudo-convergence, and loop repetition driven by six systemic architectural defects:

1. **State-Locked Utility Scoring:** As soon as an initial hypothesis is confirmed (which `InvestigationWorker` does immediately on cycle 1), the utility function locks `ResponseWorker` at a permanent maximum score of `1.0`. All other workers are mathematically suppressed to scores between `0.0` and `0.12`.
2. **Total Absence of Repeat-Selection Penalties or Cooldowns:** `select_worker` has zero awareness of previous worker selections, zero capability exclusion, and zero repeat-selection penalties. It deterministically selects `response` consecutively on every subsequent cycle.
3. **Evidence Duplication & Infinite Provenance Pollution:** `ResponseWorker` emits the identical 4 containment findings every execution. `PlannerEngine` inserts every finding as a new `Evidence` record without deduplication, persisting dozens of identical evidence rows.
4. **Unconditional Baseline Confidence Inflation:** Even when a worker generates **zero evidence** and neutral confidence signals (`0.50`), the `ConfidenceEngine` awards an unconditional positive logit delta (+0.233 logit / +0.03 to +0.06 probability). This is driven by synthetic formulas for historical similarity (`0.2 + cycle * 0.12`), single-worker agreement default (`0.5`), and ungrounded knowledge retrieval.
5. **Inoperable Stagnation Detection:** The stagnation detection logic checks `gain > 0.02` across recent cycles. Because the unconditional baseline confidence drift guarantees a gain between `+0.04` and `+0.09` every cycle, the stagnation counter `cycles_since_confidence_gain` is **reset to 0 on every single cycle**. Stagnation cannot trigger during normal or even completely stalled worker executions.
6. **Bypassed Replanning Architecture:** Explicit replanning (`decision_type = "replan"`, `[REPLAN]` summary) is never evaluated or called in `PlannerEngine.run_cycle`. The non-linear `DynamicPlanner` authored in Phase 9 was completely bypassed by `PlannerEngine`, leaving the live runtime running a rigid 5-line utility formula.
7. **`max_cycles_reached` as De Facto Termination:** Scenarios terminate via `max_cycles_reached` in P1 benchmark runs solely because the benchmark budget (`max_cycles=6`) cuts off the run before the response worker spam reaches `0.85` (which occurs at cycle 10). Safety termination is functioning as the sole regular termination mechanism.

---

## 2. Complete Threshold Inventory & Audit

Every threshold, constant, weight, and decision boundary in the Planner and Confidence engines was extracted from source code and audited:

| Parameter | Current Value | Source File / Function | Behavioral Effect | Basis |
|---|---:|---|---|---|
| `CONFIDENCE_AUTO_COMPLETE_THRESHOLD` | `0.85` | `config.py:34`, `selection.py:90` | Closes investigation and marks status as `completed` if cycle >= 3. | **Arbitrary initial constant** (no ROC/calibration curve basis). |
| `MIN_CYCLES_FOR_COMPLETION` | `3` | `selection.py:91`, `engine.py:295` | Prevents termination before cycle 3 even if confidence exceeds 0.85. | **Design assumption** (safety guard to prevent 1-step premature close). |
| `STAGNATION_CYCLE_LIMIT` | `3` | `config.py:35`, `selection.py:97` | Triggers termination with reason `stagnation` and requests analyst review. | **Design assumption** (reasonable threshold, but invalidated by drift). |
| `STAGNATION_GAIN_THRESHOLD` | `0.02` | `engine.py:59` | Minimum confidence delta to reset stagnation counter. | **Arbitrary initial constant** (set below baseline drift of 0.04-0.08). |
| `MAX_PLANNING_CYCLES` | `15` (`6` in eval) | `config.py:33`, `selection.py:85`, `eval_harness.py:42` | Hard termination safety cap triggering `max_cycles_reached`. | **Design assumption** (budget constraint; 6 is too low for 0.85 threshold). |
| `WEIGHT_DETECTION` | `0.15` | `config.py:38`, `confidence.py:21` | Multiplier for worker raw confidence signal. | **Arbitrary initial constant** (heuristic weighting). |
| `WEIGHT_EVIDENCE` | `0.20` | `config.py:39`, `confidence.py:22` | Multiplier for evidence count and source diversity. | **Arbitrary initial constant** (heuristic weighting). |
| `WEIGHT_CORRELATION` | `0.15` | `config.py:40`, `confidence.py:23` | Multiplier for edge/node ratio in graph. | **Arbitrary initial constant** (heuristic weighting). |
| `WEIGHT_KNOWLEDGE` | `0.15` | `config.py:41`, `confidence.py:24` | Multiplier for ChromaDB RAG chunk similarity. | **Arbitrary initial constant** (heuristic weighting). |
| `WEIGHT_AGREEMENT` | `0.15` | `config.py:42`, `confidence.py:25` | Multiplier for cross-worker confidence variance. | **Arbitrary initial constant** (heuristic weighting). |
| `WEIGHT_HISTORICAL` | `0.20` | `config.py:43`, `confidence.py:26` | Multiplier for historical case similarity. | **Arbitrary initial constant** (heuristic weighting). |
| `HISTORICAL_SCORE_SLOPE` | `0.12` | `engine.py:216` | Formula `min(0.85, 0.2 + cycle * 0.12)` artificially grows historical similarity every cycle. | **Arbitrary initial constant** (synthetic simulation artifact). |
| `HISTORICAL_SCORE_BASE` | `0.20` | `engine.py:216` | Starting historical similarity score on cycle 0. | **Arbitrary initial constant** (synthetic simulation artifact). |
| `UNTRIAGED_EVENT_GATE` | `cycle == 0` | `engine.py:78` | Sets `untriaged_event_count = 1 if cycle == 0 else 0`. | **Design assumption** (disables Detection worker forever after cycle 1). |
| `GRAPH_DENSITY_SCALE` | `0.2` | `engine.py:81` | Formula `min(1.0, len(ev) * 0.2)` hits 1.0 when evidence >= 5. | **Arbitrary initial constant** (disables Correlation worker when ev >= 5). |
| `RESPONSE_UTILITY_GATE` | `1.0` | `selection.py:68-71` | If `has_confirmed_hypothesis == True`, sets Response score to 1.0. | **Design assumption** (creates permanent utility lock). |
| `REPORTING_CONF_GATE` | `0.65` | `selection.py:62` | Minimum confidence required before Reporting can score 1.0. | **Design assumption** (gated behind stagnation which never occurs). |
| `REPORTING_STAGNATION_GATE` | `1` | `selection.py:62` | Requires `cycles_since_gain >= 1` for Reporting to score 1.0. | **Design assumption** (unreachable because cycles_since_gain is always 0). |
| `EVIDENCE_SATURATION_DIVISOR` | `5.0` | `confidence.py:52` | Divisor in `min(1.0, count / 5.0)` saturating evidence quantity. | **Design assumption** (assumes 5 findings is saturated). |
| `CORROBORATION_BONUS` | `1.2` | `confidence.py:50` | Multiplier applied when worker findings count > 1. | **Design assumption** (rewards quantity, not independent corroboration). |
| `SINGLE_WORKER_AGREEMENT` | `0.5` | `confidence.py:71` | Fallback delta when only 1 worker confidence is passed. | **Arbitrary initial constant** (adds constant +0.075 weighted delta every cycle). |
| `LOGIT_CLAMP_EPSILON` | `1e-5` | `confidence.py:7` | Numerical stability clamp for logit transforms `(1e-5, 1 - 1e-5)`. | **Externally derived** (standard numerical practice). |
| `RAG_TOP_K` | `3` | `engine.py:126` | Number of chunks retrieved per cycle from ChromaDB. | **Design assumption** (standard vector DB top-k). |
| `RAG_FALLBACK_SIMILARITY` | `0.65` | `engine.py:226` | Assumed similarity when ChromaDB returns empty. | **Arbitrary initial constant** (adds constant +0.078 weighted delta). |
| `MITRE_SOURCE_RELIABILITY` | `0.95` | `engine.py:227` | Weight assigned to knowledge chunks containing MITRE. | **Design assumption** (high trust in curated MITRE ATT&CK). |
| `FALLBACK_SOURCE_RELIABILITY`| `0.80` | `engine.py:227` | Weight assigned to non-MITRE knowledge chunks. | **Design assumption** (moderate trust). |

---

## 3. Full Investigation Decision Trace (`infiltration` Scenario)

A complete cycle-by-cycle execution trace was captured directly from real DB records running the `infiltration` scenario through `PlannerEngine`:

```
Execution Seed: 5 synthetic telemetry events + 1 initial active hypothesis (confidence: 0.35)
Initial Investigation Confidence: 0.1500 (very_low)
```

### Cycle 1
- **State Before Decision:**
  - Cycle: `0`, Confidence: `0.1500`, Evidence Count: `5`
  - Hypothesis: `"Malicious macro/payload executed powershell.exe..."` (status: `active`, conf: `0.3500`)
  - Gaps / Contradictions: None, Untriaged Events: `1`, Graph Density: `1.0`
  - Previous Worker: `None`
- **Candidate Selection:**
  - `detection`: `0.2000` (untriaged: 1, total: 5)
  - `correlation`: `0.0000` (density 1.0 clamped: `5 * (1.0 - 1.0) = 0.0`)
  - `investigation`: `0.6500` (`1.0 - 0.35 = 0.65`)
  - `reporting`: `0.0000` (conf < 0.65, cycles_since_gain < 1)
  - `response`: `0.0000` (`has_confirmed_hypothesis` is `False`)
- **Decision:**
  - Selected Worker: `investigation` (Capability: `investigation.execute`, Score: `0.6500`)
  - Rationale: Formulates and validates attack hypotheses using retrieved cybersecurity knowledge.
  - Decision Nature: **Initial Strategy Selection**
- **Worker Result:**
  - Status: `success`, Latency: `12ms`
  - Produced Evidence: `1` record (`ev_id: c4a1...`), Genuinely New: `1`, Duplicate: `0`
  - Finding: `"Investigation validated hypothesis 'Malicious Macro Execution with Encoded PowerShell Reverse Shell'. Grounded in MITRE ATT&CK technique T1566.001."`
  - Hypothesis Updates: Status changed from `active` to `confirmed`, confidence updated to `0.8800`.
- **State After Execution:**
  - Confidence: `0.1500` -> `0.1916` ($\Delta = +0.0416$ prob / $+0.2950$ logit)
  - Factor Breakdown: `detection: +0.0570`, `evidence: +0.0200`, `correlation: +0.0250`, `knowledge: +0.0780`, `agreement: +0.0750`, `historical: +0.0400`
  - Evidence Count: `6` ($+1$)

---

### Cycle 2
- **State Before Decision:**
  - Cycle: `1`, Confidence: `0.1916`, Evidence Count: `6`
  - Hypothesis: Confirmed (`0.8800`)
  - Gaps: Untriaged events: `0`, Graph Density: `1.0`
  - Previous Worker: `investigation`
- **Candidate Selection:**
  - `detection`: `0.0000` (untriaged_event_count is 0)
  - `correlation`: `0.0000` (graph density is 1.0)
  - `investigation`: `0.1200` (`1.0 - 0.88 = 0.12`)
  - `reporting`: `0.0000` (conf 0.1916 < 0.65)
  - `response`: `1.0000` (`has_confirmed_hypothesis` is `True`)
- **Decision:**
  - Selected Worker: `response` (Capability: `response.execute`, Score: `1.0000`)
  - Rationale: Response worker generated 4 prioritized containment actions with risk/impact evaluations.
  - Decision Nature: **Strategy Change (Investigation -> Response)**
- **Worker Result:**
  - Status: `success`, Latency: `2ms`
  - Produced Evidence: `4` records, Genuinely New: `4`, Duplicate: `0`
  - Findings: (1) Network Isolate Host, (2) Block Inbound/Outbound IP, (3) Terminate powershell.exe, (4) Force Password Reset.
- **State After Execution:**
  - Confidence: `0.1916` -> `0.2537` ($\Delta = +0.0621$ prob / $+0.3610$ logit)
  - Factor Breakdown: `detection: +0.0675`, `evidence: +0.0576`, `correlation: +0.0187`, `knowledge: +0.0780`, `agreement: +0.0750`, `historical: +0.0640`
  - Evidence Count: `10` ($+4$)

---

### Cycle 3
- **State Before Decision:**
  - Cycle: `2`, Confidence: `0.2537`, Evidence Count: `10`
  - Hypothesis: Confirmed (`0.8800`)
  - Previous Worker: `response`
- **Candidate Selection:**
  - `detection`: `0.0000`, `correlation`: `0.0000`, `investigation`: `0.1200`, `reporting`: `0.0000`, `response`: `1.0000`
- **Decision:**
  - Selected Worker: `response` (Capability: `response.execute`, Score: `1.0000`)
  - Decision Nature: **Unpenalized Consecutive Continuation (Repeat 1)**
- **Worker Result:**
  - Status: `success`, Latency: `2ms`
  - Produced Evidence: `4` records, **Genuinely New: 0, Duplicate: 4**
  - Findings: Exact duplicate descriptions of Cycle 2 actions.
- **State After Execution:**
  - Confidence: `0.2537` -> `0.3281` ($\Delta = +0.0744$ prob / $+0.3620$ logit)
  - Factor Breakdown: `detection: +0.0675`, `evidence: +0.0411`, `correlation: +0.0125`, `knowledge: +0.0780`, `agreement: +0.0750`, `historical: +0.0880`
  - Evidence Count: `14` ($+4$ duplicates)

---

### Cycle 4
- **State Before Decision:**
  - Cycle: `3`, Confidence: `0.3281`, Evidence Count: `14`
  - Previous Worker: `response`
- **Candidate Selection:**
  - `detection`: `0.0000`, `correlation`: `0.0000`, `investigation`: `0.1200`, `reporting`: `0.0000`, `response`: `1.0000`
- **Decision:**
  - Selected Worker: `response` (Score: `1.0000`)
  - Decision Nature: **Unpenalized Consecutive Continuation (Repeat 2)**
- **Worker Result:**
  - Status: `success`, Produced Evidence: `4` records, **Genuinely New: 0, Duplicate: 4**
- **State After Execution:**
  - Confidence: `0.3281` -> `0.4151` ($\Delta = +0.0870$ prob / $+0.3740$ logit)
  - Factor Breakdown: `detection: +0.0675`, `evidence: +0.0320`, `correlation: +0.0094`, `knowledge: +0.0780`, `agreement: +0.0750`, `historical: +0.1120`
  - Evidence Count: `18` ($+4$ duplicates)

---

### Cycle 5
- **State Before Decision:**
  - Cycle: `4`, Confidence: `0.4151`, Evidence Count: `18`
  - Previous Worker: `response`
- **Candidate Selection:**
  - `detection`: `0.0000`, `correlation`: `0.0000`, `investigation`: `0.1200`, `reporting`: `0.0000`, `response`: `1.0000`
- **Decision:**
  - Selected Worker: `response` (Score: `1.0000`)
  - Decision Nature: **Unpenalized Consecutive Continuation (Repeat 3)**
- **Worker Result:**
  - Status: `success`, Produced Evidence: `4` records, **Genuinely New: 0, Duplicate: 4**
- **State After Execution:**
  - Confidence: `0.4151` -> `0.5118` ($\Delta = +0.0967$ prob / $+0.3900$ logit)
  - Factor Breakdown: `detection: +0.0675`, `evidence: +0.0262`, `correlation: +0.0075`, `knowledge: +0.0780`, `agreement: +0.0750`, `historical: +0.1360`
  - Evidence Count: `22` ($+4$ duplicates)

---

### Cycle 6
- **State Before Decision:**
  - Cycle: `5`, Confidence: `0.5118`, Evidence Count: `22`
  - Previous Worker: `response`
- **Candidate Selection:**
  - `detection`: `0.0000`, `correlation`: `0.0000`, `investigation`: `0.1200`, `reporting`: `0.0000`, `response`: `1.0000`
- **Decision:**
  - Selected Worker: `response` (Score: `1.0000`)
  - Decision Nature: **Unpenalized Consecutive Continuation (Repeat 4)**
- **Worker Result:**
  - Status: `success`, Produced Evidence: `4` records, **Genuinely New: 0, Duplicate: 4**
- **State After Execution:**
  - Confidence: `0.5118` -> `0.6121` ($\Delta = +0.1003$ prob / $+0.4090$ logit)
  - Factor Breakdown: `detection: +0.0675`, `evidence: +0.0222`, `correlation: +0.0062`, `knowledge: +0.0780`, `agreement: +0.0750`, `historical: +0.1600`
  - Evidence Count: `26` ($+4$ duplicates)
- **Termination Check:**
  - Cycle `6 == max_cycles (6)`. Terminated with reason: `max_cycles_reached`.

---

## 4. Worker Utility Score Comparison Matrix

Across all 6 cycles of the `infiltration` investigation, the candidate utility scores were:

| Cycle | Previous Worker | Detection | Correlation | Investigation | Reporting | Response | Winner |
|---|---|---:|---:|---:|---:|---:|---|
| **1** | None | 0.2000 | 0.0000 | **0.6500** | 0.0000 | 0.0000 | `investigation` |
| **2** | `investigation` | 0.0000 | 0.0000 | 0.1200 | 0.0000 | **1.0000** | `response` |
| **3** | `response` | 0.0000 | 0.0000 | 0.1200 | 0.0000 | **1.0000** | `response` |
| **4** | `response` | 0.0000 | 0.0000 | 0.1200 | 0.0000 | **1.0000** | `response` |
| **5** | `response` | 0.0000 | 0.0000 | 0.1200 | 0.0000 | **1.0000** | `response` |
| **6** | `response` | 0.0000 | 0.0000 | 0.1200 | 0.0000 | **1.0000** | `response` |

### Utility Defect Analysis
1. **Detection is artificially starved:** `untriaged_event_count` is hardcoded as `1 if cycle == 0 else 0`. Once Cycle 1 starts, Detection utility collapses permanently to `0.0`.
2. **Correlation is artificially starved:** `graph_density` is calculated as `min(1.0, evidence_count * 0.2)`. Because 5 events are seeded at start, `graph_density = 1.0` immediately. The formula `evidence_count * (1.0 - graph_density)` evaluates to `N * 0.0 = 0.0`. Correlation can never run unless initial evidence is $< 5$ (which occurred only in `web_attacks`, where it ran twice before collapsing).
3. **Investigation is suppressed after hypothesis confirmation:** `1.0 - max(hypotheses_confidences) = 1.0 - 0.88 = 0.12`. It can never overcome `1.0`.
4. **Reporting is unreachable:** Requires `confidence >= 0.65` AND `cycles_since_confidence_gain >= 1`. Even when confidence reaches 0.65, `cycles_since_gain` is 0 because of artificial drift.
5. **Response locks at 1.0 indefinitely:** `if state.has_confirmed_hypothesis: scores["response"] = 1.0`. There is no condition checking whether response actions were already formulated, whether the investigation is concluded, or whether containment has already succeeded.

---

## 5. Repeated Worker Selection Root Cause Analysis

Addressing the six specific questions mandated by the audit:

### Question 1: Why did the Response capability have the highest utility?
**Answer:** Because `select_worker` assigns `scores["response"] = 1.0` whenever `state.has_confirmed_hypothesis` is `True`. In Cycle 1, `InvestigationWorker` validated the initial hypothesis and set its status to `"confirmed"`. From Cycle 2 onward, `has_confirmed_hypothesis` remained permanently `True`. Since all other four worker utility formulas evaluate to $\le 0.12$, `response` was guaranteed the highest score.

### Question 2: What utility scores did the other capabilities receive?
**Answer:** On every cycle from Cycle 2 through Cycle 6:
- `detection`: **0.0000** (because `untriaged_event_count` was 0)
- `correlation`: **0.0000** (because `graph_density` saturated at 1.0)
- `investigation`: **0.1200** (because hypothesis confidence was 0.88, yielding $1.0 - 0.88$)
- `reporting`: **0.0000** (because confidence was $< 0.65$ and `cycles_since_gain` was 0)
- `response`: **1.0000**

### Question 3: Did the previous Response execution produce genuinely new information?
**Answer: NO.** In Cycle 2, `ResponseWorker` produced 4 initial containment recommendations. In Cycles 3, 4, 5, and 6, `ResponseWorker` produced the **exact same 4 containment recommendations** with identical text, identical entity references (`WORKSTATION-04`, `13.58.225.34`, `corp\jdoe`), and identical risk levels. Across Cycles 3-6, **0 genuinely new pieces of information** were produced.

### Question 4: Did the repeated execution answer a new unresolved question?
**Answer: NO.** The `PlannerEngine` execution loop does not track unresolved questions (`unresolved_questions` list is not maintained or checked by `PlannerEngine.run_cycle`). No questions were formulated, modified, or answered during repeated selections.

### Question 5: Did confidence increase because of novel evidence or because repeated simulated evidence received additional weight?
**Answer: Confidence increased primarily because of synthetic baseline formulas, not novel evidence.**  
Of the $+0.4090$ logit delta in Cycle 6:
- **$+0.1600$ (39.1%)** came from `historical`, which increases unconditionally by $+0.12$ every cycle based purely on `planning_cycle_count`.
- **$+0.0780$ (19.1%)** came from `knowledge`, which queries ChromaDB for the fixed title and returns $\sim 0.65$ similarity regardless of worker actions.
- **$+0.0750$ (18.3%)** came from `agreement`, which defaults to $+0.50$ delta ($0.5 \times 0.15 = 0.075$) because only a single worker confidence signal is provided.
- **$+0.0675$ (16.5%)** came from `detection`, where the repeated simulated `ResponseWorker` signal (`0.95`) was credited again.
- **Only $+0.0222$ (5.4%)** came from `evidence`, and even that was based on raw count ($26$ duplicate records) rather than genuine novelty.

### Question 6: Was the Planner aware that the same capability had already been used?
**Answer: NO.** `select_worker` takes only `InvestigationStateSnapshot`. The snapshot does **not** contain `previous_worker`, `worker_history`, or any execution tally. The `select_worker` function contains no code checking prior decisions, no cooldown mechanism, and no penalty for repeated capability invocation.

---

## 6. Confidence Model Audit & Mathematical Decomposition

The `ConfidenceEngine` computes the updated confidence via:
$$\text{Confidence}_{\text{new}} = \sigma\left(\text{logit}(\text{Confidence}_{\text{current}}) + \Delta\right)$$
where $\Delta = \sum_{i=1}^{6} w_i \cdot \delta_i$.

### Factor-Level Decomposition (Cycle 4 Example)
Current Confidence: `0.3281` ($\text{logit} = -0.7168$)

$$\begin{aligned}
\Delta &= w_{\text{det}} \delta_{\text{det}} + w_{\text{ev}} \delta_{\text{ev}} + w_{\text{corr}} \delta_{\text{corr}} + w_{\text{know}} \delta_{\text{know}} + w_{\text{agree}} \delta_{\text{agree}} + w_{\text{hist}} \delta_{\text{hist}} \\
&= (0.15 \times 0.450) + (0.20 \times 0.160) + (0.15 \times 0.0625) + (0.15 \times 0.520) + (0.15 \times 0.500) + (0.20 \times 0.560) \\
&= 0.0675 + 0.0320 + 0.0094 + 0.0780 + 0.0750 + 0.1120 \\
&= +0.3739
\end{aligned}$$

$$\text{Confidence}_{\text{new}} = \sigma(-0.7168 + 0.3739) = \sigma(-0.3429) = 0.4151 \quad (\text{Net Probability Gain: } +0.0870)$$

### Verification of Audit Checkpoints

| Audit Requirement | Verification Result | Evidence & Code Location |
|---|---|---|
| **Can the same evidence influence confidence more than once?** | **YES (Confirmed Defect)** | `engine.py:164-176` inserts all worker findings into `Evidence` table on every cycle with no deduplication. `total_evidence` in `confidence.py:49` counts all persisted rows. |
| **Does simulated evidence receive the same weight as observed evidence?** | **YES (Confirmed Defect)** | `ResponseWorker.confidence_signal = 0.95` (`response_worker.py:53`) is passed directly into `raw_detection` in `confidence.py:45`, receiving the exact same weight ($0.15$) as genuine detection sensor events. |
| **Do repeated worker executions receive diminishing returns?** | **NO (Confirmed Defect)** | While `source_diversity` in evidence quality drops slightly, `historical_sim_score` increases by $+0.12$ every cycle (`engine.py:216`). The total delta $\Delta$ actually **grew** from $+0.3610$ in Cycle 2 to $+0.4090$ in Cycle 6. |
| **Is evidence source diversity correctly measured?** | **NO (Confirmed Defect)** | `distinct_sources` in `engine.py:211` queries distinct `source_type` strings. All worker outputs share the single string `"worker_output"`, so distinct sources is always $\le 2$ regardless of how many different workers participate. |
| **Can confidence increase when no genuinely new evidence was obtained?** | **YES (Confirmed Defect)** | In controlled Test Case A, a worker producing **0 evidence** and neutral signal still produced a confidence gain of $+0.0556$ probability ($+0.3830$ logit). |

---

## 7. Stagnation and Replanning Validation

Controlled empirical tests were executed against real database instances (persisted in test suite `test_decision_logic_audit.py`):

### Case A — No Progress
- **Scenario:** A worker executes but produces `0` findings (`new_evidence = []`) and neutral confidence signal (`0.50`).
- **Observed Behavior:**
  - Cycle 1: Confidence `0.1500` -> `0.2056` ($\text{gain} = +0.0556$)
  - Cycle 2: Confidence `0.2056` -> `0.2507` ($\text{gain} = +0.0451$)
  - Cycle 3: Confidence `0.2507` -> `0.3071` ($\text{gain} = +0.0564$)
  - Cycle 4: Confidence `0.3071` -> `0.3755` ($\text{gain} = +0.0684$)
- **Stagnation Counter:** `cycles_since_confidence_gain = 0` across all 4 cycles.
- **Root Cause:** In `engine.py:59`, the code checks `if gain > 0.02: break`. Because the baseline drift produces a gain of $+0.045$ to $+0.068$ even with zero findings, `gain > 0.02` is always `True`. The counter never increments.
- **Next-Cycle Decision:** The Planner continues unaware that no progress was made.

### Case B — Repeated / Duplicate Evidence
- **Scenario:** `ResponseWorker` runs in consecutive cycles producing identical recommendations.
- **Observed Behavior:**
  - Cycle 1 (Initial Response): Evidence count `1` -> `5`, Confidence gain $+0.0723$.
  - Cycle 2 (Duplicate Response): Evidence count `5` -> `9`, Confidence gain $+0.0763$.
  - Cycle 3 (Duplicate Response): Evidence count `9` -> `13`, Confidence gain $+0.0864$.
- **Finding:** Duplicate evidence produces **accelerating** confidence gain ($+0.0723 \to +0.0864$) rather than zero or diminishing gain.

### Case C — Strategy Failure & Replanning
- **Requirement:** When a capability fails to advance the investigation, Planner must detect insufficient progress, record an explicit replan decision (`[REPLAN]`), and select an alternative capability.
- **Observed Behavior:**
  - Source inspection of `PlannerEngine.run_cycle` (`engine.py`) reveals **zero references to replanning**.
  - `PlannerEngine` does not inspect `last_error`, does not compute capability failure, and does not set `decision_type = "replan"`.
  - The entire replanning architecture authored in `DynamicPlanner` (`app/planner/decider.py:75-90`) is **dead code in the production runtime**. `PlannerEngine` directly imports and calls `select_worker()`, bypassing `DynamicPlanner`.
  - **Verdict:** Genuine autonomous replanning does **not** occur in Project Sentinel runtime execution.

---

## 8. Termination Logic Audit

Each termination condition was audited against real execution:

### Condition 1: High-Confidence Termination (`confidence >= 0.85` and `cycle >= 3`)
- **Can it actually be reached?** **YES.**
- **Under what circumstances?** When `max_steps` is set to $\ge 10$, the loop reaches confidence `0.8910` at Cycle 10.
- **Is it legitimate?** **NO.** It reaches `0.8910` purely by executing `ResponseWorker` 9 times consecutively, inserting 36 duplicate containment actions into the database and accumulating artificial historical drift. It represents pseudo-convergence through repetition, not genuine analytical certainty.

### Condition 2: Stagnation Termination (`cycles_since_confidence_gain >= 3`)
- **Can it actually be reached?**
  - In unit tests where fake decisions with `gain = 0.01` are manually inserted: **YES** (`should_terminate` returns `True`, reason: `stagnation`).
  - In actual execution: **NO.** Because normal and stalled executions always produce `gain > 0.04`, the counter never reaches 3.
- **Root Cause:** Threshold mismatch between hardcoded `gain > 0.02` and baseline minimum drift ($\ge 0.04$).

### Condition 3: Maximum-Cycle Safety Termination (`cycle >= max_cycles`)
- **Can it actually be reached?** **YES.**
- **Investigation of P1 Results:** All five P1 scenarios terminated via `max_cycles_reached` because:
  1. The evaluation harness set `max_cycles = 6`.
  2. At Cycle 6, confidence had reached $\sim 0.612$, which is below the $0.85$ threshold.
  3. Stagnation was bypassed by the artificial drift.
  4. Max-cycles was the only remaining exit condition.
- **Verdict:** `max_cycles_reached` is currently acting as the **normal termination mechanism** rather than a safety guard.

---

## 9. Identified Defects and Architectural Weaknesses

### Defect 1 (P0 — Correctness): Permanent Utility State Locking
- **File:** `backend/app/planner/selection.py:68-71`
- **Mechanism:** `scores["response"] = 1.0` if `has_confirmed_hypothesis`. Once confirmed, response dominates all other workers indefinitely.

### Defect 2 (P0 — Correctness): Unconditional Baseline Confidence Inflation
- **File:** `backend/app/planner/engine.py:216`, `backend/app/planner/confidence.py:61-75`
- **Mechanism:** Synthetic historical score formula `0.2 + cycle * 0.12`, single-worker agreement default `0.5`, and RAG fallback `0.65` inject $> +0.22$ logit delta on every cycle even with 0 findings.

### Defect 3 (P0 — Correctness): Stagnation Counter Reset Due to Drift
- **File:** `backend/app/planner/engine.py:59`
- **Mechanism:** Threshold `gain > 0.02` is smaller than the unconditional baseline drift ($\sim 0.045$), making `cycles_since_gain` permanently 0.

### Defect 4 (P0 — Correctness): Unbounded Duplicate Evidence Persistence
- **File:** `backend/app/planner/engine.py:164-176`
- **Mechanism:** Every finding in `worker_result.new_evidence` is inserted into `Evidence` without checking for identical description/entities.

### Defect 5 (P1 — Adaptivity): Bypassed Replanning Architecture
- **File:** `backend/app/planner/engine.py:138` vs `backend/app/planner/decider.py:15-90`
- **Mechanism:** `PlannerEngine` directly invokes `select_worker()`, leaving `DynamicPlanner`'s replan logic completely disconnected.

### Defect 6 (P1 — Adaptivity): Total Lack of Capability History and Repeat Penalties
- **File:** `backend/app/planner/selection.py:39-76`
- **Mechanism:** `select_worker` has no access to previous worker selections and implements no diminishing returns or repeat penalties.

---

## 10. Prioritized Recommendations

### Priority 0: Correctness Defects (Must Fix Before Any Behavioral Claims)
1. **Deduplicate Evidence on Insertion:** Check for identical `description` + `investigation_id` before adding to `Evidence`. If duplicate, mark as corroboration timestamp rather than new evidence.
2. **Eliminate Synthetic Historical Slope:** Remove `0.2 + cycle * 0.12` from `engine.py`. Replace with genuine historical incident lookup or set `historical_sim_score = 0.0` when no historical match exists.
3. **Condition Baseline Factors on Worker Findings:** If a worker produces 0 evidence, set $\delta_{\text{evidence}} = 0$, $\delta_{\text{knowledge}} = 0$, and $\delta_{\text{historical}} = 0$.
4. **Fix Stagnation Calibration:** Calculate stagnation based on **net new evidence** and **significant analytical gain** ($\ge 0.05$), and ensure zero-progress cycles increment `cycles_since_confidence_gain`.
5. **Decouple Response from Perpetual 1.0:** Once `ResponseWorker` has executed and formulated containment actions for the confirmed hypothesis, set its utility to `0.0` (or `0.10`) unless a new hypothesis or containment failure occurs.

### Priority 1: Adaptive Behavior Improvements
1. **Unify `PlannerEngine` with `DynamicPlanner`:** Replace the hardcoded call to `select_worker()` in `engine.py` with `DynamicPlanner.formulate_decision()`.
2. **Implement Capability Repeat-Selection Penalty:** Apply exponential decay $U'(w) = U(w) \cdot \gamma^{k}$ where $k$ is the consecutive selection count ($\gamma = 0.3$).
3. **Support Explicit Replan Triggers:** When stagnation $\ge 2$ or a worker yields 0 findings, log `[REPLAN]` in decision rationale and force capability diversification.
4. **Fix Detection and Correlation Utility Lifecycles:** Allow Detection to triage background event streams across cycles. Compute Graph Density dynamically from actual entity relationships rather than simple evidence count scaling.

### Priority 2: Calibration and Evaluation Improvements
1. **Re-evaluate Confidence Band Boundaries:** Calibrate the $0.85$ completion threshold against actual multi-scenario empirical distributions.
2. **Dynamic Cycle Budgeting:** Set cycle budget dynamically based on investigation complexity rather than arbitrary $6$ or $15$.

---

## 11. Automated Regression Verification Suite

To ensure these defects are tracked and verifiable without regressions, an automated test suite was added in [`backend/tests/test_decision_logic_audit.py`](file:///c:/Users/Aaditya%20Rana/OneDrive/Desktop/SEM5/CDAC-IP/backend/tests/test_decision_logic_audit.py):

| Test Name | Target Defect | Verification Status |
|---|---|---|
| `test_response_utility_locking_and_lack_of_repeat_penalty` | Permanent 1.0 score for Response worker | **PASSED** (Confirmed Defect) |
| `test_zero_progress_creates_artificial_confidence_gain` | Baseline drift resetting stagnation counter | **PASSED** (Confirmed Defect) |
| `test_duplicate_evidence_persistence_and_confidence_accumulation` | Duplicate evidence insertion and confidence inflation | **PASSED** (Confirmed Defect) |
| `test_baseline_confidence_drift_components` | Factor breakdown showing $>0.15$ baseline drift | **PASSED** (Confirmed Defect) |
| `test_stagnation_termination_when_forced_low_gain` | Termination logic functionality when low gain forced | **PASSED** (Confirmed Mechanism) |

All 118 backend tests (including the 5 new regression tests) pass cleanly:
```powershell
pytest backend/tests/
# 118 passed in 2.43s
```

---

## 12. Concise Audit Verdicts

| Audit Question | Verdict | Rationale |
|---|---|---|
| **Are the thresholds currently justified?** | **NO** | High-confidence ($0.85$) and stagnation gain ($0.02$) are arbitrary initial constants. The stagnation threshold is calibrated below the artificial drift, making it inoperable. |
| **Is confidence convergence behaving correctly?** | **NO** | Confidence convergence is artificial. It accumulates positive deltas from synthetic historical formulas, single-worker defaults, and duplicate evidence rather than genuine threat corroboration. |
| **Is repeated worker selection legitimate or a logic problem?** | **LOGIC PROBLEM** | It is caused by a hardcoded `1.0` utility lock for Response combined with total lack of repeat penalties or cooldowns. Repeated executions yield duplicate records without new insight. |
| **Does stagnation detection work in actual execution?** | **NO** | While the `should_terminate` function contains correct branching, the stagnation counter never reaches the threshold in actual execution because artificial drift perpetually resets it. |
| **Does genuine replanning occur?** | **NO** | `PlannerEngine.run_cycle` contains zero replanning logic. `DynamicPlanner` is bypassed in the live runtime. |
| **Is max_cycles acting as a safety guard or normal termination?** | **NORMAL TERMINATION** | In standard benchmark evaluation runs ($N=6$), all scenarios terminate via `max_cycles_reached` as their regular exit mechanism. |

---
*Report completed by Project Sentinel Backend Decision Logic Audit Team.*
