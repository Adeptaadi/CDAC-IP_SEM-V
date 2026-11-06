import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCw,
  ChevronRight,
} from 'lucide-react';
import { workspaceClient } from '../api/workspaceClient';
import { reviewClient } from '../api/reviewClient';
import {
  InvestigationWorkspaceProjection,
  KeyFinding,
} from '../types/workspace';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge, BadgeVariant } from '../components/ui/Badge';
import { Tabs } from '../components/ui/Tabs';
import { Drawer } from '../components/ui/Drawer';
import { Modal } from '../components/ui/Modal';
import { LoadingState, ErrorState, EmptyState } from '../components/ui/States';

export const InvestigatePage: React.FC = () => {
  const { id: routeInvestigationId } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Workspace Data State
  const [workspace, setWorkspace] = useState<InvestigationWorkspaceProjection | null>(null);
  const [activeTab, setActiveTab] = useState<string>('storyline');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Review & Execution Action State
  const [isExecutingStep, setIsExecutingStep] = useState<boolean>(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [reviewModalOpen, setReviewModalOpen] = useState<boolean>(false);
  const [selectedReviewDecision, setSelectedReviewDecision] = useState<'approve' | 'reject'>('approve');
  const [analystComment, setAnalystComment] = useState<string>('');

  // Level-2 Drawer State
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [selectedFinding, setSelectedFinding] = useState<KeyFinding | null>(null);

  const fetchWorkspace = async (investigationId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await workspaceClient.getWorkspace(investigationId);
      setWorkspace(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load investigation workspace');
    } finally {
      setIsLoading(false);
    }
  };

  // If no ID is provided in route, pick the most recent investigation or prompt selection
  useEffect(() => {
    if (routeInvestigationId) {
      fetchWorkspace(routeInvestigationId);
    } else {
      // Find latest investigation
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
  }, [routeInvestigationId]);

  // Handle single autonomous step execution
  const handleExecuteNextStep = async () => {
    if (!workspace?.threat.investigation_id || isExecutingStep) return;
    setIsExecutingStep(true);
    try {
      await workspaceClient.executeStep(workspace.threat.investigation_id);
      await fetchWorkspace(workspace.threat.investigation_id);
    } catch (err: any) {
      setError(err.message || 'Step execution failed');
    } finally {
      setIsExecutingStep(false);
    }
  };

  // Handle human review approval or rejection
  const handleSubmitReviewDecision = async () => {
    if (!workspace?.human_review?.review_id) return;
    setIsSubmittingReview(true);
    try {
      await reviewClient.submitDecision(workspace.human_review.review_id, {
        decision: selectedReviewDecision,
        analyst_id: 'SOC-ANALYST-104',
        analyst_comments: analystComment || 'Authorized via Sentinel Agentic Workspace',
      });
      setReviewModalOpen(false);
      await fetchWorkspace(workspace.threat.investigation_id);
    } catch (err: any) {
      setError(err.message || 'Failed to submit review decision');
    } finally {
      setIsSubmittingReview(false);
    }
  };

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

  if (!workspace) {
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

  const { threat, planner, key_findings, orchestration_history, recommendation, human_review } = workspace;

  const severityBadgeVariant: BadgeVariant =
    threat.severity === 'critical' ? 'critical' : threat.severity === 'high' ? 'high' : 'medium';

  // Count capability occurrences for dynamic revisit detection
  const workerCounts: Record<string, number> = {};
  orchestration_history.forEach((step) => {
    if (step.selected_worker) {
      workerCounts[step.selected_worker] = (workerCounts[step.selected_worker] || 0) + 1;
    }
  });

  return (
    <div className="flex-1 flex flex-col w-full bg-zinc-950 overflow-hidden">
      {/* ========================================================================= */}
      {/* 1. LEVEL 0 COMMAND ANCHOR (STICKY TOP BAR)                                */}
      {/* ========================================================================= */}
      <section className="bg-zinc-950 border-b border-zinc-800 p-4 shrink-0 space-y-3 shadow-md z-20">
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
                <Badge variant="violet" size="sm">
                  {threat.status}
                </Badge>
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

          {/* Calibrated Confidence & Single-Step Control */}
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
                Calibrated Confidence
              </div>
              <div className="flex items-center gap-2 justify-end">
                <div className="w-24 bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-blue-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${Math.round(threat.confidence * 100)}%` }}
                  />
                </div>
                <span className="font-mono text-sm font-bold text-zinc-100">
                  {Math.round(threat.confidence * 100)}%
                </span>
              </div>
            </div>

            <Button
              variant="secondary"
              size="sm"
              icon={<RotateCw className="w-3.5 h-3.5" />}
              isLoading={isExecutingStep}
              onClick={handleExecuteNextStep}
              title="Execute single autonomous planner cycle"
            >
              Step Planner
            </Button>
          </div>
        </div>

        {/* Level 0 Grounded Action Card (If recommendation exists) */}
        {recommendation && (
          <div className="bg-zinc-900/90 border border-zinc-800 rounded-lg p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="flex items-start gap-2.5">
              <div className="w-6 h-6 rounded bg-amber-950/80 border border-amber-700/80 text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                <AlertTriangle className="w-3.5 h-3.5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <strong className="text-zinc-100 font-semibold uppercase tracking-wider text-[11px]">
                    Recommended Action: {recommendation.action}
                  </strong>
                  <Badge variant={recommendation.approval_status === 'approved' ? 'success' : 'high'} size="sm">
                    {recommendation.approval_status}
                  </Badge>
                </div>
                <p className="text-zinc-400 mt-0.5">{recommendation.rationale}</p>
                {recommendation.supporting_findings.length > 0 && (
                  <div className="flex items-center gap-1.5 mt-1 text-[11px] font-mono text-zinc-400">
                    <span className="text-zinc-500">Supporting Citations:</span>
                    {recommendation.supporting_findings.map((sf) => (
                      <span key={sf.finding_id} className="text-blue-400 hover:underline cursor-pointer">
                        {sf.finding_id.slice(0, 8)}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {recommendation.approval_status === 'pending' && human_review ? (
                <>
                  <Button
                    variant="primary"
                    size="sm"
                    icon={<CheckCircle2 className="w-3.5 h-3.5" />}
                    onClick={() => {
                      setSelectedReviewDecision('approve');
                      setReviewModalOpen(true);
                    }}
                  >
                    Approve Containment
                  </Button>
                  <Button
                    variant="danger"
                    size="sm"
                    icon={<XCircle className="w-3.5 h-3.5" />}
                    onClick={() => {
                      setSelectedReviewDecision('reject');
                      setReviewModalOpen(true);
                    }}
                  >
                    Reject
                  </Button>
                </>
              ) : (
                <Badge variant="success" size="md">
                  Contained & Approved
                </Badge>
              )}
            </div>
          </div>
        )}
      </section>

      {/* ========================================================================= */}
      {/* 2. SUB-VIEW TABS SWITCHER                                                 */}
      {/* ========================================================================= */}
      <div className="bg-zinc-950/80 border-b border-zinc-800 shrink-0">
        <Tabs
          tabs={[
            { id: 'storyline', label: 'Storyline', count: orchestration_history.length },
            { id: 'activity', label: 'Agent Activity' },
            { id: 'evidence', label: 'Evidence Ledger', count: key_findings.length },
            { id: 'details', label: 'Forensic Details' },
          ]}
          activeTab={activeTab}
          onChange={setActiveTab}
        />
      </div>

      {/* ========================================================================= */}
      {/* 3. PRIMARY CONTENT STAGE                                                  */}
      {/* ========================================================================= */}
      <div className="flex-1 overflow-y-auto p-6 max-w-6xl mx-auto w-full">
        {/* VIEW 1: STORYLINE (CONCEPT A NARRATIVE STREAM) */}
        {activeTab === 'storyline' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Chronological Cycle Feed */}
            <div className="lg:col-span-2 space-y-4">
              <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider flex items-center justify-between">
                <span>Chronological Investigation Narrative</span>
                <span className="font-mono text-[10px] text-zinc-500">{orchestration_history.length} Decision Cycles</span>
              </h2>

              {orchestration_history.length === 0 ? (
                <EmptyState
                  title="No Planning Cycles Executed Yet"
                  description="Click 'Step Planner' above to initiate the autonomous investigation loop."
                />
              ) : (
                <div className="space-y-3 relative before:absolute before:inset-0 before:left-4 before:w-0.5 before:bg-zinc-800">
                  {orchestration_history.map((step, idx) => {
                    const isRevisit = (workerCounts[step.selected_worker || ''] || 0) > 1 && idx > 0;
                    return (
                      <div
                        key={idx}
                        className={`relative pl-8 transition-all group ${
                          step.selected_worker === 'response' ? 'border-emerald-500/50' : ''
                        }`}
                      >
                        {/* Circle Bullet on timeline rail */}
                        <div className="absolute left-2.5 top-3.5 w-3 h-3 rounded-full bg-zinc-950 border-2 border-blue-500 z-10 -translate-x-1/2" />

                        <div className="bg-zinc-900/80 border border-zinc-800 hover:border-zinc-700 rounded-lg p-3.5 transition-colors">
                          <div className="flex items-center justify-between gap-2 mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-mono font-bold text-zinc-300">
                                Cycle {step.cycle}
                              </span>
                              <Badge variant="violet" size="sm">
                                {step.selected_worker || 'planner'}
                              </Badge>
                              {isRevisit && (
                                <Badge variant="high" size="sm">
                                  Revisit
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-2 font-mono text-[11px]">
                              {step.confidence_delta !== undefined && step.confidence_delta !== null && (
                                <span className={step.confidence_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                                  {step.confidence_delta >= 0 ? '+' : ''}
                                  {step.confidence_delta.toFixed(3)} ΔC
                                </span>
                              )}
                              <span className="text-zinc-500">·</span>
                              <span className="text-zinc-500">{step.latency_ms || 12}ms</span>
                            </div>
                          </div>

                          {/* State Trigger */}
                          {step.rationale && (
                            <div className="text-xs text-zinc-300 mb-2">
                              <span className="text-zinc-500 font-mono text-[10px] uppercase block">Trigger Rationale:</span>
                              <p className="mt-0.5">{step.rationale}</p>
                            </div>
                          )}

                          {/* Observation / Evidence Yield */}
                          {step.observation && (
                            <div className="text-xs text-zinc-400 bg-zinc-950/60 p-2 rounded border border-zinc-800/60">
                              <span className="text-zinc-500 font-mono text-[10px] uppercase block">Yield Outcome:</span>
                              <p className="mt-0.5 text-zinc-300 font-mono text-[11px]">{step.observation}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Right 1 Col: Tri-Part State Box */}
            <div className="space-y-4">
              <Card>
                <CardHeader
                  title="Investigation State"
                  description="Strict cognitive breakdown of verified facts vs. open gaps"
                />

                <div className="space-y-4 text-xs">
                  {/* WHAT WE KNOW */}
                  <div>
                    <span className="text-[10px] font-mono font-semibold text-emerald-400 uppercase tracking-wider block mb-1">
                      [WHAT WE KNOW] (Verified Facts)
                    </span>
                    <ul className="space-y-1 text-zinc-300 bg-zinc-950/40 p-2 rounded border border-zinc-800/60 font-mono text-[11px]">
                      {threat.affected_entities.map((e) => (
                        <li key={e.id} className="truncate">
                          • {e.type.toUpperCase()}: {e.label}
                        </li>
                      ))}
                      {key_findings.slice(0, 2).map((f) => (
                        <li key={f.finding_id} className="truncate text-zinc-400">
                          • {f.summary}
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* WHAT WE SUSPECT */}
                  <div>
                    <span className="text-[10px] font-mono font-semibold text-amber-400 uppercase tracking-wider block mb-1">
                      [WHAT WE SUSPECT] (Hypothesis)
                    </span>
                    <div className="bg-zinc-950/40 p-2 rounded border border-zinc-800/60 text-zinc-300 text-[11px]">
                      {planner.current_observation || 'Evaluating anomalous outbound communication pattern against command and control signatures.'}
                    </div>
                  </div>

                  {/* WHAT REMAINS UNRESOLVED */}
                  <div>
                    <span className="text-[10px] font-mono font-semibold text-rose-400 uppercase tracking-wider block mb-1">
                      [WHAT REMAINS UNRESOLVED] (Gaps)
                    </span>
                    <ul className="space-y-1 text-zinc-400 bg-zinc-950/40 p-2 rounded border border-zinc-800/60 text-[11px]">
                      {planner.unresolved_questions.length > 0 ? (
                        planner.unresolved_questions.map((q, idx) => (
                          <li key={idx}>? {q}</li>
                        ))
                      ) : (
                        <li>• No unresolved questions remaining for current cycle</li>
                      )}
                    </ul>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        )}

        {/* VIEW 2: AGENT ACTIVITY (DYNAMIC OBSERVABILITY) */}
        {activeTab === 'activity' && (
          <div className="space-y-6">
            <Card>
              <CardHeader
                title="Planner Orchestration Telemetry"
                description="Observable decision records, capability selection frequencies, and execution latencies"
              />
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs font-mono">
                <div className="bg-zinc-950 p-3 rounded border border-zinc-800">
                  <span className="text-zinc-500 text-[10px]">TOTAL CYCLES</span>
                  <div className="text-lg font-bold text-zinc-100 mt-1">{orchestration_history.length}</div>
                </div>
                <div className="bg-zinc-950 p-3 rounded border border-zinc-800">
                  <span className="text-zinc-500 text-[10px]">CAPABILITY REVISITS</span>
                  <div className="text-lg font-bold text-violet-400 mt-1">
                    {Object.values(workerCounts).filter((c) => c > 1).length}
                  </div>
                </div>
                <div className="bg-zinc-950 p-3 rounded border border-zinc-800">
                  <span className="text-zinc-500 text-[10px]">ACTIVE CAPABILITY</span>
                  <div className="text-sm font-bold text-blue-400 mt-1 uppercase">
                    {planner.active_capability?.name || 'IDLE'}
                  </div>
                </div>
                <div className="bg-zinc-950 p-3 rounded border border-zinc-800">
                  <span className="text-zinc-500 text-[10px]">REPLAN STATUS</span>
                  <div className="text-sm font-bold text-amber-400 mt-1">
                    {planner.is_replanning ? 'ACTIVE REPLAN' : 'STABLE'}
                  </div>
                </div>
              </div>
            </Card>

            <Card>
              <CardHeader
                title="Capability Selection Frequency"
                description="Breakdown of which worker capabilities were selected by the Planner"
              />
              <div className="space-y-2">
                {Object.entries(workerCounts).map(([worker, count]) => (
                  <div key={worker} className="flex items-center justify-between text-xs font-mono p-2 rounded bg-zinc-950/60 border border-zinc-800">
                    <span className="uppercase text-zinc-300">{worker}</span>
                    <span className="text-zinc-400">{count} executions</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* VIEW 3: EVIDENCE LEDGER */}
        {activeTab === 'evidence' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                Discovered Evidence & Key Findings ({key_findings.length})
              </h2>
            </div>

            {key_findings.length === 0 ? (
              <EmptyState
                title="No Evidence Records Discovered Yet"
                description="As workers execute, findings and artifacts will appear in this ledger."
              />
            ) : (
              <div className="space-y-2.5">
                {key_findings.map((finding) => (
                  <div
                    key={finding.finding_id}
                    onClick={() => {
                      setSelectedFinding(finding);
                      setDrawerOpen(true);
                    }}
                    className="p-3.5 bg-zinc-900/80 hover:bg-zinc-900 border border-zinc-800 hover:border-zinc-700 rounded-lg cursor-pointer transition-all flex items-start justify-between gap-4"
                  >
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-mono font-bold text-blue-400">
                          {finding.finding_id.slice(0, 8)}
                        </span>
                        <Badge variant="neutral" size="sm">
                          {finding.source_type}
                        </Badge>
                        {finding.mitre_technique_id && (
                          <span className="text-[10px] font-mono bg-blue-950/60 text-blue-300 border border-blue-800 px-1.5 py-0.2 rounded">
                            {finding.mitre_technique_id}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-zinc-200">{finding.summary}</p>
                    </div>

                    <ChevronRight className="w-4 h-4 text-zinc-500 shrink-0 mt-1" />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* VIEW 4: DETAILS */}
        {activeTab === 'details' && (
          <div className="space-y-4">
            <Card>
              <CardHeader
                title="Forensic Diagnostic Telemetry"
                description="Raw system records and cryptographic provenance metadata"
              />
              <pre className="bg-zinc-950 p-4 rounded border border-zinc-800 text-[11px] font-mono text-zinc-400 overflow-x-auto">
                {JSON.stringify(workspace.workspace_metadata, null, 2)}
              </pre>
            </Card>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 4. LEVEL 2 SLIDE-OVER DRAWER (PROGRESSIVE DISCLOSURE)                     */}
      {/* ========================================================================= */}
      <Drawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        title={selectedFinding ? `Finding: ${selectedFinding.finding_id.slice(0, 8)}` : 'Diagnostic Telemetry'}
        subtitle={selectedFinding?.source_type}
      >
        {selectedFinding && (
          <div className="space-y-4">
            <div>
              <span className="text-zinc-500 uppercase font-mono text-[10px]">Summary:</span>
              <p className="text-zinc-200 mt-1 leading-relaxed">{selectedFinding.summary}</p>
            </div>

            {selectedFinding.mitre_technique_id && (
              <div>
                <span className="text-zinc-500 uppercase font-mono text-[10px]">MITRE ATT&CK Technique:</span>
                <div className="mt-1 font-mono text-blue-400 bg-zinc-900 p-2 rounded border border-zinc-800">
                  {selectedFinding.mitre_technique_id}
                </div>
              </div>
            )}

            <div>
              <span className="text-zinc-500 uppercase font-mono text-[10px]">Provenance Status:</span>
              <div className="mt-1 font-mono text-zinc-300 bg-zinc-900 p-2 rounded border border-zinc-800">
                {selectedFinding.provenance.provenance_status} · Worker: {selectedFinding.provenance.source_worker || 'system'}
              </div>
            </div>
          </div>
        )}
      </Drawer>

      {/* ========================================================================= */}
      {/* 5. HUMAN REVIEW CONFIRMATION MODAL                                        */}
      {/* ========================================================================= */}
      <Modal
        isOpen={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        title="Human Authorization Sign-Off"
        footer={
          <>
            <Button variant="ghost" onClick={() => setReviewModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant={selectedReviewDecision === 'approve' ? 'primary' : 'danger'}
              isLoading={isSubmittingReview}
              onClick={handleSubmitReviewDecision}
            >
              Confirm {selectedReviewDecision === 'approve' ? 'Approval' : 'Rejection'}
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
