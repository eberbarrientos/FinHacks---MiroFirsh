/**
 * MiroFish API client for cascade simulation
 */

import { apiClient } from './api-client';

export interface MiroFishRunRequest {
  portfolio_id: string;
  scenario_id: string;
}

export interface MiroFishRunResponse {
  run_id: string;
  status: string;
  message?: string;
}

export interface CascadeEvent {
  entity?: string;
  issuer?: string;
  event_type?: string;
  loss?: number;
  impact?: number;
  description?: string;
  timestamp?: string;
}

export interface MiroFishResultResponse {
  run_id: string;
  status: string;
  cascade_events?: CascadeEvent[];
  dependency_narrative?: string;
  propagated_loss?: number;
  affected_entity_count?: number;
  created_at?: string;
  completed_at?: string;
  error?: string;
}

/**
 * Trigger MiroFish cascade simulation
 */
export async function triggerCascadeSimulation(
  portfolioId: string,
  scenarioId: string
): Promise<MiroFishRunResponse> {
  return apiClient.post<MiroFishRunResponse>('/api/mirofish/run', {
    portfolio_id: portfolioId,
    scenario_id: scenarioId,
  });
}

/**
 * Get MiroFish simulation results
 */
export async function getSimulationResults(runId: string): Promise<MiroFishResultResponse> {
  return apiClient.get<MiroFishResultResponse>(`/api/mirofish/run/${runId}`);
}

/**
 * Poll for simulation completion
 * 
 * Polls every 5 seconds until simulation completes or times out
 */
export async function pollSimulationResults(
  runId: string,
  maxAttempts: number = 12,
  interval: number = 5000
): Promise<MiroFishResultResponse> {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const result = await getSimulationResults(runId);
    
    // Check if completed
    if (result.status === 'completed' || result.status === 'failed' || result.status === 'unavailable') {
      return result;
    }
    
    // Wait before next poll
    if (attempt < maxAttempts - 1) {
      await new Promise(resolve => setTimeout(resolve, interval));
    }
  }
  
  // Timeout - return last result
  return await getSimulationResults(runId);
}

// Export as object for consistency
export const mirofishApi = {
  trigger: triggerCascadeSimulation,
  getResults: getSimulationResults,
  poll: pollSimulationResults,
  // Convenience method to get results by portfolio and scenario
  async getSimulationResults(portfolioId: string, scenarioId: string): Promise<MiroFishResultResponse | null> {
    try {
      // Try to get existing results - this would need a backend endpoint
      // For now, return null and let components handle it
      return null;
    } catch {
      return null;
    }
  },
};
