import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  ShieldAlert,
  Play,
  FastForward,
  Pause,
  Cpu,
  RefreshCw,
  Terminal,
  Zap,
  Clock,
  BarChart3,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

import { AttackTimeline, TimelineEventItem } from './AttackTimeline';
import { EntityGraphCanvas } from './EntityGraphCanvas';
import { HypothesisMatrix, HypothesisItem } from './HypothesisMatrix';
import { ContainmentPanel, RecommendationItem } from './ContainmentPanel';
import { ReportViewer, ReportItem } from './ReportViewer';
import { AgentThoughtStream, ThoughtLog } from './AgentThoughtStream';
import { AgentOrbitalMap } from './AgentOrbitalMap';
import { UtilityBreakdownView } from './UtilityBreakdownView';
import { FactorDecompositionView } from './FactorDecompositionView';

interface InvestigationState {
  investigation_id: string;
  title: string;
  status: string;
  confidence: number;
  confidence_state: string;
  current_goal?: string;
  planning_cycles: number;
  evidence_count: number;
  evidence: Array<{
    evidence_id: string;
    source_type: string;
    source_ref?: string;
    description: string;
    entity_refs?: any;
    produced_by_worker?: string;
    created_at: string;
  }>;
  timeline_events: TimelineEventItem[];
  hypotheses: HypothesisItem[];
  reports: ReportItem[];
  recommendations: RecommendationItem[];
  entity_graph: {
    nodes: Array<{ id: string; label: string; type: 'host' | 'ip' | 'user' | 'process' }>;
    edges: Array<{ source: string; target: string; evidence_id?: string }>;
    density: number;
  };
}

interface PlannerDecision {
  decision_id: string;
  cycle_number: number;
  selected_worker: string;
  selection_score?: number;
  utility_scores?: Record<string, number>;
  factor_contributions?: Record<string, any>;
  rag_citations?: Array<{ category: string; text: string; similarity_score: number; reliability_weight: number }>;
  confidence_delta?: number;
  latency_ms?: number;
  knowledge_need?: string;
  confidence_before: number;
  confidence_after: number;
  explanation_summary: string;
  created_at: string;
}

interface InvestigationStudioTabProps {
  apiBase: string;
  investigations: Array<{
    investigation_id: string;
    title: string;
    status: string;
    current_confidence: number;
    confidence_state: string;
    planning_cycle_count: number;
  }>;
  selectedId: string | null;
  onSelectInvestigation: (id: string) => void;
  onRefreshList: () => void;
}

