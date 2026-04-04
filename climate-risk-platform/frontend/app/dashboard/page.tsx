/**
 * Main Dashboard Page - Phase 8: Integration and Wiring
 * 
 * Integrates all components into a cohesive dashboard:
 * - TopNav with portfolio/scenario selection
 * - PortfolioStatsRow with animated metrics
 * - ClimateRiskMap with interactive markers
 * - IssuerRiskTable with sortable data
 * - Charts (LossWaterfall, SectorHeatmap)
 * - MiroFish panels (DependencyGraph, Narrative)
 * - RecommendationsPanel
 * 
 * Implements data flow from API to all components with error boundaries
 */

'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import { useDashboardStore } from '@/store/dashboardStore'
import {
  PortfolioStatsRow,
  IssuerRiskTable,
  ScenarioSelector,
  UploadPortfolioModal,
  ExportReportButton,
  ClearFilterButton,
  DependencyGraphPanel,
  MiroFishNarrativePanel,
  RecommendationsPanel,
  StatsRowLoader,
  MapLoader,
  TableLoader,
  ChartLoader,
  PortfolioEmptyState,
  RiskResultsEmptyState,
} from '@/components'
import { portfolioApi } from '@/lib/portfolio-api'
import { riskApi } from '@/lib/risk-api'
import { scenarioApi } from '@/lib/scenario-api'
import { mirofishApi } from '@/lib/mirofish-api'
import { recommendationApi } from '@/lib/recommendation-api'
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Lazy load heavy components
const ClimateRiskMap = dynamic(
  () => import('@/components/ClimateRiskMap').then(mod => ({ default: mod.ClimateRiskMap })),
  {
    loading: () => <MapLoader />,
    ssr: false,
  }
)

const LossWaterfallChart = dynamic(
  () => import('@/components/LossWaterfallChart').then(mod => ({ default: mod.LossWaterfallChart })),
  {
    loading: () => <ChartLoader />,
    ssr: false,
  }
)

const SectorHeatmap = dynamic(
  () => import('@/components/SectorHeatmap').then(mod => ({ default: mod.SectorHeatmap })),
  {
    loading: () => <ChartLoader />,
    ssr: false,
  }
)

interface Portfolio {
  id: string
  name: string
  base_currency: string
  holdings_count: number
  total_value: number
}

interface Scenario {
  id: string
  name: string
  scenario_type: string
  severity: string
}

interface RiskSummary {
  climate_var: number
  stressed_drawdown: number
  top_hotspot: string
  top_sector_risk: string
  concentration_metrics: any
}

interface RiskResults {
  holdings: any[]
  portfolio_metrics: any
}

