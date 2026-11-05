---
name: frontend-development
description: >-
  Expert workflows, UI/UX architecture principles, and implementation standards for modern
  frontend engineering with React, TypeScript, and TailwindCSS. Use this skill when designing,
  refactoring, building, or simplifying web applications, SOC/enterprise dashboards, complex state
  flows, and component systems.
---

# Frontend Development & UI Simplification Skill

This skill guides the design, engineering, and refactoring of modern, high-performance web applications with a focus on **visual clarity, component modularity, and cognitive ease**.

---

## 1. Core Engineering Philosophy

1. **Clarity Over Clutter:** A user interface should never force an operator to parse more than one primary focal area at a time. Avoid "IDE Syndrome" (too many simultaneous split panels, toolbars, and dockers) unless strictly required for a multi-window coding editor.
2. **Progressive Disclosure:** Surface the 20% of information that delivers 80% of actionable value first. Place deep diagnostic telemetry, raw JSON objects, and secondary math into drawers, modals, or dedicated tabs.
3. **Deterministic State & Clean Types:** Never use `any`. Component props must be backed by strict TypeScript interfaces. All asynchronous operations must handle `loading`, `error`, `empty`, and `success` states explicitly.
4. **Visual Hierarchy & Design Tokens:** Use a consistent dark or light theme palette with defined semantic colors:
   - **Critical/Breach:** Crimson / Rose (`bg-rose-950 text-rose-300 border-rose-800`)
   - **High Risk:** Amber / Orange (`bg-amber-950 text-amber-300 border-amber-800`)
   - **Medium/Notice:** Blue / Cyan (`bg-blue-950 text-blue-300 border-blue-800`)
   - **Success/Verified:** Emerald / Green (`bg-emerald-950 text-emerald-300 border-emerald-800`)
   - **Neutral/Muted:** Zinc / Slate (`bg-zinc-900 border-zinc-800 text-zinc-400`)

---

## 2. Standard 6-Step Workflow: UI Simplification & Building

When tasked with building or refactoring a frontend:

### Step 1: Inventory User Jobs-to-be-Done (JTBD)
Identify what the operator actually visits the page to accomplish:
- Example: *"Triage incoming threats, run an investigation, approve containment actions, download report."*
- Separate primary actions from background diagnostics.

### Step 2: Establish Top-Level Information Architecture
Choose an uncluttered top-level layout:
- **Top Navigation Bar:** Product identity + primary views (e.g. `Incidents & Triage`, `Investigation Canvas`, `Governance & Response`).
- **Global Status Header:** Quick operational metrics (Active Hunts, Critical Incidents, System Health).
- **Focused Canvas:** The selected view receives 100% of the viewport width without competing side panels.

### Step 3: Implement Modular Component Hierarchy
Follow the single-responsibility rule:
- Keep components under 250 lines of code.
- Extract recurring UI patterns (stat cards, badges, modal dialogs, data tables) into reusable primitives under `src/components/ui/`.
- Decouple API fetch logic into dedicated service clients or React hooks (`useInvestigation`, `useAlerts`).

### Step 4: Apply Responsive Typography & Spacing
- Use monospace fonts (`font-mono`) strictly for machine identifiers (IPs, hashes, UUIDs, code, commands).
- Use clean sans-serif (`font-sans`, Inter/Geist/system-ui) for labels, headings, narrative summaries, and explanations.
- Standardize padding: `p-4` or `p-6` for page containers, `gap-4` for grid layouts, `px-3 py-1.5` for buttons.

### Step 5: Smooth Micro-Interactions & Feedback
- Always provide immediate visual feedback for user triggers: spinners, disabled button states, and toast notifications.
- Use smooth transitions (`transition-all duration-200`) for tab switches and hover states.
- Avoid abrupt layout shifts (reserve skeleton loaders or fixed aspect-ratio containers).

### Step 6: Verify Build & Type Integrity
Always verify frontend compilation before concluding:
```bash
npm --prefix frontend run build
```
Ensure zero TypeScript (`tsc`) warnings or unused variable errors.

---

## 3. Specialized References

For detailed guidelines in specific domains, consult:
- **[UI Simplification Runbook](./references/ui-simplification.md):** How to turn cluttered multi-pane interfaces into clean enterprise products.
- **[Component Architecture Guide](./references/component-architecture.md):** Best practices for React, TypeScript props, state management, and custom hooks.
- **[Cybersecurity & SOC Design Patterns](./references/cybersecurity-soc-patterns.md):** Industry-standard UX patterns for threat hunting, MITRE ATT&CK matrices, attack timelines, and containment workflows.
