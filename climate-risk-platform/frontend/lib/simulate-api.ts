/**
 * Cascade simulation API client
 */
import { apiClient } from './api-client'

export interface SimulationRequest {
  portfolio_id: string
  event_description: string
  severity: string
  num_rounds: number
}

export interface CascadeEvent {
  round: number
  source: string
  target: string
  type: string
  description: string
  loss: number
  severity: string
}

export interface AffectedEntity {
  entity: string
  sector: string
  region: string
  market_value: number
  total_loss: number
  loss_pct: number
  is_portfolio_holding?: boolean
  company_type?: string
}

export interface SimulationResult {
  scenario: string
  event_type: string
  affected_regions: string[]
  severity: string
  simulation_rounds: number
  total_direct_loss: number
  total_cascaded_loss: number
  total_loss: number
  cascade_amplification: number
  narrative: string
  cascade_events: CascadeEvent[]
  affected_entities: AffectedEntity[]
  dependency_chains: string[][]
  recommendations: string[]
}

export const simulateApi = {
  async runSimulation(request: SimulationRequest): Promise<SimulationResult> {
    return apiClient.post<SimulationResult>('/api/simulate/run', request)
  },
}
