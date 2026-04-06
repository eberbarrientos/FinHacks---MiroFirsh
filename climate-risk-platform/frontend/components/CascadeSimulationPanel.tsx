'use client'

/**
 * CascadeSimulationPanel - Premium agent-based cascade simulation interface
 * 
 * Features:
 * - Natural language event input
 * - Quick scenario buttons
 * - Real-time simulation progress
 * - Agent network visualization
 * - Cascade timeline
 * - Detailed results with narrative, events, entities, and recommendations
 */

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { simulateApi, type SimulationResult, type CascadeEvent } from '@/lib/simulate-api'
import { AgentNetworkGraph, type AgentNode, type CascadeEdge } from './AgentNetworkGraph'
import { AgentCascadeTimeline, type TimelineEvent } from './AgentCascadeTimeline'
import { ContainerScroll } from '@/components/ui/container-scroll-animation'

interface Props {
  portfolioId: string
  className?: string
}

const SEVERITY_COLORS = {
  low: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  medium: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  high: 'text-red-400 bg-red-500/10 border-red-500/30',
  critical: 'text-red-300 bg-red-500/20 border-red-500/50',
  extreme: 'text-red-200 bg-red-500/30 border-red-500/60',
}

const QUICK_SCENARIOS = [
  { label: '🌀 Hurricane', region: 'Texas Gulf', desc: 'Category 5 hurricane hits the Texas Gulf Coast with 160mph winds and massive storm surge' },
  { label: '🔥 Wildfire', region: 'California', desc: 'Severe wildfire season across Northern and Southern California with multiple active fires' },
  { label: '🌊 Flood', region: 'Midwest', desc: 'Major flooding from heavy rainfall across Iowa, Illinois, and Missouri river basins' },
  { label: '🌡️ Heatwave', region: 'Southwest', desc: 'Extreme heat dome over Arizona, Nevada, and Southern California exceeding 120°F for weeks' },
  { label: '💰 Carbon Tax', region: 'National', desc: 'Federal carbon tax of $150 per ton CO2 affecting all high-emission sectors nationwide' },
  { label: '🏜️ Drought', region: 'Southwest', desc: 'Multi-year severe drought impacting water supply and agriculture in Arizona and New Mexico' },
  { label: '🌪️ Tornado', region: 'Midwest', desc: 'Severe tornado outbreak across Oklahoma, Kansas, and Nebraska with multiple EF4+ tornadoes' },
  { label: '❄️ Winter Storm', region: 'Northeast', desc: 'Major winter storm with heavy snow and ice affecting New York, New Jersey, and New England' },
]

