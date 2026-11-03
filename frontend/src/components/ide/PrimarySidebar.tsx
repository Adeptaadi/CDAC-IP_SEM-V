import React from 'react';
import {
  ChevronDown,
  ChevronRight,
  Plus,
  Play,
  Sparkles,
  Search,
  ShieldAlert,
  BarChart2,
  Cpu,
  Layers,
  FileText
} from 'lucide-react';
import { ActivityBarItem } from './ActivityBar';

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

interface Investigation {
  investigation_id: string;
  title: string;
  status: string;
  current_confidence: number;
  confidence_state: string;
  planning_cycle_count: number;
  created_at: string;
}

interface PrimarySidebarProps {
  activeItem: ActivityBarItem;
  scenarios: Scenario[];
  selectedScenarioId: string;
  onSelectScenario: (id: string) => void;
  investigations: Investigation[];
  selectedInvestigationId: string | null;
  onSelectInvestigation: (id: string) => void;
  onCreateInvestigation: (title: string) => void;
  onAutoHuntScenario: () => void;
  isAutoHunting: boolean;
  onSeedKnowledge: () => void;
  isSeedingKnowledge: boolean;
  onQueryKnowledge: (query: string) => void;
  knowledgeQuery: string;
  setKnowledgeQuery: (q: string) => void;
  retrievedContext: any;
  isQueryingKnowledge: boolean;
  pendingApprovalsCount: number;
  onOpenView: (viewId: string) => void;
}

