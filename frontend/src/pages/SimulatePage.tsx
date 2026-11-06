import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Play, CheckCircle2, Sliders } from 'lucide-react';
import { datasetClient } from '../api/datasetClient';
import { workspaceClient } from '../api/workspaceClient';
import { ScenarioMetadata } from '../types/dataset';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { LoadingState, ErrorState } from '../components/ui/States';

export const SimulatePage: React.FC = () => {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<ScenarioMetadata[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('botnet_c2');
  const [executionMode, setExecutionMode] = useState<'instant' | 'streaming'>('instant');
  const [maxSteps, setMaxSteps] = useState<number>(6);
  const [replaySpeed, setReplaySpeed] = useState<number>(1.0);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLaunching, setIsLaunching] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchScenarios = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await datasetClient.getScenarios();
      setScenarios(data);
      if (data.length > 0 && !data.some((s) => s.scenario_id === selectedScenarioId)) {
        setSelectedScenarioId(data[0].scenario_id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend dataset service');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchScenarios();
  }, []);

  const selectedScenario = scenarios.find((s) => s.scenario_id === selectedScenarioId);

  const handleLaunchInvestigation = async () => {
    if (!selectedScenario) return;
    setIsLaunching(true);
    setError(null);

    try {
      // 1. Create a new formal Investigation record
      const title = `Autonomous Hunt: ${selectedScenario.name}`;
      const invRes = await workspaceClient.createInvestigation(
        title,
        `Neutralize and investigate ${selectedScenario.name} (${selectedScenario.scenario_id})`
      );
      const newInvId = invRes.investigation_id;

      if (executionMode === 'instant') {
        // Run autonomous loop up to maxSteps
        await workspaceClient.runAutonomous(newInvId, maxSteps);
      } else {
        // Prepare scenario file and load into streaming replayer
        await datasetClient.prepareScenario(selectedScenario.scenario_id);
        await datasetClient.loadReplay(selectedScenario.scenario_id, replaySpeed, 50);
        await datasetClient.startReplay();
      }

      // 2. Navigate directly to the live investigation workspace
      navigate(`/investigate/${newInvId}`);
    } catch (err: any) {
      setError(err.message || 'Failed to launch investigation');
      setIsLaunching(false);
    }
  };

  if (isLoading) {
    return <LoadingState message="Loading verified CSE-CIC-IDS2018 benchmark scenarios..." className="min-h-[500px]" />;
  }

  if (error && scenarios.length === 0) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <ErrorState
          title="Backend Unreachable"
          message={error}
          onRetry={fetchScenarios}
        />
      </div>
    );
  }

  return (
    <div className="flex-1 p-6 max-w-6xl mx-auto w-full space-y-6">
      {/* Page Header */}
      <div className="border-b border-zinc-800 pb-4">
        <div className="flex items-center gap-2 text-xs font-mono text-blue-400 uppercase tracking-wider mb-1">
          <Zap className="w-4 h-4 text-blue-500" />
          <span>Threat Simulation & Scenario Injection</span>
        </div>
        <h1 className="text-xl font-bold text-zinc-100 tracking-tight">
          Select Benchmark Threat Scenario
        </h1>
        <p className="text-xs text-zinc-400 mt-1 max-w-3xl">
          Inject empirical telemetry derived from the CSE-CIC-IDS2018 cybersecurity benchmark.
          Sentinel's autonomous Planner will continuously evaluate state, select capabilities, and formulate grounded containment recommendations.
        </p>
      </div>

      {error && (
        <div className="bg-rose-950/40 border border-rose-800 text-rose-300 text-xs px-4 py-2.5 rounded-md flex items-center justify-between">
          <span>{error}</span>
          <Button variant="ghost" size="sm" onClick={() => setError(null)}>Dismiss</Button>
        </div>
      )}

      {/* Step 1: Scenario Selection Grid */}
      <div>
        <h2 className="text-xs font-semibold text-zinc-300 uppercase tracking-wider mb-3 flex items-center gap-2">
          <span className="w-4 h-4 rounded-full bg-zinc-800 text-zinc-300 flex items-center justify-center text-[10px] font-mono">1</span>
          <span>Verified Attack Scenarios (CSE-CIC-IDS2018)</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {scenarios.map((scen) => {
            const isSelected = scen.scenario_id === selectedScenarioId;
            return (
              <div
                key={scen.scenario_id}
                onClick={() => setSelectedScenarioId(scen.scenario_id)}
                className={`p-4 rounded-lg border text-left cursor-pointer transition-all duration-150 flex flex-col justify-between ${
                  isSelected
                    ? 'bg-blue-950/30 border-blue-500/80 shadow-md shadow-blue-950/30 ring-1 ring-blue-500/50'
                    : 'bg-zinc-900/60 border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900'
                }`}
              >
                <div>
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-sm font-semibold text-zinc-100 leading-snug">{scen.name}</h3>
                    {isSelected ? (
                      <CheckCircle2 className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                    ) : (
                      <span className="w-4 h-4 rounded-full border border-zinc-700 shrink-0 mt-0.5" />
                    )}
                  </div>
                  <p className="text-xs text-zinc-400 line-clamp-2 mb-3">{scen.description}</p>
                </div>

                <div className="space-y-2 pt-2 border-t border-zinc-800/60">
                  <div className="flex flex-wrap gap-1">
                    {scen.mitre_techniques.slice(0, 2).map((t) => (
                      <span key={t} className="text-[10px] font-mono bg-zinc-800/80 text-zinc-300 px-1.5 py-0.2 rounded border border-zinc-700/60">
                        {t}
                      </span>
                    ))}
                    {scen.mitre_techniques.length > 2 && (
                      <span className="text-[10px] font-mono text-zinc-500">+{scen.mitre_techniques.length - 2}</span>
                    )}
                  </div>
                  <div className="text-[10px] font-mono text-zinc-500 flex items-center justify-between">
                    <span>{scen.dataset_source}</span>
                    <span>{scen.day}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step 2: Selected Scenario Deep Detail & Execution Configuration */}
      {selectedScenario && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
          {/* Left: Detailed Scenario Narrative */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader
                title={`Target Scenario: ${selectedScenario.name}`}
                description="Verified benchmark metadata, gold hypothesis, and MITRE mapping"
              />
              <div className="space-y-3 text-xs">
                <div>
                  <span className="text-zinc-500 uppercase font-mono text-[10px]">Gold Hypothesis:</span>
                  <p className="text-zinc-200 mt-0.5 bg-zinc-950/60 p-2.5 rounded border border-zinc-800/80 font-mono text-[11px] leading-relaxed">
                    "{selectedScenario.gold_hypothesis}"
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div>
                    <span className="text-zinc-500 uppercase font-mono text-[10px]">MITRE Tactics:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedScenario.mitre_tactics.map((tac) => (
                        <Badge key={tac} variant="info" size="sm">
                          {tac}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-zinc-500 uppercase font-mono text-[10px]">MITRE Techniques:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {selectedScenario.mitre_techniques.map((tec) => (
                        <span key={tec} className="text-[10px] font-mono bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded border border-zinc-700">
                          {tec}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Right: Execution Parameter Controls */}
          <div className="space-y-4">
            <Card>
              <CardHeader
                title="Simulation Controls"
                description="Controls grounded in actual backend capabilities"
                action={<Sliders className="w-4 h-4 text-zinc-400" />}
              />

              <div className="space-y-4 text-xs">
                {/* Mode Selector */}
                <div>
                  <label className="text-zinc-400 font-medium block mb-1.5">Execution Mode</label>
                  <div className="space-y-1.5">
                    <label className={`flex items-start gap-2 p-2 rounded border cursor-pointer transition-colors ${
                      executionMode === 'instant' ? 'bg-blue-950/40 border-blue-500/60 text-zinc-200' : 'border-zinc-800 text-zinc-400'
                    }`}>
                      <input
                        type="radio"
                        name="execMode"
                        checked={executionMode === 'instant'}
                        onChange={() => setExecutionMode('instant')}
                        className="mt-0.5"
                      />
                      <div>
                        <div className="font-semibold text-zinc-200 text-xs">Autonomous Investigation</div>
                        <div className="text-[11px] text-zinc-400">Runs autonomous Planner loop until confidence or max cycles.</div>
                      </div>
                    </label>

                    <label className={`flex items-start gap-2 p-2 rounded border cursor-pointer transition-colors ${
                      executionMode === 'streaming' ? 'bg-blue-950/40 border-blue-500/60 text-zinc-200' : 'border-zinc-800 text-zinc-400'
                    }`}>
                      <input
                        type="radio"
                        name="execMode"
                        checked={executionMode === 'streaming'}
                        onChange={() => setExecutionMode('streaming')}
                        className="mt-0.5"
                      />
                      <div>
                        <div className="font-semibold text-zinc-200 text-xs">Streaming Replayer</div>
                        <div className="text-[11px] text-zinc-400">Stream events into ingest queue via live replayer instance.</div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Sub-parameters */}
                {executionMode === 'instant' ? (
                  <div>
                    <div className="flex items-center justify-between text-zinc-400 mb-1">
                      <span>Max Planning Cycles:</span>
                      <span className="font-mono text-zinc-200">{maxSteps} cycles</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="12"
                      value={maxSteps}
                      onChange={(e) => setMaxSteps(Number(e.target.value))}
                      className="w-full accent-blue-500"
                    />
                  </div>
                ) : (
                  <div>
                    <label className="text-zinc-400 font-medium block mb-1">Replay Speed Multiplier</label>
                    <div className="grid grid-cols-4 gap-1.5">
                      {[1.0, 2.0, 5.0, 10.0].map((s) => (
                        <button
                          key={s}
                          type="button"
                          onClick={() => setReplaySpeed(s)}
                          className={`py-1 text-xs font-mono rounded border text-center ${
                            replaySpeed === s
                              ? 'bg-blue-600 text-white border-blue-500'
                              : 'bg-zinc-800 text-zinc-300 border-zinc-700 hover:bg-zinc-750'
                          }`}
                        >
                          {s}x
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Launch Action Button */}
                <div className="pt-2">
                  <Button
                    variant="primary"
                    size="lg"
                    className="w-full justify-center"
                    icon={<Play className="w-4 h-4 fill-current" />}
                    isLoading={isLaunching}
                    onClick={handleLaunchInvestigation}
                  >
                    Launch Investigation
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
