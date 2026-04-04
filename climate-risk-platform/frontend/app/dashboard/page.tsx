'use client'

import { useEffect, useState, useMemo } from 'react'
import dynamic from 'next/dynamic'
import { useDashboardStore } from '@/store/dashboardStore'
import {
  PortfolioStatsRow,
  IssuerRiskTable,
  ScenarioSelector,
  ExportReportButton,
  ClearFilterButton,
  RecommendationsPanel,
  StatsRowLoader,
  MapLoader,
  ChartLoader,
  PortfolioEmptyState,
  RiskResultsEmptyState,
} from '@/components'
import { CascadeSimulationPanel } from '@/components/CascadeSimulationPanel'
import { portfolioApi } from '@/lib/portfolio-api'
import { riskApi, type HoldingRisk } from '@/lib/risk-api'
import { scenarioApi, type Scenario } from '@/lib/scenario-api'
import { recommendationApi } from '@/lib/recommendation-api'
import { ErrorBoundary } from '@/components/ErrorBoundary'

const ClimateRiskMap = dynamic(
  () => import('@/components/ClimateRiskMap').then(mod => ({ default: mod.ClimateRiskMap })),
  { loading: () => <MapLoader />, ssr: false }
)
const LossWaterfallChart = dynamic(
  () => import('@/components/LossWaterfallChart').then(mod => ({ default: mod.LossWaterfallChart })),
  { loading: () => <ChartLoader />, ssr: false }
)
const SectorHeatmap = dynamic(
  () => import('@/components/SectorHeatmap').then(mod => ({ default: mod.SectorHeatmap })),
  { loading: () => <ChartLoader />, ssr: false }
)

interface Portfolio {
  id: string; name: string; base_currency: string; holdings_count: number; total_value: number
}

