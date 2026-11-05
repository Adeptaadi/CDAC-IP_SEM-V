# Cybersecurity & SOC Dashboard Design Patterns

Best practices for designing security analytics, threat hunting consoles, and human-in-the-loop workflows.

---

## 1. Threat Severity Visual Hierarchy

| Severity | Color Tokens (Tailwind) | Hex Code | Visual Meaning |
|---|---|---|---|
| **Critical** | `bg-red-950/80 text-red-300 border-red-800` | `#EF4444` | Immediate active breach, credential dump, or C2 beacon. |
| **High** | `bg-amber-950/80 text-amber-300 border-amber-800` | `#F59E0B` | Suspicious privilege escalation, brute force burst. |
| **Medium** | `bg-blue-950/80 text-blue-300 border-blue-800` | `#3B82F6` | Policy violation, port sweep, unusual outbound flow. |
| **Low / Info** | `bg-zinc-900 text-zinc-400 border-zinc-800` | `#71717A` | Standard audit record or benign flow. |

---

## 2. Attack Timeline Visualization

- **Orientation:** Vertical chronological timeline with latest events at bottom or top (clearly labeled).
- **Node markers:** Circular icon nodes indicating event source (`Network Flow`, `Process Spawn`, `Auth Record`).
- **Timestamp display:** Format as ISO or local HH:mm:ss in muted monospace font (`text-zinc-500 font-mono text-xs`).
- **Collapsible Payload:** Show event headline; expand to view command-line arguments, IP addresses, or packet counts.

---

## 3. Entity Graph Visualization

- Graph nodes must have distinct colors by entity type:
  - **Hosts:** Sky Blue (`#38BDF8`)
  - **IP Addresses:** Emerald Green (`#34D399`)
  - **Users:** Purple (`#A855F7`)
  - **Processes:** Amber (`#FBBF24`)
- Node labels should truncate at 16 characters with full string on hover tooltip.
- Include a small legend banner in the corner of the canvas.

---

## 4. Human-In-The-Loop (HITL) Containment Governance

Never allow automated destructive or disruptive actions without explicit human confirmation:
1. **Clear Rationale:** State *why* the agent recommended the containment action.
2. **Blast Radius Assessment:** State *what* systems will be impacted (e.g. *"Host WS-01 isolated from subnet; agent management port 8443 kept open"*).
3. **Rollback Assurance:** State *how* the action can be reverted (e.g. *"Adapter re-enabled via agent control"*).
4. **Approval Action Pair:**
   - **Approve & Simulate:** Primary Emerald/Cyan button.
   - **Reject:** Red/Muted button with mandatory reason field.
