import { request } from './client';
import {
  InvestigationWorkspaceProjection,
  InvestigationSummary,
  InvestigationStateSnapshot,
} from '../types/workspace';

export const workspaceClient = {
  /**
   * Fetches the unified workspace projection (P0 API)
   * GET /api/investigations/{id}/workspace
   */
  getWorkspace: (investigationId: string): Promise<InvestigationWorkspaceProjection> => {
    return request<InvestigationWorkspaceProjection>({
      method: 'GET',
      url: `/api/investigations/${investigationId}/workspace`,
    });
  },

  /**
   * Lists investigations for the History archive
   * GET /api/investigations
   */
  listInvestigations: (limit: number = 50, statusFilter?: string): Promise<InvestigationSummary[]> => {
    return request<InvestigationSummary[]>({
      method: 'GET',
      url: '/api/investigations',
      params: {
        limit,
        status_filter: statusFilter,
      },
    });
  },

  /**
   * Retrieves full details for a single investigation
   * GET /api/investigations/{id}
   */
  getInvestigation: (investigationId: string): Promise<any> => {
    return request<any>({
      method: 'GET',
      url: `/api/investigations/${investigationId}`,
    });
  },

  /**
   * Retrieves immutable version snapshots for deterministic replay
   * GET /api/investigations/{id}/snapshots
   */
  getSnapshots: (investigationId: string): Promise<InvestigationStateSnapshot[]> => {
    return request<InvestigationStateSnapshot[]>({
      method: 'GET',
      url: `/api/investigations/${investigationId}/snapshots`,
    });
  },

  /**
   * Executes a single autonomous planning cycle
   * POST /api/planner/investigations/{id}/step
   */
  executeStep: (investigationId: string): Promise<any> => {
    return request<any>({
      method: 'POST',
      url: `/api/planner/investigations/${investigationId}/step`,
    });
  },

  /**
   * Runs the continuous autonomous planning loop
   * POST /api/planner/investigations/{id}/run
   */
  runAutonomous: (investigationId: string, maxSteps: number = 10): Promise<any> => {
    return request<any>({
      method: 'POST',
      url: `/api/planner/investigations/${investigationId}/run`,
      params: { max_steps: maxSteps },
    });
  },

  /**
   * Creates a new investigation directly
   * POST /api/investigations
   */
  createInvestigation: (title: string, currentGoal?: string): Promise<{ investigation_id: string; title: string }> => {
    return request<{ investigation_id: string; title: string }>({
      method: 'POST',
      url: '/api/investigations',
      data: {
        title,
        current_goal: currentGoal || 'Autonomous investigation of anomalous security signals',
      },
    });
  },
};
