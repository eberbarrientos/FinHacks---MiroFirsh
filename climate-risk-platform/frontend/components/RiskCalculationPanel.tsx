'use client'

import { useState } from 'react'
import { riskApi, type TaskStatus, type PortfolioRiskResult } from '@/lib/risk-api'

interface RiskCalculationPanelProps {
  portfolioId: string
  scenarioId: string
  onResultsReady?: (result: PortfolioRiskResult) => void
}

export function RiskCalculationPanel({
  portfolioId,
  scenarioId,
  onResultsReady,
}: RiskCalculationPanelProps) {
  const [isCalculating, setIsCalculating] = useState(false)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<PortfolioRiskResult | null>(null)

  const handleCalculate = async () => {
    try {
      setIsCalculating(true)
      setError(null)
      setTaskStatus(null)
      setResult(null)

      // Trigger calculation
      const response = await riskApi.calculateRisk({
        portfolio_id: portfolioId,
        scenario_id: scenarioId,
      })

      // Poll for completion
      const finalStatus = await riskApi.pollTaskCompletion(
        response.task_id,
        (status) => {
          setTaskStatus(status)
        }
      )

      if (finalStatus.status === 'completed' && finalStatus.result) {
        setResult(finalStatus.result)
        if (onResultsReady) {
          onResultsReady(finalStatus.result)
        }
      } else if (finalStatus.status === 'failed') {
        setError(finalStatus.error || 'Calculation failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate risk')
    } finally {
      setIsCalculating(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'queued':
        return 'text-yellow-400'
      case 'processing':
        return 'text-cyan-400'
      case 'completed':
        return 'text-emerald-400'
      case 'failed':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const getStatusMessage = (status: string) => {
    switch (status) {
      case 'queued':
        return 'Queued for processing...'
      case 'processing':
        return 'Analyzing portfolio risk...'
      case 'completed':
        return 'Risk calculation completed!'
      case 'failed':
        return 'Calculation failed'
      default:
        return 'Unknown status'
    }
  }

  return (
    <div className="p-6 rounded-2xl bg-gray-900/50 backdrop-blur-sm border border-gray-800">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold text-white">Risk Analysis</h3>
        <button
          onClick={handleCalculate}
          disabled={isCalculating || !portfolioId || !scenarioId}
          className={`
            px-6 py-2.5 rounded-xl font-medium transition-all duration-200
            ${
              isCalculating || !portfolioId || !scenarioId
                ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                : 'bg-gradient-to-r from-cyan-500 to-teal-500 text-white hover:from-cyan-600 hover:to-teal-600 hover:shadow-lg hover:shadow-cyan-500/30'
            }
          `}
        >
          {isCalculating ? 'Calculating...' : 'Calculate Risk'}
        </button>
      </div>

      {/* Progress indicator */}
      {isCalculating && taskStatus && (
        <div className="mb-6 p-4 rounded-xl bg-gray-800/50 border border-gray-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="relative">
              <div className="w-10 h-10 rounded-full border-2 border-gray-700 flex items-center justify-center">
                <svg
                  className={`animate-spin h-5 w-5 ${getStatusColor(taskStatus.status)}`}
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              </div>
            </div>
            <div>
              <p className={`font-medium ${getStatusColor(taskStatus.status)}`}>
                {getStatusMessage(taskStatus.status)}
              </p>
              <p className="text-sm text-gray-500">Task ID: {taskStatus.task_id.slice(0, 8)}...</p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r from-cyan-500 to-teal-500 transition-all duration-500 ${
                taskStatus.status === 'queued'
                  ? 'w-1/4'
                  : taskStatus.status === 'processing'
                  ? 'w-3/4 animate-pulse'
                  : 'w-full'
              }`}
            />
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-red-400 mt-0.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div>
              <p className="font-medium text-red-400">Calculation Error</p>
              <p className="text-sm text-red-300 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results summary */}
      {result && (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-emerald-400">
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-medium">Risk calculation completed successfully</span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700">
              <p className="text-sm text-gray-400 mb-1">Holdings Analyzed</p>
              <p className="text-2xl font-bold text-white">{result.holdings_count}</p>
            </div>

            <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700">
              <p className="text-sm text-gray-400 mb-1">Portfolio Value</p>
              <p className="text-2xl font-bold text-white">
                ${(result.portfolio_metrics.portfolio_value / 1_000_000).toFixed(1)}M
              </p>
            </div>

            <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700">
              <p className="text-sm text-gray-400 mb-1">Climate VaR</p>
              <p className="text-2xl font-bold text-amber-400">
                ${(result.portfolio_metrics.climate_var / 1_000_000).toFixed(1)}M
              </p>
            </div>

            <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700">
              <p className="text-sm text-gray-400 mb-1">Stressed Drawdown</p>
              <p className="text-2xl font-bold text-red-400">
                {result.portfolio_metrics.stressed_drawdown.toFixed(2)}%
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700">
            <p className="text-sm text-gray-400 mb-2">Top Risk Concentrations</p>
            <div className="flex flex-wrap gap-2">
              <span className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 text-sm">
                📍 {result.portfolio_metrics.top_hotspot}
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                🏢 {result.portfolio_metrics.top_sector_risk}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!isCalculating && !result && !error && (
        <div className="text-center py-8 text-gray-500">
          <svg
            className="w-12 h-12 mx-auto mb-3 opacity-50"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <p>Click "Calculate Risk" to analyze portfolio climate exposure</p>
        </div>
      )}
    </div>
  )
}

