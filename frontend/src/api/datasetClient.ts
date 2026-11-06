import { request } from './client';
import { ScenarioMetadata, ReplayStatus } from '../types/dataset';

export const datasetClient = {
  /**
   * Lists the 5 verified CSE-CIC-IDS2018 scenarios
   * GET /api/dataset/scenarios
   */
  getScenarios: (): Promise<ScenarioMetadata[]> => {
    return request<ScenarioMetadata[]>({
      method: 'GET',
      url: '/api/dataset/scenarios',
    });
  },

  /**
   * Retrieves specific scenario metadata
   * GET /api/dataset/scenarios/{id}
   */
  getScenarioDetails: (scenarioId: string): Promise<ScenarioMetadata> => {
    return request<ScenarioMetadata>({
      method: 'GET',
      url: `/api/dataset/scenarios/${scenarioId}`,
    });
  },

  /**
   * Prepares and normalizes scenario telemetry on disk
   * POST /api/dataset/prepare/{scenario_id}
   */
  prepareScenario: (scenarioId: string): Promise<any> => {
    return request<any>({
      method: 'POST',
      url: `/api/dataset/prepare/${scenarioId}`,
    });
  },

  /**
   * Loads a scenario into the streaming replayer
   * POST /api/dataset/replay/load/{scenario_id}
   */
  loadReplay: (scenarioId: string, speed: number = 1.0, batchSize: number = 50): Promise<ReplayStatus> => {
    return request<ReplayStatus>({
      method: 'POST',
      url: `/api/dataset/replay/load/${scenarioId}`,
      params: { speed, batch_size: batchSize },
    });
  },

  /**
   * Starts or resumes streaming replay
   * POST /api/dataset/replay/start
   */
  startReplay: (): Promise<ReplayStatus> => {
    return request<ReplayStatus>({
      method: 'POST',
      url: '/api/dataset/replay/start',
    });
  },

  /**
   * Dispatches the next N events incrementally
   * POST /api/dataset/replay/step
   */
  stepReplay: (count: number = 1): Promise<ReplayStatus> => {
    return request<ReplayStatus>({
      method: 'POST',
      url: '/api/dataset/replay/step',
      params: { count },
    });
  },

  /**
   * Pauses streaming replay
   * POST /api/dataset/replay/pause
   */
  pauseReplay: (): Promise<ReplayStatus> => {
    return request<ReplayStatus>({
      method: 'POST',
      url: '/api/dataset/replay/pause',
    });
  },

  /**
   * Resets the replayer back to T0
   * POST /api/dataset/replay/reset
   */
  resetReplay: (): Promise<ReplayStatus> => {
    return request<ReplayStatus>({
      method: 'POST',
      url: '/api/dataset/replay/reset',
    });
  },

  /**
   * Retrieves current streaming status
   * GET /api/dataset/replay/status
   */
  getReplayStatus: (): Promise<ReplayStatus> => {
    return request<ReplayStatus>({
      method: 'GET',
      url: '/api/dataset/replay/status',
    });
  },
};
