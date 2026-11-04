import React from 'react';
import {
  FileText,
  Layers,
  Cpu,
  BarChart2,
  ShieldCheck,
  BarChart3,
  ShieldAlert,
  X,
  ChevronRight
} from 'lucide-react';

import { AttackTimeline, TimelineEventItem } from '../AttackTimeline';
import { EntityGraphCanvas } from '../EntityGraphCanvas';
import { HypothesisMatrix, HypothesisItem } from '../HypothesisMatrix';
import { ReportViewer, ReportItem } from '../ReportViewer';
import { FactorDecompositionView } from '../FactorDecompositionView';
import { ContainmentPanel, RecommendationItem } from '../ContainmentPanel';
import { BenchmarkTab } from '../BenchmarkTab';
import { AgentOrbitalMap } from '../AgentOrbitalMap';
import { AlertsTab } from '../AlertsTab';

export interface TabItem {
  id: string;
  title: string;
  type: 'timeline' | 'graph' | 'matrix' | 'reports' | 'math' | 'utility' | 'containment' | 'benchmarks' | 'orbital' | 'alerts';
}

interface CentralWorkspaceProps {
  apiBase: string;
  tabs: TabItem[];
  activeTabId: string;
  onSelectTab: (id: string) => void;
  onCloseTab: (id: string) => void;
  // Live investigation data
  investigation: {
    investigation_id: string;
    title: string;
    status: string;
    current_confidence: number;
    confidence_state: string;
    planning_cycle_count: number;
  } | null;
  state: {
    timeline_events: TimelineEventItem[];
    entity_graph: {
      nodes: Array<{ id: string; label: string; type: 'host' | 'ip' | 'user' | 'process' }>;
      edges: Array<{ source: string; target: string; evidence_id?: string }>;
      density: number;
    };
    hypotheses: HypothesisItem[];
    reports: ReportItem[];
    recommendations: RecommendationItem[];
    evidence: any[];
  } | null;
  decisions: any[];
  activeWorker: string | null;
  workerLatencies: Record<string, number>;
  onRefreshInvestigation: () => void;
  scenarioName?: string;
}

