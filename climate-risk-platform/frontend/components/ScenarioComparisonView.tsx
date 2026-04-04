'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { compareScenarios, type ScenarioComparison } from '@/lib/scenario-api';
import { ScenarioCompareChart } from './ScenarioCompareChart';

interface ScenarioComparisonViewProps {
  portfolioId: string;
  scenarioIds: string[];
  onRemoveScenario?: (scenarioId: string) => void;
}

export function ScenarioComparisonView({
  portfolioId,
  scenarioIds,
  onRemoveScenario
}: ScenarioComparisonViewProps) {
  const [comparison, setComparison] = useState<ScenarioComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (scenarioIds.length >= 2) {
      loadComparison();
    }
  }, [portfolioId, scenarioIds]);

  const loadComparison = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await compareScenarios(portfolioId, scenarioIds);
      setComparison(data);
    } catch (err) {
      console.error('Error loading scenario comparison:', err);
      setError('Failed to load scenario comparison');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-slate-400">Loading comparison...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-6 text-center">
        <div className="text-red-400">{error}</div>
        <button
          onClick={loadComparison}
          className="mt-4 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-red-300 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!comparison) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Comparison Grid */}
      <div className={`grid gap-4 ${
        comparison.scenarios.length === 2 ? 'grid-cols-2' :
        comparison.scenarios.length === 3 ? 'grid-cols-3' :
        'grid-cols-4'
      }`}>
        <AnimatePresence mode="popLayout">
          {comparison.scenarios.map((scenario, index) => (
            <motion.div
              key={scenario.scenario_id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`bg-slate-800/50 backdrop-blur-sm border rounded-2xl p-6 ${
                scenario.scenario_id === comparison.highest_risk_scenario.scenario_id
                  ? 'border-red-500/50 ring-2 ring-red-500/20'
                  : 'border-slate-700/50'
              }`}
            >
              {/* Scenario Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-slate-100 mb-1">
                    {scenario.scenario_name}
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      scenario.severity === 'high'
                        ? 'bg-red-500/20 text-red-300'
                        : scenario.severity === 'medium'
                        ? 'bg-amber-500/20 text-amber-300'
                        : 'bg-emerald-500/20 text-emerald-300'
                    }`}>
                      {scenario.severity}
                    </span>
                    <span className="text-xs text-slate-500">
                      {scenario.time_horizon}
                    </span>
                  </div>
                </div>
                {onRemoveScenario && (
                  <button
                    onClick={() => onRemoveScenario(scenario.scenario_id)}
                    className="text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Highest Risk Badge */}
              {scenario.scenario_id === comparison.highest_risk_scenario.scenario_id && (
                <div className="mb-4 px-3 py-1.5 bg-red-500/20 border border-red-500/30 rounded-lg">
                  <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    <span className="text-xs font-medium text-red-300">Highest Risk</span>
                  </div>
                </div>
              )}

              {/* Key Metrics */}
              <div className="space-y-4">
                <div>
                  <div className="text-xs text-slate-500 mb-1">Portfolio Value</div>
                  <div className="text-2xl font-bold text-slate-100">
                    ${(scenario.portfolio_value / 1_000_000).toFixed(1)}M
                  </div>
                </div>

                <div>
                  <div className="text-xs text-slate-500 mb-1">Climate VaR</div>
                  <div className="text-2xl font-bold text-red-400">
                    ${(scenario.climate_var / 1_000_000).toFixed(2)}M
                  </div>
                </div>

                <div>
                  <div className="text-xs text-slate-500 mb-1">Stressed Drawdown</div>
                  <div className="text-2xl font-bold text-amber-400">
                    {scenario.stressed_drawdown.toFixed(2)}%
                  </div>
                </div>

                {/* Top Risks */}
                <div>
                  <div className="text-xs text-slate-500 mb-2">Top Risks</div>
                  <div className="space-y-2">
                    {scenario.top_risks.slice(0, 3).map((risk, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs">
                        <span className="text-slate-400 truncate flex-1">
                          {risk.asset_name}
                        </span>
                        <span className={`font-medium ml-2 ${
                          risk.combined_score >= 75 ? 'text-red-400' :
                          risk.combined_score >= 50 ? 'text-amber-400' :
                          'text-emerald-400'
                        }`}>
                          {risk.combined_score.toFixed(0)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Delta Chart */}
      {comparison.deltas.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <ScenarioCompareChart comparison={comparison} />
        </motion.div>
      )}

      {/* Delta Details Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.5 }}
        className="bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6"
      >
        <h3 className="text-lg font-bold text-slate-100 mb-4">Scenario Deltas</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider pb-3">
                  Comparison
                </th>
                <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider pb-3">
                  Climate VaR Δ
                </th>
                <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider pb-3">
                  Climate VaR Δ %
                </th>
                <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider pb-3">
                  Drawdown Δ
                </th>
                <th className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider pb-3">
                  Drawdown Δ %
                </th>
              </tr>
            </thead>
            <tbody>
              {comparison.deltas.map((delta, index) => (
                <tr key={index} className="border-b border-slate-700/30 last:border-0">
                  <td className="py-3 text-sm text-slate-300">
                    <div className="flex items-center gap-2">
                      <span className="text-slate-500">{delta.from_scenario}</span>
                      <svg className="w-4 h-4 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                      <span className="text-slate-300">{delta.to_scenario}</span>
                    </div>
                  </td>
                  <td className={`py-3 text-right text-sm font-medium ${
                    delta.climate_var_delta > 0 ? 'text-red-400' : 'text-emerald-400'
                  }`}>
                    {delta.climate_var_delta > 0 ? '+' : ''}
                    ${(delta.climate_var_delta / 1_000_000).toFixed(2)}M
                  </td>
                  <td className={`py-3 text-right text-sm font-medium ${
                    delta.climate_var_delta_pct > 0 ? 'text-red-400' : 'text-emerald-400'
                  }`}>
                    {delta.climate_var_delta_pct > 0 ? '+' : ''}
                    {delta.climate_var_delta_pct.toFixed(1)}%
                  </td>
                  <td className={`py-3 text-right text-sm font-medium ${
                    delta.stressed_drawdown_delta > 0 ? 'text-red-400' : 'text-emerald-400'
                  }`}>
                    {delta.stressed_drawdown_delta > 0 ? '+' : ''}
                    {delta.stressed_drawdown_delta.toFixed(2)}%
                  </td>
                  <td className={`py-3 text-right text-sm font-medium ${
                    delta.stressed_drawdown_delta_pct > 0 ? 'text-red-400' : 'text-emerald-400'
                  }`}>
                    {delta.stressed_drawdown_delta_pct > 0 ? '+' : ''}
                    {delta.stressed_drawdown_delta_pct.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}
