/**
 * Map API client for geospatial endpoints
 */

import { apiClient } from './api-client';

export interface HoldingMapData {
  holding_id: string;
  asset_name: string;
  issuer_name: string;
  sector: string;
  latitude: number;
  longitude: number;
  combined_score: number;
  expected_loss: number;
  physical_score?: number;
  transition_score?: number;
}

export interface HotspotData {
  region: string;
  latitude: number;
  longitude: number;
  holding_count: number;
  total_expected_loss: number;
  avg_combined_score: number;
  max_combined_score: number;
}

export interface MapHoldingsResponse {
  portfolio_id: string;
  scenario_id: string;
  holdings_count: number;
  holdings: HoldingMapData[];
}

export interface HotspotsResponse {
  portfolio_id: string;
  scenario_id: string;
  threshold_score: number;
  hotspots_count: number;
  hotspots: HotspotData[];
}

/**
 * Get holdings with geospatial data for map visualization
 */
export async function getMapHoldings(
  portfolioId: string,
  scenarioId: string
): Promise<MapHoldingsResponse> {
  return apiClient.get<MapHoldingsResponse>(
    `/api/map/holdings?portfolio_id=${portfolioId}&scenario_id=${scenarioId}`
  );
}

/**
 * Get geographic hotspots with high climate risk concentration
 */
export async function getHotspots(
  portfolioId: string,
  scenarioId: string,
  thresholdScore: number = 70.0
): Promise<HotspotsResponse> {
  return apiClient.get<HotspotsResponse>(
    `/api/map/hotspots?portfolio_id=${portfolioId}&scenario_id=${scenarioId}&threshold_score=${thresholdScore}`
  );
}
