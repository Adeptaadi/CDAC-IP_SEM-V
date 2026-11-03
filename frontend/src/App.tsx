import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ShieldAlert,
  Search,
  LayoutGrid
} from 'lucide-react';

// Antigravity IDE UI Subcomponents
import { ActivityBar, ActivityBarItem } from './components/ide/ActivityBar';
import { PrimarySidebar } from './components/ide/PrimarySidebar';
import { CentralWorkspace, TabItem } from './components/ide/CentralWorkspace';
import { AgentCopilotPane } from './components/ide/AgentCopilotPane';
import { BottomDockPanel } from './components/ide/BottomDockPanel';
import { StatusBar } from './components/ide/StatusBar';

// ThoughtLog interface
import { ThoughtLog } from './components/AgentThoughtStream';

interface Investigation {
  investigation_id: string;
  title: string;
  status: string;
  current_confidence: number;
  confidence_state: string;
  current_goal?: string;
  planning_cycle_count: number;
  created_at: string;
}

interface Scenario {
  scenario_id: string;
  name: string;
  dataset_source: string;
  day: string;
  description: string;
  mitre_tactics: string[];
  mitre_techniques: string[];
  gold_hypothesis: string;
}

interface ReplayStatus {
  scenario: string | null;
  state: 'IDLE' | 'PLAYING' | 'PAUSED' | 'COMPLETED';
  speed: number;
  total_events: number;
  dispatched_events_count: number;
  progress_percent: number;
  latest_event: any | null;
}

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  // Navigation & UI Layout State
  const [activeActivity, setActiveActivity] = useState<ActivityBarItem>('explorer');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [copilotOpen, setCopilotOpen] = useState(true);
  const [bottomDockOpen, setBottomDockOpen] = useState(true);

  // Tabbed Workspace State
  const [openTabs, setOpenTabs] = useState<TabItem[]>([
    { id: 'timeline', title: 'AttackTimeline.canvas', type: 'timeline' },
    { id: 'graph', title: 'EntityGraph.visual', type: 'graph' },
    { id: 'matrix', title: 'Hypotheses.matrix', type: 'matrix' },
    { id: 'reports', title: 'ForensicReport.md', type: 'reports' },
    { id: 'math', title: 'ConfidenceDecay.math', type: 'math' },
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('timeline');

  // Backend Data State
  const [health, setHealth] = useState<{ status: string; service: string } | null>(null);
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [selectedInvestigationId, setSelectedInvestigationId] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('infiltration');

  // Replayer State
  const [replayStatus, setReplayStatus] = useState<ReplayStatus>({
    scenario: null,
    state: 'IDLE',
    speed: 1.0,
    total_events: 0,
    dispatched_events_count: 0,
    progress_percent: 0,
    latest_event: null,
  });

  // Knowledge RAG State
  const [knowledgeQuery, setKnowledgeQuery] = useState('');
  const [retrievedContext, setRetrievedContext] = useState<any | null>(null);
  const [isQueryingKnowledge, setIsQueryingKnowledge] = useState(false);
  const [isSeedingKnowledge, setIsSeedingKnowledge] = useState(false);

  // Active Investigation Data Snapshot
  const [investigationFullState, setInvestigationFullState] = useState<any | null>(null);
  const [decisions, setDecisions] = useState<any[]>([]);
  const [activeWorker, setActiveWorker] = useState<string | null>(null);
  const [workerLatencies, setWorkerLatencies] = useState<Record<string, number>>({});
  const [thoughtLogs, setThoughtLogs] = useState<ThoughtLog[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [isExecutingStep, setIsExecutingStep] = useState(false);
  const [isRunningAuto, setIsRunningAuto] = useState(false);
  const [isAutoHunting, setIsAutoHunting] = useState(false);

  // Initial load
  useEffect(() => {
    fetchHealth();
    fetchInvestigations();
    fetchScenarios();

    const interval = setInterval(() => {
      fetchReplayStatus();
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  // When selected investigation changes, fetch its full state and connect WS
  useEffect(() => {
    if (selectedInvestigationId) {
      fetchFullState(selectedInvestigationId);
      fetchDecisions(selectedInvestigationId);

      const wsUrl = API_BASE.replace(/^http/, 'ws') + `/ws/investigations/${selectedInvestigationId}`;
      let ws: WebSocket | null = null;
      try {
        ws = new WebSocket(wsUrl);
        ws.onopen = () => setWsConnected(true);
        ws.onclose = () => setWsConnected(false);
        ws.onerror = () => setWsConnected(false);
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'PLANNER_DECISION') {
              fetchFullState(selectedInvestigationId);
              fetchDecisions(selectedInvestigationId);
              setThoughtLogs((prev) => [
                ...prev,
                {
                  id: String(Date.now()),
                  timestamp: new Date().toLocaleTimeString(),
                  category: 'PLANNER',
                  workerType: data.selected_worker,
                  cycleNumber: data.cycle_number,
                  message: data.explanation_summary,
                  details: {
                    confidence_after: data.confidence_after,
                  },
                },
              ]);
            }
          } catch (e) {
            // non-json ws tick
          }
        };
      } catch (e) {
        // ws err
      }

      return () => {
        if (ws) ws.close();
      };
    }
  }, [selectedInvestigationId]);

  const fetchHealth = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/health`);
      setHealth(res.data);
    } catch (e) {
      setHealth({ status: 'offline', service: 'API Gateway Unreachable' });
    }
  };

  const fetchInvestigations = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/investigations`);
      setInvestigations(res.data);
      if (res.data.length > 0 && !selectedInvestigationId) {
        setSelectedInvestigationId(res.data[0].investigation_id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchScenarios = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/dataset/scenarios`);
      setScenarios(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchReplayStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/dataset/replay/status`);
      setReplayStatus(res.data);
    } catch (e) {
      // ignore
    }
  };

  const fetchFullState = async (id: string) => {
    try {
      const res = await axios.get(`${API_BASE}/api/planner/investigations/${id}/state`);
      setInvestigationFullState(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchDecisions = async (id: string) => {
    try {
      const res = await axios.get(`${API_BASE}/api/planner/investigations/${id}/decisions`);
      setDecisions(res.data);
      if (res.data.length > 0) {
        const latest = res.data[res.data.length - 1];
        setActiveWorker(latest.selected_worker);
        if (latest.latency_ms) {
          setWorkerLatencies((prev) => ({ ...prev, [latest.selected_worker]: latest.latency_ms }));
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Replayer handlers
  const handleStartReplay = async () => {
    try {
      await axios.post(`${API_BASE}/api/dataset/replay/start`);
      fetchReplayStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handlePauseReplay = async () => {
    try {
      await axios.post(`${API_BASE}/api/dataset/replay/pause`);
      fetchReplayStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleResetReplay = async () => {
    try {
      await axios.post(`${API_BASE}/api/dataset/replay/reset`);
      fetchReplayStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleChangeSpeed = async (speed: number) => {
    try {
      await axios.post(`${API_BASE}/api/dataset/replay/speed`, null, { params: { speed } });
      fetchReplayStatus();
    } catch (e) {
      console.error(e);
    }
  };

  // Knowledge RAG handlers
  const handleSeedKnowledge = async () => {
    setIsSeedingKnowledge(true);
    try {
      await axios.post(`${API_BASE}/api/knowledge/seed`);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSeedingKnowledge(false);
    }
  };

  const handleQueryKnowledge = async (queryText: string) => {
    if (!queryText) return;
    setIsQueryingKnowledge(true);
    try {
      const res = await axios.post(`${API_BASE}/api/knowledge/query`, {
        query: queryText,
        top_k: 4,
      });
      setRetrievedContext(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsQueryingKnowledge(false);
    }
  };

  // Autonomous planning handlers
  const handleExecuteCycle = async () => {
    if (!selectedInvestigationId || isExecutingStep) return;
    setIsExecutingStep(true);
    try {
      const res = await axios.post(`${API_BASE}/api/planner/investigations/${selectedInvestigationId}/cycle`);
      await fetchFullState(selectedInvestigationId);
      await fetchDecisions(selectedInvestigationId);
      await fetchInvestigations();

      setThoughtLogs((prev) => [
        ...prev,
        {
          id: String(Date.now()),
          timestamp: new Date().toLocaleTimeString(),
          category: 'PLANNER',
          workerType: res.data.selected_worker,
          cycleNumber: res.data.cycle_number,
          message: res.data.explanation_summary,
          details: {
            confidence_after: res.data.confidence_after,
          },
        },
      ]);
    } catch (e) {
      console.error(e);
    } finally {
      setIsExecutingStep(false);
    }
  };

  const handleExecuteAuto = async () => {
    if (!selectedInvestigationId || isRunningAuto) return;
    setIsRunningAuto(true);
    try {
      await axios.post(`${API_BASE}/api/planner/investigations/${selectedInvestigationId}/run`, null, {
        params: { max_steps: 6 },
      });
      await fetchFullState(selectedInvestigationId);
      await fetchDecisions(selectedInvestigationId);
      await fetchInvestigations();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunningAuto(false);
    }
  };

  const handleCreateInvestigation = async (title: string) => {
    try {
      const res = await axios.post(`${API_BASE}/api/investigations`, {
        title,
        initial_goal: 'Autonomous investigation of anomalous telemetry signals',
      });
      await fetchInvestigations();
      if (res.data?.investigation_id) {
        setSelectedInvestigationId(res.data.investigation_id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleAutoHuntScenario = async () => {
    setIsAutoHunting(true);
    try {
      await axios.post(`${API_BASE}/api/dataset/prepare/${selectedScenarioId}`);
      await axios.post(`${API_BASE}/api/dataset/replay/load/${selectedScenarioId}`, null, {
        params: { speed: 10 },
      });
      await axios.post(`${API_BASE}/api/dataset/replay/start`);

      const scName = scenarios.find((s) => s.scenario_id === selectedScenarioId)?.name || selectedScenarioId;
      const res = await axios.post(`${API_BASE}/api/investigations`, {
        title: `Autonomous Hunt: ${scName}`,
        initial_goal: `Investigate telemetry signals and neutralize ${scName}`,
      });

      const invId = res.data.investigation_id;
      setSelectedInvestigationId(invId);
      await fetchInvestigations();

      await axios.post(`${API_BASE}/api/planner/investigations/${invId}/run`, null, {
        params: { max_steps: 6 },
      });

      await fetchFullState(invId);
      await fetchDecisions(invId);
      await fetchInvestigations();
    } catch (e) {
      console.error(e);
    } finally {
      setIsAutoHunting(false);
    }
  };

  // Tab management
  const handleOpenView = (viewId: string) => {
    const existing = openTabs.find((t) => t.id === viewId);
    if (!existing) {
      const typeMap: Record<string, { title: string; type: TabItem['type'] }> = {
        timeline: { title: 'AttackTimeline.canvas', type: 'timeline' },
        graph: { title: 'EntityGraph.visual', type: 'graph' },
        matrix: { title: 'Hypotheses.matrix', type: 'matrix' },
        reports: { title: 'ForensicReport.md', type: 'reports' },
        math: { title: 'ConfidenceDecay.math', type: 'math' },
        containment: { title: 'Containment.governance', type: 'containment' },
        benchmarks: { title: 'BenchmarkSuite.eval', type: 'benchmarks' },
        orbital: { title: 'AgentOrbital.map', type: 'orbital' },
      };
      const def = typeMap[viewId] || { title: `${viewId}.canvas`, type: 'timeline' };
      setOpenTabs((prev) => [...prev, { id: viewId, title: def.title, type: def.type }]);
    }
    setActiveTabId(viewId);
  };

  const handleCloseTab = (id: string) => {
    if (openTabs.length <= 1) return;
    const remaining = openTabs.filter((t) => t.id !== id);
    setOpenTabs(remaining);
    if (activeTabId === id) {
      setActiveTabId(remaining[remaining.length - 1].id);
    }
  };

  const currentInvestigation = investigations.find((i) => i.investigation_id === selectedInvestigationId) || null;
  const currentScenarioDetails = scenarios.find((s) => s.scenario_id === selectedScenarioId);
  const pendingApprovalsCount = (investigationFullState?.recommendations || []).filter(
    (r: any) => r.approval_status === 'pending'
  ).length;

  return (
    <div className="h-screen w-screen bg-[#070A12] text-gray-100 flex flex-col font-sans overflow-hidden">
      {/* 1. Top Window Titlebar & Quick Action Palette */}
      <header className="h-9 bg-[#090D17] border-b border-gray-800/80 px-3 flex items-center justify-between select-none z-40 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="flex items-center gap-2 text-white font-bold text-xs tracking-wider">
            <span className="w-4 h-4 rounded bg-blue-600 flex items-center justify-center text-[10px]">Δ</span>
            <span>ANTIGRAVITY IDE</span>
            <span className="text-[10px] bg-blue-950 text-blue-400 border border-blue-800 px-1.5 py-0.2 rounded font-mono">
              PROJECT SENTINEL
            </span>
          </div>

          <span className="text-gray-700">|</span>

          {/* Quick Scenario Capsule */}
          <div className="flex items-center gap-1.5 text-xs text-gray-300 font-mono">
            <span className="text-gray-500">Scenario:</span>
            <select
              value={selectedScenarioId}
              onChange={(e) => setSelectedScenarioId(e.target.value)}
              className="bg-black/60 border border-gray-700 rounded px-2 py-0.5 text-[11px] text-white focus:outline-none focus:border-blue-500"
            >
              {scenarios.map((s) => (
                <option key={s.scenario_id} value={s.scenario_id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Center Global Search / Command Bar */}
        <div className="hidden md:flex items-center gap-2 bg-[#0C111F] border border-gray-800 rounded-lg px-3 py-1 text-xs text-gray-400 w-96 justify-between cursor-pointer hover:border-gray-700 transition">
          <div className="flex items-center gap-2 truncate">
            <Search className="w-3.5 h-3.5 text-gray-500" />
            <span className="text-[11px] truncate">
              {currentInvestigation ? `Active: ${currentInvestigation.title}` : 'Search artifacts, MITRE techniques (Ctrl+P)'}
            </span>
          </div>
          <div className="flex items-center gap-1 font-mono text-[10px] text-gray-500 bg-gray-900 border border-gray-800 px-1.5 py-0.5 rounded">
            <span>⌘K</span>
          </div>
        </div>

        {/* Right Quick Status & Layout Toggles */}
        <div className="flex items-center space-x-2">
          {/* HITL Pending Badge */}
          {pendingApprovalsCount > 0 && (
            <button
              onClick={() => handleOpenView('containment')}
              className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-amber-950/80 border border-amber-700 text-amber-300 text-[10px] font-mono animate-pulse"
              title={`${pendingApprovalsCount} Containment Approvals Pending`}
            >
              <ShieldAlert className="w-3 h-3 text-amber-400" />
              <span>{pendingApprovalsCount} Approvals Required</span>
            </button>
          )}

          {/* Layout Pane Toggles */}
          <button
            onClick={() => setSidebarOpen((v) => !v)}
            title={sidebarOpen ? 'Hide Primary Sidebar' : 'Show Primary Sidebar'}
            className={`p-1.5 rounded transition ${
              sidebarOpen ? 'text-blue-400 bg-blue-950/40' : 'text-gray-400 hover:text-white'
            }`}
          >
            <LayoutGrid className="w-3.5 h-3.5" />
          </button>
        </div>
      </header>

      {/* 2. Main Middle Workspace Area (Activity Bar + Sidebar + Central Canvas + Copilot) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Leftmost Activity Bar Rail */}
        <ActivityBar
          activeItem={activeActivity}
          onSelectItem={(item) => {
            setActiveActivity(item);
            if (!sidebarOpen) setSidebarOpen(true);
            if (item === 'containment') handleOpenView('containment');
            if (item === 'benchmarks') handleOpenView('benchmarks');
          }}
          copilotOpen={copilotOpen}
          onToggleCopilot={() => setCopilotOpen((v) => !v)}
          bottomDockOpen={bottomDockOpen}
          onToggleBottomDock={() => setBottomDockOpen((v) => !v)}
          apiHealthy={health?.status === 'healthy'}
          pendingApprovalsCount={pendingApprovalsCount}
        />

        {/* Collapsible Primary Sidebar Context */}
        {sidebarOpen && (
          <PrimarySidebar
            activeItem={activeActivity}
            scenarios={scenarios}
            selectedScenarioId={selectedScenarioId}
            onSelectScenario={(id) => setSelectedScenarioId(id)}
            investigations={investigations}
            selectedInvestigationId={selectedInvestigationId}
            onSelectInvestigation={(id) => setSelectedInvestigationId(id)}
            onCreateInvestigation={handleCreateInvestigation}
            onAutoHuntScenario={handleAutoHuntScenario}
            isAutoHunting={isAutoHunting}
            onSeedKnowledge={handleSeedKnowledge}
            isSeedingKnowledge={isSeedingKnowledge}
            onQueryKnowledge={handleQueryKnowledge}
            knowledgeQuery={knowledgeQuery}
            setKnowledgeQuery={setKnowledgeQuery}
            retrievedContext={retrievedContext}
            isQueryingKnowledge={isQueryingKnowledge}
            pendingApprovalsCount={pendingApprovalsCount}
            onOpenView={handleOpenView}
          />
        )}

        {/* Central Dynamic Tabbed Canvas */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <CentralWorkspace
            apiBase={API_BASE}
            tabs={openTabs}
            activeTabId={activeTabId}
            onSelectTab={(id) => setActiveTabId(id)}
            onCloseTab={handleCloseTab}
            investigation={currentInvestigation}
            state={investigationFullState}
            decisions={decisions}
            activeWorker={activeWorker}
            workerLatencies={workerLatencies}
            onRefreshInvestigation={() => {
              if (selectedInvestigationId) {
                fetchFullState(selectedInvestigationId);
                fetchDecisions(selectedInvestigationId);
                fetchInvestigations();
              }
            }}
            scenarioName={currentScenarioDetails?.name}
          />

          {/* Bottom Dock Console (Telemetry Replayer, Terminal, Audit Bus) */}
          <BottomDockPanel
            isOpen={bottomDockOpen}
            onToggle={() => setBottomDockOpen(false)}
            replayStatus={replayStatus}
            scenarioName={currentScenarioDetails?.name}
            onStartReplay={handleStartReplay}
            onPauseReplay={handlePauseReplay}
            onResetReplay={handleResetReplay}
            onChangeSpeed={handleChangeSpeed}
            thoughtLogs={thoughtLogs}
          />
        </div>

        {/* Right-hand Auxiliary Copilot Pane with Slash Commands */}
        {copilotOpen && (
          <AgentCopilotPane
            confidence={currentInvestigation?.current_confidence || 0}
            activeWorker={activeWorker}
            thoughtLogs={thoughtLogs}
            onExecuteCycle={handleExecuteCycle}
            onExecuteAuto={handleExecuteAuto}
            isRunningAuto={isRunningAuto}
            isExecutingStep={isExecutingStep}
            onOpenView={handleOpenView}
          />
        )}
      </div>

      {/* 3. Bottom Status Bar */}
      <StatusBar
        scenarioName={currentScenarioDetails?.name}
        investigationTitle={currentInvestigation?.title}
        cycleNumber={currentInvestigation?.planning_cycle_count || 0}
        confidence={currentInvestigation?.current_confidence || 0}
        confidenceState={currentInvestigation?.confidence_state || 'idle'}
        activeWorker={activeWorker}
        apiHealthy={health?.status === 'healthy'}
        wsConnected={wsConnected}
        replayState={replayStatus.state}
      />
    </div>
  );
}
