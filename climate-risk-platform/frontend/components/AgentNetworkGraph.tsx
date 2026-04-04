'use client'

/**
 * AgentNetworkGraph - Premium interactive visualization of company agents and their dependencies
 * 
 * Features:
 * - Force-directed graph with smooth animations
 * - Agent cards showing company details and risk profiles
 * - Cascade flow visualization with animated edges
 * - Click to expand agent details
 * - Zoom and pan support
 */

import React, { useEffect, useRef, useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export interface AgentNode {
  id: string
  name: string
  sector: string
  region: string
  marketValue: number
  riskScore: number
  loss: number
  lossPct: number
  dependencies: string[]
  isDirectlyAffected: boolean
  cascadeRound: number
}

export interface CascadeEdge {
  source: string
  target: string
  type: string
  loss: number
  round: number
}

interface AgentNetworkGraphProps {
  agents: AgentNode[]
  edges: CascadeEdge[]
  onAgentSelect?: (agent: AgentNode | null) => void
  className?: string
}

const SECTOR_COLORS: Record<string, string> = {
  'Energy': '#ef4444',
  'Utilities': '#f97316',
  'Real Estate': '#8b5cf6',
  'Transportation': '#3b82f6',
  'Agriculture': '#22c55e',
  'Materials': '#64748b',
  'Technology': '#06b6d4',
  'Financials': '#eab308',
  'Healthcare': '#ec4899',
  'Consumer Discretionary': '#a855f7',
  'Consumer Staples': '#14b8a6',
  'Communication Services': '#6366f1',
}

const getRiskColor = (score: number) => {
  if (score >= 70) return '#ef4444'
  if (score >= 50) return '#f59e0b'
  if (score >= 30) return '#eab308'
  return '#22c55e'
}

export function AgentNetworkGraph({ agents, edges, onAgentSelect, className = '' }: AgentNetworkGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [positions, setPositions] = useState<Map<string, { x: number; y: number }>>(new Map())
  const [selectedAgent, setSelectedAgent] = useState<AgentNode | null>(null)
  const [hoveredAgent, setHoveredAgent] = useState<string | null>(null)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  // Initialize positions using force-directed layout
  useEffect(() => {
    if (!agents.length) return

    const newPositions = new Map<string, { x: number; y: number }>()
    const centerX = dimensions.width / 2
    const centerY = dimensions.height / 2
    const radius = Math.min(dimensions.width, dimensions.height) * 0.35

    // Group agents by cascade round for radial layout
    const roundGroups = new Map<number, AgentNode[]>()
    agents.forEach(agent => {
      const round = agent.cascadeRound
      if (!roundGroups.has(round)) roundGroups.set(round, [])
      roundGroups.get(round)!.push(agent)
    })

    // Position agents in concentric circles by round
    roundGroups.forEach((groupAgents, round) => {
      const ringRadius = radius * (0.3 + round * 0.25)
      groupAgents.forEach((agent, i) => {
        const angle = (2 * Math.PI * i) / groupAgents.length - Math.PI / 2
        newPositions.set(agent.id, {
          x: centerX + ringRadius * Math.cos(angle),
          y: centerY + ringRadius * Math.sin(angle),
        })
      })
    })

    setPositions(newPositions)
  }, [agents, dimensions])

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setDimensions({ width: rect.width, height: Math.max(500, rect.height) })
      }
    }
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  const handleAgentClick = (agent: AgentNode) => {
    setSelectedAgent(selectedAgent?.id === agent.id ? null : agent)
    onAgentSelect?.(selectedAgent?.id === agent.id ? null : agent)
  }

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === containerRef.current || (e.target as HTMLElement).classList.contains('graph-bg')) {
      setIsDragging(true)
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y })
    }
  }

  const handleMouseUp = () => setIsDragging(false)

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    setZoom(z => Math.max(0.5, Math.min(2, z * delta)))
  }

  const fmt = (n: number) => {
    if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
    if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
    if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
    return `$${n.toFixed(0)}`
  }

  if (!agents.length) {
    return (
      <div className={`rounded-2xl bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 p-8 ${className}`}>
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-sm">🔗</span>
          Agent Network
        </h3>
        <div className="flex items-center justify-center h-64 text-slate-400">
          Run a simulation to see the agent network
        </div>
      </div>
    )
  }

  return (
    <div className={`rounded-2xl bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-slate-700/50 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-sm">🔗</span>
          Agent Network
          <span className="text-sm font-normal text-slate-400 ml-2">({agents.length} agents, {edges.length} connections)</span>
        </h3>
        <div className="flex items-center gap-2">
          <button onClick={() => setZoom(z => Math.min(2, z * 1.2))} className="p-1.5 rounded-lg bg-slate-800/50 text-slate-400 hover:text-white transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" /></svg>
          </button>
          <button onClick={() => setZoom(z => Math.max(0.5, z * 0.8))} className="p-1.5 rounded-lg bg-slate-800/50 text-slate-400 hover:text-white transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" /></svg>
          </button>
          <button onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }) }} className="p-1.5 rounded-lg bg-slate-800/50 text-slate-400 hover:text-white transition-colors text-xs">
            Reset
          </button>
        </div>
      </div>

      {/* Graph Container */}
      <div
        ref={containerRef}
        className="relative graph-bg cursor-grab active:cursor-grabbing"
        style={{ height: '500px', background: 'radial-gradient(circle at center, rgba(15,23,42,0.8) 0%, rgba(2,6,23,0.95) 100%)' }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        {/* Grid pattern */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-20">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(100,116,139,0.3)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>

        {/* Transformed content */}
        <div
          className="absolute inset-0"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
          }}
        >
          {/* Edges */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none">
            {edges.map((edge, i) => {
              const sourcePos = positions.get(edge.source)
              const targetPos = positions.get(edge.target)
              if (!sourcePos || !targetPos) return null

              const isHighlighted = hoveredAgent === edge.source || hoveredAgent === edge.target ||
                selectedAgent?.id === edge.source || selectedAgent?.id === edge.target

              return (
                <g key={i}>
                  <line
                    x1={sourcePos.x}
                    y1={sourcePos.y}
                    x2={targetPos.x}
                    y2={targetPos.y}
                    stroke={isHighlighted ? 'rgba(6,182,212,0.6)' : 'rgba(100,116,139,0.3)'}
                    strokeWidth={isHighlighted ? 2 : 1}
                    strokeDasharray={edge.round > 1 ? '4,4' : undefined}
                  />
                  {/* Animated flow indicator */}
                  {isHighlighted && (
                    <circle r="3" fill="#06b6d4">
                      <animateMotion
                        dur="1.5s"
                        repeatCount="indefinite"
                        path={`M${sourcePos.x},${sourcePos.y} L${targetPos.x},${targetPos.y}`}
                      />
                    </circle>
                  )}
                </g>
              )
            })}
          </svg>

          {/* Agent Nodes */}
          {agents.map(agent => {
            const pos = positions.get(agent.id)
            if (!pos) return null

            const isSelected = selectedAgent?.id === agent.id
            const isHovered = hoveredAgent === agent.id
            const sectorColor = SECTOR_COLORS[agent.sector] || '#64748b'
            const riskColor = getRiskColor(agent.riskScore)

            return (
              <motion.div
                key={agent.id}
                className="absolute cursor-pointer"
                style={{
                  left: pos.x,
                  top: pos.y,
                  transform: 'translate(-50%, -50%)',
                }}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: agent.cascadeRound * 0.1, type: 'spring', stiffness: 200 }}
                onClick={() => handleAgentClick(agent)}
                onMouseEnter={() => setHoveredAgent(agent.id)}
                onMouseLeave={() => setHoveredAgent(null)}
              >
                <div
                  className={`relative transition-all duration-200 ${isSelected || isHovered ? 'z-20' : 'z-10'}`}
                  style={{ transform: isSelected || isHovered ? 'scale(1.1)' : 'scale(1)' }}
                >
                  {/* Glow effect for affected agents */}
                  {agent.isDirectlyAffected && (
                    <div
                      className="absolute inset-0 rounded-xl blur-xl opacity-50"
                      style={{ background: riskColor, transform: 'scale(1.5)' }}
                    />
                  )}

                  {/* Agent card */}
                  <div
                    className={`relative rounded-xl p-2 backdrop-blur-sm border transition-all ${
                      isSelected ? 'bg-slate-800/90 border-cyan-500/50 shadow-lg shadow-cyan-500/20' :
                      isHovered ? 'bg-slate-800/80 border-slate-600/50' :
                      'bg-slate-900/70 border-slate-700/30'
                    }`}
                    style={{ minWidth: isSelected || isHovered ? '160px' : '100px' }}
                  >
                    {/* Sector indicator */}
                    <div
                      className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-slate-900"
                      style={{ background: sectorColor }}
                    />

                    {/* Risk indicator */}
                    <div
                      className="absolute -top-1 -left-1 w-3 h-3 rounded-full border-2 border-slate-900"
                      style={{ background: riskColor }}
                    />

                    {/* Content */}
                    <div className="text-center">
                      <div className="text-xs font-medium text-white truncate max-w-[140px]">
                        {agent.name.length > 20 ? agent.name.substring(0, 18) + '...' : agent.name}
                      </div>
                      {(isSelected || isHovered) && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          className="mt-1 space-y-0.5"
                        >
                          <div className="text-[10px] text-slate-400">{agent.sector}</div>
                          <div className="text-[10px] text-slate-500">{agent.region}</div>
                          <div className="flex items-center justify-center gap-2 mt-1">
                            <span className="text-[10px] text-red-400">{fmt(agent.loss)}</span>
                            <span className="text-[10px] text-slate-500">({agent.lossPct.toFixed(1)}%)</span>
                          </div>
                        </motion.div>
                      )}
                    </div>

                    {/* Cascade round badge */}
                    {agent.cascadeRound > 0 && (
                      <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 px-1.5 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-500/30 text-[9px] text-cyan-400">
                        R{agent.cascadeRound}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 p-3 rounded-xl bg-slate-900/80 backdrop-blur-sm border border-slate-700/50 text-xs">
          <div className="text-slate-400 mb-2 font-medium">Risk Level</div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-slate-500">Low</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-yellow-500" />
              <span className="text-slate-500">Med</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-amber-500" />
              <span className="text-slate-500">High</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-red-500" />
              <span className="text-slate-500">Critical</span>
            </div>
          </div>
        </div>

        {/* Round indicator */}
        <div className="absolute bottom-4 right-4 p-3 rounded-xl bg-slate-900/80 backdrop-blur-sm border border-slate-700/50 text-xs">
          <div className="text-slate-400 mb-2 font-medium">Cascade Rounds</div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <div className="w-4 h-4 rounded bg-red-500/30 border border-red-500/50 flex items-center justify-center text-[9px] text-red-400">0</div>
              <span className="text-slate-500">Direct</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-4 h-4 rounded bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-[9px] text-cyan-400">1+</div>
              <span className="text-slate-500">Cascade</span>
            </div>
          </div>
        </div>
      </div>

      {/* Selected Agent Detail Panel */}
      <AnimatePresence>
        {selectedAgent && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="p-4 border-t border-slate-700/50 bg-slate-800/30"
          >
            <div className="flex items-start justify-between">
              <div>
                <h4 className="text-white font-medium">{selectedAgent.name}</h4>
                <p className="text-sm text-slate-400">{selectedAgent.sector} • {selectedAgent.region}</p>
              </div>
              <button
                onClick={() => { setSelectedAgent(null); onAgentSelect?.(null) }}
                className="p-1 rounded-lg hover:bg-slate-700/50 text-slate-400 hover:text-white transition-colors"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="grid grid-cols-4 gap-4 mt-3">
              <div className="text-center p-2 rounded-lg bg-slate-900/50">
                <div className="text-lg font-bold text-white">{fmt(selectedAgent.marketValue)}</div>
                <div className="text-xs text-slate-500">Market Value</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-slate-900/50">
                <div className="text-lg font-bold text-red-400">{fmt(selectedAgent.loss)}</div>
                <div className="text-xs text-slate-500">Total Loss</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-slate-900/50">
                <div className="text-lg font-bold" style={{ color: getRiskColor(selectedAgent.riskScore) }}>{selectedAgent.riskScore.toFixed(0)}</div>
                <div className="text-xs text-slate-500">Risk Score</div>
              </div>
              <div className="text-center p-2 rounded-lg bg-slate-900/50">
                <div className="text-lg font-bold text-cyan-400">R{selectedAgent.cascadeRound}</div>
                <div className="text-xs text-slate-500">Cascade Round</div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