export default function DashboardPage() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null)
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [riskHoldings, setRiskHoldings] = useState<HoldingRisk[]>([])
  const [portfolioValue, setPortfolioValue] = useState(0)
  const [climateVar, setClimateVar] = useState(0)
  const [stressedDrawdown, setStressedDrawdown] = useState(0)
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [isLoadingRisk, setIsLoadingRisk] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeView, setActiveView] = useState<'dashboard' | 'simulate'>('simulate')
  const { filter, clearFilter } = useDashboardStore()

  useEffect(() => { loadPortfolios(); loadScenarios() }, [])
  useEffect(() => {
    if (selectedPortfolio && selectedScenario && activeView === 'dashboard') loadRiskData()
  }, [selectedPortfolio, selectedScenario, activeView])

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

  const loadScenarios = async () => {
    try {
      const stored = await scenarioApi.list()
      if (stored.length > 0) {
        setScenarios(stored)
        if (!selectedScenario) setSelectedScenario(stored[0])
      }
    } catch { /* scenarios optional for simulate view */ }
  }

  const loadRiskData = async () => {
    if (!selectedPortfolio || !selectedScenario) return
    setIsLoadingRisk(true); setError(null)
    try {
      const summary = await riskApi.getPortfolioSummary(selectedPortfolio.id, selectedScenario.id)
      setPortfolioValue(summary.portfolio_value)
      setClimateVar(summary.climate_var)
      setStressedDrawdown(summary.stressed_drawdown)
      const results = await riskApi.getRiskResults(selectedPortfolio.id, selectedScenario.id)
      setRiskHoldings(results.holdings)
      try {
        const recs = await recommendationApi.getRecommendations(selectedPortfolio.id, selectedScenario.id)
        setRecommendations(recs)
      } catch {}
    } catch {
      setError('No risk data yet. Select a scenario and click to calculate risk first.')
      setRiskHoldings([])
    } finally { setIsLoadingRisk(false) }
  }

  // Derived chart data
  const sectorLossData = useMemo(() => {
    const map: Record<string, number> = {}
    for (const h of riskHoldings) map[h.sector] = (map[h.sector] || 0) + h.expected_loss
    return Object.entries(map).map(([sector, loss]) => ({ sector, loss })).sort((a, b) => b.loss - a.loss)
  }, [riskHoldings])

  const sectorRiskData = useMemo(() => {
    const map: Record<string, { scores: number[]; count: number; totalValue: number }> = {}
    for (const h of riskHoldings) {
      if (!map[h.sector]) map[h.sector] = { scores: [], count: 0, totalValue: 0 }
      map[h.sector].scores.push(h.combined_score)
      map[h.sector].count += 1
      map[h.sector].totalValue += h.market_value
    }
    return Object.entries(map).map(([sector, s]) => ({
      sector, risk_score: s.scores.reduce((a, b) => a + b, 0) / s.scores.length,
      holdings_count: s.count, total_exposure: s.totalValue,
    }))
  }, [riskHoldings])

  const issuerRiskData = useMemo(() => {
    const map: Record<string, { totalLoss: number; maxScore: number; count: number }> = {}
    for (const h of riskHoldings) {
      if (!map[h.issuer_name]) map[h.issuer_name] = { totalLoss: 0, maxScore: 0, count: 0 }
      map[h.issuer_name].totalLoss += h.expected_loss
      map[h.issuer_name].maxScore = Math.max(map[h.issuer_name].maxScore, h.combined_score)
      map[h.issuer_name].count += 1
    }
    return Object.entries(map)
      .map(([issuer_name, i]) => ({ issuer_name, aggregated_loss: i.totalLoss, combined_score: i.maxScore, holdings_count: i.count }))
      .sort((a, b) => b.aggregated_loss - a.aggregated_loss)
  }, [riskHoldings])

  const topHotspot = useMemo(() => {
    if (!riskHoldings.length) return 'N/A'
    const r: Record<string, number[]> = {}
    for (const h of riskHoldings) {
      const region = (h as any).state_region || h.sector
      if (!r[region]) r[region] = []
      r[region].push(h.combined_score)
    }
    let best = 'N/A', bestAvg = 0
    for (const [region, scores] of Object.entries(r)) {
      const avg = scores.reduce((a, b) => a + b, 0) / scores.length
      if (avg > bestAvg) { bestAvg = avg; best = region }
    }
    return best
  }, [riskHoldings])

  const topSectorRisk = useMemo(() => {
    if (!sectorRiskData.length) return 'N/A'
    return [...sectorRiskData].sort((a, b) => b.risk_score - a.risk_score)[0]?.sector || 'N/A'
  }, [sectorRiskData])

  const hasRiskData = riskHoldings.length > 0

  if (portfolios.length === 0 && !isLoadingRisk) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <TopNav portfolios={[]} selectedPortfolio={null} activeView={activeView} onViewChange={setActiveView} />
        <div className="p-8"><PortfolioEmptyState onUpload={() => {}} /></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <TopNav portfolios={portfolios} selectedPortfolio={selectedPortfolio}
        onPortfolioChange={id => { const p = portfolios.find(x => x.id === id); if (p) { setSelectedPortfolio(p); clearFilter() } }}
        activeView={activeView} onViewChange={setActiveView}
        scenarios={scenarios} selectedScenario={selectedScenario}
        onScenarioChange={id => { const s = scenarios.find(x => x.id === id); if (s) { setSelectedScenario(s); clearFilter() } }}
        onRiskCalculated={() => loadRiskData()} />

      <div className="p-6 space-y-6">
        {error && <div className="max-w-7xl mx-auto bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4 text-amber-400 text-sm">{error}</div>}

        {activeView === 'simulate' && selectedPortfolio && (
          <div className="max-w-7xl mx-auto">
            <CascadeSimulationPanel portfolioId={selectedPortfolio.id} />
          </div>
        )}

        {activeView === 'dashboard' && (
          <>
            {filter.holdingId && (
              <div className="max-w-7xl mx-auto flex items-center justify-between bg-cyan-500/10 border border-cyan-500/20 rounded-2xl p-4">
                <div className="text-cyan-400 text-sm">Filtered by: <span className="font-semibold">{filter.assetName}</span></div>
                <ClearFilterButton />
              </div>
            )}
            {!hasRiskData ? (
              <div className="max-w-7xl mx-auto"><RiskResultsEmptyState /></div>
            ) : (
              <div className="max-w-7xl mx-auto space-y-6">
                <ErrorBoundary fallback={<div className="text-red-400">Stats error</div>}>
                  {isLoadingRisk ? <StatsRowLoader /> : (
                    <PortfolioStatsRow portfolioValue={portfolioValue} climateVar={climateVar}
                      stressedDrawdown={stressedDrawdown} topHotspot={topHotspot} topSectorRisk={topSectorRisk} />
                  )}
                </ErrorBoundary>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <ErrorBoundary fallback={<div className="text-red-400">Map error</div>}>
                    <ClimateRiskMap portfolioId={selectedPortfolio?.id || ''} scenarioId={selectedScenario?.id || ''} />
                  </ErrorBoundary>
                  <div className="space-y-6">
                    <ErrorBoundary fallback={<div className="text-red-400">Chart error</div>}>
                      <LossWaterfallChart data={sectorLossData} />
                    </ErrorBoundary>
                    <ErrorBoundary fallback={<div className="text-red-400">Heatmap error</div>}>
                      <SectorHeatmap data={sectorRiskData} />
                    </ErrorBoundary>
                  </div>
                </div>
                <ErrorBoundary fallback={<div className="text-red-400">Table error</div>}>
                  <IssuerRiskTable data={issuerRiskData} />
                </ErrorBoundary>
                <ErrorBoundary fallback={<div className="text-red-400">Recommendations error</div>}>
                  <RecommendationsPanel recommendations={recommendations} />
                </ErrorBoundary>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

interface TopNavProps {
  portfolios: Portfolio[]
  selectedPortfolio: Portfolio | null
  onPortfolioChange?: (id: string) => void
  activeView: 'dashboard' | 'simulate'
  onViewChange: (view: 'dashboard' | 'simulate') => void
  scenarios?: Scenario[]
  selectedScenario?: Scenario | null
  onScenarioChange?: (id: string) => void
  onRiskCalculated?: () => void
}

function TopNav({ portfolios, selectedPortfolio, onPortfolioChange, activeView, onViewChange,
  scenarios, selectedScenario, onScenarioChange, onRiskCalculated }: TopNavProps) {
  return (
    <nav className="sticky top-0 z-50 border-b border-slate-800 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-base font-bold text-slate-100">Climate Risk Intelligence</h1>
              </div>
            </div>

            {/* View Toggle */}
            <div className="flex bg-slate-800/50 rounded-lg p-0.5 border border-slate-700/50">
              <button onClick={() => onViewChange('simulate')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeView === 'simulate' ? 'bg-cyan-500/20 text-cyan-400' : 'text-slate-400 hover:text-slate-200'}`}>
                ⚡ Simulate
              </button>
              <button onClick={() => onViewChange('dashboard')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeView === 'dashboard' ? 'bg-cyan-500/20 text-cyan-400' : 'text-slate-400 hover:text-slate-200'}`}>
                📊 Dashboard
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {portfolios.length > 0 && onPortfolioChange && (
              <select value={selectedPortfolio?.id || ''} onChange={e => onPortfolioChange(e.target.value)}
                className="px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500">
                {portfolios.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            )}
            {activeView === 'dashboard' && scenarios && scenarios.length > 0 && selectedPortfolio && onScenarioChange && (
              <ScenarioSelector scenarios={scenarios} selectedScenario={selectedScenario || null}
                onScenarioChange={onScenarioChange} portfolioId={selectedPortfolio.id}
                onRiskCalculated={onRiskCalculated} />
            )}
            {activeView === 'dashboard' && selectedPortfolio && selectedScenario && (
              <ExportReportButton portfolioId={selectedPortfolio.id} scenarioId={selectedScenario.id} />
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
