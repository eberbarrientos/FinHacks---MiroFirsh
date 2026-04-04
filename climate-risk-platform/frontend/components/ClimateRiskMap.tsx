'use client';

/**
 * ClimateRiskMap Component
 * 
 * Interactive map visualization using Mapbox GL showing climate risk across portfolio holdings.
 * Features:
 * - Risk markers scaled by combined_score
 * - Color coding: green (0-40), amber (40-70), red (70-100)
 * - Hover tooltips with holding details
 * - Click to filter dashboard
 * - Hotspot highlighting with pulsing animation
 * - Risk overlay layers (physical, transition, expected loss)
 */

import React, { useEffect, useRef, useState } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { getMapHoldings, getHotspots, HoldingMapData, HotspotData } from '@/lib/map-api';
import { useDashboardStore } from '@/store/dashboardStore';

// Mapbox access token - should be set via environment variable
const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || '';

interface ClimateRiskMapProps {
  portfolioId: string;
  scenarioId: string;
  className?: string;
}

type RiskLayer = 'combined' | 'physical' | 'transition' | 'loss';

/**
 * Get color based on risk score
 * Green (0-40), Amber (40-70), Red (70-100)
 */
function getRiskColor(score: number): string {
  if (score < 40) return '#10b981'; // green-500
  if (score < 70) return '#f59e0b'; // amber-500
  return '#ef4444'; // red-500
}

/**
 * Get marker size based on risk score
 */
function getMarkerSize(score: number): number {
  if (score < 40) return 8;
  if (score < 70) return 12;
  return 16;
}