export default function DashboardPage() {
  // State management
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null)
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [riskSummary, setRiskSummary] = useState<RiskSummary | null>(null)
  const [riskResults, setRiskResults] = useState<RiskResults | null>(null)
  const [mirofishData, setMirofishData] = useState<any>(null)
  const [recommendations, setRecommendations] = useState<any[]>([])
  const [isLoadingRisk, setIsLoadingRisk] = useState(false)
  const [isLoadingMirofish, setIsLoadingMirofish] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)

  const { filter, clearFilter } = useDashboardStore()

  // Load portfolios on mount
  useEffect(() => {
    loadPortfolios()
    loadScenarios()
  }, [])

  // Load risk data when portfolio and scenario are selected
  useEffect(() => {
    if (selectedPortfolio && selectedScenario) {
      loadRiskData()
    }
  }, [selectedPortfolio, selectedScenario])

  const loadPortfolios = async () => {
    try {
      const data = await portfolioApi.listPortfolios()
      // Fetch summary for each portfolio to get holdings_count and total_value
      const portfoliosWithSummary = await Promise.all(
        data.map(async (p) => {
          try {
            const summary = await portfolioApi.getPortfolio(p.id)
            return summary
          } catch {
            return { ...p, holdings_count: 0, total_value: 0 }
          }
        })
      )
      setPortfolios(portfoliosWithSummary)
      if (portfoliosWithSummary.length > 0 && !selectedPortfolio) {
        setSelectedPortfolio(portfoliosWithSummary[0])
      }
    } catch (err) {
      console.error('Failed to load portfolios:', err)
      setError('Failed to load portfolios')
    }
  }

  const loadScenarios = async () => {
    try {
      const templates = await scenarioApi.getTemplates()
      setScenarios(templates)
      if (templates.length > 0 && !selectedScenario) {
        setSelectedScenario(templates[0])
      }
    } catch (err) {
      console.error('Failed to load scenarios:', err)
      setError('Failed to load scenarios')
    }
  }

  const loadRiskData = async () => {
    if (!selectedPortfolio || !selectedScenario) return

    setIsLoadingRisk(true)
    setError(null)

    try {
      // Load risk summary
      const summary = await riskApi.getPortfolioSummary(selectedPortfolio.id, selectedScenario.id)
      setRiskSummary({
        climate_var: summary.climate_var,
        stressed_drawdown: summary.stressed_drawdown,
        top_hotspot: 'N/A', // Will be computed from map data
        top_sector_risk: 'N/A', // Will be computed from risk results
        concentration_metrics: null,
      })

      // Load detailed risk results
      const results = await riskApi.getRiskResults(selectedPortfolio.id, selectedScenario.id)
      setRiskResults({
        holdings: results.holdings,
        portfolio_metrics: null,
      })

      // Load recommendations
      const recs = await recommendationApi.getRecommendations(selectedPortfolio.id, selectedScenario.id)
      setRecommendations(recs)

      // Load MiroFish cascade data
      loadMirofishData()
    } catch (err) {
      console.error('Failed to load risk data:', err)
      setError('Failed to load risk data. Please try calculating risk first.')
    } finally {
      setIsLoadingRisk(false)
    }
  }

  const loadMirofishData = async () => {
    if (!selectedPortfolio || !selectedScenario) return

    setIsLoadingMirofish(true)

    try {
      const data = await mirofishApi.getSimulationResults(selectedPortfolio.id, selectedScenario.id)
      setMirofishData(data)
    } catch (err) {
      console.error('Failed to load MiroFish data:', err)
      // Don't set error - MiroFish is optional
    } finally {
      setIsLoadingMirofish(false)
    }
  }

  const handlePortfolioChange = (portfolioId: string) => {
    const portfolio = portfolios.find(p => p.id === portfolioId)
    if (portfolio) {
      setSelectedPortfolio(portfolio)
      clearFilter()
    }
  }

  const handleScenarioChange = (scenarioId: string) => {
    const scenario = scenarios.find(s => s.id === scenarioId)
    if (scenario) {
      setSelectedScenario(scenario)
      clearFilter()
    }
  }

  const handleRiskCalculated = () => {
    loadRiskData()
  }

  const handlePortfolioUploaded = () => {
    loadPortfolios()
    setShowUploadModal(false)
  }

  // Show empty state if no portfolio
  if (portfolios.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <TopNav
          portfolios={[]}
          selectedPortfolio={null}
          scenarios={[]}
          selectedScenario={null}
          onPortfolioChange={() => {}}
          onScenarioChange={() => {}}
          onUploadClick={() => setShowUploadModal(true)}
        />
        <div className="p-8">
          <PortfolioEmptyState onUploadClick={() => setShowUploadModal(true)} />
        </div>
        {showUploadModal && (
          <UploadPortfolioModal
            onClose={() => setShowUploadModal(false)}
            onSuccess={handlePortfolioUploaded}
          />
        )}
      </div>
    )
  }

  // Show empty state if no risk data
  const hasRiskData = riskSummary && riskResults

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Top Navigation */}
      <TopNav
        portfolios={portfolios}
        selectedPortfolio={selectedPortfolio}
        scenarios={scenarios}
        selectedScenario={selectedScenario}
        onPortfolioChange={handlePortfolioChange}
        onScenarioChange={handleScenarioChange}
        onUploadClick={() => setShowUploadModal(true)}
        onRiskCalculated={handleRiskCalculated}
      />

      {/* Main Dashboard Content */}
      <div className="p-8 space-y-8">
        {/* Error Display */}
        {error && (
          <div className="max-w-7xl mx-auto">
            <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 text-red-400">
              {error}
            </div>
          </div>
        )}

        {/* Filter Indicator */}
        {filter.holdingId && (
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between bg-cyan-500/10 border border-cyan-500/20 rounded-2xl p-4">
              <div className="text-cyan-400">
                Filtered by: <span className="font-semibold">{filter.assetName}</span>
                {filter.issuerName && <span className="text-slate-400"> ({filter.issuerName})</span>}
              </div>
              <ClearFilterButton />
            </div>
          </div>
        )}

        {!hasRiskData ? (
          <div className="max-w-7xl mx-auto">
            <RiskResultsEmptyState
              portfolioName={selectedPortfolio?.name}
              scenarioName={selectedScenario?.name}
            />
          </div>
        ) : (
          <div className="max-w-7xl mx-auto space-y-8">
            {/* Portfolio Stats Row */}
            <ErrorBoundary fallback={<div className="text-red-400">Failed to load statistics</div>}>
              {isLoadingRisk ? (
                <StatsRowLoader />
              ) : (
                <PortfolioStatsRow
                  portfolioValue={selectedPortfolio?.total_value || 0}
                  climateVar={riskSummary?.climate_var || 0}
                  stressedDrawdown={riskSummary?.stressed_drawdown || 0}
                  topHotspot={riskSummary?.top_hotspot || 'N/A'}
                  topSectorRisk={riskSummary?.top_sector_risk || 'N/A'}
                />
              )}
            </ErrorBoundary>

            {/* Map and Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Climate Risk Map */}
              <ErrorBoundary fallback={<div className="text-red-400">Failed to load map</div>}>
                <ClimateRiskMap
                  portfolioId={selectedPortfolio?.id || ''}
                  scenarioId={selectedScenario?.id || ''}
                />
              </ErrorBoundary>

              {/* Charts Column */}
              <div className="space-y-6">
                <ErrorBoundary fallback={<div className="text-red-400">Failed to load chart</div>}>
                  <LossWaterfallChart
                    portfolioId={selectedPortfolio?.id || ''}
                    scenarioId={selectedScenario?.id || ''}
                  />
                </ErrorBoundary>

                <ErrorBoundary fallback={<div className="text-red-400">Failed to load heatmap</div>}>
                  <SectorHeatmap
                    portfolioId={selectedPortfolio?.id || ''}
                    scenarioId={selectedScenario?.id || ''}
                  />
                </ErrorBoundary>
              </div>
            </div>

            {/* Issuer Risk Table */}
            <ErrorBoundary fallback={<div className="text-red-400">Failed to load table</div>}>
              <IssuerRiskTable
                portfolioId={selectedPortfolio?.id || ''}
                scenarioId={selectedScenario?.id || ''}
              />
            </ErrorBoundary>

            {/* MiroFish Panels Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ErrorBoundary fallback={<div className="text-red-400">Failed to load dependency graph</div>}>
                <DependencyGraphPanel
                  portfolioId={selectedPortfolio?.id || ''}
                  scenarioId={selectedScenario?.id || ''}
                  isLoading={isLoadingMirofish}
                />
              </ErrorBoundary>

              <ErrorBoundary fallback={<div className="text-red-400">Failed to load narrative</div>}>
                <MiroFishNarrativePanel
                  portfolioId={selectedPortfolio?.id || ''}
                  scenarioId={selectedScenario?.id || ''}
                  isLoading={isLoadingMirofish}
                />
              </ErrorBoundary>
            </div>

            {/* Recommendations Panel */}
            <ErrorBoundary fallback={<div className="text-red-400">Failed to load recommendations</div>}>
              <RecommendationsPanel
                recommendations={recommendations}
                isLoading={isLoadingRisk}
              />
            </ErrorBoundary>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <UploadPortfolioModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={handlePortfolioUploaded}
        />
      )}
    </div>
  )
}

