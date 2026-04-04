'use client'

/**
 * AgentCascadeTimeline - Animated timeline showing cascade propagation
 * 
 * Shows how the climate event cascades through agents over time
 * with animated entries and real-time updates
 */

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export interface TimelineEvent {
  round: number
  source: string
  target: string
  type: string
  loss: number
  severity: string
  description?: string
}

interface AgentCascadeTimelineProps {
  events: TimelineEvent[]
  isSimulating?: boolean
  className?: string
}

const SEVERITY_STYLES = {
  low: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', dot: 'bg-emerald-500' },
  medium: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', dot: 'bg-amber-500' },
  high: { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-500' },
  critical: { bg: 'bg-red-500/20', border: 'border-red-500/50', text: 'text-red-300', dot: 'bg-red-400' },
}

const EVENT_TYPE_ICONS: Record<string, string> = {
  direct_impact: '⚡',
  supply_chain_disruption: '🔗',
  insurance_cascade: '🛡️',
  grid_failure_cascade: '⚡',
  default: '📊',
}

export function AgentCascadeTimeline({ events, isSimulating, className = '' }: AgentCascadeTimelineProps) {
  const [visibleCount, setVisibleCount] = useState(0)
  const [expandedRound, setExpandedRound] = useState<number | null>(null)

  // Animate events appearing one by one during simulation
  useEffect(() => {
    if (isSimulating) {
      setVisibleCount(0)
      const interval = setInterval(() => {
        setVisibleCount(c => {
          if (c >= events.length) {
            clearInterval(interval)
            return c
          }
          return c + 1
        })
      }, 150)
      return () => clearInterval(interval)
    } else {
      setVisibleCount(events.length)
    }
  }, [events.length, isSimulating])

  // Group events by round
  const eventsByRound = events.reduce((acc, event) => {
    if (!acc[event.round]) acc[event.round] = []
    acc[event.round].push(event)
    return acc
  }, {} as Record<number, TimelineEvent[]>)

  const rounds = Object.keys(eventsByRound).map(Number).sort((a, b) => a - b)

  const fmt = (n: number) => {
    if (n >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
    if (n >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
    if (n >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
    return `$${n.toFixed(0)}`
  }

  const visibleEvents = events.slice(0, visibleCount)

  if (!events.length) {
    return (
      <div className={`rounded-2xl bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center text-sm">⏱️</span>
          Cascade Timeline
        </h3>
        <div className="flex items-center justify-center h-32 text-slate-400">
          No cascade events yet
        </div>
      </div>
    )
  }

  return (
    <div className={`rounded-2xl bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-slate-700/50 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center text-sm">⏱️</span>
          Cascade Timeline
          {isSimulating && (
            <span className="ml-2 flex items-center gap-1 text-sm font-normal text-cyan-400">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              Simulating...
            </span>
          )}
        </h3>
        <div className="text-sm text-slate-400">
          {visibleCount} / {events.length} events
        </div>
      </div>

      {/* Timeline */}
      <div className="p-4 max-h-[400px] overflow-y-auto">
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500/50 via-slate-700/50 to-transparent" />

          {rounds.map((round, roundIndex) => {
            const roundEvents = eventsByRound[round]
            const visibleRoundEvents = roundEvents.filter(e => visibleEvents.includes(e))
            const isExpanded = expandedRound === round
            const roundLoss = roundEvents.reduce((sum, e) => sum + e.loss, 0)

            if (visibleRoundEvents.length === 0) return null

            return (
              <div key={round} className="relative mb-4">
                {/* Round header */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: roundIndex * 0.1 }}
                  className="flex items-center gap-3 mb-2 cursor-pointer"
                  onClick={() => setExpandedRound(isExpanded ? null : round)}
                >
                  {/* Round indicator */}
                  <div className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                    round === 0 ? 'bg-red-500/20 text-red-400 border border-red-500/50' : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50'
                  }`}>
                    R{round}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-white">
                        {round === 0 ? 'Direct Impact' : `Cascade Round ${round}`}
                      </span>
                      <span className="text-sm text-red-400 font-mono">{fmt(roundLoss)}</span>
                    </div>
                    <div className="text-xs text-slate-500">
                      {visibleRoundEvents.length} event{visibleRoundEvents.length !== 1 ? 's' : ''}
                    </div>
                  </div>

                  <svg
                    className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </motion.div>

                {/* Events */}
                <AnimatePresence>
                  {(isExpanded || visibleRoundEvents.length <= 3) && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="ml-11 space-y-2"
                    >
                      {visibleRoundEvents.map((event, eventIndex) => {
                        const style = SEVERITY_STYLES[event.severity as keyof typeof SEVERITY_STYLES] || SEVERITY_STYLES.medium
                        const icon = EVENT_TYPE_ICONS[event.type] || EVENT_TYPE_ICONS.default

                        return (
                          <motion.div
                            key={`${event.source}-${event.target}-${eventIndex}`}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: eventIndex * 0.05 }}
                            className={`p-3 rounded-xl ${style.bg} border ${style.border}`}
                          >
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 text-sm">
                                  <span className="text-lg">{icon}</span>
                                  <span className="text-slate-200 truncate">{event.source}</span>
                                  <svg className="w-4 h-4 text-slate-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                                  </svg>
                                  <span className="text-slate-200 truncate">{event.target}</span>
                                </div>
                                <div className="text-xs text-slate-500 mt-1">
                                  {event.type.replace(/_/g, ' ')}
                                </div>
                              </div>
                              <div className="text-right flex-shrink-0">
                                <div className={`text-sm font-mono ${style.text}`}>{fmt(event.loss)}</div>
                                <div className={`text-xs ${style.text} opacity-70`}>{event.severity}</div>
                              </div>
                            </div>
                          </motion.div>
                        )
                      })}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Collapsed summary */}
                {!isExpanded && visibleRoundEvents.length > 3 && (
                  <div className="ml-11 text-xs text-slate-500">
                    +{visibleRoundEvents.length - 3} more events (click to expand)
                  </div>
                )}
              </div>
            )
          })}

          {/* Loading indicator */}
          {isSimulating && visibleCount < events.length && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-3 ml-4"
            >
              <div className="w-8 h-8 rounded-full bg-slate-800/50 border border-slate-700/50 flex items-center justify-center">
                <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
              </div>
              <span className="text-sm text-slate-400">Processing cascade effects...</span>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}
