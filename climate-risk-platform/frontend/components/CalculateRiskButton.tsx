'use client'

import { useState } from 'react'
import { riskApi, type TaskStatus } from '@/lib/risk-api'

interface CalculateRiskButtonProps {
  portfolioId: string
  scenarioId: string
  onCalculationComplete?: (result: TaskStatus) => void
  onCalculationError?: (error: Error) => void
  className?: string
}

export function CalculateRiskButton({
  portfolioId,
  scenarioId,
  onCalculationComplete,
  onCalculationError,
  className = '',
}: CalculateRiskButtonProps) {
  const [isCalculating, setIsCalculating] = useState(false)
  const [progress, setProgress] = useState<string>('')
  const [error, setError] = useState<string | null>(null)

  const handleCalculateRisk = async () => {
    try {
      setIsCalculating(true)
      setError(null)
      setProgress('Initiating risk calculation...')

      // Trigger risk calculation
      const response = await riskApi.calculateRisk({
        portfolio_id: portfolioId,
        scenario_id: scenarioId,
      })

      setProgress('Processing risk analysis...')

      // Poll for completion
      const result = await riskApi.pollTaskCompletion(
        response.task_id,
        (status) => {
          // Update progress based on status
          if (status.status === 'queued') {
            setProgress('Queued for processing...')
          } else if (status.status === 'processing') {
            setProgress('Calculating risk scores...')
          }
        }
      )

      if (result.status === 'completed') {
        setProgress('Risk calculation completed!')
        if (onCalculationComplete) {
          onCalculationComplete(result)
        }
      } else if (result.status === 'failed') {
        const errorMsg = result.error || 'Risk calculation failed'
        setError(errorMsg)
        if (onCalculationError) {
          onCalculationError(new Error(errorMsg))
        }
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to calculate risk'
      setError(errorMsg)
      if (onCalculationError) {
        onCalculationError(err instanceof Error ? err : new Error(errorMsg))
      }
    } finally {
      setIsCalculating(false)
    }
  }

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <button
        onClick={handleCalculateRisk}
        disabled={isCalculating || !portfolioId || !scenarioId}
        className={`
          px-6 py-3 rounded-xl font-medium transition-all duration-200
          ${
            isCalculating || !portfolioId || !scenarioId
              ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
              : 'bg-gradient-to-r from-cyan-500 to-teal-500 text-white hover:from-cyan-600 hover:to-teal-600 hover:shadow-lg hover:shadow-cyan-500/50'
          }
        `}
      >
        {isCalculating ? (
          <span className="flex items-center gap-2">
            <svg
              className="animate-spin h-5 w-5"
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
            Calculating...
          </span>
        ) : (
          'Calculate Risk'
        )}
      </button>

      {/* Progress indicator */}
      {isCalculating && progress && (
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" />
          <span>{progress}</span>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  )
}

