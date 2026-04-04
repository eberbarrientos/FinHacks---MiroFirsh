/**
 * SectorHeatmap Component
 * 
 * Displays risk intensity across sectors using a color gradient heatmap.
 * Uses green (low risk) to red (high risk) gradient with hover tooltips.
 * 
 * Requirements: 8.4
 */

'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface SectorRiskData {
  sector: string
  risk_score: number
  holdings_count: number
  total_exposure: number
}

interface SectorHeatmapProps {
  data: SectorRiskData[]
  className?: string
}

interface TooltipData {
  sector: string
  risk_score: number
  holdings_count: number
  total_exposure: number
  x: number
  y: number
}

export function SectorHeatmap({ data, className }: SectorHeatmapProps) {
  const [hoveredSector, setHoveredSector] = useState<TooltipData | null>(null)

  // Get color based on risk score (0-100)
  const getRiskColor = (score: number) => {
    if (score < 20) return 'bg-emerald-500'
    if (score < 40) return 'bg-green-500'
    if (score < 60) return 'bg-yellow-500'
    if (score < 80) return 'bg-orange-500'
    return 'bg-red-500'
  }

  const getRiskColorHex = (score: number) => {
    if (score < 20) return '#10b981' // emerald-500
    if (score < 40) return '#22c55e' // green-500
    if (score < 60) return '#eab308' // yellow-500
    if (score < 80) return '#f97316' // orange-500
    return '#ef4444' // red-500
  }

  const getRiskLabel = (score: number) => {
    if (score < 20) return 'Very Low'
    if (score < 40) return 'Low'
    if (score < 60) return 'Medium'
    if (score < 80) return 'High'
    return 'Very High'
  }

  // Handle mouse enter on cell
  const handleMouseEnter = (sector: SectorRiskData, event: React.MouseEvent) => {
    const rect = event.currentTarget.getBoundingClientRect()
    setHoveredSector({
      sector: sector.sector,
      risk_score: sector.risk_score,
      holdings_count: sector.holdings_count,
      total_exposure: sector.total_exposure,
      x: rect.left + rect.width / 2,
      y: rect.top,
    })
  }

  const handleMouseLeave = () => {
    setHoveredSector(null)
  }

  // Sort data by risk score for better visualization
  const sortedData = [...data].sort((a, b) => b.risk_score - a.risk_score)

  return (
    <div className={cn('rounded-2xl bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 p-6', className)}>
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-100 mb-2">Sector Risk Heatmap</h3>
        <p className="text-sm text-slate-400">
          Risk intensity across portfolio sectors
        </p>
      </div>

      {/* Heatmap Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
        {sortedData.map((sector, index) => (
          <motion.div
            key={sector.sector}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            onMouseEnter={(e) => handleMouseEnter(sector, e)}
            onMouseLeave={handleMouseLeave}
            className={cn(
              'relative rounded-xl p-4 cursor-pointer',
              'transition-all duration-300',
              'hover:scale-105 hover:shadow-xl',
              'border border-slate-700/50 hover:border-slate-600'
            )}
            style={{
              backgroundColor: `${getRiskColorHex(sector.risk_score)}20`,
            }}
          >
            {/* Sector name */}
            <div className="text-sm font-semibold text-slate-100 mb-2 truncate">
              {sector.sector}
            </div>

            {/* Risk score badge */}
            <div className="flex items-center justify-between">
              <span
                className={cn(
                  'inline-flex items-center px-2 py-1 rounded-full text-xs font-bold text-white',
                  getRiskColor(sector.risk_score)
                )}
              >
                {sector.risk_score.toFixed(0)}
              </span>
              <span className="text-xs text-slate-400">
                {sector.holdings_count} assets
              </span>
            </div>

            {/* Visual bar indicator */}
            <div className="mt-3 h-1.5 bg-slate-700/30 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${sector.risk_score}%` }}
                transition={{ duration: 0.8, delay: index * 0.05 }}
                className={cn('h-full', getRiskColor(sector.risk_score))}
              />
            </div>
          </motion.div>
        ))}
      </div>

      {/* Color scale legend */}
      <div className="mt-8 pt-6 border-t border-slate-700/50">
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-400">Risk Scale</span>
          <span className="text-xs text-slate-500">Score: 0 - 100</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-3 rounded-full bg-gradient-to-r from-emerald-500 via-yellow-500 to-red-500" />
        </div>
        <div className="flex items-center justify-between mt-2 text-xs text-slate-400">
          <span>Low Risk</span>
          <span>Medium Risk</span>
          <span>High Risk</span>
        </div>
      </div>

      {/* Tooltip */}
      <AnimatePresence>
        {hoveredSector && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ duration: 0.15 }}
            className="fixed z-50 pointer-events-none"
            style={{
              left: hoveredSector.x,
              top: hoveredSector.y - 10,
              transform: 'translate(-50%, -100%)',
            }}
          >
            <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-lg p-4 shadow-2xl min-w-[200px]">
              <div className="text-sm font-bold text-slate-100 mb-3 border-b border-slate-700 pb-2">
                {hoveredSector.sector}
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Risk Score:</span>
                  <span className={cn(
                    'text-sm font-bold',
                    hoveredSector.risk_score < 40 ? 'text-emerald-400' :
                    hoveredSector.risk_score < 70 ? 'text-amber-400' :
                    'text-red-400'
                  )}>
                    {hoveredSector.risk_score.toFixed(1)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Risk Level:</span>
                  <span className="text-sm font-semibold text-slate-200">
                    {getRiskLabel(hoveredSector.risk_score)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Holdings:</span>
                  <span className="text-sm font-mono text-slate-200">
                    {hoveredSector.holdings_count}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">Exposure:</span>
                  <span className="text-sm font-mono text-cyan-400">
                    ${(hoveredSector.total_exposure / 1_000_000).toFixed(1)}M
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
