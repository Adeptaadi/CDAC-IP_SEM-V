/**
 * Dataset & Scenario Simulation Types
 * Directly maps to backend schemas in app.ingest.scenarios and ReplaySession
 */

export interface ScenarioMetadata {
  scenario_id: string;
  name: string;
  dataset_source: string;
  day: string;
  description: string;
  mitre_tactics: string[];
  mitre_techniques: string[];
  gold_hypothesis: string;
  raw_filename: string;
  normalized_filename: string;
}

export type ReplayStreamingState = 'IDLE' | 'PLAYING' | 'PAUSED' | 'COMPLETED';

export interface ReplayStatus {
  scenario: string | null;
  state: ReplayStreamingState;
  speed: number;
  total_events: number;
  dispatched_events_count: number;
  progress_percent: number;
  latest_event?: any | null;
  dispatched_in_step?: number;
}
