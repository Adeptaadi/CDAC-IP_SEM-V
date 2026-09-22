import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ShieldAlert,
  Play,
  FastForward,
  Pause,
  Cpu,
  RefreshCw,
  Terminal
} from 'lucide-react';

import { AttackTimeline, TimelineEventItem } from './AttackTimeline';
import { EntityGraphCanvas } from './EntityGraphCanvas';
import { HypothesisMatrix, HypothesisItem } from './HypothesisMatrix';
import { ContainmentPanel, RecommendationItem } from './ContainmentPanel';
import { ReportViewer, ReportItem } from './ReportViewer';

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
  const [activeSubTab, setActiveSubTab] = useState<'timeline' | 'graph' | 'evidence' | 'reports'>('timeline');
  const [isRunningAuto, setIsRunningAuto] = useState(false);
  const [isExecutingStep, setIsExecutingStep] = useState(false);

  useEffect(() => {
    if (selectedId) {
      fetchFullState(selectedId);
      fetchDecisions(selectedId);
    }
  }, [selectedId]);

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
    } catch (e) {
      console.error(e);
    }
  };

  const handleStep = async () => {
    if (!selectedId) return;
    setIsExecutingStep(true);
    try {
      await axios.post(`${apiBase}/api/planner/investigations/${selectedId}/step`);
      await fetchFullState(selectedId);
      await fetchDecisions(selectedId);
      onRefreshList();
    } catch (e) {
      console.error(e);
    } finally {
      setIsExecutingStep(false);
    }
  };

  const handleRunAutonomous = async () => {
    if (!selectedId) return;
    setIsRunningAuto(true);
    try {
      await axios.post(`${apiBase}/api/planner/investigations/${selectedId}/run`, null, {
        params: { max_steps: 8 },
      });
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
          Select an active case from the queue or launch a threat hunting investigation to inspect the autonomous multi-agent reasoning loop.
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

  return (
    <div className="space-y-6">
      {/* Investigation Control Ribbon */}
      <div className="bg-[#111827] border border-gray-800 rounded-xl p-5 space-y-4">
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
            </div>
            <h2 className="text-lg font-bold text-white tracking-wide">{state.title}</h2>
            <p className="text-xs text-gray-400 flex items-center gap-1.5 font-mono">
              <span className="text-blue-400">Current Goal:</span> {state.current_goal || 'Assess threat signals'}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleStep}
              disabled={isExecutingStep || isRunningAuto || state.status === 'completed'}
              className="bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold px-4 py-2 rounded-lg border border-gray-700 flex items-center gap-1.5 transition disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 text-blue-400" />
              <span>{isExecutingStep ? 'Executing Cycle...' : 'Step (+1 Cycle)'}</span>
            </button>

            <button
              onClick={handleRunAutonomous}
              disabled={isRunningAuto || isExecutingStep || state.status === 'completed'}
              className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 transition disabled:opacity-50 shadow-lg shadow-blue-950"
            >
              <FastForward className="w-3.5 h-3.5" />
              <span>{isRunningAuto ? 'Running Autonomous Loop...' : 'Run Autonomous Loop'}</span>
            </button>

            <button
              onClick={handlePauseResume}
              className="bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs px-3 py-2 rounded-lg border border-gray-700 transition"
              title={state.status === 'active' ? 'Pause Hunt' : 'Resume Hunt'}
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

      {/* Main Studio Workspace Tabs */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Columns: Primary Panels */}
        <div className="lg:col-span-2 space-y-6">
          {/* Navigation Sub-Tabs */}
          <div className="flex items-center justify-between border-b border-gray-800 pb-2">
            <div className="flex gap-2">
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

          {/* Sub-Tab 1: Timeline & Hypotheses */}
          {activeSubTab === 'timeline' && (
            <div className="space-y-6">
              <HypothesisMatrix hypotheses={state.hypotheses} />
              <AttackTimeline events={state.timeline_events} />
            </div>
          )}

          {/* Sub-Tab 2: Entity Correlation Graph */}
          {activeSubTab === 'graph' && (
            <div className="bg-[#111827] border border-gray-800 p-5 rounded-xl">
              <EntityGraphCanvas
                nodes={state.entity_graph.nodes}
                edges={state.entity_graph.edges}
                density={state.entity_graph.density}
              />
            </div>
          )}

          {/* Sub-Tab 3: Evidence Vault */}
          {activeSubTab === 'evidence' && (
            <div className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-800 flex justify-between items-center text-xs font-semibold uppercase text-gray-300">
                <span>Corroborated Evidence Records</span>
                <span className="text-gray-500 font-mono">{state.evidence.length} Entries</span>
              </div>
              <div className="divide-y divide-gray-800 max-h-96 overflow-y-auto">
                {state.evidence.map((ev) => (
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

          {/* Sub-Tab 4: Reports & Containment */}
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

        {/* Right Column: Planner Decision Trace / Audit Log & Live Actions */}
        <div className="space-y-6">
          <ContainmentPanel
            recommendations={state.recommendations}
            apiBase={apiBase}
            onActionComplete={() => fetchFullState(selectedId)}
          />

          <div className="bg-[#111827] border border-gray-800 rounded-xl p-4 space-y-3">
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

            <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-1">
              {decisions.length === 0 ? (
                <div className="p-4 text-center text-gray-500 text-xs">
                  No planner cycles logged yet. Click "Step" or "Run Autonomous" to execute.
                </div>
              ) : (
                decisions.map((d) => (
                  <div
                    key={d.decision_id}
                    className="p-3 bg-gray-900 border border-gray-800 rounded-lg text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-blue-400">
                        Cycle #{d.cycle_number} → {d.selected_worker.toUpperCase()}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400 font-semibold">
                        {(d.confidence_before * 100).toFixed(0)}% → {(d.confidence_after * 100).toFixed(0)}%
                      </span>
                    </div>

                    <p className="text-gray-300 text-[11px] leading-relaxed">
                      {d.explanation_summary}
                    </p>

                    {d.knowledge_need && (
                      <div className="text-[10px] font-mono text-purple-300 bg-purple-950/60 border border-purple-800/70 p-1.5 rounded">
                        <strong className="text-purple-400">RAG Context:</strong> {d.knowledge_need}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
