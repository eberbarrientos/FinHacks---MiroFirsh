'use client'

import React, { useEffect, useRef, useState, useMemo } from 'react'
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
  isPortfolioHolding?: boolean
}

export interface CascadeEdge {
  source: string
  target: string
  type: string
  loss: number
  round: number
}

interface Props {
  agents: AgentNode[]
  edges: CascadeEdge[]
  onAgentSelect?: (agent: AgentNode | null) => void
  className?: string
}

const SECTOR_COLORS: Record<string, string> = {
  Energy: '#ef4444', Utilities: '#f97316', 'Real Estate': '#8b5cf6',
  Transportation: '#3b82f6', Agriculture: '#22c55e', Materials: '#94a3b8',
  Technology: '#06b6d4', Financials: '#eab308', Healthcare: '#ec4899',
  'Consumer Discretionary': '#a855f7', 'Consumer Staples': '#14b8a6',
  'Communication Services': '#6366f1',
}

const fmt = (n: number) => {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

export function AgentNetworkGraph({ agents, edges, onAgentSelect, className = '' }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [selected, setSelected] = useState<AgentNode | null>(null)
  const [hovered, setHovered] = useState<string | null>(null)
  const [dims, setDims] = useState({ w: 800, h: 560 })

  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        const r = containerRef.current.getBoundingClientRect()
        setDims({ w: r.width || 800, h: 560 })
      }
    }
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])

  // Layout: group by sector, spread in a grid-like arrangement
  const positions = useMemo(() => {
    const map = new Map<string, { x: number; y: number }>()
    if (!agents.length) return map

    // Group by sector
    const bySector = new Map<string, AgentNode[]>()
    agents.forEach(a => {
      if (!bySector.has(a.sector)) bySector.set(a.sector, [])
      bySector.get(a.sector)!.push(a)
    })

    const sectorList = Array.from(bySector.keys())
    const cols = Math.ceil(Math.sqrt(sectorList.length))
    const rows = Math.ceil(sectorList.length / cols)
    const cellW = dims.w / (cols + 0.5)
    const cellH = dims.h / (rows + 0.5)
    const pad = 30

    sectorList.forEach((sector, si) => {
      const col = si % cols
      const row = Math.floor(si / cols)
      const cx = cellW * (col + 0.75)
      const cy = cellH * (row + 0.75)
      const group = bySector.get(sector)!
      // Arrange agents in a small circle within the cell
      const r = Math.min(cellW, cellH) * 0.3
      group.forEach((agent, ai) => {
        const angle = (2 * Math.PI * ai) / group.length - Math.PI / 2
        const spread = group.length === 1 ? 0 : r
        map.set(agent.id, {
          x: cx + spread * Math.cos(angle),
          y: cy + spread * Math.sin(angle),
        })
      })
    })
    return map
  }, [agents, dims])

  // Which edges to highlight
  const highlightSet = useMemo(() => {
    const s = new Set<string>()
    if (!hovered && !selected) return s
    const focusId = hovered || selected?.id
    edges.forEach(e => {
      if (e.source === focusId || e.target === focusId) {
        s.add(e.source)
        s.add(e.target)
      }
    })
    return s
  }, [hovered, selected, edges])

  const handleClick = (a: AgentNode) => {
    const next = selected?.id === a.id ? null : a
    setSelected(next)
    onAgentSelect?.(next)
  }

  if (!agents.length) {
    return (
      <div className={`rounded-2xl bg-slate-900/50 border border-slate-700/50 p-8 ${className}`}>
        <h3 className="text-lg font-semibold text-white mb-4">🔗 Agent Network</h3>
        <div className="flex items-center justify-center h-48 text-slate-500 text-sm">
          Run a simulation to see the agent dependency network
        </div>
      </div>
    )
  }

  const focusId = hovered || selected?.id
  const hasFocus = !!focusId

  return (
    <div className={`rounded-2xl bg-slate-900/50 border border-slate-700/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-white font-semibold">🔗 Agent Network</span>
          <span className="text-slate-500">
            {agents.length} agents · {edges.length} links
          </span>
        </div>
        {/* Sector legend - compact */}
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {Array.from(new Set(agents.map(a => a.sector))).slice(0, 6).map(s => (
            <div key={s} className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full" style={{ background: SECTOR_COLORS[s] || '#64748b' }} />
              <span className="text-[10px] text-slate-500">{s}</span>
            </div>
          ))}
        </div>
      </div>

      {/* SVG Graph */}
      <div ref={containerRef} className="relative" style={{ height: dims.h }}>
        <svg
          ref={svgRef}
          width={dims.w}
          height={dims.h}
          className="w-full"
          style={{ background: 'radial-gradient(ellipse at center, #0f172a 0%, #020617 100%)' }}
        >
          {/* Subtle grid */}
          <defs>
            <pattern id="agrid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(51,65,85,0.15)" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#agrid)" />

          {/* Edges - only show relevant ones when focused */}
          {edges.map((edge, i) => {
            const sp = positions.get(edge.source)
            const tp = positions.get(edge.target)
            if (!sp || !tp) return null

            const isLit = highlightSet.has(edge.source) && highlightSet.has(edge.target)
            // When something is focused, dim unrelated edges heavily
            if (hasFocus && !isLit) return null

            return (
              <line
                key={i}
                x1={sp.x} y1={sp.y} x2={tp.x} y2={tp.y}
                stroke={isLit ? 'rgba(6,182,212,0.5)' : 'rgba(71,85,105,0.12)'}
                strokeWidth={isLit ? 1.5 : 0.5}
                strokeDasharray={edge.round > 1 ? '3,3' : undefined}
              />
            )
          })}

          {/* Nodes */}
          {agents.map(agent => {
            const pos = positions.get(agent.id)
            if (!pos) return null

            const isSel = selected?.id === agent.id
            const isHov = hovered === agent.id
            const isLit = highlightSet.has(agent.id)
            const dimmed = hasFocus && !isLit && !isSel && !isHov
            const color = SECTOR_COLORS[agent.sector] || '#64748b'
            // Size by loss magnitude (min 5, max 16)
            const baseR = Math.max(5, Math.min(16, 5 + (agent.lossPct / 2)))
            const r = isSel || isHov ? baseR + 3 : baseR
            const isPortfolio = agent.isPortfolioHolding !== false

            return (
              <g
                key={agent.id}
                style={{ cursor: 'pointer', opacity: dimmed ? 0.2 : 1, transition: 'opacity 0.2s' }}
                onClick={() => handleClick(agent)}
                onMouseEnter={() => setHovered(agent.id)}
                onMouseLeave={() => setHovered(null)}
              >
                {/* Outer ring for portfolio holdings */}
                {isPortfolio && (
                  <circle cx={pos.x} cy={pos.y} r={r + 3}
                    fill="none" stroke={color} strokeWidth={1.5}
                    strokeDasharray="2,2" opacity={0.5}
                  />
                )}
                {/* Main circle */}
                <circle cx={pos.x} cy={pos.y} r={r}
                  fill={color}
                  fillOpacity={agent.isDirectlyAffected ? 0.9 : 0.55}
                  stroke={isSel ? '#06b6d4' : isHov ? '#e2e8f0' : 'rgba(0,0,0,0.3)'}
                  strokeWidth={isSel ? 2.5 : isHov ? 1.5 : 0.5}
                />
                {/* Label - show on hover/select, or always for large nodes */}
                {(isSel || isHov || (isLit && hasFocus) || (!hasFocus && baseR > 10)) && (
                  <text
                    x={pos.x} y={pos.y - r - 5}
                    textAnchor="middle"
                    fill="#e2e8f0"
                    fontSize={isSel || isHov ? 11 : 9}
                    fontWeight={isSel ? 600 : 400}
                  >
                    {agent.name.length > 22 ? agent.name.slice(0, 20) + '…' : agent.name}
                  </text>
                )}
              </g>
            )
          })}
        </svg>

        {/* Bottom-left: shape legend */}
        <div className="absolute bottom-3 left-3 flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800/60 text-[10px] text-slate-400">
          <div className="flex items-center gap-1">
            <svg width="14" height="14"><circle cx="7" cy="7" r="5" fill="#3b82f6" opacity="0.7" stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="2,2" /></svg>
            Portfolio
          </div>
          <div className="flex items-center gap-1">
            <svg width="14" height="14"><circle cx="7" cy="7" r="5" fill="#3b82f6" opacity="0.5" /></svg>
            Dependency
          </div>
          <div className="flex items-center gap-1">
            <svg width="14" height="14"><circle cx="7" cy="7" r="7" fill="#ef4444" opacity="0.8" /></svg>
            High loss
          </div>
          <div className="flex items-center gap-1">
            <svg width="14" height="14"><circle cx="7" cy="7" r="4" fill="#22c55e" opacity="0.5" /></svg>
            Low loss
          </div>
        </div>
      </div>

      {/* Detail panel */}
      <AnimatePresence>
        {selected && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-slate-700/50 bg-slate-800/40 px-4 py-3"
          >
            <div className="flex items-center justify-between mb-2">
              <div>
                <span className="text-white font-medium text-sm">{selected.name}</span>
                <span className="text-slate-500 text-xs ml-2">
                  {selected.sector} · {selected.region}
                  {selected.isPortfolioHolding !== false ? ' · Portfolio' : ' · Dependency chain'}
                </span>
              </div>
              <button onClick={() => { setSelected(null); onAgentSelect?.(null) }}
                className="text-slate-500 hover:text-white text-xs">✕</button>
            </div>
            <div className="grid grid-cols-4 gap-3">
              {[
                { label: 'Market Value', value: fmt(selected.marketValue), color: 'text-white' },
                { label: 'Total Loss', value: fmt(selected.loss), color: 'text-red-400' },
                { label: 'Loss %', value: `${selected.lossPct.toFixed(1)}%`, color: selected.lossPct > 10 ? 'text-red-400' : selected.lossPct > 5 ? 'text-amber-400' : 'text-emerald-400' },
                { label: 'Cascade Round', value: selected.cascadeRound === 0 ? 'Direct' : `Round ${selected.cascadeRound}`, color: 'text-cyan-400' },
              ].map((s, i) => (
                <div key={i} className="text-center p-2 rounded-lg bg-slate-900/50">
                  <div className={`text-base font-bold ${s.color}`}>{s.value}</div>
                  <div className="text-[10px] text-slate-500">{s.label}</div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
