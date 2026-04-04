/**
 * Risk calculation API client methods
 */

import { apiClient } from './api-client'

export interface RiskCalculationRequest {
  portfolio_id: string
  scenario_id: string
}

export interface RiskCalculationResponse {
  task_id: string
  status: string
  message: string
}

export interface TaskStatus {
  task_id: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  portfolio_id: string
  scenario_id: string
  result?: PortfolioRiskResult
  error?: string
}

export interface HoldingRisk {
  holding_id: string
  asset_name: string
  issuer_name: string
  sector: string
  market_value: number
  physical_score: number
  transition_score: number
  combined_score: number
  expected_loss: number
  confidence: string
  calculated_at: string
}

export interface IssuerAggregated {
  [issuer: string]: {
    aggregated_loss: number
    total_market_value: number
    loss_percentage: number
    holdings_count: number
  }
}

export interface ConcentrationMetrics {
  sector_concentration: { [sector: string]: number }
  geography_concentration: { [region: string]: number }
  issuer_concentration: { [issuer: string]: number }
  sector_penalty: number
  geography_penalty: number
  issuer_penalty: number
  total_penalty: number
}

export interface PortfolioMetrics {
  portfolio_value: number
  climate_var: number
  stressed_drawdown: number
  top_hotspot: string
  top_sector_risk: string
  issuer_aggregated: IssuerAggregated
  concentration_metrics: ConcentrationMetrics
}

export interface PortfolioRiskResult {
  holdings_count: number
  portfolio_metrics: PortfolioMetrics
  risk_results: Array<{
    holding_id: string
    physical_score: number
    transition_score: number
    combined_score: number
    expected_loss: number
    confidence: string
  }>
}

export interface RiskResultsResponse {
  portfolio_id: string
  scenario_id: string
  holdings: HoldingRisk[]
}

export interface PortfolioSummary {
  portfolio_id: string
  scenario_id: string
  portfolio_value: number
  climate_var: number
  stressed_drawdown: number
  holdings_count: number
  top_risks: Array<{
    asset_name: string
    issuer_name: string
    combined_score: number
    expected_loss: number
  }>
}

export const riskApi = {
  /**
   * Trigger risk calculation for a portfolio and scenario
   */
  async calculateRisk(request: RiskCalculationRequest): Promise<RiskCalculationResponse> {
    return apiClient.post<RiskCalculationResponse>('/api/risk/run', request)
  },

  /**
   * Get the status of a risk calculation task
   */
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    return apiClient.get<TaskStatus>(`/api/risk/task/${taskId}`)
  },

  /**
   * Poll task status until completion or failure
   * @param taskId - The task ID to poll
   * @param onProgress - Optional callback for progress updates
   * @param maxAttempts - Maximum number of polling attempts (default: 60)
   * @param intervalMs - Polling interval in milliseconds (default: 2000)
   */
  async pollTaskCompletion(
    taskId: string,
    onProgress?: (status: TaskStatus) => void,
    maxAttempts = 60,
    intervalMs = 2000
  ): Promise<TaskStatus> {
    let attempts = 0

    while (attempts < maxAttempts) {
      const status = await this.getTaskStatus(taskId)

      if (onProgress) {
        onProgress(status)
      }

      if (status.status === 'completed' || status.status === 'failed') {
        return status
      }

      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, intervalMs))
      attempts++
    }

    throw new Error('Task polling timeout - maximum attempts reached')
  },

  /**
   * Get risk calculation results for a portfolio and scenario
   */
  async getRiskResults(portfolioId: string, scenarioId: string): Promise<RiskResultsResponse> {
    return apiClient.get<RiskResultsResponse>(
      `/api/risk/results?portfolio_id=${portfolioId}&scenario_id=${scenarioId}`
    )
  },

  /**
   * Get portfolio-level summary metrics
   */
  async getPortfolioSummary(portfolioId: string, scenarioId: string): Promise<PortfolioSummary> {
    return apiClient.get<PortfolioSummary>(
      `/api/risk/summary?portfolio_id=${portfolioId}&scenario_id=${scenarioId}`
    )
  },
}