export function ClimateRiskMap({ portfolioId, scenarioId, className = '' }: ClimateRiskMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [holdings, setHoldings] = useState<HoldingMapData[]>([]);
  const [hotspots, setHotspots] = useState<HotspotData[]>([]);
  const [activeLayer, setActiveLayer] = useState<RiskLayer>('combined');
  const { filterByHolding } = useDashboardStore();

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    if (!MAPBOX_TOKEN) {
      setError('Mapbox token not configured');
      setLoading(false);
      return;
    }

    mapboxgl.accessToken = MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11', // Dark mode style
      center: [-98, 38.5], // Center of US
      zoom: 3,
      pitch: 0,
      bearing: 0,
    });

    // Add navigation controls
    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right');

    map.current.on('load', () => {
      setLoading(false);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Fetch holdings and hotspots data
  useEffect(() => {
    if (!portfolioId || !scenarioId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        const [holdingsData, hotspotsData] = await Promise.all([
          getMapHoldings(portfolioId, scenarioId),
          getHotspots(portfolioId, scenarioId, 70.0),
        ]);
        setHoldings(holdingsData.holdings);
        setHotspots(hotspotsData.hotspots);
        setError(null);
      } catch (err) {
        console.error('Error fetching map data:', err);
        setError('Failed to load map data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [portfolioId, scenarioId]);

  // Add markers to map
  useEffect(() => {
    if (!map.current || !holdings.length) return;

    // Clear existing markers
    const markers = document.querySelectorAll('.mapboxgl-marker');
    markers.forEach((marker) => marker.remove());

    // Add holding markers
    holdings.forEach((holding) => {
      const score = getScoreForLayer(holding, activeLayer);
      const color = getRiskColor(score);
      const size = getMarkerSize(score);

      // Create marker element
      const el = document.createElement('div');
      el.className = 'risk-marker';
      el.style.width = `${size}px`;
      el.style.height = `${size}px`;
      el.style.backgroundColor = color;
      el.style.borderRadius = '50%';
      el.style.border = '2px solid rgba(255, 255, 255, 0.8)';
      el.style.cursor = 'pointer';
      el.style.transition = 'all 0.3s ease';

      // Hover effect
      el.addEventListener('mouseenter', () => {
        el.style.transform = 'scale(1.3)';
        el.style.boxShadow = '0 0 20px rgba(255, 255, 255, 0.6)';
      });

      el.addEventListener('mouseleave', () => {
        el.style.transform = 'scale(1)';
        el.style.boxShadow = 'none';
      });

      // Click handler - filter dashboard
      el.addEventListener('click', () => {
        filterByHolding(holding.holding_id, holding.asset_name, holding.issuer_name);
        // Smooth pan to marker
        map.current?.flyTo({
          center: [holding.longitude, holding.latitude],
          zoom: 8,
          duration: 1500,
        });
      });

      // Create popup
      const popup = new mapboxgl.Popup({
        offset: 15,
        closeButton: false,
        className: 'risk-popup',
      }).setHTML(`
        <div class="p-3 bg-gray-900/95 backdrop-blur-sm rounded-lg border border-gray-700">
          <div class="font-semibold text-white mb-1">${holding.asset_name}</div>
          <div class="text-sm text-gray-300 mb-2">${holding.issuer_name}</div>
          <div class="space-y-1 text-xs">
            <div class="flex justify-between">
              <span class="text-gray-400">Risk Score:</span>
              <span class="font-semibold" style="color: ${color}">${score.toFixed(1)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Expected Loss:</span>
              <span class="text-white">$${(holding.expected_loss / 1000000).toFixed(2)}M</span>
            </div>
          </div>
        </div>
      `);

      // Add marker to map
      new mapboxgl.Marker(el)
        .setLngLat([holding.longitude, holding.latitude])
        .setPopup(popup)
        .addTo(map.current!);
    });

    // Add hotspot markers with pulsing animation
    hotspots.forEach((hotspot) => {
      const el = document.createElement('div');
      el.className = 'hotspot-marker';
      el.innerHTML = `
        <div class="relative">
          <div class="absolute inset-0 bg-red-500 rounded-full animate-ping opacity-75"></div>
          <div class="relative bg-red-600 rounded-full w-6 h-6 border-2 border-white"></div>
        </div>
      `;

      const popup = new mapboxgl.Popup({
        offset: 15,
        closeButton: false,
      }).setHTML(`
        <div class="p-3 bg-gray-900/95 backdrop-blur-sm rounded-lg border border-red-700">
          <div class="font-semibold text-red-400 mb-1">🔥 Hotspot: ${hotspot.region}</div>
          <div class="space-y-1 text-xs">
            <div class="flex justify-between">
              <span class="text-gray-400">Holdings:</span>
              <span class="text-white">${hotspot.holding_count}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Avg Risk:</span>
              <span class="text-red-400">${hotspot.avg_combined_score.toFixed(1)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-400">Total Loss:</span>
              <span class="text-white">$${(hotspot.total_expected_loss / 1000000).toFixed(2)}M</span>
            </div>
          </div>
        </div>
      `);

      new mapboxgl.Marker(el)
        .setLngLat([hotspot.longitude, hotspot.latitude])
        .setPopup(popup)
        .addTo(map.current!);
    });
  }, [holdings, hotspots, activeLayer, filterByHolding]);

  // Helper function to get score based on active layer
  function getScoreForLayer(holding: HoldingMapData, layer: RiskLayer): number {
    switch (layer) {
      case 'physical':
        return holding.physical_score || holding.combined_score;
      case 'transition':
        return holding.transition_score || holding.combined_score;
      case 'loss':
        // Normalize expected loss to 0-100 scale for visualization
        const maxLoss = Math.max(...holdings.map((h) => h.expected_loss));
        return (holding.expected_loss / maxLoss) * 100;
      case 'combined':
      default:
        return holding.combined_score;
    }
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center h-full bg-gray-900/50 backdrop-blur-sm rounded-2xl border border-gray-800 ${className}`}>
        <div className="text-center p-8">
          <div className="text-red-400 text-lg font-semibold mb-2">Map Error</div>
          <div className="text-gray-400 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Map Container */}
      <div
        ref={mapContainer}
        className="w-full h-full rounded-2xl overflow-hidden"
        style={{ minHeight: '500px' }}
      />

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 backdrop-blur-sm rounded-2xl">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mx-auto mb-4"></div>
            <div className="text-gray-300">Loading map data...</div>
          </div>
        </div>
      )}

      {/* Layer Controls - Glassmorphism */}
      {!loading && (
        <div className="absolute top-4 left-4 bg-gray-900/70 backdrop-blur-md rounded-xl border border-gray-700/50 p-2 shadow-lg">
          <div className="text-xs text-gray-400 mb-2 px-2">Risk Layer</div>
          <div className="space-y-1">
            {[
              { id: 'combined', label: 'Combined' },
              { id: 'physical', label: 'Physical' },
              { id: 'transition', label: 'Transition' },
              { id: 'loss', label: 'Expected Loss' },
            ].map((layer) => (
              <button
                key={layer.id}
                onClick={() => setActiveLayer(layer.id as RiskLayer)}
                className={`w-full px-3 py-2 text-sm rounded-lg transition-all ${
                  activeLayer === layer.id
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                    : 'text-gray-300 hover:bg-gray-800/50'
                }`}
              >
                {layer.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Legend - Glassmorphism */}
      {!loading && (
        <div className="absolute bottom-4 left-4 bg-gray-900/70 backdrop-blur-md rounded-xl border border-gray-700/50 p-3 shadow-lg">
          <div className="text-xs text-gray-400 mb-2">Risk Level</div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span className="text-xs text-gray-300">Low (0-40)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-500"></div>
              <span className="text-xs text-gray-300">Medium (40-70)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-xs text-gray-300">High (70-100)</span>
            </div>
          </div>
        </div>
      )}

      {/* Stats - Glassmorphism */}
      {!loading && holdings.length > 0 && (
        <div className="absolute bottom-4 right-4 bg-gray-900/70 backdrop-blur-md rounded-xl border border-gray-700/50 p-3 shadow-lg">
          <div className="text-xs text-gray-400 mb-2">Map Stats</div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between gap-4">
              <span className="text-gray-400">Holdings:</span>
              <span className="text-white font-semibold">{holdings.length}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-400">Hotspots:</span>
              <span className="text-red-400 font-semibold">{hotspots.length}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
