# UI Simplification Runbook: De-Cluttering Complex Web Applications

When an interface grows organically across multiple development phases, it often suffers from **Visual Saturation**:
- Too many panes visible at the same time (Activity Bar + Left Sidebar + Tab Bar + Canvas + Right Copilot + Bottom Terminal).
- Deeply nested scrollbars and tiny sub-panels.
- Lack of clear focal hierarchy (everything competes for attention).

This guide provides a systematic procedure to convert cluttered screens into clean, professional, enterprise-grade applications.

---

## 1. The 3-Tier Categorization Filter

Sort every UI element into one of three tiers:

| Tier | Purpose | Placement |
|---|---|---|
| **Tier 1: Core Action (Primary)** | What the user needs 80% of the time (e.g. view incident title, see severity, approve action, run cycle). | **Directly visible on main screen**, given primary visual weight. |
| **Tier 2: Contextual Detail (Secondary)** | Needed to verify or understand Tier 1 (e.g. entity attributes, event logs, raw timestamps). | **Collapsible side drawer, accordion, or tabbed detail view**. |
| **Tier 3: Diagnostic / Debug (Tertiary)** | Low-level developer telemetry (e.g. logit math formulas, raw JSON payloads, socket latency). | **Hidden behind an "Advanced Telemetry" modal or settings drawer**. |

---

## 2. Structural Transformation: From IDE Layout to App Layout

### The Problem (Anti-Pattern)
```text
+---+---------------+-------------------------+---------+
| A | Activity List | Tab 1 | Tab 2 | Tab 3   | Copilot |
| c |---------------|-------------------------| Drawer  |
| t | Tree View     | Active Canvas Screen    |         |
| i |               |                         |         |
| v |               |-------------------------|         |
| e |               | Bottom Dock Console     |         |
+---+---------------+-------------------------+---------+
```
*Why it fails:* User has 5 independent focus zones and 4 scrollbars.

### The Solution (Top-Nav Enterprise Pattern)
```text
+-------------------------------------------------------------------+
| [Brand / Logo]   [1. Alerts & Triage]   [2. Hunt Studio]   [3. HITL Governance]  |
+-------------------------------------------------------------------+
|  Hero Metric Ribbon: [Active Hunts: 2] [Critical: 1] [ECE: 0.09]  |
+-------------------------------------------------------------------+
|                                                                   |
|                      FOCUSED FULL-WIDTH CANVAS                    |
|                (Timeline, Graph, or Alert Feed)                   |
|                                                                   |
+-------------------------------------------------------------------+
|  Clean Status Bar: System Ready | API: Connected                  |
+-------------------------------------------------------------------+
```
*Why it succeeds:* Single focal flow, clear mental model, maximum space for data visualization.

---

## 3. Data Tables & Card Rows

- Avoid tiny squished cards with dense walls of text.
- Use **card rows** with clear spacing:
  - Left: Severity badge + Incident Title + MITRE tags.
  - Center: Timestamp + Affected entities.
  - Right: Action button (`Inspect Hunt`, `Approve Containment`).
- Truncate long strings (hashes, commands) with an explicit copy button or tooltip.

---

## 4. Color & Contrast Rules

- Use a dark canvas with high contrast foreground text (`#0B0F19` background, `#F3F4F6` text).
- Avoid neon clashes. Stick to Tailwind's muted borders (`border-zinc-800` or `border-gray-800/80`).
- Reserve bold accent colors (Blue, Rose, Amber) strictly for status indicators and primary call-to-action buttons.
