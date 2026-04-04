'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { type ScenarioComparison } from '@/lib/scenario-api';

interface ScenarioCompareChartProps {
  comparison: ScenarioComparison;
}

export function ScenarioCompareChart({ comparison }: ScenarioCompareChartProps) {
  // Prepare data for the chart
  const chartData = comparison.scenarios.map((scenario) => ({
    name: scenario.scenario_name.length > 20 
      ? scenario.scenario_name.substring(0, 20) + '...' 
      : scenario.scenario_name,
    fullName: scenario.scenario_name,
    climateVar: scenario.climate_var / 1_000_000, // Convert to millions
    stressedDrawdown: scenario.stressed_drawdown,
    isHighestRisk: scenario.scenario_id === comparison.highest_risk_scenario.scenario_id
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800/95 backdrop-blur-md border border-slate-700/50 rounded-xl p-4 shadow-2xl">
          <div className="text-sm font-semibold text-slate-100 mb-2">
            {data.fullName}
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-slate-400">Climate VaR:</span>
              <span className="text-sm font-medium text-red-400">
                ${data.climateVar.toFixed(2)}M
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs text-slate-400">Stressed Drawdown:</span>
              <span className="text-sm font-medium text-amber-400">
                {data.stressedDrawdown.toFixed(2)}%
              </span>
            </div>
          </div>
          {data.isHighestRisk && (
            <div className="mt-2 pt-2 border-t border-slate-700/50">
              <span className="text-xs text-red-400 font-medium">⚠ Highest Risk</span>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6">
      <h3 className="text-lg font-bold text-slate-100 mb-4">Scenario Comparison</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Climate VaR Comparison */}
        <div>
          <h4 className="text-sm font-semibold text-slate-400 mb-3">Climate VaR ($ Millions)</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
              <XAxis 
                dataKey="name" 
                stroke="#94a3b8"
                fontSize={12}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                stroke="#94a3b8"
                fontSize={12}
                tickFormatter={(value) => `$${value}M`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="climateVar" radius={[8, 8, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`}
                    fill={entry.isHighestRisk ? '#ef4444' : '#06b6d4'}
                    opacity={entry.isHighestRisk ? 1 : 0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Stressed Drawdown Comparison */}
        <div>
          <h4 className="text-sm font-semibold text-slate-400 mb-3">Stressed Drawdown (%)</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
              <XAxis 
                dataKey="name" 
                stroke="#94a3b8"
                fontSize={12}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                stroke="#94a3b8"
                fontSize={12}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="stressedDrawdown" radius={[8, 8, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`}
                    fill={entry.isHighestRisk ? '#ef4444' : '#f59e0b'}
                    opacity={entry.isHighestRisk ? 1 : 0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-6">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-cyan-500"></div>
          <span className="text-xs text-slate-400">Standard Risk</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span className="text-xs text-slate-400">Highest Risk</span>
        </div>
      </div>
    </div>
  );
}