export const CentralWorkspace: React.FC<CentralWorkspaceProps> = ({
  apiBase,
  tabs,
  activeTabId,
  onSelectTab,
  onCloseTab,
  investigation,
  state,
  decisions,
  activeWorker,
  workerLatencies,
  onRefreshInvestigation,
  scenarioName,
}) => {
  const activeTab = tabs.find((t) => t.id === activeTabId) || tabs[0];

  const getTabIcon = (type: TabItem['type']) => {
    switch (type) {
      case 'timeline':
        return <FileText className="w-3.5 h-3.5 text-blue-400" />;
      case 'graph':
        return <Layers className="w-3.5 h-3.5 text-emerald-400" />;
      case 'matrix':
        return <Cpu className="w-3.5 h-3.5 text-purple-400" />;
      case 'reports':
        return <FileText className="w-3.5 h-3.5 text-amber-400" />;
      case 'math':
        return <BarChart2 className="w-3.5 h-3.5 text-pink-400" />;
      case 'containment':
        return <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />;
      case 'benchmarks':
        return <BarChart3 className="w-3.5 h-3.5 text-indigo-400" />;
      case 'orbital':
        return <Layers className="w-3.5 h-3.5 text-orange-400" />;
      case 'alerts':
        return <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />;
      default:
        return <FileText className="w-3.5 h-3.5 text-gray-400" />;
    }
  };

  const latestDecision = decisions.length > 0 ? decisions[decisions.length - 1] : null;

  return (
    <div className="flex-1 flex flex-col bg-[#0B0F19] overflow-hidden select-none">
      {/* Editor Tab Bar */}
      <div className="h-9 bg-[#090D16] border-b border-gray-800/80 flex items-center px-1 overflow-x-auto custom-scrollbar shrink-0">
        <div className="flex items-center gap-1">
          {tabs.map((tab) => {
            const isActive = tab.id === activeTabId;
            return (
              <div
                key={tab.id}
                onClick={() => onSelectTab(tab.id)}
                className={`group flex items-center gap-2 px-3 py-1.5 text-xs rounded-t border-t-2 cursor-pointer transition select-none ${
                  isActive
                    ? 'bg-[#0B0F19] text-white border-blue-500 font-medium'
                    : 'border-transparent text-gray-400 hover:text-gray-200 hover:bg-gray-800/40'
                }`}
              >
                {getTabIcon(tab.type)}
                <span className="font-mono text-[11px] truncate max-w-[160px]">{tab.title}</span>
                {tabs.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onCloseTab(tab.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded hover:bg-gray-700/60 text-gray-400 hover:text-white transition"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Breadcrumb Navigation Bar */}
      <div className="h-7 px-4 bg-[#0D121F]/80 border-b border-gray-800/60 flex items-center justify-between text-[11px] text-gray-400 font-mono shrink-0">
        <div className="flex items-center gap-1.5 truncate">
          <span className="text-blue-400">sentinel</span>
          <ChevronRight className="w-3 h-3 text-gray-600" />
          <span className="text-gray-300">{scenarioName || 'Autonomous Hunt'}</span>
          <ChevronRight className="w-3 h-3 text-gray-600" />
          <span className="text-gray-200 truncate">{investigation?.title || 'Active Investigation'}</span>
          <ChevronRight className="w-3 h-3 text-gray-600" />
          <span className="text-white font-semibold">{activeTab.title}</span>
        </div>

        {/* Quick Cycle & Confidence Capsule */}
        {investigation && (
          <div className="flex items-center gap-2">
            <span className="text-gray-400">
              Cycle <strong className="text-white">{investigation.planning_cycle_count}</strong>
            </span>
            <span className="text-gray-600">|</span>
            <span className="text-gray-400">
              Posterior: <strong className="text-blue-400">{(investigation.current_confidence * 100).toFixed(1)}%</strong>
            </span>
          </div>
        )}
      </div>

      {/* Active Tab Canvas Body */}
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        {/* Attack Timeline Canvas */}
        {activeTab.type === 'timeline' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-white">Reconstructed Multi-Stage Attack Sequence</h2>
                <p className="text-xs text-gray-400">
                  Chronological alignment of host and network evidence normalized across timestamps.
                </p>
              </div>
              <span className="text-xs font-mono bg-blue-950 text-blue-300 border border-blue-800 px-2.5 py-1 rounded">
                Events: {state?.timeline_events.length || 0}
              </span>
            </div>
            <AttackTimeline events={state?.timeline_events || []} />
          </div>
        )}

        {/* Entity Graph Visual */}
        {activeTab.type === 'graph' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-white">Cross-Telemetry Security Entity Graph</h2>
                <p className="text-xs text-gray-400">
                  Network and host entities mapped across hosts, users, IPs, and process executions.
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs font-mono">
                <span className="bg-gray-800 text-gray-300 px-2 py-0.5 rounded border border-gray-700">
                  Nodes: {state?.entity_graph.nodes.length || 0}
                </span>
                <span className="bg-gray-800 text-gray-300 px-2 py-0.5 rounded border border-gray-700">
                  Edges: {state?.entity_graph.edges.length || 0}
                </span>
                <span className="bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded border border-emerald-800">
                  Density: {(state?.entity_graph.density || 0).toFixed(2)}
                </span>
              </div>
            </div>
            <EntityGraphCanvas
              nodes={state?.entity_graph.nodes || []}
              edges={state?.entity_graph.edges || []}
              density={state?.entity_graph.density || 0}
            />
          </div>
        )}

        {/* Hypothesis Matrix */}
        {activeTab.type === 'matrix' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-white">Threat Hypothesis & Contradiction Matrix</h2>
                <p className="text-xs text-gray-400">
                  Formulated attack explanations with supporting and contradicting evidentiary links.
                </p>
              </div>
              <span className="text-xs font-mono bg-purple-950 text-purple-300 border border-purple-800 px-2.5 py-1 rounded">
                Hypotheses: {state?.hypotheses.length || 0}
              </span>
            </div>
            <HypothesisMatrix hypotheses={state?.hypotheses || []} />
          </div>
        )}

        {/* Forensic Incident Reports */}
        {activeTab.type === 'reports' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-white">Forensic Incident Reports (Twin-Tier)</h2>
                <p className="text-xs text-gray-400">
                  Executive briefing for leadership paired with full technical forensic reconstruction.
                </p>
              </div>
              <span className="text-xs font-mono bg-amber-950 text-amber-300 border border-amber-800 px-2.5 py-1 rounded">
                Generated: {state?.reports.length || 0}
              </span>
            </div>
            <ReportViewer reports={state?.reports || []} />
          </div>
        )}

        {/* Factor Decomposition / Mathematical Logit Decay */}
        {activeTab.type === 'math' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-sm font-semibold text-white">Mathematical Logit Factor Decomposition (IS §1.3)</h2>
              <p className="text-xs text-gray-400">
                Log-odds Bayesian updates decomposed into detection, evidence, correlation, and knowledge components.
              </p>
            </div>
            {latestDecision?.factor_contributions ? (
              <FactorDecompositionView
                factorContributions={latestDecision.factor_contributions}
                confidenceBefore={latestDecision.confidence_before}
                confidenceAfter={latestDecision.confidence_after}
                confidenceDelta={latestDecision.confidence_delta}
                cycleNumber={latestDecision.cycle_number}
              />
            ) : (
              <div className="p-8 border border-dashed border-gray-800 rounded-xl text-center text-gray-500 text-xs font-mono">
                No active mathematical decisions recorded yet. Run a planning cycle to view Bayesian logit breakdown.
              </div>
            )}
          </div>
        )}

        {/* Containment HITL Panel */}
        {activeTab.type === 'containment' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-white">Human-In-The-Loop Containment Actions</h2>
                <p className="text-xs text-gray-400">
                  Review and authorize automated response actions (Network isolation, IP blocks, session resets).
                </p>
              </div>
            </div>
            <ContainmentPanel
              recommendations={state?.recommendations || []}
              apiBase={apiBase}
              onActionComplete={onRefreshInvestigation}
            />
          </div>
        )}

        {/* Benchmarks Lab */}
        {activeTab.type === 'benchmarks' && (
          <div className="space-y-4">
            <BenchmarkTab apiBase={apiBase} />
          </div>
        )}

        {/* Agent Orbital Map */}
        {activeTab.type === 'orbital' && (
          <div className="space-y-4">
            <AgentOrbitalMap
              activeWorker={activeWorker}
              activeCycle={investigation?.planning_cycle_count || 0}
              confidence={investigation?.current_confidence || 0}
              workerLatencies={workerLatencies}
            />
          </div>
        )}

        {/* Real-Time Detection Alerts & Incident Candidates */}
        {activeTab.type === 'alerts' && (
          <div className="space-y-4">
            <AlertsTab
              apiBase={apiBase}
              onPromoteCandidate={() => onRefreshInvestigation()}
            />
          </div>
        )}
      </div>
    </div>
  );
};
