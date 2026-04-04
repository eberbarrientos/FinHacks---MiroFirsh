/**
 * Portfolio API client methods
 */

import { apiClient } from './api-client'

export interface Portfolio {
  id: string
  name: string
  base_currency: string
  created_at: string
  updated_at: string
}

export interface PortfolioSummary {
  id: string
  name: string
  base_currency: string
  holdings_count: number
  total_value: number
  created_at: string
  updated_at: string
}

export interface Holding {
  id: string
  portfolio_id: string
  asset_id: string
  asset_name: string
  asset_type: string
  issuer_name: string
  sector: string
  country: string
  state_region?: string
  latitude: number
  longitude: number
  market_value: number
  revenue_exposure_pct?: number
  carbon_intensity_proxy?: number
  insurance_dependency_score?: number
  supply_chain_dependency_score?: number
  created_at: string
}

export const portfolioApi = {
  async createPortfolio(data: { name: string; base_currency?: string }): Promise<Portfolio> {
    return apiClient.post<Portfolio>('/api/portfolios', data)
  },

  async getPortfolio(portfolioId: string): Promise<PortfolioSummary> {
    return apiClient.get<PortfolioSummary>(`/api/portfolios/${portfolioId}`)
  },

  async listPortfolios(skip = 0, limit = 100): Promise<Portfolio[]> {
    return apiClient.get<Portfolio[]>(`/api/portfolios?skip=${skip}&limit=${limit}`)
  },

  async uploadHoldings(portfolioId: string, file: File) {
    return apiClient.uploadFile(`/api/portfolios/${portfolioId}/upload-holdings`, file)
  },

  async getHoldings(portfolioId: string, skip = 0, limit = 100) {
    return apiClient.get<{
      portfolio_id: string
      holdings: Holding[]
      total_count: number
      skip: number
      limit: number
    }>(`/api/portfolios/${portfolioId}/holdings?skip=${skip}&limit=${limit}`)
  },

  async createSamplePortfolio() {
    return apiClient.post<{
      portfolio_id: string
      name: string
      base_currency: string
      holdings_count: number
      message: string
    }>('/api/portfolios/sample/create')
  },

  async getScenarioHistory(portfolioId: string) {
    return apiClient.get<Array<{
      scenario_id: string
      scenario_name: string
      scenario_type: string
      severity: string
      time_horizon: string
      last_executed: string
      holdings_count: number
    }>>(`/api/portfolios/${portfolioId}/scenario-history`)
  },
}