export const PrimarySidebar: React.FC<PrimarySidebarProps> = ({
  activeItem,
  scenarios,
  selectedScenarioId,
  onSelectScenario,
  investigations,
  selectedInvestigationId,
  onSelectInvestigation,
  onCreateInvestigation,
  onAutoHuntScenario,
  isAutoHunting,
  onSeedKnowledge,
  isSeedingKnowledge,
  onQueryKnowledge,
  knowledgeQuery,
  setKnowledgeQuery,
  retrievedContext,
  isQueryingKnowledge,
  pendingApprovalsCount,
  onOpenView,
}) => {
  const [newHuntTitle, setNewHuntTitle] = React.useState('');
  const [showNewHuntInput, setShowNewHuntInput] = React.useState(false);
  const [expandedSections, setExpandedSections] = React.useState<Record<string, boolean>>({
    hunts: true,
    scenarios: true,
    views: true,
    rag: true,
  });

  const toggleSection = (s: string) => {
    setExpandedSections((prev) => ({ ...prev, [s]: !prev[s] }));
  };

  const handleCreateHunt = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHuntTitle.trim()) return;
    onCreateInvestigation(newHuntTitle.trim());
    setNewHuntTitle('');
    setShowNewHuntInput(false);
  };

  return (
    <div className="w-64 bg-[#0D121F] border-r border-gray-800/80 flex flex-col h-full shrink-0 select-none text-xs">
      {/* Sidebar Header */}
      <div className="h-9 px-3 border-b border-gray-800/80 flex items-center justify-between text-gray-400 font-semibold uppercase tracking-wider text-[11px] bg-[#0A0E18]">
        <span>
          {activeItem === 'explorer' && 'Explorer : Sentinel Workspace'}
          {activeItem === 'studio' && 'Threat Studio Navigator'}
          {activeItem === 'containment' && 'Containment Queue'}
          {activeItem === 'benchmarks' && 'Evaluation Harness'}
          {activeItem === 'knowledge' && 'Knowledge & RAG Engine'}
          {activeItem === 'settings' && 'Platform Settings'}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-4">
        {/* ================= EXPLORER / STUDIO NAVIGATOR ================= */}
        {(activeItem === 'explorer' || activeItem === 'studio') && (
          <>
            {/* Quick Views Navigation */}
            <div>
              <div
                onClick={() => toggleSection('views')}
                className="flex items-center justify-between px-2 py-1 text-gray-400 hover:text-gray-200 cursor-pointer font-medium uppercase tracking-wider text-[10px]"
              >
                <span className="flex items-center gap-1.5">
                  {expandedSections.views ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  Canvas Editors
                </span>
              </div>
              {expandedSections.views && (
                <div className="mt-1 space-y-0.5 pl-2 font-mono">
                  {[
                    { id: 'timeline', label: 'AttackTimeline.canvas', icon: <FileText className="w-3.5 h-3.5 text-blue-400" /> },
                    { id: 'graph', label: 'EntityGraph.visual', icon: <Layers className="w-3.5 h-3.5 text-emerald-400" /> },
                    { id: 'matrix', label: 'Hypotheses.matrix', icon: <Cpu className="w-3.5 h-3.5 text-purple-400" /> },
                    { id: 'reports', label: 'ForensicReport.md', icon: <FileText className="w-3.5 h-3.5 text-amber-400" /> },
                    { id: 'math', label: 'ConfidenceDecay.math', icon: <BarChart2 className="w-3.5 h-3.5 text-pink-400" /> },
                    { id: 'orbital', label: 'AgentOrbital.map', icon: <Layers className="w-3.5 h-3.5 text-orange-400" /> },
                  ].map((v) => (
                    <button
                      key={v.id}
                      onClick={() => onOpenView(v.id)}
                      className="w-full flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-800/60 text-gray-300 hover:text-white text-left transition"
                    >
                      {v.icon}
                      <span>{v.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Active Investigations / Hunts Tree */}
            <div>
              <div
                onClick={() => toggleSection('hunts')}
                className="flex items-center justify-between px-2 py-1 text-gray-400 hover:text-gray-200 cursor-pointer font-medium uppercase tracking-wider text-[10px]"
              >
                <span className="flex items-center gap-1.5">
                  {expandedSections.hunts ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  Investigations ({investigations.length})
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowNewHuntInput(true);
                  }}
                  title="New Investigation"
                  className="p-1 hover:bg-gray-800 rounded text-gray-300 hover:text-white"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>
              </div>

              {expandedSections.hunts && (
                <div className="mt-1 space-y-1 pl-1">
                  {showNewHuntInput && (
                    <form onSubmit={handleCreateHunt} className="p-1.5 bg-gray-900 border border-blue-600/50 rounded mb-2">
                      <input
                        type="text"
                        autoFocus
                        placeholder="Investigation title..."
                        value={newHuntTitle}
                        onChange={(e) => setNewHuntTitle(e.target.value)}
                        className="w-full bg-black/60 border border-gray-700 px-2 py-1 text-[11px] rounded text-white focus:outline-none focus:border-blue-500"
                      />
                      <div className="flex justify-end gap-1 mt-1.5">
                        <button
                          type="button"
                          onClick={() => setShowNewHuntInput(false)}
                          className="px-2 py-0.5 text-[10px] text-gray-400 hover:text-white"
                        >
                          Cancel
                        </button>
                        <button
                          type="submit"
                          className="px-2 py-0.5 text-[10px] bg-blue-600 hover:bg-blue-500 text-white rounded font-medium"
                        >
                          Create
                        </button>
                      </div>
                    </form>
                  )}

                  {investigations.map((inv) => {
                    const isSelected = selectedInvestigationId === inv.investigation_id;
                    return (
                      <div
                        key={inv.investigation_id}
                        onClick={() => onSelectInvestigation(inv.investigation_id)}
                        className={`px-2 py-1.5 rounded cursor-pointer transition flex flex-col gap-0.5 border ${
                          isSelected
                            ? 'bg-blue-950/40 border-blue-600/50 text-white'
                            : 'border-transparent text-gray-300 hover:bg-gray-800/50 hover:text-white'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium truncate max-w-[140px]" title={inv.title}>
                            {inv.title}
                          </span>
                          <span
                            className={`text-[9px] px-1.5 py-0.2 rounded font-mono font-semibold uppercase ${
                              inv.current_confidence >= 0.75
                                ? 'bg-red-950 text-red-400 border border-red-800'
                                : inv.current_confidence >= 0.4
                                ? 'bg-amber-950 text-amber-400 border border-amber-800'
                                : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            }`}
                          >
                            {(inv.current_confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[10px] text-gray-400">
                          <span>Cycles: {inv.planning_cycle_count}</span>
                          <span className="capitalize">{inv.status}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Benchmark Scenarios Tree */}
            <div>
              <div
                onClick={() => toggleSection('scenarios')}
                className="flex items-center justify-between px-2 py-1 text-gray-400 hover:text-gray-200 cursor-pointer font-medium uppercase tracking-wider text-[10px]"
              >
                <span className="flex items-center gap-1.5">
                  {expandedSections.scenarios ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  CSE-CIC-IDS2018 Scenarios
                </span>
              </div>

              {expandedSections.scenarios && (
                <div className="mt-1 space-y-1 pl-1">
                  {scenarios.map((sc) => {
                    const isSelected = selectedScenarioId === sc.scenario_id;
                    return (
                      <div
                        key={sc.scenario_id}
                        onClick={() => onSelectScenario(sc.scenario_id)}
                        className={`p-2 rounded cursor-pointer transition border ${
                          isSelected
                            ? 'bg-indigo-950/40 border-indigo-600/50 text-white'
                            : 'border-transparent text-gray-300 hover:bg-gray-800/40 hover:text-white'
                        }`}
                      >
                        <div className="font-medium text-[11px] truncate">{sc.name}</div>
                        <div className="text-[10px] text-gray-400 mt-0.5 line-clamp-1">{sc.description}</div>
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {sc.mitre_techniques.slice(0, 2).map((t) => (
                            <span key={t} className="text-[9px] bg-gray-900 border border-gray-700 px-1 rounded text-cyan-400 font-mono">
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  })}

                  {/* 1-Click Autonomous Hunt Trigger */}
                  <div className="pt-2">
                    <button
                      onClick={onAutoHuntScenario}
                      disabled={isAutoHunting}
                      className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 text-white py-1.5 px-3 rounded-md font-medium text-[11px] flex items-center justify-center gap-1.5 shadow-md shadow-blue-900/20 transition"
                    >
                      <Sparkles className="w-3.5 h-3.5 animate-pulse" />
                      <span>{isAutoHunting ? 'Hunting Scenario...' : 'Autonomous Hunt 1-Click'}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {/* ================= CONTAINMENT HITL SECTION ================= */}
        {activeItem === 'containment' && (
          <div className="space-y-3">
            <div className="p-2 bg-amber-950/20 border border-amber-800/40 rounded text-amber-300 text-[11px]">
              <div className="font-semibold flex items-center gap-1.5 mb-1">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <span>Governance Policy</span>
              </div>
              <p className="text-gray-300 text-[10px] leading-relaxed">
                Automated containment is staged as recommendations requiring human-on-the-loop sign-off before network/process isolation.
              </p>
            </div>

            <div className="border border-gray-800 rounded p-2 bg-gray-900/40">
              <span className="text-gray-400 uppercase text-[10px] font-semibold">Active Approvals</span>
              <div className="mt-1 text-2xl font-bold font-mono text-white">
                {pendingApprovalsCount} <span className="text-xs text-amber-400 font-normal">Pending</span>
              </div>
            </div>

            <button
              onClick={() => onOpenView('containment')}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white py-1.5 rounded font-medium"
            >
              Open Containment Workstation
            </button>
          </div>
        )}

        {/* ================= BENCHMARK LAB SECTION ================= */}
        {activeItem === 'benchmarks' && (
          <div className="space-y-3">
            <div className="p-2 bg-blue-950/20 border border-blue-800/40 rounded text-blue-300 text-[11px]">
              <div className="font-semibold flex items-center gap-1.5 mb-1">
                <BarChart2 className="w-4 h-4 text-blue-400" />
                <span>Scientific Validation</span>
              </div>
              <p className="text-gray-300 text-[10px] leading-relaxed">
                Evaluates Planner Accuracy, Evidence Coverage, Hallucination Rate, and Expected Calibration Error (ECE) across 5 scenarios.
              </p>
            </div>

            <button
              onClick={() => onOpenView('benchmarks')}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-1.5 rounded font-medium flex items-center justify-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5" />
              <span>Launch Benchmark Harness</span>
            </button>
          </div>
        )}

        {/* ================= KNOWLEDGE & RAG SECTION ================= */}
        {activeItem === 'knowledge' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 uppercase text-[10px] font-semibold">ChromaDB Store</span>
              <button
                onClick={onSeedKnowledge}
                disabled={isSeedingKnowledge}
                className="text-[10px] bg-gray-800 hover:bg-gray-700 text-blue-400 px-2 py-0.5 rounded border border-gray-700"
              >
                {isSeedingKnowledge ? 'Seeding...' : 'Seed MITRE'}
              </button>
            </div>

            {/* Query Box */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                onQueryKnowledge(knowledgeQuery);
              }}
              className="space-y-1.5"
            >
              <div className="relative">
                <input
                  type="text"
                  placeholder="Semantic query (e.g. macro)..."
                  value={knowledgeQuery}
                  onChange={(e) => setKnowledgeQuery(e.target.value)}
                  className="w-full bg-black/60 border border-gray-700 pl-7 pr-2 py-1.5 rounded text-[11px] text-white focus:outline-none focus:border-blue-500"
                />
                <Search className="w-3.5 h-3.5 text-gray-500 absolute left-2 top-2" />
              </div>
              <button
                type="submit"
                disabled={isQueryingKnowledge || !knowledgeQuery}
                className="w-full bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white py-1 rounded text-[11px] font-medium"
              >
                {isQueryingKnowledge ? 'Searching...' : 'Search ATT&CK RAG'}
              </button>
            </form>

            {/* Results */}
            {retrievedContext && retrievedContext.chunks && (
              <div className="space-y-1.5 mt-2">
                <span className="text-[10px] text-gray-400 uppercase font-semibold">Retrieved Chunks:</span>
                {retrievedContext.chunks.map((c: any, idx: number) => (
                  <div key={idx} className="p-2 bg-gray-900 border border-gray-800 rounded font-mono text-[10px]">
                    <div className="flex items-center justify-between text-blue-400 mb-0.5">
                      <span className="uppercase">{c.category}</span>
                      <span>{(c.similarity_score * 100).toFixed(0)}% sim</span>
                    </div>
                    <div className="text-gray-300 line-clamp-3">{c.text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ================= SETTINGS SECTION ================= */}
        {activeItem === 'settings' && (
          <div className="space-y-3 text-gray-300">
            <div className="border border-gray-800 rounded p-2.5 bg-gray-900/50 space-y-2">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">LLM Orchestrator</span>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-gray-400">Daemon:</span>
                <span className="font-mono text-emerald-400">Ollama (Local)</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-gray-400">Active Model:</span>
                <span className="font-mono text-white">qwen2.5:latest</span>
              </div>
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-gray-400">Air-Gap Fallback:</span>
                <span className="font-mono text-blue-400">Deterministic</span>
              </div>
            </div>

            <div className="border border-gray-800 rounded p-2.5 bg-gray-900/50 space-y-2">
              <span className="text-[10px] uppercase font-semibold text-gray-400 block">Persistence</span>
              <div className="text-[11px] text-gray-400 flex justify-between">
                <span>Database:</span>
                <span className="font-mono text-white">PostgreSQL / SQLite</span>
              </div>
              <div className="text-[11px] text-gray-400 flex justify-between">
                <span>Vector Store:</span>
                <span className="font-mono text-white">ChromaDB</span>
              </div>
              <div className="text-[11px] text-gray-400 flex justify-between">
                <span>Audit Trail:</span>
                <span className="font-mono text-emerald-400">Enabled (HITL)</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
