import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ShieldAlert,
  Activity,
  Cpu,
  Database,
  Terminal,
  Play,
  Pause,
  RotateCcw,
  CheckCircle,
  Layers,
  Radio,
  Clock,
  Flame,
  FileCode2
} from 'lucide-react';

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

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [health, setHealth] = useState<{ status: string; service: string } | null>(null);
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [selectedWorkerResult, setSelectedWorkerResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  // Dataset Replay State
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('infiltration');
  const [replaySpeed, setReplaySpeed] = useState<number>(1.0);
  const [replayStatus, setReplayStatus] = useState<ReplayStatus>({
    scenario: null,
    state: 'IDLE',
    speed: 1.0,
    total_events: 0,
    dispatched_events_count: 0,
    progress_percent: 0,
    latest_event: null,
  });

  useEffect(() => {
    fetchHealth();
    fetchInvestigations();
    fetchScenarios();

    const interval = setInterval(() => {
      fetchReplayStatus();
    }, 1000);
    return () => clearInterval(interval);
  }, []);

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
      // ignore offline polling errors
    }
  };

  const handleLoadScenario = async () => {
    try {
      await axios.post(`${API_BASE}/api/dataset/prepare/${selectedScenarioId}`);
      const res = await axios.post(`${API_BASE}/api/dataset/replay/load/${selectedScenarioId}`, null, {
        params: { speed: replaySpeed },
      });
      setReplayStatus(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleStartReplay = async () => {
    try {
      const res = await axios.post(`${API_BASE}/api/dataset/replay/start`);
      setReplayStatus(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handlePauseReplay = async () => {
    try {
      const res = await axios.post(`${API_BASE}/api/dataset/replay/pause`);
      setReplayStatus(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleResetReplay = async () => {
    try {
      const res = await axios.post(`${API_BASE}/api/dataset/replay/reset`);
      setReplayStatus(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const createInvestigation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle) return;
    try {
      await axios.post(`${API_BASE}/api/investigations`, {
        title: newTitle,
        initial_goal: 'Investigate initial telemetry anomaly',
      });
      setNewTitle('');
      fetchInvestigations();
    } catch (e) {
      console.error(e);
    }
  };

  const runPlannerDryRun = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/planner/dry-run-selection`, null, {
        params: {
          untriaged_events: 3,
          total_events: 5,
          evidence_count: 2,
          graph_density: 0.2,
          hypotheses_confidences: '0.3,0.5',
        },
      });
      setSelectedWorkerResult(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const currentScenarioDetails = scenarios.find((s) => s.scenario_id === selectedScenarioId);

  return (
    <div className="min-h-screen bg-[#0B0F19] text-gray-100 flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-800 bg-[#111827]/80 backdrop-blur px-6 py-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-600/20 border border-blue-500/40 rounded-lg text-blue-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-wide text-white flex items-center gap-2">
              PROJECT SENTINEL
              <span className="text-xs bg-blue-950 text-blue-400 border border-blue-800 px-2 py-0.5 rounded font-mono">
                SOC v1.0
              </span>
            </h1>
            <p className="text-xs text-gray-400">Agentic AI-Powered Threat Hunting Platform</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs bg-gray-900 border border-gray-800 px-3 py-1.5 rounded-full">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'
              }`}
            />
            <span className="text-gray-300 font-mono">
              Backend: {health ? health.status : 'Connecting...'}
            </span>
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Dataset Replayer & Active Investigations */}
        <section className="lg:col-span-2 space-y-6">
          {/* 5-Scenario Live Replay Suite */}
          <div className="bg-[#111827] border border-gray-800 p-5 rounded-xl space-y-4">
            <div className="flex items-center justify-between border-b border-gray-800 pb-3">
              <div className="flex items-center space-x-2 text-blue-400">
                <Radio className="w-5 h-5 text-emerald-400 animate-pulse" />
                <h2 className="font-semibold text-sm text-gray-200 tracking-wide uppercase">
                  CSE-CIC-IDS2018 Telemetry Replay Engine (PRD FR-102)
                </h2>
              </div>
              <span className="text-xs font-mono bg-gray-900 border border-gray-800 px-2.5 py-1 rounded text-gray-400">
                State: <strong className="text-emerald-400">{replayStatus.state}</strong>
              </span>
            </div>

            {/* Scenario Picker */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  Select Attack Scenario
                </label>
                <select
                  value={selectedScenarioId}
                  onChange={(e) => setSelectedScenarioId(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 text-sm rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                >
                  {scenarios.map((s) => (
                    <option key={s.scenario_id} value={s.scenario_id}>
                      {s.name} ({s.day})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                  Replay Speed
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {[1, 5, 10, 50].map((spd) => (
                    <button
                      key={spd}
                      type="button"
                      onClick={() => setReplaySpeed(spd)}
                      className={`text-xs font-mono py-2 rounded-lg border transition ${
                        replaySpeed === spd
                          ? 'bg-blue-600 text-white border-blue-500 font-bold'
                          : 'bg-gray-900 text-gray-300 border-gray-700 hover:bg-gray-800'
                      }`}
                    >
                      {spd === 50 ? 'Max' : `${spd}x`}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Scenario Details Preview */}
            {currentScenarioDetails && (
              <div className="bg-gray-900/70 border border-gray-800 p-3 rounded-lg text-xs space-y-2">
                <p className="text-gray-300">{currentScenarioDetails.description}</p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {currentScenarioDetails.mitre_techniques.map((tech) => (
                    <span
                      key={tech}
                      className="bg-blue-950 text-blue-400 border border-blue-800 px-2 py-0.5 rounded font-mono text-[10px]"
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Replay Controls & Live Progress */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleLoadScenario}
                  className="bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-semibold px-4 py-2 rounded-lg border border-gray-700 transition"
                >
                  Load Scenario
                </button>
                <button
                  onClick={handleStartReplay}
                  disabled={replayStatus.state === 'PLAYING'}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center space-x-1.5 transition disabled:opacity-50"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Start Stream</span>
                </button>
                <button
                  onClick={handlePauseReplay}
                  disabled={replayStatus.state !== 'PLAYING'}
                  className="bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center space-x-1.5 transition disabled:opacity-50"
                >
                  <Pause className="w-3.5 h-3.5" />
                  <span>Pause</span>
                </button>
                <button
                  onClick={handleResetReplay}
                  className="bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-semibold px-3 py-2 rounded-lg border border-gray-700 transition"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="text-xs font-mono text-gray-400">
                Dispatched:{' '}
                <strong className="text-white">
                  {replayStatus.dispatched_events_count} / {replayStatus.total_events}
                </strong>{' '}
                ({replayStatus.progress_percent}%)
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-900 rounded-full h-2 overflow-hidden border border-gray-800">
              <div
                className="bg-blue-500 h-2 transition-all duration-300"
                style={{ width: `${replayStatus.progress_percent}%` }}
              />
            </div>
          </div>

          {/* Quick Metrics */}
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#111827] border border-gray-800 p-4 rounded-xl">
              <div className="flex items-center justify-between text-gray-400 text-xs font-semibold uppercase">
                <span>Active Cases</span>
                <Activity className="w-4 h-4 text-blue-400" />
              </div>
              <p className="text-2xl font-bold text-white mt-2">{investigations.length}</p>
            </div>
            <div className="bg-[#111827] border border-gray-800 p-4 rounded-xl">
              <div className="flex items-center justify-between text-gray-400 text-xs font-semibold uppercase">
                <span>Avg Confidence</span>
                <Cpu className="w-4 h-4 text-emerald-400" />
              </div>
              <p className="text-2xl font-bold text-white mt-2">
                {investigations.length > 0
                  ? `${Math.round(
                      (investigations.reduce((acc, i) => acc + Number(i.current_confidence), 0) /
                        investigations.length) *
                        100
                    )}%`
                  : 'N/A'}
              </p>
            </div>
            <div className="bg-[#111827] border border-gray-800 p-4 rounded-xl">
              <div className="flex items-center justify-between text-gray-400 text-xs font-semibold uppercase">
                <span>Dataset Scenarios</span>
                <Layers className="w-4 h-4 text-purple-400" />
              </div>
              <p className="text-2xl font-bold text-white mt-2">5 Loaded</p>
            </div>
          </div>

          {/* Trigger New Investigation */}
          <div className="bg-[#111827] border border-gray-800 p-4 rounded-xl">
            <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">
              Trigger New Autonomous Investigation
            </h2>
            <form onSubmit={createInvestigation} className="flex gap-2">
              <input
                type="text"
                placeholder="Investigation Title (e.g., Infiltration via Macro Payload)..."
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="flex-1 bg-gray-900 border border-gray-700 text-sm rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500"
              />
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm px-5 py-2 rounded-lg transition"
              >
                Launch
              </button>
            </form>
          </div>

          {/* Investigation List */}
          <div className="bg-[#111827] border border-gray-800 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-800 flex justify-between items-center">
              <h3 className="font-semibold text-gray-200 text-sm">Investigations Queue</h3>
              <button
                onClick={fetchInvestigations}
                className="text-xs text-blue-400 hover:underline"
              >
                Refresh
              </button>
            </div>

            <div className="divide-y divide-gray-800">
              {investigations.length === 0 ? (
                <div className="p-8 text-center text-gray-500 text-sm">
                  No active investigations found. Create one above to test the orchestrator loop.
                </div>
              ) : (
                investigations.map((inv) => (
                  <div
                    key={inv.investigation_id}
                    className="p-4 hover:bg-gray-800/50 transition flex items-center justify-between"
                  >
                    <div>
                      <h4 className="font-medium text-white text-sm">{inv.title}</h4>
                      <p className="text-xs text-gray-400 mt-1">
                        Goal: {inv.current_goal || 'None'} • Cycles: {inv.planning_cycle_count}
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`text-xs px-2.5 py-1 rounded-full font-mono font-medium ${
                          inv.confidence_state === 'high' || inv.confidence_state === 'very_high'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-amber-950 text-amber-400 border border-amber-800'
                        }`}
                      >
                        {inv.confidence_state.toUpperCase()} (
                        {Math.round(Number(inv.current_confidence) * 100)}%)
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </section>

        {/* Right Col: Planner Utility Engine & System Status */}
        <section className="space-y-6">
          {/* Planner Decision Utility Test */}
          <div className="bg-[#111827] border border-gray-800 p-5 rounded-xl">
            <div className="flex items-center space-x-2 text-blue-400 mb-3">
              <Terminal className="w-5 h-5" />
              <h3 className="font-semibold text-sm text-gray-200">Planner Utility Engine Test</h3>
            </div>
            <p className="text-xs text-gray-400 mb-4">
              Simulate the mathematical utility function (IS §3.2) that dynamically selects the optimal specialized worker.
            </p>

            <button
              onClick={runPlannerDryRun}
              disabled={loading}
              className="w-full bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-mono font-semibold py-2.5 px-4 rounded-lg border border-gray-700 flex items-center justify-center space-x-2 transition"
            >
              <Play className="w-3.5 h-3.5 text-emerald-400" />
              <span>{loading ? 'Evaluating...' : 'Evaluate Next Best Action'}</span>
            </button>

            {selectedWorkerResult && (
              <div className="mt-4 p-3 bg-gray-900 border border-gray-800 rounded-lg text-xs font-mono">
                <div className="text-gray-400">Selected Worker:</div>
                <div className="text-emerald-400 font-bold uppercase text-sm mt-0.5">
                  {selectedWorkerResult.selected_worker} Worker
                </div>
                <div className="text-gray-400 mt-2">Max Utility Score:</div>
                <div className="text-blue-400 font-bold mt-0.5">
                  {selectedWorkerResult.utility_score.toFixed(4)}
                </div>
              </div>
            )}
          </div>

          {/* ADR Records Summary */}
          <div className="bg-[#111827] border border-gray-800 p-5 rounded-xl space-y-3">
            <h3 className="font-semibold text-sm text-gray-200 flex items-center gap-2">
              <FileCode2 className="w-4 h-4 text-purple-400" />
              Architecture Decision Records
            </h3>
            <div className="space-y-2 text-xs">
              <div className="p-2.5 bg-gray-900 border border-gray-800 rounded-lg">
                <span className="font-mono text-blue-400 font-semibold">ADR-001:</span>
                <p className="text-gray-300 mt-0.5">3-Tier Polyglot Persistence (Postgres + ChromaDB + Redis)</p>
              </div>
              <div className="p-2.5 bg-gray-900 border border-gray-800 rounded-lg">
                <span className="font-mono text-purple-400 font-semibold">ADR-002:</span>
                <p className="text-gray-300 mt-0.5">CSE-CIC-IDS2018 5-Scenario Suite Benchmark Telemetry</p>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
