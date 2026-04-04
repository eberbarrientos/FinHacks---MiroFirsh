'use client'

import { useEffect, useState } from 'react'
import { CascadeSimulationPanel } from '@/components/CascadeSimulationPanel'
import { portfolioApi } from '@/lib/portfolio-api'
import { PortfolioEmptyState } from '@/components'

interface Portfolio {
  id: string
  name: string
  base_currency: string
  holdings_count: number
  total_value: number
}

export default function DashboardPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => { loadPortfolios() }, [])

  const loadPortfolios = async () => {
    try {
      const data = await portfolioApi.listPortfolios()
      const withSummary = await Promise.all(
        data.map(async (p) => {
          try { return await portfolioApi.getPortfolio(p.id) }
          catch { return { ...p, holdings_count: 0, total_value: 0 } }
        })
      )
      setPortfolios(withSummary)
      if (withSummary.length > 0 && !selectedPortfolio) setSelectedPortfolio(withSummary[0])
    } catch { setError('Failed to load portfolios') }
  }

  if (portfolios.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <TopNav portfolios={[]} selectedPortfolio={null} />
        <div className="p-8"><PortfolioEmptyState onUpload={() => {}} /></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <TopNav
        portfolios={portfolios}
        selectedPortfolio={selectedPortfolio}
        onPortfolioChange={id => {
          const p = portfolios.find(x => x.id === id)
          if (p) setSelectedPortfolio(p)
        }}
      />
      <div className="p-6">
        {error && (
          <div className="max-w-7xl mx-auto mb-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4 text-amber-400 text-sm">
            {error}
          </div>
        )}
        {selectedPortfolio && (
          <div className="max-w-7xl mx-auto">
            <CascadeSimulationPanel portfolioId={selectedPortfolio.id} />
          </div>
        )}
      </div>
    </div>
  )
}

interface TopNavProps {
  portfolios: Portfolio[]
  selectedPortfolio: Portfolio | null
  onPortfolioChange?: (id: string) => void
}

function TopNav({ portfolios, selectedPortfolio, onPortfolioChange }: TopNavProps) {
  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-100">Climate Risk Intelligence</h1>
              <p className="text-[10px] text-slate-500">MiroFish-powered Agent Cascade Simulation</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {portfolios.length > 0 && onPortfolioChange && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">Portfolio:</span>
                <select
                  value={selectedPortfolio?.id || ''}
                  onChange={e => onPortfolioChange(e.target.value)}
                  className="px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                >
                  {portfolios.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            )}
            {selectedPortfolio && (
              <div className="text-xs text-slate-500 px-3 py-1.5 bg-slate-800/30 rounded-lg border border-slate-700/30">
                {selectedPortfolio.holdings_count} holdings · ${(selectedPortfolio.total_value / 1e6).toFixed(0)}M
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
