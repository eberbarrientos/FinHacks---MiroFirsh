/**
 * Recommendation API client methods
 */

import { apiClient } from './api-client'

export interface Recommendation {
  id: string
  portfolio_id: string
  scenario_id: string
  recommendation_type: 'rebalance' | 'diversify' | 'hedge' | 'watchlist' | 'insurance_review'
  priority: 'critical' | 'high' | 'medium' | 'low'
  message: string
  affected_holdings?: string[]
  potential_impact?: number
  created_at: string
}

export const recommendationApi = {
  async getRecommendations(portfolioId: string, scenarioId: string): Promise<Recommendation[]> {
    return apiClient.get<Recommendation[]>(
      `/api/recommendations?portfolio_id=${portfolioId}&scenario_id=${scenarioId}`
    )
  },

  async generateRecommendations(portfolioId: string, scenarioId: string) {
    return apiClient.post<{
      message: string
      count: number
      portfolio_id: string
      scenario_id: string
    }>(`/api/recommendations/generate?portfolio_id=${portfolioId}&scenario_id=${scenarioId}`)
  },
}
