/**
 * Scenario API client
 */

import { apiClient } from './api-client';

export interface ScenarioTemplate {
  name: string;
  scenario_type: string;
  severity: string;
  time_horizon: string;
  description: string;
  parameters: Record<string, any>;
}

export interface Scenario {
  id: string;
  name: string;
  scenario_type: string;
  severity: string;
  time_horizon: string;
  parameters?: Record<string, any>;
  created_at: string;
}

export interface ScenarioCreate {
  name: string;
  scenario_type: string;
  severity: string;
  time_horizon: string;
  parameters?: Record<string, any>;
}

export interface StressTestResult {
  scenario_id: string;
  scenario_name: string;
  scenario_type: string;
  severity: string;
  time_horizon: string;
  results: {
    holdings_count: number;
    portfolio_metrics: {
      portfolio_value: number;
      climate_var: number;
      stressed_drawdown: number;
      top_hotspot: string;
      top_sector_risk: string;
    };
  };
}

export interface ScenarioComparison {
  portfolio_id: string;
  scenarios: Array<{
    scenario_id: string;
    scenario_name: string;
    scenario_type: string;
    severity: string;
    time_horizon: string;
    portfolio_value: number;
    climate_var: number;
    stressed_drawdown: number;
    top_risks: Array<{
      asset_name: string;
      issuer_name: string;
      combined_score: number;
      expected_loss: number;
    }>;
  }>;
  deltas: Array<{
    from_scenario: string;
    to_scenario: string;
    climate_var_delta: number;
    climate_var_delta_pct: number;
    stressed_drawdown_delta: number;
    stressed_drawdown_delta_pct: number;
  }>;
  highest_risk_scenario: {
    scenario_id: string;
    scenario_name: string;
    climate_var: number;
  };
}

/**
 * Get all predefined scenario templates
 */
export async function getScenarioTemplates(): Promise<ScenarioTemplate[]> {
  return apiClient.get('/api/scenarios/templates');
}

/**
 * Create a custom scenario
 */
export async function createScenario(scenarioData: ScenarioCreate): Promise<Scenario> {
  return apiClient.post('/api/scenarios', scenarioData);
}

/**
 * List all stored scenarios
 */
export async function listScenarios(): Promise<Scenario[]> {
  return apiClient.get('/api/scenarios');
}

/**
 * Get a specific scenario by ID
 */
export async function getScenario(scenarioId: string): Promise<Scenario> {
  return apiClient.get(`/api/scenarios/${scenarioId}`);
}

/**
 * Run stress test for a scenario on a portfolio
 */
export async function stressTestScenario(
  scenarioId: string,
  portfolioId: string
): Promise<StressTestResult> {
  return apiClient.post(
    `/api/scenarios/${scenarioId}/stress-test?portfolio_id=${portfolioId}`
  );
}

/**
 * Compare multiple scenarios for a portfolio
 */
export async function compareScenarios(
  portfolioId: string,
  scenarioIds: string[]
): Promise<ScenarioComparison> {
  return apiClient.get(`/api/scenarios/compare?portfolio_id=${portfolioId}&scenario_ids=${scenarioIds.join(',')}`);
}

// Export as object for consistency
export const scenarioApi = {
  getTemplates: getScenarioTemplates,
  create: createScenario,
  list: listScenarios,
  get: getScenario,
  stressTest: stressTestScenario,
  compare: compareScenarios,
};
