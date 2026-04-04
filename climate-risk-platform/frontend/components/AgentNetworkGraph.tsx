'use client'

import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react'
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

const EDGE_LABELS: Record<string, string> = {
  supply_chain_disruption: 'supply chain',
  insurance_cascade: 'insurance',
  grid_failure_cascade: 'grid failure',
  direct_impact: 'direct',
  operational_disruption: 'operations',
}

const fmt = (n: number) => {
  if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

// Simple physics node for the force simulation
interface PhysicsNode {
  id: string
  x: number
  y: number
  vx: number
  vy: number
  sector: string
}

export function AgentNetworkGraph({ agents, edges, onAgentSelect, className = '' }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [selected, setSelected] = useState<AgentNode | null>(null)
  const [hovered, setHovered] = useState<string | null>(null)
  const [dims, setDims] = useState({ w: 900, h: 580 })
  const nodesRef = useRef<Map<string, PhysicsNode>>(new Map())
  const animRef = useRef<number>(0)
  const frameRef = useRef(0)

  // Resize
  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        const r = containerRef.current.getBoundingClientRect()
        setDims({ w: r.width || 900, h: 580 })
      }
    }
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])

  // Sector clusters: compute center positions for each sector
  const sectorCenters = useMemo(() => {
    const centers = new Map<string, { x: number; y: number }>()
    const bySector = new Map<string, AgentNode[]>()
    agents.forEach(a => {
      if (!bySector.has(a.sector)) bySector.set(a.sector, [])
      bySector.get(a.sector)!.push(a)
    })
    const sectorList = Array.from(bySector.keys())
    const cols = Math.ceil(Math.sqrt(sectorList.length))
    const cellW = dims.w / (cols + 0.5)
    const cellH = dims.h / (Math.ceil(sectorList.length / cols) + 0.5)
    sectorList.forEach((sector, i) => {
      centers.set(sector, {
        x: cellW * ((i % cols) + 0.75),
        y: cellH * (Math.floor(i / cols) + 0.75),
      })
    })
    return centers
  }, [agents, dims])

  // Connected nodes for the selected agent
  const connectedSet = useMemo(() => {
    const s = new Set<string>()
    const focusId = hovered || selected?.id
    if (!focusId) return s
    s.add(focusId)
    edges.forEach(e => {
      if (e.source === focusId) s.add(e.target)
      if (e.target === focusId) s.add(e.source)
    })
    return s
  }, [hovered, selected, edges])

  // Initialize physics nodes when agents change
  useEffect(() => {
    const map = new Map<string, PhysicsNode>()
    agents.forEach(a => {
      const center = sectorCenters.get(a.sector) || { x: dims.w / 2, y: dims.h / 2 }
      // Start near sector center with some jitter
      const existing = nodesRef.current.get(a.id)
      map.set(a.id, {
        id: a.id,
        x: existing?.x ?? center.x + (Math.random() - 0.5) * 80,
        y: existing?.y ?? center.y + (Math.random() - 0.5) * 80,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        sector: a.sector,
      })
    })
    nodesRef.current = map
  }, [agents, sectorCenters, dims])

  // Agent lookup
  const agentMap = useMemo(() => {
    const m = new Map<string, AgentNode>()
    agents.forEach(a => m.set(a.id, a))
    return m
  }, [agents])

  // Canvas animation loop
  useEffect(() => {
    if (!agents.length) return
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    canvas.width = dims.w * dpr
    canvas.height = dims.h * dpr
    ctx.scale(dpr, dpr)

    const focusId = hovered || selected?.id

    const tick = () => {
      frameRef.current++
      const nodes = nodesRef.current
      const t = frameRef.current * 0.02

      // Physics: gentle forces
      nodes.forEach((node) => {
        const center = sectorCenters.get(node.sector) || { x: dims.w / 2, y: dims.h / 2 }
        // Pull toward sector center
        node.vx += (center.x - node.x) * 0.003
        node.vy += (center.y - node.y) * 0.003
        // Gentle breathing motion
        node.vx += Math.sin(t + node.x * 0.01) * 0.02
        node.vy += Math.cos(t + node.y * 0.01) * 0.02
      })

      // Repulsion between nearby nodes
      const nodeArr = Array.from(nodes.values())
      for (let i = 0; i < nodeArr.length; i++) {
        for (let j = i + 1; j < nodeArr.length; j++) {
          const a = nodeArr[i], b = nodeArr[j]
          const dx = b.x - a.x, dy = b.y - a.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          if (dist < 60) {
            const force = (60 - dist) * 0.01
            const fx = (dx / dist) * force, fy = (dy / dist) * force
            a.vx -= fx; a.vy -= fy
            b.vx += fx; b.vy += fy
          }
        }
      }

      // Edge attraction (gentle)
      edges.forEach(e => {
        const sn = nodes.get(e.source), tn = nodes.get(e.target)
        if (!sn || !tn) return
        const dx = tn.x - sn.x, dy = tn.y - sn.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        if (dist > 120) {
          const f = (dist - 120) * 0.0005
          sn.vx += (dx / dist) * f
          sn.vy += (dy / dist) * f
          tn.vx -= (dx / dist) * f
          tn.vy -= (dy / dist) * f
        }
      })

      // Update positions with damping
      nodes.forEach(node => {
        node.vx *= 0.92
        node.vy *= 0.92
        node.x += node.vx
        node.y += node.vy
        // Boundary
        node.x = Math.max(30, Math.min(dims.w - 30, node.x))
        node.y = Math.max(30, Math.min(dims.h - 30, node.y))
      })

      // --- DRAW ---
      ctx.clearRect(0, 0, dims.w, dims.h)

      // Background
      const grad = ctx.createRadialGradient(dims.w / 2, dims.h / 2, 0, dims.w / 2, dims.h / 2, dims.w * 0.6)
      grad.addColorStop(0, '#0f172a')
      grad.addColorStop(1, '#020617')
      ctx.fillStyle = grad
      ctx.fillRect(0, 0, dims.w, dims.h)

      // Sector cluster labels
      sectorCenters.forEach((center, sector) => {
        ctx.fillStyle = 'rgba(148,163,184,0.15)'
        ctx.font = '600 13px system-ui'
        ctx.textAlign = 'center'
        ctx.fillText(sector, center.x, center.y - 55)
      })

      // Edges
      edges.forEach(e => {
        const sn = nodes.get(e.source), tn = nodes.get(e.target)
        if (!sn || !tn) return

        const isConnected = focusId && (connectedSet.has(e.source) && connectedSet.has(e.target))
        const isFocusEdge = focusId && (e.source === focusId || e.target === focusId)

        // When focused, hide unrelated edges
        if (focusId && !isConnected) return

        ctx.beginPath()
        ctx.moveTo(sn.x, sn.y)
        ctx.lineTo(tn.x, tn.y)

        if (isFocusEdge) {
          ctx.strokeStyle = 'rgba(6,182,212,0.5)'
          ctx.lineWidth = 2
          ctx.setLineDash([])
        } else if (isConnected) {
          ctx.strokeStyle = 'rgba(6,182,212,0.25)'
          ctx.lineWidth = 1
          ctx.setLineDash([])
        } else {
          ctx.strokeStyle = 'rgba(71,85,105,0.08)'
          ctx.lineWidth = 0.5
          ctx.setLineDash([2, 4])
        }
        ctx.stroke()
        ctx.setLineDash([])

        // Edge label — only on focused edges
        if (isFocusEdge) {
          const mx = (sn.x + tn.x) / 2, my = (sn.y + tn.y) / 2
          const label = EDGE_LABELS[e.type] || e.type.replace(/_/g, ' ')
          ctx.fillStyle = 'rgba(6,182,212,0.7)'
          ctx.font = '500 9px system-ui'
          ctx.textAlign = 'center'
          ctx.fillText(label, mx, my - 4)
          ctx.fillStyle = 'rgba(248,113,113,0.7)'
          ctx.fillText(fmt(e.loss), mx, my + 8)
        }
      })

      // Animated flow particles on focused edges
      if (focusId) {
        edges.forEach(e => {
          if (e.source !== focusId && e.target !== focusId) return
          const sn = nodes.get(e.source), tn = nodes.get(e.target)
          if (!sn || !tn) return
          const progress = ((frameRef.current * 2 + e.loss * 0.0001) % 100) / 100
          const px = sn.x + (tn.x - sn.x) * progress
          const py = sn.y + (tn.y - sn.y) * progress
          ctx.beginPath()
          ctx.arc(px, py, 2.5, 0, Math.PI * 2)
          ctx.fillStyle = 'rgba(6,182,212,0.8)'
          ctx.fill()
        })
      }

      // Nodes
      agents.forEach(agent => {
        const node = nodes.get(agent.id)
        if (!node) return

        const isSel = selected?.id === agent.id
        const isHov = hovered === agent.id
        const isConn = connectedSet.has(agent.id)
        const dimmed = focusId && !isConn && !isSel && !isHov
        const color = SECTOR_COLORS[agent.sector] || '#64748b'
        const baseR = Math.max(6, Math.min(18, 6 + agent.lossPct * 0.8))
        const r = isSel ? baseR + 4 : isHov ? baseR + 2 : baseR
        // Gentle pulse for directly affected
        const pulse = agent.isDirectlyAffected ? 1 + Math.sin(t * 2) * 0.08 : 1
        const drawR = r * pulse

        ctx.globalAlpha = dimmed ? 0.12 : 1

        // Glow for selected
        if (isSel) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, drawR + 8, 0, Math.PI * 2)
          ctx.fillStyle = color.replace(')', ',0.15)').replace('rgb', 'rgba')
          ctx.fill()
        }

        // Portfolio ring
        if (agent.isPortfolioHolding !== false) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, drawR + 3, 0, Math.PI * 2)
          ctx.strokeStyle = color
          ctx.lineWidth = 1.5
          ctx.setLineDash([3, 3])
          ctx.stroke()
          ctx.setLineDash([])
        }

        // Main circle
        ctx.beginPath()
        ctx.arc(node.x, node.y, drawR, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.globalAlpha = dimmed ? 0.12 : agent.isDirectlyAffected ? 0.9 : 0.6
        ctx.fill()

        // Border
        ctx.globalAlpha = dimmed ? 0.12 : 1
        ctx.strokeStyle = isSel ? '#06b6d4' : isHov ? '#e2e8f0' : 'rgba(0,0,0,0.2)'
        ctx.lineWidth = isSel ? 2.5 : isHov ? 1.5 : 0.5
        ctx.stroke()

        // Label
        const showLabel = isSel || isHov || (isConn && focusId) || (!focusId && baseR > 12)
        if (showLabel) {
          ctx.fillStyle = dimmed ? 'rgba(226,232,240,0.2)' : '#e2e8f0'
          ctx.font = isSel ? '600 11px system-ui' : '400 9px system-ui'
          ctx.textAlign = 'center'
          const name = agent.name.length > 20 ? agent.name.slice(0, 18) + '…' : agent.name
          ctx.fillText(name, node.x, node.y - drawR - 5)

          // Show loss on hover/select
          if (isSel || isHov) {
            ctx.fillStyle = 'rgba(248,113,113,0.9)'
            ctx.font = '600 10px system-ui'
            ctx.fillText(fmt(agent.loss), node.x, node.y + drawR + 12)
          }
        }

        ctx.globalAlpha = 1
      })

      // Legend overlay
      ctx.fillStyle = 'rgba(2,6,23,0.75)'
      ctx.fillRect(8, dims.h - 32, 280, 26)
      ctx.fillStyle = 'rgba(148,163,184,0.6)'
      ctx.font = '400 9px system-ui'
      ctx.textAlign = 'left'
      ctx.fillText('⬤ = company agent  ◌ = portfolio holding  size = loss %  click to expand', 14, dims.h - 16)

      animRef.current = requestAnimationFrame(tick)
    }

    animRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(animRef.current)
  }, [agents, edges, dims, selected, hovered, sectorCenters, connectedSet])

  // Hit testing for mouse events
  const getNodeAt = useCallback((mx: number, my: number): AgentNode | null => {
    const nodes = nodesRef.current
    let closest: AgentNode | null = null
    let closestDist = 20 // max click distance
    agents.forEach(agent => {
      const node = nodes.get(agent.id)
      if (!node) return
      const dx = node.x - mx, dy = node.y - my
      const dist = Math.sqrt(dx * dx + dy * dy)
      const r = Math.max(6, Math.min(18, 6 + agent.lossPct * 0.8))
      if (dist < r + 5 && dist < closestDist) {
        closestDist = dist
        closest = agent
      }
    })
    return closest
  }, [agents])

  const [popupPos, setPopupPos] = useState<{ x: number; y: number } | null>(null)

  const handleClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return
    const mx = e.clientX - rect.left, my = e.clientY - rect.top
    const agent = getNodeAt(mx, my)
    const next = agent && selected?.id === agent.id ? null : agent
    setSelected(next)
    setPopupPos(next ? { x: mx, y: my } : null)
    onAgentSelect?.(next)
  }, [getNodeAt, selected, onAgentSelect])

  const handleMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return
    const agent = getNodeAt(e.clientX - rect.left, e.clientY - rect.top)
    setHovered(agent?.id || null)
    if (canvasRef.current) canvasRef.current.style.cursor = agent ? 'pointer' : 'default'
  }, [getNodeAt])

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

  // Build dependency detail for selected agent
  const selectedDeps = useMemo(() => {
    if (!selected) return { incoming: [] as { name: string; type: string; loss: number }[], outgoing: [] as { name: string; type: string; loss: number }[] }
    const incoming = edges.filter(e => e.target === selected.id).map(e => ({
      name: e.source, type: e.type, loss: e.loss,
    }))
    const outgoing = edges.filter(e => e.source === selected.id).map(e => ({
      name: e.target, type: e.type, loss: e.loss,
    }))
    return { incoming, outgoing }
  }, [selected, edges])

  return (
    <div className={`rounded-2xl bg-slate-900/50 border border-slate-700/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700/50 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-white font-semibold">🔗 Agent Network</span>
          <span className="text-slate-500">{agents.length} agents · {edges.length} cascade links</span>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {Array.from(new Set(agents.map(a => a.sector))).slice(0, 7).map(s => (
            <div key={s} className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full" style={{ background: SECTOR_COLORS[s] || '#64748b' }} />
              <span className="text-[10px] text-slate-500">{s}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Canvas */}
      <div ref={containerRef} className="relative" style={{ height: dims.h }}>
        <canvas
          ref={canvasRef}
          style={{ width: dims.w, height: dims.h }}
          onClick={handleClick}
          onMouseMove={handleMove}
          onMouseLeave={() => setHovered(null)}
        />

        {/* Floating popup near clicked node */}
        <AnimatePresence>
          {selected && popupPos && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 10 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className="absolute z-20 w-72 pointer-events-auto"
              style={{
                left: Math.min(popupPos.x + 15, dims.w - 290),
                top: Math.min(popupPos.y - 20, dims.h - 300),
              }}
            >
              <div className="rounded-xl bg-slate-900/95 backdrop-blur-xl border border-slate-600/50 shadow-2xl shadow-black/50 p-3">
                {/* Header */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full" style={{ background: SECTOR_COLORS[selected.sector] || '#64748b' }} />
                    <span className="text-white font-semibold text-sm">{selected.name}</span>
                  </div>
                  <button onClick={() => { setSelected(null); setPopupPos(null); onAgentSelect?.(null) }}
                    className="text-slate-500 hover:text-white text-xs p-1 rounded hover:bg-slate-700/50">✕</button>
                </div>
                <div className="text-[10px] text-slate-500 mb-2">
                  {selected.sector} · {selected.region} · {selected.isPortfolioHolding !== false ? 'Portfolio holding' : 'Dependency chain'}
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="text-center p-1.5 rounded-lg bg-slate-800/60">
                    <div className="text-xs font-bold text-white">${fmt(selected.marketValue)}</div>
                    <div className="text-[9px] text-slate-500">Value</div>
                  </div>
                  <div className="text-center p-1.5 rounded-lg bg-slate-800/60">
                    <div className="text-xs font-bold text-red-400">${fmt(selected.loss)}</div>
                    <div className="text-[9px] text-slate-500">Loss</div>
                  </div>
                  <div className="text-center p-1.5 rounded-lg bg-slate-800/60">
                    <div className={`text-xs font-bold ${selected.lossPct > 10 ? 'text-red-400' : selected.lossPct > 5 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {selected.lossPct.toFixed(1)}%
                    </div>
                    <div className="text-[9px] text-slate-500">Loss %</div>
                  </div>
                </div>

                {/* Cascade chain */}
                {selectedDeps.incoming.length > 0 && (
                  <div className="mb-2">
                    <div className="text-[9px] text-slate-500 uppercase tracking-wider mb-1">Damaged by</div>
                    {selectedDeps.incoming.slice(0, 4).map((d, i) => (
                      <div key={i} className="flex items-center gap-1 text-[10px] py-0.5">
                        <span className="text-cyan-400">→</span>
                        <span className="text-slate-300 truncate flex-1">{d.name}</span>
                        <span className="text-slate-600">{EDGE_LABELS[d.type] || d.type.replace(/_/g, ' ')}</span>
                        <span className="text-red-400 font-mono">{fmt(d.loss)}</span>
                      </div>
                    ))}
                    {selectedDeps.incoming.length > 4 && (
                      <div className="text-[9px] text-slate-600">+{selectedDeps.incoming.length - 4} more</div>
                    )}
                  </div>
                )}
                {selectedDeps.outgoing.length > 0 && (
                  <div>
                    <div className="text-[9px] text-slate-500 uppercase tracking-wider mb-1">Cascades to</div>
                    {selectedDeps.outgoing.slice(0, 4).map((d, i) => (
                      <div key={i} className="flex items-center gap-1 text-[10px] py-0.5">
                        <span className="text-amber-400">←</span>
                        <span className="text-slate-300 truncate flex-1">{d.name}</span>
                        <span className="text-slate-600">{EDGE_LABELS[d.type] || d.type.replace(/_/g, ' ')}</span>
                        <span className="text-red-400 font-mono">{fmt(d.loss)}</span>
                      </div>
                    ))}
                    {selectedDeps.outgoing.length > 4 && (
                      <div className="text-[9px] text-slate-600">+{selectedDeps.outgoing.length - 4} more</div>
                    )}
                  </div>
                )}
                {selectedDeps.incoming.length === 0 && selectedDeps.outgoing.length === 0 && (
                  <div className="text-[10px] text-slate-600 italic">
                    {selected.cascadeRound === 0 ? 'Directly hit by climate event' : 'Affected through sector-level cascade'}
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
