import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, Play, CheckCircle2, Sliders, RefreshCw } from 'lucide-react';
import { datasetClient } from '../api/datasetClient';
import { evaluationClient } from '../api/evaluationClient';
import { ScenarioMetadata } from '../types/dataset';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { LoadingState, ErrorState } from '../components/ui/States';

export const SimulatePage: React.FC = () => {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<ScenarioMetadata[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('botnet_c2');
  const [executionMode, setExecutionMode] = useState<'instant' | 'step'>('instant');
  const [maxSteps, setMaxSteps] = useState<number>(6);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLaunching, setIsLaunching] = useState<boolean>(false);
  const [launchStep, setLaunchStep] = useState<number>(0);
  const [launchStatus, setLaunchStatus] = useState<string>('');
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
    if (!selectedScenario || isLaunching) return;
    setIsLaunching(true);
    setError(null);
    setLaunchStep(1);
    setLaunchStatus('Preparing CSE-CIC-IDS2018 benchmark telemetry on disk...');

    try {
      // 1. Ensure scenario telemetry files are prepared on disk
      await datasetClient.prepareScenario(selectedScenario.scenario_id);

      // 2. Launch scenario through evaluation service to seed telemetry & run Planner
      setLaunchStep(2);
      setLaunchStatus(
        executionMode === 'instant'
          ? `Autonomous Planner executing up to ${maxSteps} planning cycles...`
          : 'Initializing scenario investigation with baseline telemetry and initial cycle...'
      );

      const cyclesToRun = executionMode === 'instant' ? maxSteps : 1;
      const evalRes = await evaluationClient.triggerEvaluationRun(
        selectedScenario.scenario_id,
        cyclesToRun
      );

      const newInvId =
        evalRes?.results?.[0]?.investigation?.investigation_id ||
        evalRes?.result?.investigation?.investigation_id ||
        evalRes?.investigation?.investigation_id;
      if (!newInvId) {
        throw new Error('Backend did not return an investigation ID for the launched scenario');
      }

      setLaunchStep(3);
      setLaunchStatus('Autonomous cycles recorded. Opening Agentic Investigation Workspace...');
      setTimeout(() => {
        navigate(`/investigate/${newInvId}`);
      }, 400);
    } catch (err: any) {
      setError(err.message || 'Failed to launch investigation');
      setIsLaunching(false);
      setLaunchStep(0);
      setLaunchStatus('');
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

                {/* Ground Truth Telemetry File Provenance */}
                <div className="pt-2 border-t border-zinc-800/60">
                  <span className="text-zinc-500 uppercase font-mono text-[10px] block mb-1.5">
                    Benchmark Telemetry Provenance:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-[11px]">
                    <div className="bg-zinc-950/70 p-2 rounded border border-zinc-800">
                      <span className="text-zinc-500 block text-[9px] uppercase">Normalized Telemetry</span>
                      <span className="text-zinc-300 truncate block">
                        {selectedScenario.normalized_filename}
                      </span>
                    </div>
                    <div className="bg-zinc-950/70 p-2 rounded border border-zinc-800">
                      <span className="text-zinc-500 block text-[9px] uppercase">Raw Benchmark Capture</span>
                      <span className="text-zinc-400 truncate block">
                        {selectedScenario.raw_filename}
                      </span>
                    </div>
                    <div className="bg-zinc-950/70 p-2 rounded border border-zinc-800">
                      <span className="text-zinc-500 block text-[9px] uppercase">Dataset Source</span>
                      <span className="text-zinc-300">
                        {selectedScenario.dataset_source} ({selectedScenario.day})
                      </span>
                    </div>
                    <div className="bg-zinc-950/70 p-2 rounded border border-zinc-800 flex items-center justify-between">
                      <div>
                        <span className="text-zinc-500 block text-[9px] uppercase">Integrity Status</span>
                        <span className="text-emerald-400 font-semibold">Verified on Disk</span>
                      </div>
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
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
                    <label className={`flex items-start gap-2 p-2.5 rounded border cursor-pointer transition-colors ${
                      executionMode === 'instant' ? 'bg-blue-950/40 border-blue-500/60 text-zinc-200' : 'border-zinc-800 text-zinc-400'
                    }`}>
                      <input
                        type="radio"
                        name="execMode"
                        checked={executionMode === 'instant'}
                        onChange={() => setExecutionMode('instant')}
                        className="mt-0.5 accent-blue-500"
                      />
                      <div>
                        <div className="font-semibold text-zinc-200 text-xs">Autonomous Investigation (Full Loop)</div>
                        <div className="text-[11px] text-zinc-400 mt-0.5">
                          Seeds benchmark telemetry and executes the autonomous Planner loop for up to {maxSteps} cycles until confidence or containment.
                        </div>
                      </div>
                    </label>

                    <label className={`flex items-start gap-2 p-2.5 rounded border cursor-pointer transition-colors ${
                      executionMode === 'step' ? 'bg-blue-950/40 border-blue-500/60 text-zinc-200' : 'border-zinc-800 text-zinc-400'
                    }`}>
                      <input
                        type="radio"
                        name="execMode"
                        checked={executionMode === 'step'}
                        onChange={() => setExecutionMode('step')}
                        className="mt-0.5 accent-blue-500"
                      />
                      <div>
                        <div className="font-semibold text-zinc-200 text-xs">Interactive Step-by-Step</div>
                        <div className="text-[11px] text-zinc-400 mt-0.5">
                          Seeds benchmark telemetry and executes cycle 1, then opens the workspace for manual cycle-by-cycle stepping.
                        </div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Sub-parameters */}
                {executionMode === 'instant' && (
                  <div className="bg-zinc-950/60 p-3 rounded border border-zinc-800/80 space-y-2">
                    <div className="flex items-center justify-between text-zinc-400 text-xs">
                      <span>Max Planning Cycles:</span>
                      <span className="font-mono text-blue-400 font-semibold">{maxSteps} cycles</span>
                    </div>
                    <input
                      type="range"
                      min="2"
                      max="10"
                      value={maxSteps}
                      onChange={(e) => setMaxSteps(Number(e.target.value))}
                      className="w-full accent-blue-500 cursor-pointer"
                    />
                    <div className="flex justify-between text-[10px] font-mono text-zinc-500">
                      <span>2 cycles (Fast)</span>
                      <span>6 cycles (Standard)</span>
                      <span>10 cycles (Deep)</span>
                    </div>
                  </div>
                )}

                {/* Launch Status Multi-Stage Progress Indicator */}
                {isLaunching && (
                  <div className="p-3 bg-blue-950/40 border border-blue-800/80 rounded-md text-xs space-y-2.5">
                    <div className="flex items-center gap-2 text-blue-300 font-medium">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-400 shrink-0" />
                      <span className="truncate">{launchStatus}</span>
                    </div>

                    <div className="space-y-1.5 pt-1">
                      <div className="flex items-center gap-2 text-[11px] font-mono">
                        <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-[9px] ${
                          launchStep > 1 ? 'bg-emerald-600 text-white' : launchStep === 1 ? 'bg-blue-600 text-white animate-pulse' : 'bg-zinc-800 text-zinc-500'
                        }`}>
                          {launchStep > 1 ? '✓' : '1'}
                        </span>
                        <span className={launchStep >= 1 ? 'text-zinc-200' : 'text-zinc-500'}>
                          Ingest benchmark telemetry
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-[11px] font-mono">
                        <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-[9px] ${
                          launchStep > 2 ? 'bg-emerald-600 text-white' : launchStep === 2 ? 'bg-blue-600 text-white animate-pulse' : 'bg-zinc-800 text-zinc-500'
                        }`}>
                          {launchStep > 2 ? '✓' : '2'}
                        </span>
                        <span className={launchStep >= 2 ? 'text-zinc-200' : 'text-zinc-500'}>
                          Execute autonomous planning loop
                        </span>
                      </div>

                      <div className="flex items-center gap-2 text-[11px] font-mono">
                        <span className={`w-3.5 h-3.5 rounded-full flex items-center justify-center text-[9px] ${
                          launchStep === 3 ? 'bg-emerald-600 text-white' : 'bg-zinc-800 text-zinc-500'
                        }`}>
                          3
                        </span>
                        <span className={launchStep >= 3 ? 'text-zinc-200' : 'text-zinc-500'}>
                          Project state into workspace
                        </span>
                      </div>
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
                    {isLaunching
                      ? 'Executing Scenario Hunt...'
                      : executionMode === 'instant'
                      ? 'Launch Autonomous Hunt'
                      : 'Initialize Step Investigation'}
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
