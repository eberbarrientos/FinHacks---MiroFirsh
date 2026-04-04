/**
 * API client for executive report generation
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface ReportGenerationParams {
  portfolioId: string
  scenarioId: string
}

/**
 * Generate and download executive PDF report
 */
export async function generateExecutiveReport(
  params: ReportGenerationParams
): Promise<Blob> {
  const { portfolioId, scenarioId } = params
  
  const response = await fetch(
    `${API_BASE_URL}/api/reports/executive?portfolio_id=${portfolioId}&scenario_id=${scenarioId}`,
    {
      method: 'GET',
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to generate report' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }

  return response.blob()
}

/**
 * Trigger report download in browser
 */
export function downloadReport(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}
