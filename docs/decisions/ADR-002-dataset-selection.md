# ADR-002: Selection of CSE-CIC-IDS2018 5-Scenario Suite for Benchmark Telemetry

**Date:** 2026-09-21  
**Status:** Accepted  
**Deciders:** Project Sentinel Architecture Team  

---

## 1. Context and Problem Statement

The official Project Problem Statement explicitly recommends using public datasets (`CICIDS, KDD Cup`) and defines the core requirement:
> *"Correlate security events across logs and network telemetry."*

We needed to select a public dataset that provides both **Host System Logs (Windows Event Logs)** and **Network Telemetry (Flows/Packets)** while remaining lightweight enough to be used in continuous development and Docker testing environments.

---

## 2. Decision

We choose **CSE-CIC-IDS2018** (specifically a curated 5-scenario subset), rather than legacy **KDD Cup 1999** or generic network-only datasets:

1. **Scenario 1:** Infiltration & Lateral Movement (`Thursday-01-03-2018`)
2. **Scenario 2:** Credential Access / Brute Force (`Wednesday-14-02-2018`)
3. **Scenario 3:** Web Application Attacks (`Thursday-22-02-2018`)
4. **Scenario 4:** Botnet Command & Control (`Friday-02-03-2018`)
5. **Scenario 5:** Denial of Service / DDoS (`Thursday-15-02-2018`)

We build a dedicated **Normalization & Temporal Alignment Pipeline** (`backend/app/ingest/`) that ingests these scenario files, converts them into standard `TelemetryEvent` JSON structures, and streams them through Redis to simulate live SOC feeds.

---

## 3. Consequences

### Positive
* **Requirement Alignment:** Fulfills the requirement to correlate heterogeneous host logs with network telemetry.
* **Storage Efficiency:** Only ~550 MB total disk footprint for all 5 scenarios combined, avoiding the ~450 GB full raw PCAP capture.
* **Reproducibility:** Academic baselines can be directly benchmarked against published Canadian Institute for Cybersecurity standards.
* **Diverse MITRE Coverage:** Covers Initial Access, Execution, Credential Access, Lateral Movement, C2, and Exfiltration.

### Negative / Trade-offs
* **Ingestion Mapping:** Requires custom normalization logic for mapping CIC flow headers and Windows Event IDs into a unified schema.
