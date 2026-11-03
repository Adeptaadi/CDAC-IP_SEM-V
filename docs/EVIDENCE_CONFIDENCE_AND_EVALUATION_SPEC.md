# Project Sentinel — Evidence, Confidence & Evaluation Specification (ECES)

**Document Type:** Evidence Management, Confidence Modeling and Evaluation Specification  
**Version:** 1.0  
**Status:** Proposed Architecture Upgrade  
**Primary Focus:** Evidence Quality, Claim-Based Confidence Modeling, Multi-Level Evaluation, and Baseline Comparative Experiments  
**Related Components:** Orchestration Core, Capabilities, Confidence Engine, Benchmark Runner

---

# 1. Purpose & Core Evaluation Principle

Project Sentinel establishes scientific rigor through empirical evaluation rather than subjective LLM generation:

> **Confidence must be derived from evidence and system behavior, not from an LLM simply stating that it is confident.**  
> **Agent performance must be evaluated using measurable outcomes compared against a deterministic baseline, not subjective impressions.**

---

# 2. The Three Evaluation Layers

```text
┌───────────────────────────────────────────────────────────────┐
│                   LEVEL 1: EVIDENCE QUALITY                   │
│  Is the individual evidence reliable, relevant, and traceable? │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                 LEVEL 2: INVESTIGATION QUALITY                │
│  Does the collected evidence support the final conclusion?    │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                LEVEL 3: ORCHESTRATION QUALITY                 │
│  Did the orchestrator choose useful actions & avoid waste?    │
└───────────────────────────────────────────────────────────────┘
```

Separating these three levels ensures that errors are correctly isolated:
- Level 1 failure = Low-quality or noisy sensor telemetry.
- Level 2 failure = Poor reasoning or unverified hypothesis synthesis.
- Level 3 failure = Orchestration thrashing or redundant tool selection.

---

# 3. Evidence Quality Dimensions & Strength Scoring

Evidence quality is evaluated across five objective dimensions:

$$\text{Evidence Strength} = \text{Reliability} + \text{Relevance} + \text{Traceability} + \text{Timeliness} + \text{Completeness}$$

| Dimension | Evaluation Question | Measurement Standard |
| :--- | :--- | :--- |
| **Reliability** | How trustworthy is the producing source? | Normalized raw logs ($1.0$) vs. heuristic rule ($0.8$) vs. LLM inference ($0.5$). |
| **Relevance** | How directly does it address the active gap? | Cosine/entity overlap with the target hypothesis. |
| **Traceability** | Can it be linked backward to raw event IDs? | Complete raw event hash chain ($1.0$) vs. unsupported statement ($0.0$). |
| **Timeliness** | Does the timestamp fit the attack sequence? | Temporal window proximity to trigger event. |
| **Completeness** | Does it cover required analytical attributes? | Ratio of populated parameters (source, destination, process, user). |

---

# 4. Claim-Based Confidence Architecture

The platform computes confidence for **specific claims**, rejecting a single global number:
- *Claim 1:* "Endpoint WORKSTATION-04 executed obfuscated PowerShell." ($\text{Conf} = 0.94$)
- *Claim 2:* "PowerShell spawned an outbound reverse shell to external IP." ($\text{Conf} = 0.88$)
- *Claim 3:* "Active user account credentials were breached." ($\text{Conf} = 0.62$, uncorroborated)

### Mathematical Confidence Model
$$\text{Claim Confidence} = S_{\text{support}} + Q_{\text{evidence}} + C_{\text{coverage}} - P_{\text{contradiction}} - P_{\text{uncertainty}}$$

| Factor | Contribution | Description |
| :--- | :--- | :--- |
| **$S_{\text{support}}$** | $+0.35$ max | Weight of corroborating empirical observations |
| **$Q_{\text{evidence}}$** | $+0.25$ max | Provenance and source reliability scores |
| **$C_{\text{coverage}}$** | $+0.20$ max | Ratio of necessary hypothesis criteria fulfilled |
| **$P_{\text{contradiction}}$** | $-0.10$ each | Penalty per unresolved contradiction |
| **$P_{\text{uncertainty}}$** | $-0.05$ each | Penalty per unresolved critical evidence gap |

```text
Confidence Score Bands:
├── 0.80 - 1.00 : High (Eligible for automated containment recommendation)
├── 0.50 - 0.79 : Moderate (Mandatory analyst review required)
└── Below 0.50  : Low / Inconclusive (Escalate or mark inconclusive)
```

**Rule:** Confidence is an **evidence-based decision score**, never a statistical claim of mathematical truth.

---

# 5. Independent Capability-Level Metrics

