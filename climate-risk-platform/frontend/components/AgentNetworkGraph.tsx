'use client'

import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { GlowCard } from '@/components/ui/spotlight-card'

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
  if (n >= 1e9) return `${(n / 1e9).toFixed(1)}B`
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K`
  return `${n.toFixed(0)}`
}

interface PhysicsNode {
  id: string; x: number; y: number; vx: number; vy: number; sector: string
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

  useEffect(() => {
    const map = new Map<string, PhysicsNode>()
    agents.forEach(a => {
      const center = sectorCenters.get(a.sector) || { x: dims.w / 2, y: dims.h / 2 }
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

      nodes.forEach((node) => {
        const center = sectorCenters.get(node.sector) || { x: dims.w / 2, y: dims.h / 2 }
        node.vx += (center.x - node.x) * 0.003
        node.vy += (center.y - node.y) * 0.003
        node.vx += Math.sin(t + node.x * 0.01) * 0.02
        node.vy += Math.cos(t + node.y * 0.01) * 0.02
      })

      const nodeArr = Array.from(nodes.values())
      for (let i = 0; i < nodeArr.length; i++) {
        for (let j = i + 1; j < nodeArr.length; j++) {
          const a = nodeArr[i], b = nodeArr[j]
          const dx = b.x - a.x, dy = b.y - a.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          if (dist < 60) {
            const force = (60 - dist) * 0.01
            const fx = (dx / dist) * force, fy = (dy / dist) * force
            a.vx -= fx; a.vy -= fy; b.vx += fx; b.vy += fy
          }
        }
      }

      edges.forEach(e => {
        const sn = nodes.get(e.source), tn = nodes.get(e.target)
        if (!sn || !tn) return
        const dx = tn.x - sn.x, dy = tn.y - sn.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        if (dist > 120) {
          const f = (dist - 120) * 0.0005
          sn.vx += (dx / dist) * f; sn.vy += (dy / dist) * f
          tn.vx -= (dx / dist) * f; tn.vy -= (dy / dist) * f
        }
      })

      nodes.forEach(node => {
        node.vx *= 0.92; node.vy *= 0.92
        node.x += node.vx; node.y += node.vy
        node.x = Math.max(30, Math.min(dims.w - 30, node.x))
        node.y = Math.max(30, Math.min(dims.h - 30, node.y))
      })

      ctx.clearRect(0, 0, dims.w, dims.h)

      // Deep dark background with subtle grid
      ctx.fillStyle = 'rgba(2, 6, 23, 0.97)'
      ctx.fillRect(0, 0, dims.w, dims.h)

      // Subtle dot grid
      ctx.fillStyle = 'rgba(148,163,184,0.04)'
      for (let gx = 0; gx < dims.w; gx += 32) {
        for (let gy = 0; gy < dims.h; gy += 32) {
          ctx.beginPath(); ctx.arc(gx, gy, 1, 0, Math.PI * 2); ctx.fill()
        }
      }

      // Sector cluster labels with pill background
      sectorCenters.forEach((center, sector) => {
        const color = SECTOR_COLORS[sector] || '#64748b'
        const label = sector
        ctx.font = '600 11px system-ui'
        const tw = ctx.measureText(label).width
        const px = 10, py = 5
        ctx.fillStyle = `${color}18`
        ctx.beginPath()
        const rx = center.x - tw / 2 - px, ry = center.y - 68 - py
        ctx.roundRect(rx, ry, tw + px * 2, 22, 6)
        ctx.fill()
        ctx.strokeStyle = `${color}40`
        ctx.lineWidth = 1
        ctx.stroke()
        ctx.fillStyle = `${color}cc`
        ctx.textAlign = 'center'
        ctx.fillText(label, center.x, center.y - 58)
      })

      // Edges — draw all when no focus, only connected when focused
      edges.forEach(e => {
        const sn = nodes.get(e.source), tn = nodes.get(e.target)
        if (!sn || !tn) return
        const isConnected = focusId && connectedSet.has(e.source) && connectedSet.has(e.target)
        const isFocusEdge = focusId && (e.source === focusId || e.target === focusId)
        if (focusId && !isConnected) return

        const dx = tn.x - sn.x, dy = tn.y - sn.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        // Curved edges via quadratic bezier
        const mx = (sn.x + tn.x) / 2 + dy * 0.12
        const my = (sn.y + tn.y) / 2 - dx * 0.12

        ctx.beginPath()
        ctx.moveTo(sn.x, sn.y)
        ctx.quadraticCurveTo(mx, my, tn.x, tn.y)

        if (isFocusEdge) {
          ctx.strokeStyle = 'rgba(6,182,212,0.6)'
          ctx.lineWidth = 1.5
          ctx.setLineDash([])
        } else {
          ctx.strokeStyle = 'rgba(6,182,212,0.12)'
          ctx.lineWidth = 0.8
          ctx.setLineDash([3, 5])
        }
        ctx.stroke()
        ctx.setLineDash([])

        // Arrow head on focused edges
        if (isFocusEdge) {
          const angle = Math.atan2(tn.y - my, tn.x - mx)
          const ar = 6
          ctx.beginPath()
          ctx.moveTo(tn.x, tn.y)
          ctx.lineTo(tn.x - ar * Math.cos(angle - 0.4), tn.y - ar * Math.sin(angle - 0.4))
          ctx.lineTo(tn.x - ar * Math.cos(angle + 0.4), tn.y - ar * Math.sin(angle + 0.4))
          ctx.closePath()
          ctx.fillStyle = 'rgba(6,182,212,0.7)'
          ctx.fill()

          // Edge label
          ctx.fillStyle = 'rgba(6,182,212,0.8)'
          ctx.font = '500 9px system-ui'
          ctx.textAlign = 'center'
          const label = EDGE_LABELS[e.type] || e.type.replace(/_/g, ' ')
          ctx.fillText(label, mx, my - 5)
          ctx.fillStyle = 'rgba(248,113,113,0.8)'
          ctx.fillText(`$${fmt(e.loss)}`, mx, my + 7)
        }
      })

      // Flow particles on focused edges
      if (focusId) {
        edges.forEach(e => {
          if (e.source !== focusId && e.target !== focusId) return
          const sn = nodes.get(e.source), tn = nodes.get(e.target)
          if (!sn || !tn) return
          const progress = ((frameRef.current * 1.5 + e.loss * 0.0001) % 100) / 100
          const px = sn.x + (tn.x - sn.x) * progress
          const py = sn.y + (tn.y - sn.y) * progress
          const grd = ctx.createRadialGradient(px, py, 0, px, py, 4)
          grd.addColorStop(0, 'rgba(6,182,212,1)')
          grd.addColorStop(1, 'rgba(6,182,212,0)')
          ctx.beginPath(); ctx.arc(px, py, 4, 0, Math.PI * 2)
          ctx.fillStyle = grd; ctx.fill()
        })
      }

      // Nodes
      agents.forEach(agent => {
        const node = nodes.get(agent.id)
        if (!node) return
        const isSel = selected?.id === agent.id
        const isHov = hovered === agent.id
        const isConn = connectedSet.has(agent.id)
        const dimmed = !!(focusId && !isConn && !isSel && !isHov)
        const color = SECTOR_COLORS[agent.sector] || '#64748b'
        const baseR = Math.max(7, Math.min(20, 7 + agent.lossPct * 0.9))
        const r = isSel ? baseR + 5 : isHov ? baseR + 3 : baseR
        const pulse = agent.isDirectlyAffected ? 1 + Math.sin(t * 2.5) * 0.1 : 1
        const drawR = r * pulse

        ctx.globalAlpha = dimmed ? 0.1 : 1

        // Outer glow ring for selected
        if (isSel) {
          const glow = ctx.createRadialGradient(node.x, node.y, drawR, node.x, node.y, drawR + 16)
          glow.addColorStop(0, `${color}50`)
          glow.addColorStop(1, `${color}00`)
          ctx.beginPath(); ctx.arc(node.x, node.y, drawR + 16, 0, Math.PI * 2)
          ctx.fillStyle = glow; ctx.fill()
        }

        // Halo for directly affected
        if (agent.isDirectlyAffected && !dimmed) {
          ctx.beginPath(); ctx.arc(node.x, node.y, drawR + 6, 0, Math.PI * 2)
          ctx.strokeStyle = `${color}60`
          ctx.lineWidth = 1
          ctx.setLineDash([2, 3])
          ctx.stroke(); ctx.setLineDash([])
        }

        // Portfolio dashed ring
        if (agent.isPortfolioHolding !== false) {
          ctx.beginPath(); ctx.arc(node.x, node.y, drawR + 3, 0, Math.PI * 2)
          ctx.strokeStyle = `${color}90`
          ctx.lineWidth = 1.5
          ctx.setLineDash([3, 3])
          ctx.stroke(); ctx.setLineDash([])
        }

        // Node fill with radial gradient
        const nodeGrad = ctx.createRadialGradient(node.x - drawR * 0.3, node.y - drawR * 0.3, 0, node.x, node.y, drawR)
        const alpha = dimmed ? '20' : agent.isDirectlyAffected ? 'ee' : '99'
        nodeGrad.addColorStop(0, `${color}${alpha}`)
        nodeGrad.addColorStop(1, `${color}${dimmed ? '10' : '55'}`)
        ctx.beginPath(); ctx.arc(node.x, node.y, drawR, 0, Math.PI * 2)
        ctx.fillStyle = nodeGrad; ctx.fill()

        // Node border
        ctx.strokeStyle = isSel ? '#06b6d4' : isHov ? '#f1f5f9' : `${color}80`
        ctx.lineWidth = isSel ? 2 : isHov ? 1.5 : 0.8
        ctx.stroke()

        // Label
        const showLabel = isSel || isHov || (isConn && !!focusId) || (!focusId && baseR > 13)
        if (showLabel) {
          const name = agent.name.length > 20 ? agent.name.slice(0, 18) + '…' : agent.name
          // Label background pill
          ctx.font = isSel ? '600 11px system-ui' : '400 9px system-ui'
          const tw = ctx.measureText(name).width
          ctx.fillStyle = 'rgba(2,6,23,0.75)'
          ctx.beginPath()
          ctx.roundRect(node.x - tw / 2 - 4, node.y - drawR - 20, tw + 8, 14, 3)
          ctx.fill()
          ctx.fillStyle = dimmed ? 'rgba(226,232,240,0.2)' : '#e2e8f0'
          ctx.textAlign = 'center'
          ctx.fillText(name, node.x, node.y - drawR - 9)

          if (isSel || isHov) {
            ctx.fillStyle = 'rgba(248,113,113,0.95)'
            ctx.font = '600 10px system-ui'
            ctx.fillText(`$${fmt(agent.loss)}`, node.x, node.y + drawR + 14)
          }
        }

        ctx.globalAlpha = 1
      })

      // Bottom legend
      ctx.fillStyle = 'rgba(2,6,23,0.8)'
      ctx.beginPath(); ctx.roundRect(8, dims.h - 34, 310, 26, 6); ctx.fill()
      ctx.strokeStyle = 'rgba(71,85,105,0.4)'; ctx.lineWidth = 1; ctx.stroke()
      ctx.fillStyle = 'rgba(148,163,184,0.5)'
      ctx.font = '400 9px system-ui'; ctx.textAlign = 'left'
      ctx.fillText('● company agent  ◌ portfolio holding  size = loss %  click to inspect', 14, dims.h - 18)

      animRef.current = requestAnimationFrame(tick)
    }

    animRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(animRef.current)
  }, [agents, edges, dims, selected, hovered, sectorCenters, connectedSet])

  const getNodeAt = useCallback((mx: number, my: number): AgentNode | null => {
    const nodes = nodesRef.current
    let closest: AgentNode | null = null
    let closestDist = 22
    agents.forEach(agent => {
      const node = nodes.get(agent.id)
      if (!node) return
      const dx = node.x - mx, dy = node.y - my
      const dist = Math.sqrt(dx * dx + dy * dy)
      const r = Math.max(7, Math.min(20, 7 + agent.lossPct * 0.9))
      if (dist < r + 6 && dist < closestDist) { closestDist = dist; closest = agent }
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
    setSelected(next); setPopupPos(next ? { x: mx, y: my } : null)
    onAgentSelect?.(next)
  }, [getNodeAt, selected, onAgentSelect])

  const handleMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return
    const agent = getNodeAt(e.clientX - rect.left, e.clientY - rect.top)
    setHovered(agent?.id || null)
    if (canvasRef.current) canvasRef.current.style.cursor = agent ? 'pointer' : 'default'
  }, [getNodeAt])

  const selectedDeps = useMemo(() => {
    if (!selected) return { incoming: [] as { name: string; type: string; loss: number }[], outgoing: [] as { name: string; type: string; loss: number }[] }
    return {
      incoming: edges.filter(e => e.target === selected.id).map(e => ({ name: e.source, type: e.type, loss: e.loss })),
      outgoing: edges.filter(e => e.source === selected.id).map(e => ({ name: e.target, type: e.type, loss: e.loss })),
    }
  }, [selected, edges])

  if (!agents.length) {
    return (
      <GlowCard customSize className={`w-full p-8 ${className}`} glowColor="cyan">
        <div className="flex flex-col items-center justify-center h-48 gap-3">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <svg className="w-6 h-6 text-cyan-500/60" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </div>
          <p className="text-slate-500 text-sm">Run a simulation to see the agent dependency network</p>
        </div>
      </GlowCard>
    )
  }

  return (
    <GlowCard customSize className={`w-full overflow-hidden ${className}`} glowColor="cyan">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <svg className="w-3.5 h-3.5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          </div>
          <div>
            <span className="text-white font-semibold text-sm">Agent Network</span>
            <span className="ml-2 text-slate-500 text-xs">{agents.length} agents · {edges.length} cascade links</span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          {Array.from(new Set(agents.map(a => a.sector))).slice(0, 7).map(s => (
            <div key={s} className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-white/5 border border-white/5">
              <div className="w-1.5 h-1.5 rounded-full" style={{ background: SECTOR_COLORS[s] || '#64748b' }} />
              <span className="text-[10px] text-slate-400">{s}</span>
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

        {/* Node detail popup */}
        <AnimatePresence>
          {selected && popupPos && (
            <motion.div
              initial={{ opacity: 0, scale: 0.92, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.92, y: 8 }}
              transition={{ type: 'spring', stiffness: 420, damping: 28 }}
              className="absolute z-20 w-72 pointer-events-auto"
              style={{
                left: Math.min(popupPos.x + 16, dims.w - 295),
                top: Math.min(popupPos.y - 20, dims.h - 310),
              }}
            >
              {/* Popup as a mini GlowCard */}
              <div
                className="rounded-xl border border-white/10 shadow-2xl shadow-black/60 p-3 overflow-hidden"
                style={{ background: 'rgba(2,6,23,0.92)', backdropFilter: 'blur(20px)' }}
              >
                {/* Accent line */}
                <div className="absolute top-0 left-0 right-0 h-px"
                  style={{ background: `linear-gradient(90deg, transparent, ${SECTOR_COLORS[selected.sector] || '#06b6d4'}80, transparent)` }} />

                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full shadow-lg" style={{ background: SECTOR_COLORS[selected.sector] || '#64748b', boxShadow: `0 0 8px ${SECTOR_COLORS[selected.sector] || '#64748b'}80` }} />
                    <span className="text-white font-semibold text-sm">{selected.name}</span>
                  </div>
                  <button
                    onClick={() => { setSelected(null); setPopupPos(null); onAgentSelect?.(null) }}
                    className="text-slate-600 hover:text-slate-300 text-xs p-1 rounded-md hover:bg-white/5 transition-colors cursor-pointer"
                  >✕</button>
                </div>

                <div className="flex items-center gap-1.5 mb-3">
                  <span className="px-1.5 py-0.5 rounded text-[9px] font-medium" style={{ background: `${SECTOR_COLORS[selected.sector] || '#64748b'}20`, color: SECTOR_COLORS[selected.sector] || '#64748b' }}>
                    {selected.sector}
                  </span>
                  <span className="text-[10px] text-slate-500">{selected.region}</span>
                  <span className="text-[10px] text-slate-600">·</span>
                  <span className="text-[10px] text-slate-500">{selected.isPortfolioHolding !== false ? 'Portfolio' : 'Dependency'}</span>
                </div>

                <div className="grid grid-cols-3 gap-1.5 mb-3">
                  {[
                    { label: 'Value', value: `$${fmt(selected.marketValue)}`, color: 'text-slate-200' },
                    { label: 'Loss', value: `$${fmt(selected.loss)}`, color: 'text-red-400' },
                    { label: 'Loss %', value: `${selected.lossPct.toFixed(1)}%`, color: selected.lossPct > 10 ? 'text-red-400' : selected.lossPct > 5 ? 'text-amber-400' : 'text-emerald-400' },
                  ].map((s, i) => (
                    <div key={i} className="text-center p-2 rounded-lg bg-white/5 border border-white/5">
                      <div className={`text-xs font-bold ${s.color}`}>{s.value}</div>
                      <div className="text-[9px] text-slate-600 mt-0.5">{s.label}</div>
                    </div>
                  ))}
                </div>

                {selectedDeps.incoming.length > 0 && (
                  <div className="mb-2">
                    <div className="text-[9px] text-slate-600 uppercase tracking-widest mb-1.5">Damaged by</div>
                    {selectedDeps.incoming.slice(0, 4).map((d, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-[10px] py-0.5">
                        <span className="text-cyan-500">→</span>
                        <span className="text-slate-300 truncate flex-1">{d.name}</span>
                        <span className="text-slate-600 text-[9px]">{EDGE_LABELS[d.type] || d.type.replace(/_/g, ' ')}</span>
                        <span className="text-red-400 font-mono text-[9px]">${fmt(d.loss)}</span>
                      </div>
                    ))}
                    {selectedDeps.incoming.length > 4 && <div className="text-[9px] text-slate-700 mt-0.5">+{selectedDeps.incoming.length - 4} more</div>}
                  </div>
                )}

                {selectedDeps.outgoing.length > 0 && (
                  <div>
                    <div className="text-[9px] text-slate-600 uppercase tracking-widest mb-1.5">Cascades to</div>
                    {selectedDeps.outgoing.slice(0, 4).map((d, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-[10px] py-0.5">
                        <span className="text-amber-500">←</span>
                        <span className="text-slate-300 truncate flex-1">{d.name}</span>
                        <span className="text-slate-600 text-[9px]">{EDGE_LABELS[d.type] || d.type.replace(/_/g, ' ')}</span>
                        <span className="text-red-400 font-mono text-[9px]">${fmt(d.loss)}</span>
                      </div>
                    ))}
                    {selectedDeps.outgoing.length > 4 && <div className="text-[9px] text-slate-700 mt-0.5">+{selectedDeps.outgoing.length - 4} more</div>}
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
    </GlowCard>
  )
}
