# Component Architecture & Clean State Management

Guidelines for structuring React 18+ and TypeScript codebases for long-term maintainability.

---

## 1. Directory Structure Standards

```text
src/
├── components/
│   ├── ui/               # Generic design primitives (Button, Modal, Badge, Card, StatMetric)
│   ├── layout/           # Header, TopNavbar, Footer, MetricRibbon
│   ├── triage/           # Incident table, CandidateCard, ScenarioPicker
│   ├── studio/           # AttackTimeline, EntityGraphCanvas, AgentThoughtLog
│   └── governance/       # ReviewQueue, SimulationModal, ReportPreview
├── hooks/                # Custom React hooks (useInvestigations, useReplay, useWebSocket)
├── services/             # Axios API client functions with typed payloads
├── types/                # Pure TypeScript domain interfaces
└── App.tsx               # Root view router & top-level state provider
```

---

## 2. Component Guidelines

### A. Props Contract First
Always define explicit types for component inputs:
```tsx
export interface IncidentCardProps {
  id: string;
  title: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  entities: string[];
  onInvestigate: (id: string) => void;
  isLoading?: boolean;
}
```

### B. Decoupled Business Logic
Avoid embedding raw `axios.post(...)` calls inside deep visual components. Pass action handlers as callbacks from parent or use dedicated hooks:
```tsx
// Good: Component is pure and testable
export const IncidentCard: React.FC<IncidentCardProps> = ({ id, title, severity, onInvestigate }) => {
  return (
    <div className="p-4 bg-zinc-900 border border-zinc-800 rounded-lg flex items-center justify-between">
      <span>{title}</span>
      <button onClick={() => onInvestigate(id)}>Investigate</button>
    </div>
  );
};
```

### C. State Hoisting & Polling Hygiene
- For real-time updates, maintain a single periodic interval in the parent or custom hook with cleanup on unmount:
```tsx
useEffect(() => {
  const timer = setInterval(fetchLatestData, 3000);
  return () => clearInterval(timer);
}, [selectedId]);
```
- Avoid redundant local states that mirror props; compute derived values inline.

---

## 3. TailwindCSS Patterns

- **Consistent Pill Badges:**
  ```tsx
  <span className="px-2 py-0.5 text-xs font-mono font-medium rounded border">
  ```
- **Custom Scrollbar Classes:**
  Ensure panels that scroll use subtle scrollbars:
  ```css
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
    height: 6px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: #1f2937;
    border-radius: 3px;
  }
  ```
