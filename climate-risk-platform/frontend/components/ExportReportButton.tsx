/**
 * Export Report Button Component
 * 
 * Triggers executive PDF report generation and download
 */

'use client'

import { useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { generateExecutiveReport, downloadReport } from '@/lib/report-api'

interface ExportReportButtonProps {
  portfolioId: string
  scenarioId: string
  portfolioName?: string
  scenarioName?: string
  className?: string
}

export function ExportReportButton({
  portfolioId,
  scenarioId,
  portfolioName = 'portfolio',
  scenarioName = 'scenario',
  className = '',
}: ExportReportButtonProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleExport = async () => {
    setIsGenerating(true)
    setError(null)

    try {
      // Generate report
      const blob = await generateExecutiveReport({
        portfolioId,
        scenarioId,
      })

      // Generate filename
      const timestamp = new Date().toISOString().split('T')[0]
      const filename = `climate_risk_report_${portfolioName}_${scenarioName}_${timestamp}.pdf`
        .replace(/\s+/g, '_')
        .toLowerCase()

      // Trigger download
      downloadReport(blob, filename)
    } catch (err) {
      console.error('Error generating report:', err)
      setError(err instanceof Error ? err.message : 'Failed to generate report')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className={className}>
      <button
        onClick={handleExport}
        disabled={isGenerating}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg
          bg-gradient-to-r from-cyan-600 to-teal-600
          hover:from-cyan-500 hover:to-teal-500
          text-white font-medium
          transition-all duration-200
          disabled:opacity-50 disabled:cursor-not-allowed
          shadow-lg hover:shadow-xl
          ${isGenerating ? 'cursor-wait' : ''}
        `}
      >
        {isGenerating ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Generating Report...</span>
          </>
        ) : (
          <>
            <Download className="w-4 h-4" />
            <span>Export Report</span>
          </>
        )}
      </button>

      {error && (
        <div className="mt-2 p-3 rounded-lg bg-red-500/10 border border-red-500/20">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}
    </div>
  )
}