```text
┌──────────────────────────┐    Precision = Relevant Retrieved / Total Retrieved
│  Correlation Capability  │──► Recall    = Relevant Retrieved / Total Relevant Available
│                          │    Latency   = Query-to-Result turnaround (ms)
└──────────────────────────┘

┌──────────────────────────┐    Stance Accuracy = Correct categorization (supports/contradicts)
│  Investigation Capability│──► Contradiction Detection Rate = Caught conflicting facts / Total
│                          │    Evidence Reference Coverage   = Findings with citations / Total
└──────────────────────────┘

┌──────────────────────────┐    Retrieval Recall@K = Ground-truth techniques in top-K chunks
│  Knowledge Retrieval RAG │──► Context Precision  = Relevant words / Total retrieved words
│                          │    Context Leakage    = Chunks misidentified as observed evidence (0%)
└──────────────────────────┘

┌──────────────────────────┐    Unsupported Claim Detection = False assertions caught / Total false
│  Evidence Validation     │──► Traceability Verification   = Checked event chains / Total claims
└──────────────────────────┘
```

---

# 6. Orchestration Quality Metrics

The adaptive orchestrator itself is evaluated against formal operational metrics:

1. **Action Relevance Rate:**
   $$\text{Relevance Rate} = \frac{\text{Actions Directly Addressing an Active Gap}}{\text{Total Actions Executed}} \quad (\text{Target} > 90\%)$$
2. **Unnecessary Action Rate:**
   $$\text{Unnecessary Rate} = \frac{\text{Redundant Actions / Actions Without Info Gain}}{\text{Total Actions Executed}} \quad (\text{Target} < 10\%)$$
3. **Duplicate Action Prevention Rate:**
   $$\text{Prevention Rate} = \frac{\text{Blocked Duplicate Signatures}}{\text{Total Attempted Duplicate Signatures}} \quad (\text{Target} = 100\%)$$
4. **Evidence Gap Resolution Rate:**
   $$\text{Gap Resolution Rate} = \frac{\text{Gaps Successfully Resolved or Declared Inconclusive}}{\text{Total Gaps Identified}} \quad (\text{Target} > 85\%)$$
5. **Replanning Quality:** Percentage of replanning events that successfully steered the investigation away from invalidated hypotheses when presented with contradictions ($>80\%$).

---

# 7. Baseline Comparative Experimentation Framework

To demonstrate that the adaptive multi-agent orchestration architecture provides quantifiable superiority over traditional designs, Sentinel implements a head-to-head evaluation against a **Fixed Sequential Baseline**:

```text
                     TEST SCENARIOS (CSE-CIC-IDS2018)
                                    │
                  ┌─────────────────┴─────────────────┐
                  ▼                                   ▼
          FIXED BASELINE                     ADAPTIVE SENTINEL
     Alert ──► Correlate ──► Investigate      State ──► Gap ──► Select ──► Validate
       ──► RAG ──► Validate ──► Report             ▲                  │
                                                   └─── Re-plan ◄─────┘
                  │                                   │
                  └─────────────────┬─────────────────┘
                                    ▼
                         EVALUATION HARNESS
                                    │
                                    ▼
                    COMPARATIVE BENCHMARK REPORT
```

### Comparative Metrics Matrix
| Dimension | Fixed Workflow Baseline | Adaptive Project Sentinel | Expected Scientific Result |
| :--- | :--- | :--- | :--- |
| **Total Actions Executed** | Fixed $N = 5$ for all scenarios | Variable ($2 \dots 7$ depending on need) | $\sim 30\%$ fewer actions on simple incidents |
| **Unnecessary Actions** | High (runs RAG/Correlation even if unneeded) | Very Low ($< 10\%$) | Statistically significant reduction in redundant compute |
| **Contradiction Handling** | Blind execution (cannot backtrack) | Automated hypothesis pivot | Recovers from false-positive triggers |
| **Evidence Traceability** | Generic summary | $100\%$ claims cite concrete `evidence_id`s | Eliminates forensic hallucination |
| **Investigation Latency** | Constant high latency | Dynamic; stops as soon as sufficiency is reached | Faster time-to-containment |

---

# 8. Evaluation File & Module Structure

```text
backend/app/
├── evidence/
│   ├── models.py              # EvidenceItem, Provenance contracts
│   ├── quality.py             # 5-dimension quality scoring
│   └── confidence.py          # Claim-based confidence engine
├── evaluation/
│   ├── runner.py              # Benchmark execution orchestrator
│   ├── scenarios.py           # 5 CSE-CIC-IDS2018 benchmark definitions
│   ├── baselines.py           # Fixed sequential baseline runner
│   ├── metrics.py             # Precision, recall, ECE, gap resolution metrics
│   └── reports.py             # Comparative markdown & JSON report export
```