export function CascadeSimulationPanel({ portfolioId, className }: Props) {
  const [eventText, setEventText] = useState('')
  const [severity, setSeverity] = useState('high')
  const [numRounds, setNumRounds] = useState(3)
  const [numCompanies, setNumCompanies] = useState(15)
  const [isRunning, setIsRunning] = useState(false)
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'network' | 'timeline' | 'narrative' | 'entities' | 'recs'>('network')
  const [selectedAgent, setSelectedAgent] = useState<AgentNode | null>(null)

  const runSimulation = async (description?: string) => {
    const desc = description || eventText
    if (!desc.trim()) return
    setIsRunning(true)
    setError(null)
    setResult(null)
    setSelectedAgent(null)
    try {
      const res = await simulateApi.runSimulation({
        portfolio_id: portfolioId,
        event_description: desc,
        severity,
        num_rounds: numRounds,
        num_companies: numCompanies,
      })
      setResult(res)
      setActiveTab('network')
    } catch (e: any) {
      setError(e.message || 'Simulation failed')
    } finally {
      setIsRunning(false)
    }
  }

  // Transform result data for visualization components
  const { agentNodes, cascadeEdges, timelineEvents } = useMemo(() => {
    if (!result) return { agentNodes: [], cascadeEdges: [], timelineEvents: [] }

    // Build a lookup from affected_entities for rich data
    const entityDataMap = new Map(result.affected_entities.map(e => [e.entity, e]))

    // Collect ALL unique company names that appear in cascade events (source or target)
    const allNames = new Set<string>()
    result.affected_entities.forEach(e => allNames.add(e.entity))
    result.cascade_events.forEach(e => {
      if (e.source !== 'Climate Event') allNames.add(e.source)
      if (e.target !== 'Climate Event') allNames.add(e.target)
    })

    // Build agent nodes — use affected_entity data when available, infer otherwise
    const agentMap = new Map<string, AgentNode>()

    allNames.forEach(name => {
      const entity = entityDataMap.get(name)
      // Find the earliest round this entity was involved
      const entityEvents = result.cascade_events.filter(
        e => e.target === name || e.source === name
      )
      const minRound = entityEvents.length > 0
        ? Math.min(...entityEvents.map(e => e.round))
        : 0

      if (entity) {
        agentMap.set(name, {
          id: name,
          name,
          sector: entity.sector,
          region: entity.region,
          marketValue: entity.market_value,
          riskScore: Math.min(entity.loss_pct * 10, 100),
          loss: entity.total_loss,
          lossPct: entity.loss_pct,
          dependencies: [],
          isDirectlyAffected: minRound === 0,
          cascadeRound: minRound,
          isPortfolioHolding: entity.is_portfolio_holding ?? true,
        })
      } else {
        // Source-only node: infer sector from cascade event types
        const outEvents = result.cascade_events.filter(e => e.source === name)
        const inferredSector = outEvents[0]?.type?.includes('grid') ? 'Utilities'
          : outEvents[0]?.type?.includes('insur') ? 'Financials'
          : 'Energy'
        agentMap.set(name, {
          id: name,
          name,
          sector: inferredSector,
          region: 'Unknown',
          marketValue: 0,
          riskScore: 0,
          loss: 0,
          lossPct: 0,
          dependencies: [],
          isDirectlyAffected: minRound === 0,
          cascadeRound: minRound,
          isPortfolioHolding: false,
        })
      }
    })

    // Build edges — now all sources and targets exist in agentMap
    const edges: CascadeEdge[] = result.cascade_events
      .filter(e => e.source !== 'Climate Event' && agentMap.has(e.source) && agentMap.has(e.target))
      .map(e => ({
        source: e.source,
        target: e.target,
        type: e.type,
        loss: e.loss,
        round: e.round,
      }))

    // Build timeline events
    const timeline: TimelineEvent[] = result.cascade_events.map(e => ({
      round: e.round,
      source: e.source,
      target: e.target,
      type: e.type,
      loss: e.loss,
      severity: e.severity,
      description: e.description,
    }))

    return {
      agentNodes: Array.from(agentMap.values()),
      cascadeEdges: edges,
      timelineEvents: timeline,
    }
  }, [result])

  const fmt = (n: number) => {
    if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
    if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
    if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
    return `$${n.toFixed(0)}`
  }

  return (
    <ContainerScroll
      titleComponent={
        <div className="mb-4">
          <p className="text-sm font-medium text-cyan-400 uppercase tracking-widest mb-2">
            Climate Risk Intelligence
          </p>
          <h1 className="text-4xl md:text-6xl font-bold text-white leading-tight">
            Agent Cascade{' '}
            <span className="text-cyan-400">Simulation</span>
          </h1>
          <p className="text-slate-400 text-base mt-3 max-w-xl mx-auto">
            Describe a climate event and watch how it cascades through your portfolio's company network
          </p>
        </div>
      }
    >
    <div className={`space-y-4 ${className || ''}`}>
      {/* Input Section */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-60px' }}
        transition={{ duration: 0.6 }}
        className="rounded-2xl bg-black/40 backdrop-blur-xl border border-white/10 p-5"
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center text-base shadow-lg shadow-cyan-500/20">⚡</span>
              Agent Cascade Simulation
            </h2>
            <p className="text-sm text-slate-400 mt-1 ml-11">
              Describe a climate event and watch how it cascades through your portfolio's company network
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span className="px-2 py-1 rounded-lg bg-slate-800/50 border border-slate-700/50">
              MiroFish-powered
            </span>
          </div>
        </div>

        {/* Quick scenario buttons */}
        <div className="mb-4">
          <div className="text-xs text-slate-500 mb-2">Quick Scenarios</div>
          <div className="flex flex-wrap gap-2">
            {QUICK_SCENARIOS.map((s, i) => (
              <button
                key={i}
                onClick={() => { setEventText(s.desc); runSimulation(s.desc) }}
                disabled={isRunning}
                className="group px-3 py-2 text-xs rounded-xl bg-slate-800/50 border border-slate-700/50 text-slate-300 hover:bg-slate-700/50 hover:border-slate-600/50 hover:text-slate-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span className="block font-medium">{s.label}</span>
                <span className="block text-[10px] text-slate-500 group-hover:text-slate-400">{s.region}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Custom input */}
        <div className="space-y-3">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={eventText}
                onChange={e => setEventText(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && runSimulation()}
                placeholder="Describe a climate event... e.g. 'Massive flooding in Florida coastal areas causing infrastructure damage'"
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-700/50 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 text-sm pr-24"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <select
                  value={severity}
                  onChange={e => setSeverity(e.target.value)}
                  className="px-2 py-1 bg-slate-800/80 border border-slate-700/50 rounded-lg text-slate-300 text-xs focus:outline-none"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="extreme">Extreme</option>
                </select>
              </div>
            </div>
            <button
              onClick={() => runSimulation()}
              disabled={isRunning || !eventText.trim()}
              className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm whitespace-nowrap shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30"
            >
              {isRunning ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Simulating...
                </span>
              ) : (
                'Run Simulation'
              )}
            </button>
          </div>

          {/* Advanced options */}
          <div className="flex items-center gap-4 text-xs flex-wrap">
            <label className="flex items-center gap-2 text-slate-400">
              <span>Companies:</span>
              <input
                type="range"
                min={5}
                max={40}
                value={numCompanies}
                onChange={e => setNumCompanies(Number(e.target.value))}
                className="w-24 accent-cyan-500"
              />
              <span className="text-cyan-400 font-mono w-6">{numCompanies}</span>
            </label>
            <label className="flex items-center gap-2 text-slate-400">
              <span>Cascade Rounds:</span>
              <select
                value={numRounds}
                onChange={e => setNumRounds(Number(e.target.value))}
                className="px-2 py-1 bg-slate-800/50 border border-slate-700/50 rounded-lg text-slate-300 focus:outline-none"
              >
                <option value={2}>2 rounds</option>
                <option value={3}>3 rounds</option>
                <option value={4}>4 rounds</option>
                <option value={5}>5 rounds</option>
              </select>
            </label>
          </div>
        </div>

        {error && (
          <div className="mt-3 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-sm text-red-400">
            {error}
          </div>
        )}
      </motion.div>

      {/* Loading State */}
      {isRunning && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl bg-slate-800/40 border border-slate-700/50 p-8"
        >
          <div className="flex flex-col items-center justify-center">
            <div className="relative w-16 h-16 mb-4">
              <div className="absolute inset-0 rounded-full border-4 border-slate-700/50" />
              <div className="absolute inset-0 rounded-full border-4 border-cyan-500 border-t-transparent animate-spin" />
              <div className="absolute inset-2 rounded-full border-4 border-teal-500 border-b-transparent animate-spin" style={{ animationDirection: 'reverse', animationDuration: '1.5s' }} />
            </div>
            <p className="text-slate-200 font-medium">Running Agent Cascade Simulation</p>
            <p className="text-xs text-slate-500 mt-1">Each company is analyzing the event and propagating effects through dependencies</p>
            <div className="flex items-center gap-4 mt-4 text-xs text-slate-400">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
                Building agent network
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" style={{ animationDelay: '0.3s' }} />
                Computing direct impacts
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" style={{ animationDelay: '0.6s' }} />
                Propagating cascades
              </span>
            </div>
          </div>
        </motion.div>
      )}

      {/* Results */}
      {result && !isRunning && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
          {/* Summary Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-40px' }}
            transition={{ duration: 0.5 }}
            className="grid grid-cols-2 md:grid-cols-6 gap-3"
          >
            {[
              { label: 'Direct Loss', value: fmt(result.total_direct_loss), color: 'text-amber-400', icon: '⚡' },
              { label: 'Cascade Loss', value: fmt(result.total_cascaded_loss), color: 'text-red-400', icon: '🔗' },
              { label: 'Total Loss', value: fmt(result.total_loss), color: 'text-red-300', icon: '💰' },
              { label: 'Amplification', value: `${result.cascade_amplification}%`, color: 'text-cyan-400', icon: '📈' },
              { label: 'Affected Agents', value: `${result.affected_entities.length}`, color: 'text-purple-400', icon: '🏢' },
              { label: 'Cascade Events', value: `${result.cascade_events.length}`, color: 'text-teal-400', icon: '⚡' },
            ].map((s, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05 }}
                className="rounded-xl bg-slate-800/50 border border-slate-700/50 p-3 text-center hover:bg-slate-800/70 transition-colors"
              >
                <div className="text-lg mb-1">{s.icon}</div>
                <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
                <div className="text-xs text-slate-500 mt-0.5">{s.label}</div>
              </motion.div>
            ))}
          </motion.div>

          {/* Event info banner */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-40px' }}
            transition={{ duration: 0.5 }}
            className="rounded-xl bg-slate-800/30 border border-slate-700/30 p-3 flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">
                {result.event_type === 'hurricane' ? '🌀' :
                 result.event_type === 'wildfire' ? '🔥' :
                 result.event_type === 'flood' ? '🌊' :
                 result.event_type === 'drought' ? '🏜️' :
                 result.event_type === 'heatwave' ? '🌡️' :
                 result.event_type === 'carbon_tax' ? '💰' : '⚡'}
              </span>
              <div>
                <div className="text-sm text-white font-medium">{result.scenario}</div>
                <div className="text-xs text-slate-500">
                  {result.event_type.replace(/_/g, ' ')} • {result.affected_regions.join(', ')} • {result.severity} severity
                </div>
              </div>
            </div>
            <div className="text-xs text-slate-400">
              {result.simulation_rounds} simulation rounds
            </div>
          </motion.div>

          {/* Tabs */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-40px' }}
            transition={{ duration: 0.6 }}
            className="rounded-2xl bg-black/30 backdrop-blur-md border border-white/10 overflow-visible"
          >
            <div className="flex border-b border-slate-700/50 overflow-x-auto">
              {[
                { key: 'network' as const, label: '🔗 Agent Network', count: agentNodes.length },
                { key: 'timeline' as const, label: '⏱️ Timeline', count: timelineEvents.length },
                { key: 'narrative' as const, label: '📝 Narrative', count: undefined },
                { key: 'entities' as const, label: '🏢 Affected', count: result.affected_entities.length },
                { key: 'recs' as const, label: '💡 Actions', count: result.recommendations.length },
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key)}
                  className={`flex-shrink-0 px-4 py-3 text-sm font-medium transition-colors whitespace-nowrap ${
                    activeTab === tab.key
                      ? 'text-cyan-400 bg-cyan-500/10 border-b-2 border-cyan-400'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/30'
                  }`}
                >
                  {tab.label}
                  {tab.count !== undefined && (
                    <span className="ml-1.5 px-1.5 py-0.5 rounded-full bg-slate-700/50 text-xs">
                      {tab.count}
                    </span>
                  )}
                </button>
              ))}
            </div>

            <div className="p-4">
              <AnimatePresence mode="wait">
                {activeTab === 'network' && (
                  <motion.div
                    key="network"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    {/* Title animates in first */}
                    <motion.div
                      initial={{ opacity: 0, y: 40 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                      className="text-center mb-6"
                    >
                      <p className="text-sm font-medium text-cyan-400 uppercase tracking-widest mb-2">
                        Cascade Dependency Map
                      </p>
                      <h2 className="text-3xl md:text-5xl font-bold text-white leading-tight">
                        {agentNodes.length} Agents ·{' '}
                        <span className="text-cyan-400">{cascadeEdges.length} Links</span>
                      </h2>
                      <p className="text-slate-400 text-sm mt-2">
                        Scroll to explore the full network
                      </p>
                    </motion.div>

                    {/* Graph animates in behind the title */}
                    <motion.div
                      initial={{ opacity: 0, y: 50, scale: 0.97 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ duration: 0.7, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
                      className="w-full h-[56rem] rounded-2xl overflow-hidden border border-white/10"
                    >
                      <AgentNetworkGraph
                        agents={agentNodes}
                        edges={cascadeEdges}
                        onAgentSelect={setSelectedAgent}
                        className="h-full"
                      />
                    </motion.div>
                  </motion.div>
                )}

                {activeTab === 'timeline' && (
                  <motion.div
                    key="timeline"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <AgentCascadeTimeline events={timelineEvents} />
                  </motion.div>
                )}

                {activeTab === 'narrative' && (
                  <motion.div
                    key="narrative"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="prose prose-invert prose-sm max-w-none"
                  >
                    <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                      {result.narrative}
                    </div>
                  </motion.div>
                )}

                {activeTab === 'entities' && (
                  <motion.div
                    key="entities"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-1"
                  >
                    {/* Header */}
                    <div className="flex items-center gap-3 text-xs text-slate-500 py-2 px-2 border-b border-slate-700/30 sticky top-0 bg-slate-800/90 backdrop-blur-sm z-10">
                      <span className="w-5"></span>
                      <span className="flex-1">Entity</span>
                      <span className="w-28">Sector</span>
                      <span className="w-20">Region</span>
                      <span className="w-20 text-right">Loss</span>
                      <span className="w-16 text-right">Loss %</span>
                    </div>
                    {result.affected_entities.map((e, i) => {
                      const isDynamic = !(e as any).is_portfolio_holding
                      return (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: Math.min(i * 0.02, 0.5) }}
                          className={`flex items-center gap-3 text-sm py-2 px-2 rounded-lg hover:bg-slate-700/30 transition-colors cursor-pointer ${isDynamic ? 'border-l-2 border-cyan-500/40' : ''}`}
                          onClick={() => {
                            const agent = agentNodes.find(a => a.id === e.entity)
                            if (agent) {
                              setSelectedAgent(agent)
                              setActiveTab('network')
                            }
                          }}
                        >
                          <span className="w-5 text-[10px]" title={isDynamic ? 'LLM-generated company' : 'Portfolio holding'}>
                            {isDynamic ? '🤖' : '📊'}
                          </span>
                          <span className="text-slate-200 flex-1 truncate font-medium">{e.entity}</span>
                          <span className="text-slate-500 text-xs w-28 truncate">{e.sector}</span>
                          <span className="text-slate-500 text-xs w-20 truncate">{e.region}</span>
                          <span className="text-red-400 font-mono text-xs w-20 text-right">{fmt(e.total_loss)}</span>
                          <span className={`text-xs w-16 text-right font-medium ${
                            e.loss_pct > 10 ? 'text-red-400' : e.loss_pct > 5 ? 'text-amber-400' : 'text-emerald-400'
                          }`}>
                            {e.loss_pct.toFixed(1)}%
                          </span>
                        </motion.div>
                      )
                    })}
                  </motion.div>
                )}

                {activeTab === 'recs' && (
                  <motion.div
                    key="recs"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-3"
                  >
                    {result.recommendations.map((r, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="flex items-start gap-3 p-3 rounded-xl bg-slate-800/30 border border-slate-700/30 hover:bg-slate-800/50 transition-colors"
                      >
                        <span className="shrink-0 w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500/20 to-teal-500/20 border border-cyan-500/30 text-cyan-400 flex items-center justify-center text-xs font-bold">
                          {i + 1}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wide">{r.category}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                              r.priority === 'high' ? 'bg-red-500/20 text-red-300' :
                              r.priority === 'medium' ? 'bg-amber-500/20 text-amber-300' :
                              'bg-emerald-500/20 text-emerald-300'
                            }`}>{r.priority}</span>
                          </div>
                          <p className="text-sm text-slate-200 font-medium">{r.action}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{r.rationale}</p>
                        </div>
                      </motion.div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
    </ContainerScroll>
  )
}
