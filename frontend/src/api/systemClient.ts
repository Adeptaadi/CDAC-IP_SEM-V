import { request } from './client';
import { SystemHealthResponse, KnowledgeStats } from '../types/system';

export const systemClient = {
  /**
   * Inspects connectivity and responsiveness of DB, Redis, ChromaDB, and Ollama
   * GET /health/dependencies
   */
  getHealthDependencies: (): Promise<SystemHealthResponse> => {
    return request<SystemHealthResponse>({
      method: 'GET',
      url: '/health/dependencies',
    });
  },

  /**
   * General liveness probe
   * GET /health/live
   */
  getHealthLive: (): Promise<{ status: string; service: string }> => {
    return request<{ status: string; service: string }>({
      method: 'GET',
      url: '/health/live',
    });
  },

  /**
   * Returns vector counts stored across all knowledge collections
   * GET /api/knowledge/stats
   */
  getKnowledgeStats: (): Promise<KnowledgeStats> => {
    return request<KnowledgeStats>({
      method: 'GET',
      url: '/api/knowledge/stats',
    });
  },

  /**
   * Queries knowledge store semantically
   * POST /api/knowledge/query
   */
  queryKnowledge: (query: string, topK: number = 4): Promise<any> => {
    return request<any>({
      method: 'POST',
      url: '/api/knowledge/query',
      data: { query, top_k: topK },
    });
  },
};