export const InvestigationStudioTab: React.FC<InvestigationStudioTabProps> = ({
  apiBase,
  investigations,
  selectedId,
  onSelectInvestigation,
  onRefreshList,
}) => {
  const [state, setState] = useState<InvestigationState | null>(null);
  const [decisions, setDecisions] = useState<PlannerDecision[]>([]);
  const [activeSubTab, setActiveSubTab] = useState<
    'timeline' | 'graph' | 'observability' | 'math' | 'evidence' | 'reports'
  >('observability');

  const [isRunningAuto, setIsRunningAuto] = useState(false);
  const [isRunningPaced, setIsRunningPaced] = useState(false);
  const [isExecutingStep, setIsExecutingStep] = useState(false);
  const [pacedInterval, setPacedInterval] = useState(1500); // ms per cycle

  const [activeWorker, setActiveWorker] = useState<string | null>(null);
  const [workerLatencies, setWorkerLatencies] = useState<Record<string, number>>({});
  const [thoughtLogs, setThoughtLogs] = useState<ThoughtLog[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  const [expandedDecisionId, setExpandedDecisionId] = useState<string | null>(null);

  const stopPacedRef = useRef(false);

  useEffect(() => {
    if (selectedId) {
      fetchFullState(selectedId);
      fetchDecisions(selectedId);

      // Connect live WebSocket stream
      const wsUrl = apiBase.replace(/^http/, 'ws') + `/ws/investigations/${selectedId}`;
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
              handleNewDecisionEvent(data);
              fetchFullState(selectedId);
              fetchDecisions(selectedId);
            }
          } catch (err) {
            // non-json ws tick
          }
        };
      } catch (e) {
        setWsConnected(false);
      }

      return () => {
        if (ws) {
          ws.close();
        }
      };
    }
  }, [selectedId, apiBase]);

  const handleNewDecisionEvent = (data: any) => {
    const timeStr = new Date().toLocaleTimeString();
    const cycleNum = data.cycle_number;
    const worker = data.selected_worker;

    setActiveWorker(worker);
    if (data.latency_ms) {
      setWorkerLatencies((prev: Record<string, number>) => ({ ...prev, [worker]: data.latency_ms }));
    }

    const newLogs: ThoughtLog[] = [
      {
        id: `plan-${Date.now()}-1`,
        timestamp: timeStr,
        category: 'PLANNER',
        cycleNumber: cycleNum,
        message: `Evaluating investigation state. Triage queue inspected. Proceeding to worker selection.`,
      },
      {
        id: `plan-${Date.now()}-2`,
        timestamp: timeStr,
        category: 'UTILITY',
        cycleNumber: cycleNum,
        message: `Argmax utility evaluated -> Winner: ${worker.toUpperCase()} (Score: ${(data.utility_score || 0).toFixed(3)}).`,
        details: data.utility_scores,
      },
    ];

    if (data.rag_citations && data.rag_citations.length > 0) {
      newLogs.push({
        id: `plan-${Date.now()}-3`,
        timestamp: timeStr,
        category: 'RAG',
        cycleNumber: cycleNum,
        message: `Semantic retrieval from ChromaDB returned ${data.rag_citations.length} MITRE/Playbook matches.`,
        details: data.rag_citations,
      });
    }

    newLogs.push({
      id: `plan-${Date.now()}-4`,
      timestamp: timeStr,
      category: 'WORKER',
      workerType: worker,
      cycleNumber: cycleNum,
      message: `${worker.toUpperCase()} executed (${data.latency_ms || 85}ms): ${data.explanation}`,
    });

    if (data.confidence_before !== undefined && data.confidence_after !== undefined) {
      const deltaStr = data.confidence_delta !== undefined ? ` (Δ ${data.confidence_delta >= 0 ? '+' : ''}${data.confidence_delta.toFixed(3)})` : '';
      newLogs.push({
        id: `plan-${Date.now()}-5`,
        timestamp: timeStr,
        category: 'BAYESIAN',
        cycleNumber: cycleNum,
        message: `Logit confidence shifted: ${(data.confidence_before * 100).toFixed(1)}% → ${(data.confidence_after * 100).toFixed(1)}% [${(data.confidence_state || 'MODERATE').toUpperCase()}]${deltaStr}`,
        details: data.factor_contributions,
      });
    }

    if (data.status === 'completed') {
      newLogs.push({
        id: `plan-${Date.now()}-6`,
        timestamp: timeStr,
        category: 'CONTAINMENT',
        cycleNumber: cycleNum,
        message: `Investigation auto-completed. Incident confirmed and pending containment actions staged for analyst review.`,
      });
    }

    setThoughtLogs((prev: ThoughtLog[]) => [...prev, ...newLogs]);
  };

  const fetchFullState = async (id: string) => {
    try {
      const res = await axios.get(`${apiBase}/api/planner/investigations/${id}/state`);
      setState(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchDecisions = async (id: string) => {
    try {
      const res = await axios.get(`${apiBase}/api/planner/investigations/${id}/decisions`);
      setDecisions(res.data);
      if (res.data.length > 0) {
        const latest = res.data[res.data.length - 1];
        setActiveWorker(latest.selected_worker);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleStep = async () => {
    if (!selectedId) return;
    setIsExecutingStep(true);
    try {
      const res = await axios.post(`${apiBase}/api/planner/investigations/${selectedId}/step`);
      if (res.data && res.data.selected_worker) {
        handleNewDecisionEvent(res.data);
      }
      await fetchFullState(selectedId);
      await fetchDecisions(selectedId);
      onRefreshList();
    } catch (e) {
      console.error(e);
    } finally {
      setIsExecutingStep(false);
    }
  };

  const handleRunPaced = async () => {
    if (!selectedId || !state) return;
    if (state.status === 'completed') return;

    setIsRunningPaced(true);
    stopPacedRef.current = false;

    try {
      while (!stopPacedRef.current) {
        const res = await axios.post(`${apiBase}/api/planner/investigations/${selectedId}/step`);
        const data = res.data;
        if (data && data.selected_worker) {
          handleNewDecisionEvent(data);
        }
        await fetchFullState(selectedId);
        await fetchDecisions(selectedId);
        onRefreshList();

        if (
          data.status === 'completed' ||
          data.status === 'escalated' ||
          data.status === 'closed_no_threat' ||
          data.termination_reason
        ) {
          break;
        }

        await new Promise((resolve) => setTimeout(resolve, pacedInterval));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunningPaced(false);
    }
  };

  const handleStopPaced = () => {
    stopPacedRef.current = true;
    setIsRunningPaced(false);
  };

  const handleRunAutonomous = async () => {
    if (!selectedId) return;
    setIsRunningAuto(true);
    try {
      const res = await axios.post(`${apiBase}/api/planner/investigations/${selectedId}/run`, null, {
        params: { max_steps: 8 },
      });
      if (res.data && res.data.cycle_history) {
        for (const cycle of res.data.cycle_history) {
          handleNewDecisionEvent(cycle);
        }
      }
      await fetchFullState(selectedId);
      await fetchDecisions(selectedId);
      onRefreshList();
    } catch (e) {
      console.error(e);
    } finally {
      setIsRunningAuto(false);
    }
  };

  const handlePauseResume = async () => {
    if (!selectedId || !state) return;
    try {
      if (state.status === 'active') {
        await axios.post(`${apiBase}/api/planner/investigations/${selectedId}/pause`);
      } else {
        await axios.post(`${apiBase}/api/planner/investigations/${selectedId}/resume`);
      }
      fetchFullState(selectedId);
      onRefreshList();
    } catch (e) {
      console.error(e);
    }
  };

  if (!selectedId || !state) {
    return (
      <div className="bg-[#111827] border border-gray-800 rounded-2xl p-12 text-center space-y-4">
        <ShieldAlert className="w-12 h-12 text-blue-400 mx-auto opacity-70 animate-bounce" />
        <h3 className="text-lg font-bold text-white">Select or Launch an Investigation</h3>
        <p className="text-xs text-gray-400 max-w-md mx-auto">
          Select an active case from the queue or launch a threat hunting scenario to inspect the autonomous multi-agent reasoning loop.
        </p>
        <div className="flex flex-wrap justify-center gap-2 pt-2">
          {investigations.map((inv) => (
            <button
              key={inv.investigation_id}
              onClick={() => onSelectInvestigation(inv.investigation_id)}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs px-3 py-2 rounded-lg border border-gray-700 font-mono transition"
            >
              {inv.title} ({Math.round(Number(inv.current_confidence) * 100)}%)
            </button>
          ))}
        </div>
      </div>
    );
  }

  const confidencePct = Math.round(Number(state.confidence) * 100);
  const latestDecision = decisions.length > 0 ? decisions[decisions.length - 1] : null;

  return (
    <div className="space-y-6">
      {/* Investigation Control Ribbon */}
      <div className="bg-[#111827] border border-gray-800 rounded-xl p-5 space-y-4 shadow-xl">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span
                className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                  state.status === 'completed'
                    ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                    : state.status === 'paused'
                    ? 'bg-amber-950 text-amber-400 border-amber-800'
                    : 'bg-blue-950 text-blue-400 border-blue-800'
                }`}
              >
                {state.status}
              </span>
              <span className="text-xs font-mono text-gray-400">
                Cycle #{state.planning_cycles} • {state.evidence_count} Evidence Items
              </span>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded-full border flex items-center gap-1 ${
                  wsConnected
                    ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800'
                    : 'bg-gray-800 text-gray-400 border-gray-700'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    wsConnected ? 'bg-emerald-400 animate-ping' : 'bg-gray-500'
                  }`}
                />
                {wsConnected ? 'Live Stream Active' : 'Polling Stream'}
              </span>
            </div>
            <h2 className="text-lg font-bold text-white tracking-wide">{state.title}</h2>
            <p className="text-xs text-gray-400 flex items-center gap-1.5 font-mono">
              <span className="text-blue-400">Current Goal:</span> {state.current_goal || 'Assess threat signals'}
            </p>
          </div>

          {/* Stepping & Paced Simulation Action Controls */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Paced Delay Selector */}
            <div className="flex items-center gap-1 bg-gray-900 border border-gray-800 px-2 py-1.5 rounded-lg text-xs font-mono text-gray-300">
              <Clock className="w-3.5 h-3.5 text-gray-500" />
              <span>Delay:</span>
              <select
                value={pacedInterval}
                onChange={(e) => setPacedInterval(Number(e.target.value))}
                className="bg-transparent text-blue-400 font-bold focus:outline-none cursor-pointer"
              >
                <option value={800} className="bg-gray-900 text-gray-200">0.8s</option>
                <option value={1500} className="bg-gray-900 text-gray-200">1.5s</option>
                <option value={2500} className="bg-gray-900 text-gray-200">2.5s</option>
              </select>
            </div>

            {/* Paced Auto-Hunt Button */}
            {isRunningPaced ? (
              <button
                onClick={handleStopPaced}
                className="bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold px-3 py-2 rounded-lg flex items-center gap-1.5 transition shadow-lg animate-pulse"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause Paced Hunt</span>
              </button>
            ) : (
              <button
                onClick={handleRunPaced}
                disabled={isExecutingStep || isRunningAuto || state.status === 'completed'}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition disabled:opacity-50 shadow-md"
              >
                <Zap className="w-3.5 h-3.5 text-cyan-300" />
                <span>Auto-Hunt (Paced)</span>
              </button>
            )}

            {/* Single Step Button */}
            <button
              onClick={handleStep}
              disabled={isExecutingStep || isRunningAuto || isRunningPaced || state.status === 'completed'}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold px-3.5 py-2 rounded-lg border border-gray-700 flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 text-blue-400" />
              <span>{isExecutingStep ? 'Thinking...' : 'Step Cycle'}</span>
            </button>

            {/* Fast Instant Auto Button */}
            <button
              onClick={handleRunAutonomous}
              disabled={isRunningAuto || isExecutingStep || isRunningPaced || state.status === 'completed'}
              className="bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs px-3 py-2 rounded-lg border border-gray-700 flex items-center gap-1.5 transition disabled:opacity-50"
              title="Fast Forward to End"
            >
              <FastForward className="w-3.5 h-3.5" />
              <span>Instant</span>
            </button>

            <button
              onClick={handlePauseResume}
              className="bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs px-2.5 py-2 rounded-lg border border-gray-700 transition"
              title={state.status === 'active' ? 'Pause Investigation' : 'Resume Investigation'}
            >
              {state.status === 'active' ? (
                <Pause className="w-3.5 h-3.5 text-amber-400" />
              ) : (
                <Play className="w-3.5 h-3.5 text-emerald-400" />
              )}
            </button>

            <button
              onClick={() => {
                fetchFullState(selectedId);
                fetchDecisions(selectedId);
              }}
              className="bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs p-2 rounded-lg border border-gray-700 transition"
              title="Refresh State"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Global Confidence Logit Bar */}
        <div className="space-y-1.5 bg-gray-900/60 p-3 rounded-lg border border-gray-800">
          <div className="flex justify-between items-center text-xs">
            <span className="font-mono text-gray-400 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-blue-400" />
              Posterior Confidence Meter (IS §1.2 Logit Updates):
            </span>
            <span className="font-mono font-bold text-emerald-400 text-sm">
              {confidencePct}% ({state.confidence_state.toUpperCase()})
            </span>
          </div>
          <div className="w-full bg-gray-950 rounded-full h-2.5 overflow-hidden border border-gray-800">
            <div
              className={`h-2.5 rounded-full transition-all duration-700 ${
                confidencePct >= 80
                  ? 'bg-gradient-to-r from-blue-500 to-emerald-400'
                  : confidencePct >= 50
                  ? 'bg-gradient-to-r from-amber-500 to-blue-500'
                  : 'bg-gradient-to-r from-gray-600 to-amber-500'
              }`}
              style={{ width: `${Math.min(100, Math.max(5, confidencePct))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Main Studio Navigation Sub-Tabs */}
      <div className="flex items-center justify-between border-b border-gray-800 pb-2">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveSubTab('observability')}
            className={`text-xs font-semibold px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition ${
              activeSubTab === 'observability'
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-gray-900 text-gray-400 hover:text-white'
            }`}
          >
            <Zap className="w-3.5 h-3.5 text-cyan-300" />
            <span>Agent Cognitive Topology & Thought Stream</span>
          </button>
          <button
            onClick={() => setActiveSubTab('math')}
            className={`text-xs font-semibold px-3.5 py-1.5 rounded-lg flex items-center gap-1.5 transition ${
              activeSubTab === 'math'
                ? 'bg-blue-600 text-white shadow-md'
                : 'bg-gray-900 text-gray-400 hover:text-white'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5 text-amber-300" />
            <span>Utility & 6-Factor Bayesian Math</span>
          </button>
          <button
            onClick={() => setActiveSubTab('timeline')}
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
              activeSubTab === 'timeline'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-900 text-gray-400 hover:text-white'
            }`}
          >
            Attack Timeline & Hypotheses
          </button>
          <button
            onClick={() => setActiveSubTab('graph')}
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
              activeSubTab === 'graph'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-900 text-gray-400 hover:text-white'
            }`}
          >
            Entity Correlation Graph
          </button>
          <button
            onClick={() => setActiveSubTab('evidence')}
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
              activeSubTab === 'evidence'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-900 text-gray-400 hover:text-white'
            }`}
          >
            Evidence Vault ({state.evidence.length})
          </button>
          <button
            onClick={() => setActiveSubTab('reports')}
            className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition ${
              activeSubTab === 'reports'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-900 text-gray-400 hover:text-white'
            }`}
          >
            Reports & Actions
          </button>
        </div>
      </div>

      {/* Main Studio Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Primary Panels */}
        <div className="lg:col-span-2 space-y-6">
          {/* Sub-Tab 0: Observability (Orbital Map + Live Thought Stream) */}
          {activeSubTab === 'observability' && (
            <div className="space-y-6">
              <AgentOrbitalMap
                activeWorker={activeWorker}
                activeCycle={state.planning_cycles}
                confidence={Number(state.confidence)}
                workerLatencies={workerLatencies}
                workerUtilities={latestDecision?.utility_scores}
              />
              <AgentThoughtStream
                logs={thoughtLogs}
                onClearLogs={() => setThoughtLogs([])}
                isStreaming={wsConnected || isRunningPaced}
              />
            </div>
          )}

          {/* Sub-Tab 1: Utility & Bayesian Math Breakdown */}
          {activeSubTab === 'math' && (
            <div className="space-y-6">
              <UtilityBreakdownView
                utilityScores={latestDecision?.utility_scores}
                selectedWorker={latestDecision?.selected_worker}
                cycleNumber={latestDecision?.cycle_number || 1}
              />
              <FactorDecompositionView
                factorContributions={latestDecision?.factor_contributions}
                confidenceBefore={latestDecision?.confidence_before || 0.0}
                confidenceAfter={latestDecision?.confidence_after || Number(state.confidence)}
                confidenceDelta={latestDecision?.confidence_delta || 0.0}
                cycleNumber={latestDecision?.cycle_number || 1}
              />
            </div>
          )}

          {/* Sub-Tab 2: Timeline & Hypotheses */}
          {activeSubTab === 'timeline' && (
            <div className="space-y-6">
              <HypothesisMatrix hypotheses={state.hypotheses} />
              <AttackTimeline events={state.timeline_events} />
            </div>
          )}

          {/* Sub-Tab 3: Entity Correlation Graph */}
          {activeSubTab === 'graph' && (
            <div className="bg-[#111827] border border-gray-800 p-5 rounded-xl">
              <EntityGraphCanvas
                nodes={state.entity_graph.nodes}
                edges={state.entity_graph.edges}
                density={state.entity_graph.density}
              />
            </div>
          )}

          {/* Sub-Tab 4: Evidence Vault */}
          {activeSubTab === 'evidence' && (
            <div className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-800 flex justify-between items-center text-xs font-semibold uppercase text-gray-300">
                <span>Corroborated Evidence Records</span>
                <span className="text-gray-500 font-mono">{state.evidence.length} Entries</span>
              </div>
              <div className="divide-y divide-gray-800 max-h-96 overflow-y-auto">
                {state.evidence.map((ev: any) => (
                  <div key={ev.evidence_id} className="p-3.5 space-y-1 text-xs hover:bg-gray-800/40">
                    <div className="flex items-center justify-between">
                      <span className="font-mono bg-gray-900 border border-gray-800 px-1.5 py-0.5 rounded text-[10px] text-blue-400 uppercase">
                        {ev.source_type}
                      </span>
                      <span className="text-[10px] text-gray-500 font-mono">
                        Worker: {ev.produced_by_worker || 'Ingest'}
                      </span>
                    </div>
                    <p className="text-gray-200 font-medium">{ev.description}</p>
                    {ev.source_ref && (
                      <p className="text-[10px] text-gray-500 font-mono truncate">{ev.source_ref}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sub-Tab 5: Reports & Containment */}
          {activeSubTab === 'reports' && (
            <div className="space-y-6">
              <ContainmentPanel
                recommendations={state.recommendations}
                apiBase={apiBase}
                onActionComplete={() => fetchFullState(selectedId)}
              />
              <ReportViewer reports={state.reports} />
            </div>
          )}
        </div>

        {/* Right Column: Planner Decision Trace / Audit Log & Factor Inspection */}
        <div className="space-y-6">
          <ContainmentPanel
            recommendations={state.recommendations}
            apiBase={apiBase}
            onActionComplete={() => fetchFullState(selectedId)}
          />

          <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 space-y-3 shadow-xl">
            <div className="flex items-center justify-between border-b border-gray-800 pb-2.5">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-purple-400" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-200">
                  Planner Decision Audit Trail
                </h3>
              </div>
              <span className="text-[10px] font-mono text-gray-400">
                {decisions.length} Cycles
              </span>
            </div>

            <div className="space-y-2.5 max-h-[600px] overflow-y-auto pr-1">
              {decisions.length === 0 ? (
                <div className="p-4 text-center text-gray-500 text-xs">
                  No planner cycles logged yet. Click "Step Cycle" or "Auto-Hunt (Paced)" to observe execution.
                </div>
              ) : (
                decisions.map((d: PlannerDecision) => {
                  const isExpanded = expandedDecisionId === d.decision_id;
                  return (
                    <div
                      key={d.decision_id}
                      className="p-3 bg-gray-900 border border-gray-800 rounded-lg text-xs space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-blue-400">
                          Cycle #{d.cycle_number} → {d.selected_worker.toUpperCase()}
                        </span>
                        <div className="flex items-center gap-2">
                          {d.latency_ms && (
                            <span className="text-[9px] font-mono text-gray-400 bg-gray-950 px-1 py-0.5 rounded">
                              {d.latency_ms}ms
                            </span>
                          )}
                          <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                            {(d.confidence_before * 100).toFixed(0)}% → {(d.confidence_after * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      <p className="text-gray-300 text-[11px] leading-relaxed">
                        {d.explanation_summary}
                      </p>

                      {d.knowledge_need && (
                        <div className="text-[10px] font-mono text-purple-300 bg-purple-950/60 border border-purple-800/70 p-1.5 rounded">
                          <strong className="text-purple-400">RAG Context:</strong> {d.knowledge_need}
                        </div>
                      )}

                      {/* Expandable Utility & Factor Details Button */}
                      {(d.utility_scores || d.factor_contributions) && (
                        <button
                          onClick={() => setExpandedDecisionId(isExpanded ? null : d.decision_id)}
                          className="w-full flex items-center justify-between text-[10px] text-gray-400 hover:text-gray-200 pt-1 border-t border-gray-800/80 transition"
                        >
                          <span className="font-mono">Inspect Math (Utility & 6 Factors)</span>
                          {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                        </button>
                      )}

                      {/* Expanded Math Details */}
                      {isExpanded && (
                        <div className="space-y-2 pt-1">
                          {d.utility_scores && (
                            <div className="p-2 bg-black/50 border border-gray-800 rounded font-mono text-[10px] space-y-1">
                              <span className="text-amber-400 font-bold">Worker Utility Scores ($U_w$):</span>
                              <div className="grid grid-cols-2 gap-1 text-gray-300">
                                {Object.entries(d.utility_scores).map(([k, v]) => (
                                  <div key={k} className="flex justify-between">
                                    <span>{k}:</span>
                                    <strong className={k === d.selected_worker ? 'text-amber-300' : 'text-gray-400'}>
                                      {Number(v).toFixed(3)}
                                    </strong>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {d.factor_contributions && (
                            <div className="p-2 bg-black/50 border border-gray-800 rounded font-mono text-[10px] space-y-1">
                              <span className="text-emerald-400 font-bold">Bayesian Factor Deltas ($w_i \cdot \delta_i$):</span>
                              <div className="grid grid-cols-2 gap-1 text-gray-300">
                                {Object.entries(d.factor_contributions).map(([k, v]: [string, any]) => (
                                  <div key={k} className="flex justify-between">
                                    <span>{k}:</span>
                                    <strong className="text-emerald-300">
                                      {v.weighted_contribution >= 0 ? `+${Number(v.weighted_contribution).toFixed(3)}` : Number(v.weighted_contribution).toFixed(3)}
                                    </strong>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
