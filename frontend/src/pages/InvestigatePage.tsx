import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ShieldAlert,
  RotateCw,
  Play,
  RefreshCw,
  RotateCcw,
} from 'lucide-react';
import { workspaceClient } from '../api/workspaceClient';
import { reviewClient } from '../api/reviewClient';
import {
  InvestigationWorkspaceProjection,
  KeyFinding,
  OrchestrationStep,
  PlannerDecisionRecord,
  ThreatSummary,
  PlannerWorkspaceState,
} from '../types/workspace';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge, BadgeVariant } from '../components/ui/Badge';
import { Tabs } from '../components/ui/Tabs';
import { Modal } from '../components/ui/Modal';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/States';
import { StorylineView } from '../components/investigation/StorylineView';
import { AgentActivityView } from '../components/investigation/AgentActivityView';
import { EvidenceLedgerView } from '../components/investigation/EvidenceLedgerView';
import { GroundedActionCard } from '../components/investigation/GroundedActionCard';
import { ForensicDrawer } from '../components/investigation/ForensicDrawer';
import { ReplayController } from '../components/investigation/ReplayController';

export const InvestigatePage: React.FC = () => {
  const { id: routeInvestigationId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Mode from URL query parameter (?mode=replay&cycle=N)
  const isReplayMode = searchParams.get('mode') === 'replay';
  const paramCycle = searchParams.get('cycle');

  // Workspace Data State
  const [workspace, setWorkspace] = useState<InvestigationWorkspaceProjection | null>(null);
  const [decisions, setDecisions] = useState<PlannerDecisionRecord[]>([]);
  const [activeTab, setActiveTab] = useState<string>('storyline');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Review & Execution Action State
  const [isExecutingStep, setIsExecutingStep] = useState<boolean>(false);
  const [isRunningAutonomous, setIsRunningAutonomous] = useState<boolean>(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [reviewModalOpen, setReviewModalOpen] = useState<boolean>(false);
  const [selectedReviewDecision, setSelectedReviewDecision] = useState<'approved' | 'rejected'>('approved');
  const [analystComment, setAnalystComment] = useState<string>('');

  // Level-2 Drawer State
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [selectedFinding, setSelectedFinding] = useState<KeyFinding | null>(null);
  const [selectedStep, setSelectedStep] = useState<OrchestrationStep | null>(null);

  // Replay State
  const [replayCycle, setReplayCycle] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [replaySpeed, setReplaySpeed] = useState<number>(1500);

  const fetchWorkspace = useCallback(async (investigationId: string, silent: boolean = false) => {
    if (!silent) setIsLoading(true);
    setError(null);
    try {
      const [projData, decData] = await Promise.all([
        workspaceClient.getWorkspace(investigationId),
        workspaceClient.getDecisions(investigationId).catch(() => [] as PlannerDecisionRecord[]),
      ]);
      setWorkspace(projData);
      setDecisions(decData || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load investigation workspace');
    } finally {
      if (!silent) setIsLoading(false);
    }
  }, []);

  // If no ID is provided in route, pick the most recent investigation
  useEffect(() => {
    if (routeInvestigationId) {
      fetchWorkspace(routeInvestigationId);
    } else {
      workspaceClient
        .listInvestigations(1)
        .then((list) => {
          if (list.length > 0) {
            navigate(`/investigate/${list[0].investigation_id}`, { replace: true });
          } else {
            setIsLoading(false);
          }
        })
        .catch((e) => {
          setError(e.message || 'Failed to list investigations');
          setIsLoading(false);
        });
    }
  }, [routeInvestigationId, fetchWorkspace, navigate]);

  // Sync replay cycle state when replay mode or cycle param changes
  useEffect(() => {
    if (isReplayMode && workspace) {
      const total = workspace.orchestration_history.length;
      if (paramCycle !== null && paramCycle !== undefined) {
        const parsed = parseInt(paramCycle, 10);
        if (!isNaN(parsed) && parsed >= 0 && parsed <= total) {
          setReplayCycle(parsed);
          return;
        }
      }
      // If cycle is uninitialized or 0, default to 1 if steps exist, else 0
      setReplayCycle((prev) => (prev > 0 && prev <= total ? prev : total > 0 ? 1 : 0));
    }
  }, [isReplayMode, workspace, paramCycle]);

  // Replay playback timer loop
  useEffect(() => {
    let timer: any = null;
    if (isReplayMode && isPlaying && workspace) {
      const total = workspace.orchestration_history.length;
      timer = setInterval(() => {
        setReplayCycle((prev) => {
          if (prev >= total) {
            setIsPlaying(false);
            return prev;
          }
          const next = prev + 1;
          setSearchParams({ mode: 'replay', cycle: String(next) });
          return next;
        });
      }, replaySpeed);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [isReplayMode, isPlaying, workspace, replaySpeed, setSearchParams]);

  // Live polling for active investigations (strictly disabled in replay mode)
  useEffect(() => {
    let pollInterval: any = null;
    if (!isReplayMode && routeInvestigationId && workspace?.threat.status === 'investigating') {
      pollInterval = setInterval(() => {
        fetchWorkspace(routeInvestigationId, true);
      }, 3500);
    }
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [isReplayMode, routeInvestigationId, workspace?.threat.status, fetchWorkspace]);

  // Replay Controller Handlers
  const handleSelectCycle = (cycle: number) => {
    setReplayCycle(cycle);
    setIsPlaying(false);
    setSearchParams({ mode: 'replay', cycle: String(cycle) });
  };

  const handlePreviousCycle = () => {
    if (replayCycle > 0) {
      handleSelectCycle(replayCycle - 1);
    }
  };

  const handleNextCycle = () => {
    const total = workspace?.orchestration_history.length || 0;
    if (replayCycle < total) {
      handleSelectCycle(replayCycle + 1);
    }
  };

  const handleTogglePlay = () => {
    const total = workspace?.orchestration_history.length || 0;
    if (replayCycle >= total && !isPlaying) {
      // Loop back to cycle 0 on replay restart
      setReplayCycle(0);
      setSearchParams({ mode: 'replay', cycle: '0' });
    }
    setIsPlaying(!isPlaying);
  };

  const handleExitReplay = () => {
    setIsPlaying(false);
    setSearchParams({});
  };

  const handleEnterReplay = () => {
    const total = workspace?.orchestration_history.length || 0;
    setSearchParams({ mode: 'replay', cycle: String(total > 0 ? 1 : 0) });
  };

  // Live execution handlers (Disabled in Replay Mode)
  const handleExecuteNextStep = async () => {
    if (isReplayMode || !workspace?.threat.investigation_id || isExecutingStep || isRunningAutonomous) return;
    setIsExecutingStep(true);
    try {
      await workspaceClient.executeStep(workspace.threat.investigation_id);
      await fetchWorkspace(workspace.threat.investigation_id, true);
    } catch (err: any) {
      setError(err.message || 'Step execution failed');
    } finally {
      setIsExecutingStep(false);
    }
  };

  const handleRunAutonomous = async () => {
    if (isReplayMode || !workspace?.threat.investigation_id || isRunningAutonomous || isExecutingStep) return;
    setIsRunningAutonomous(true);
    try {
      await workspaceClient.runAutonomous(workspace.threat.investigation_id, 6);
      await fetchWorkspace(workspace.threat.investigation_id, true);
    } catch (err: any) {
      setError(err.message || 'Autonomous execution failed');
    } finally {
      setIsRunningAutonomous(false);
    }
  };

  const handleSubmitReviewDecision = async () => {
    if (isReplayMode || !workspace?.human_review?.review_id) return;
    setIsSubmittingReview(true);
    try {
      await reviewClient.submitDecision(workspace.human_review.review_id, {
        decision: selectedReviewDecision,
        analyst_id: 'SOC-ANALYST-104',
        analyst_comments: analystComment || 'Authorized via Sentinel Agentic Workspace',
      });
      setReviewModalOpen(false);
      await fetchWorkspace(workspace.threat.investigation_id, true);
    } catch (err: any) {
      setError(err.message || 'Failed to submit review decision');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  // Drawer handlers
  const handleSelectFinding = (finding: KeyFinding) => {
    setSelectedFinding(finding);
    setSelectedStep(null);
    setDrawerOpen(true);
  };

  const handleInspectStep = (step: OrchestrationStep) => {
    setSelectedStep(step);
    setSelectedFinding(null);
    setDrawerOpen(true);
  };

  const handleSelectCitation = (findingId: string) => {
    const f = workspace?.key_findings.find((k) => k.finding_id === findingId);
    if (f) {
      setSelectedFinding(f);
      setSelectedStep(null);
      setDrawerOpen(true);
    } else {
      setActiveTab('evidence');
    }
  };

  // =========================================================================
  // HISTORICAL RECONSTRUCTION: Deterministic projection slice at Cycle K
  // =========================================================================
  const displayedWorkspace = useMemo(() => {
    if (!workspace) return null;
    if (!isReplayMode) return workspace;

    const totalSteps = workspace.orchestration_history.length;
    const K = Math.min(replayCycle, totalSteps);

    // 1. Sliced historical steps up to cycle K
    const historicalSteps = workspace.orchestration_history.slice(0, K);

    // 2. Sliced confidence at cycle K
    let historicalConfidence = workspace.threat.confidence;
    if (K === 0) {
      historicalConfidence = workspace.orchestration_history[0]?.confidence_before ?? 0.15;
    } else if (K > 0 && historicalSteps.length >= K) {
      historicalConfidence = historicalSteps[K - 1]?.confidence_after ?? workspace.threat.confidence;
    }

    // 3. Historical Threat Summary
    const historicalThreat: ThreatSummary = {
      ...workspace.threat,
      current_cycle: K,
      confidence: historicalConfidence,
      status: K < totalSteps ? 'investigating' : workspace.threat.status,
    };

    // 4. Decision mapping for findings discovered up to cycle K
    const activeDecisions = decisions.filter((d) => d.cycle_number <= K);
    const activeDecisionIds = new Set(activeDecisions.map((d) => d.decision_id));

    // Findings available at or before cycle K
    const historicalFindings = workspace.key_findings.filter((f) => {
      if (!f.provenance.planner_decision_id) return true; // Initial baseline telemetry
      return activeDecisionIds.has(f.provenance.planner_decision_id);
    });

    // 5. Planner state at cycle K
    const activeStep = K > 0 ? historicalSteps[K - 1] : null;
    const historicalPlanner: PlannerWorkspaceState = {
      ...workspace.planner,
      current_observation:
        activeStep?.observation ||
        'Initial benchmark baseline established. Autonomous Planner ready to evaluate evidence.',
      decision_rationale: activeStep?.rationale || null,
      is_replanning: activeStep ? Boolean(activeStep.is_replanning) : false,
      active_capability: activeStep
        ? {
            name: activeStep.selected_capability || `${activeStep.selected_worker}.execute`,
            worker_type: activeStep.selected_worker || 'system',
            status: 'completed',
          }
        : null,
    };

    // 6. Recommendation: Only exposed if response worker executed at or before cycle K
    const responseStepIndex = historicalSteps.findIndex((s) => s.selected_worker === 'response');
    const hasReachedResponse = responseStepIndex !== -1;
    const historicalRecommendation = hasReachedResponse ? workspace.recommendation : null;
    const historicalHumanReview = hasReachedResponse ? workspace.human_review : null;

    return {
      ...workspace,
      threat: historicalThreat,
      planner: historicalPlanner,
      orchestration_history: historicalSteps,
      key_findings: historicalFindings,
      recommendation: historicalRecommendation,
      human_review: historicalHumanReview,
    };
  }, [workspace, isReplayMode, replayCycle, decisions]);

  // Set of finding IDs discovered in cycle K specifically (for "New at this cycle" highlight)
  const newFindingIdsAtCycle = useMemo(() => {
    if (!workspace || !isReplayMode) return undefined;
    const totalSteps = workspace.orchestration_history.length;
    const K = Math.min(replayCycle, totalSteps);

    if (K === 0) {
      return new Set(
        workspace.key_findings
          .filter((f) => !f.provenance.planner_decision_id)
          .map((f) => f.finding_id)
      );
    }

    const cycleKDecision = decisions.find((d) => d.cycle_number === K);
    if (!cycleKDecision) return undefined;

    const newFindings = workspace.key_findings.filter(
      (f) => f.provenance.planner_decision_id === cycleKDecision.decision_id
    );
    return new Set(newFindings.map((f) => f.finding_id));
  }, [workspace, isReplayMode, replayCycle, decisions]);

  if (isLoading) {
    return <LoadingState message="Loading unified investigation workspace projection..." className="min-h-[500px]" />;
  }

  if (error && !workspace) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <ErrorState
          title="Investigation Unavailable"
          message={error}
          onRetry={() => routeInvestigationId && fetchWorkspace(routeInvestigationId)}
        />
      </div>
    );
  }

  if (!displayedWorkspace) {
    return (
      <div className="p-8 max-w-xl mx-auto">
        <EmptyState
          title="No Active Investigations Found"
          description="Simulate or inject a benchmark threat scenario to initiate an autonomous investigation."
          action={
            <Button variant="primary" onClick={() => navigate('/simulate')}>
              Go to Threat Simulation
            </Button>
          }
        />
      </div>
    );
  }

  const { threat, planner, key_findings, orchestration_history, recommendation, human_review } = displayedWorkspace;

  const severityBadgeVariant: BadgeVariant =
    threat.severity === 'critical' ? 'critical' : threat.severity === 'high' ? 'high' : 'medium';

  const matchedDecision = selectedStep
    ? decisions.find((d) => d.cycle_number === selectedStep.cycle)
    : null;

  return (
    <div className="flex-1 flex flex-col w-full bg-zinc-950 overflow-hidden">
      {/* ========================================================================= */}
      {/* 0. IN-CONTEXT REPLAY CONTROLLER (ACTIVE IN REPLAY MODE)                   */}
      {/* ========================================================================= */}
      {isReplayMode && (
        <ReplayController
          currentCycle={replayCycle}
          totalCycles={workspace?.orchestration_history.length || 0}
          steps={workspace?.orchestration_history || []}
          isPlaying={isPlaying}
          replaySpeed={replaySpeed}
          onPrevious={handlePreviousCycle}
          onNext={handleNextCycle}
          onTogglePlay={handleTogglePlay}
          onSelectCycle={handleSelectCycle}
          onChangeSpeed={setReplaySpeed}
          onExitReplay={handleExitReplay}
        />
      )}

      {/* ========================================================================= */}
      {/* 1. LEVEL 0 COMMAND ANCHOR (STICKY TOP BAR)                                */}
      {/* ========================================================================= */}
      <section
        className={`bg-zinc-950 border-b p-4 shrink-0 shadow-md z-20 ${
          isReplayMode ? 'border-amber-600/30 bg-amber-950/10' : 'border-zinc-800'
        }`}
      >
        <div className="max-w-6xl mx-auto space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Threat Title & Target Profile */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-md bg-rose-950/80 border border-rose-800 flex items-center justify-center text-rose-400 shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-bold text-zinc-100">{threat.title}</h1>
                <Badge variant={severityBadgeVariant} size="sm">
                  {threat.severity}
                </Badge>
                {threat.status === 'investigating' ? (
                  <Badge variant="info" size="sm">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse mr-1" />
                    Investigating
                  </Badge>
                ) : threat.status === 'awaiting_review' ? (
                  <Badge variant="high" size="sm">
                    Awaiting Review
                  </Badge>
                ) : threat.status === 'completed' ? (
                  <Badge variant="success" size="sm">
                    Completed
                  </Badge>
                ) : (
                  <Badge variant="neutral" size="sm">
                    {threat.status}
                  </Badge>
                )}

                {isReplayMode && (
                  <Badge variant="high" size="sm">
                    REPLAY: C{replayCycle}
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-3 text-xs text-zinc-400 font-mono mt-0.5">
                <span>ID: {threat.investigation_id.slice(0, 8)}...</span>
                <span>·</span>
                <span>
                  Target:{' '}
                  <strong className="text-zinc-200">
                    {threat.affected_entities[0]?.label || 'WORKSTATION-04'}
                  </strong>
                </span>
                <span>·</span>
                <span>Cycle: {threat.current_cycle} / {threat.max_cycles || 10}</span>
              </div>
            </div>
          </div>

          {/* Calibrated Confidence & Single-Step / Autonomous / Replay Controls */}
          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                {isReplayMode ? 'Historical Confidence' : 'Calibrated Confidence'}
              </div>
              <div className="flex items-center gap-2 justify-end">
                <div className="w-24 bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      isReplayMode ? 'bg-amber-400' : 'bg-blue-500'
                    }`}
                    style={{ width: `${Math.round(threat.confidence * 100)}%` }}
                  />
                </div>
                <span className="font-mono text-sm font-bold text-zinc-100">
                  {Math.round(threat.confidence * 100)}%
                </span>
              </div>
            </div>

            {/* Mode Actions: Live Execution vs Replay Trigger */}
            {!isReplayMode ? (
              <>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<RotateCcw className="w-3.5 h-3.5" />}
                  onClick={handleEnterReplay}
                  title="Replay chronological evolution of this investigation"
                >
                  Replay
                </Button>

                <Button
                  variant="secondary"
                  size="sm"
                  icon={<RotateCw className="w-3.5 h-3.5" />}
                  isLoading={isExecutingStep}
                  disabled={isRunningAutonomous || threat.status === 'completed' || threat.status === 'closed'}
                  onClick={handleExecuteNextStep}
                  title="Execute single autonomous planner cycle"
                >
                  Step Planner
                </Button>

                <Button
                  variant="primary"
                  size="sm"
                  icon={<Play className="w-3.5 h-3.5 fill-current" />}
                  isLoading={isRunningAutonomous}
                  disabled={isExecutingStep || threat.status === 'completed' || threat.status === 'closed'}
                  onClick={handleRunAutonomous}
                  title="Execute continuous autonomous loop until completion or containment"
                >
                  Run Autonomous
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  icon={<RefreshCw className="w-3.5 h-3.5" />}
                  onClick={() => fetchWorkspace(threat.investigation_id, true)}
                  title="Refresh workspace projection"
                />
              </>
            ) : (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleExitReplay}
                title="Return to live investigation mode"
              >
                Live Mode
              </Button>
            )}
          </div>
        </div>

        {/* Level 0 Grounded Action Card (Rendered if recommendation exists at this historical point) */}
        {recommendation && (
          <GroundedActionCard
            recommendation={recommendation}
            humanReview={human_review}
            onApprove={() => {
              if (isReplayMode) return;
              setSelectedReviewDecision('approved');
              setReviewModalOpen(true);
            }}
            onReject={() => {
              if (isReplayMode) return;
              setSelectedReviewDecision('rejected');
              setReviewModalOpen(true);
            }}
            onSelectCitation={handleSelectCitation}
            isReadOnly={isReplayMode}
          />
        )}
        </div>
      </section>

      {/* ========================================================================= */}
      {/* 2. SUB-VIEW TABS SWITCHER                                                 */}
      {/* ========================================================================= */}
      <div className="bg-zinc-950/80 border-b border-zinc-800 shrink-0">
        <div className="max-w-6xl mx-auto px-4">
          <Tabs
            tabs={[
              { id: 'storyline', label: 'Storyline', count: orchestration_history.length },
              { id: 'activity', label: 'Agent Activity', count: orchestration_history.length },
              { id: 'evidence', label: 'Evidence Ledger', count: key_findings.length },
              { id: 'details', label: 'Forensic Diagnostics' },
            ]}
            activeTab={activeTab}
            onChange={setActiveTab}
          />
        </div>
      </div>

      {/* ========================================================================= */}
      {/* 3. PRIMARY CONTENT STAGE                                                  */}
      {/* ========================================================================= */}
      <div className="flex-1 overflow-y-auto p-6 max-w-6xl mx-auto w-full">
        {/* VIEW 1: STORYLINE */}
        {activeTab === 'storyline' && (
          <StorylineView
            steps={orchestration_history}
            threat={threat}
            planner={planner}
            keyFindings={key_findings}
            onInspectStep={handleInspectStep}
            onStepPlanner={!isReplayMode ? handleExecuteNextStep : undefined}
            isExecutingStep={isExecutingStep}
            currentReplayCycle={isReplayMode ? replayCycle : undefined}
          />
        )}

        {/* VIEW 2: AGENT ACTIVITY */}
        {activeTab === 'activity' && (
          <AgentActivityView
            steps={orchestration_history}
            decisions={decisions}
            activeCapability={planner.active_capability}
            isReplanning={planner.is_replanning}
          />
        )}

        {/* VIEW 3: EVIDENCE LEDGER */}
        {activeTab === 'evidence' && (
          <EvidenceLedgerView
            findings={key_findings}
            onSelectFinding={handleSelectFinding}
            selectedFindingId={selectedFinding?.finding_id}
            newFindingIds={newFindingIdsAtCycle}
          />
        )}

        {/* VIEW 4: DIAGNOSTICS */}
        {activeTab === 'details' && (
          <div className="space-y-4">
            <Card>
              <CardHeader
                title={isReplayMode ? `Forensic Telemetry (Replay Cycle ${replayCycle})` : 'Forensic Diagnostic Metadata'}
                description="Raw system records, immutable state versioning, and cryptographic provenance"
              />
              <pre className="bg-zinc-950 p-4 rounded border border-zinc-800 text-[11px] font-mono text-zinc-400 overflow-x-auto">
                {JSON.stringify(
                  {
                    is_replay_mode: isReplayMode,
                    replay_cycle: isReplayMode ? replayCycle : null,
                    total_cycles: workspace?.orchestration_history?.length ?? 0,
                    threat_provenance: threat.data_provenance,
                    active_capability: planner.active_capability,
                    workspace_metadata: workspace?.workspace_metadata ?? {},
                    decisions_audit_count: decisions.length,
                  },
                  null,
                  2
                )}
              </pre>
            </Card>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 4. LEVEL 2 SLIDE-OVER FORENSIC DRAWER                                    */}
      {/* ========================================================================= */}
      <ForensicDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        finding={selectedFinding}
        step={selectedStep}
        decision={matchedDecision}
      />

      {/* ========================================================================= */}
      {/* 5. HUMAN REVIEW CONFIRMATION MODAL (ONLY ACCESSIBLE IN LIVE MODE)         */}
      {/* ========================================================================= */}
      <Modal
        isOpen={reviewModalOpen && !isReplayMode}
        onClose={() => setReviewModalOpen(false)}
        title="Human Authorization Sign-Off"
        footer={
          <>
            <Button variant="ghost" onClick={() => setReviewModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={selectedReviewDecision === 'approved' ? 'primary' : 'danger'}
              isLoading={isSubmittingReview}
              onClick={handleSubmitReviewDecision}
            >
              Confirm {selectedReviewDecision === 'approved' ? 'Approval' : 'Rejection'}
            </Button>
          </>
        }
      >
        <div className="space-y-3">
          <p className="text-xs text-zinc-300">
            You are about to <strong>{selectedReviewDecision.toUpperCase()}</strong> the recommended action:
          </p>
          <div className="bg-zinc-900 p-3 rounded border border-zinc-800 font-mono text-xs text-zinc-200">
            {recommendation?.action}
          </div>
          <div>
            <label className="text-zinc-400 block mb-1">Analyst Audit Comment (Optional):</label>
            <textarea
              value={analystComment}
              onChange={(e) => setAnalystComment(e.target.value)}
              placeholder="e.g. Verified outbound socket to remote C2 server. Approved."
              className="w-full bg-zinc-900 border border-zinc-800 rounded p-2 text-zinc-100 text-xs focus:outline-none focus:border-blue-500"
              rows={3}
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};
