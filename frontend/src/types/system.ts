/**
 * System Health & Dependency Diagnostics Types
 */

export interface DependencyStatus {
  status: 'healthy' | 'unhealthy' | 'offline' | 'unresponsive' | 'degraded' | 'online' | 'offline_fallback_mode';
  latency_ms?: number;
  engine?: string;
  mode?: string;
  provider?: string;
  model?: string;
  error?: string;
  info?: string;
}

export interface SystemHealthResponse {
  status: 'healthy' | 'degraded' | 'offline';
  environment: string;
  dependencies: {
    database: DependencyStatus;
    redis: DependencyStatus;
    chromadb: DependencyStatus;
    llm_engine: DependencyStatus;
    [key: string]: DependencyStatus;
  };
}

export interface KnowledgeStats {
  mitre_techniques_count: number;
  playbooks_count: number;
  historical_cases_count: number;
  total_vectors: number;
}