/**
 * Top Navigation Component
 */
interface TopNavProps {
  portfolios: Portfolio[]
  selectedPortfolio: Portfolio | null
  scenarios: Scenario[]
  selectedScenario: Scenario | null
  onPortfolioChange: (portfolioId: string) => void
  onScenarioChange: (scenarioId: string) => void
  onUploadClick: () => void
  onRiskCalculated?: () => void
}

function TopNav({
  portfolios,
  selectedPortfolio,
  scenarios,
  selectedScenario,
  onPortfolioChange,
  onScenarioChange,
  onUploadClick,
  onRiskCalculated,
}: TopNavProps) {
  return (
    <nav className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-8 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-100">Climate Risk Intelligence</h1>
              <p className="text-xs text-slate-400">Portfolio Analysis Platform</p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-4">
            {/* Portfolio Selector */}
            {portfolios.length > 0 && (
              <select
                value={selectedPortfolio?.id || ''}
                onChange={(e) => onPortfolioChange(e.target.value)}
                className="px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-xl text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            )}

            {/* Scenario Selector */}
            {scenarios.length > 0 && selectedPortfolio && (
              <ScenarioSelector
                scenarios={scenarios}
                selectedScenario={selectedScenario}
                onScenarioChange={onScenarioChange}
                portfolioId={selectedPortfolio.id}
                onRiskCalculated={onRiskCalculated}
              />
            )}

            {/* Upload Button */}
            <button
              onClick={onUploadClick}
              className="px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-xl text-cyan-400 hover:bg-cyan-500/20 transition-colors"
            >
              Upload Portfolio
            </button>

            {/* Export Report Button */}
            {selectedPortfolio && selectedScenario && (
              <ExportReportButton
                portfolioId={selectedPortfolio.id}
                scenarioId={selectedScenario.id}
              />
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
