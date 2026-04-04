/**
 * LossWaterfallChart Component
 * 
 * Displays contribution to total loss by sector using a waterfall chart.
 * Shows cumulative loss progression with dark mode color scheme.
 * Smooth crossfade transitions when data updates (300ms max).
 * 
 * Requirements: 8.3, 8.6, 13.4
 */

'use client'

import { useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import { cn } from '@/lib/utils'
import { ChartLoader } from './PremiumLoader'

export interface SectorLossData {
  sector: string
  loss: number
}

interface LossWaterfallChartProps {
  data: SectorLossData[]
  className?: string
  isLoading?: boolean
}

interface WaterfallDataPoint {
  sector: string
  loss: number
  start: number
  end: number
  isTotal?: boolean
}

export function LossWaterfallChart({ data, className, isLoading = false }: LossWaterfallChartProps) {
  // Show loading state
  if (isLoading) {
    return <div className={className}><ChartLoader /></div>
  }

  // Transform data into waterfall format
  const waterfallData = useMemo(() => {
    const sorted = [...data].sort((a, b) => b.loss - a.loss)
    let cumulative = 0
    
    const transformed: WaterfallDataPoint[] = sorted.map(item => {
      const start = cumulative
      const end = cumulative + item.loss
      cumulative = end
      
      return {
        sector: item.sector,
        loss: item.loss,
        start,
        end,
      }
    })

    // Add total bar
    transformed.push({
      sector: 'Total',
      loss: cumulative,
      start: 0,
      end: cumulative,
      isTotal: true,
    })

    return transformed
  }, [data])

  const totalLoss = useMemo(() => {
    return data.reduce((sum, item) => sum + item.loss, 0)
  }, [data])

  // Get color based on sector risk contribution
  const getSectorColor = (loss: number, isTotal?: boolean) => {
    if (isTotal) return '#06b6d4' // cyan-500
    
    const percentage = (loss / totalLoss) * 100
    if (percentage < 10) return '#10b981' // emerald-500
    if (percentage < 25) return '#f59e0b' // amber-500
    return '#ef4444' // red-500
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null

    const data = payload[0].payload as WaterfallDataPoint

    return (
      <div className="bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-lg p-3 shadow-xl">
        <p className="text-sm font-semibold text-slate-100 mb-2">{data.sector}</p>
        <div className="space-y-1">
          <p className="text-xs text-slate-300">
            Loss: <span className="font-mono text-cyan-400">${(data.loss / 1_000_000).toFixed(2)}M</span>
          </p>
          {!data.isTotal && (
            <p className="text-xs text-slate-400">
              Contribution: {((data.loss / totalLoss) * 100).toFixed(1)}%
            </p>
          )}
        </div>
      </div>
    )
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={`chart-${data.length}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className={cn('rounded-2xl bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 p-6', className)}
      >
      {/* Header */}
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-100 mb-2">Loss Waterfall by Sector</h3>
        <p className="text-sm text-slate-400">
          Cumulative loss contribution across sectors
        </p>
      </div>

      {/* Chart */}
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="h-[400px]"
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={waterfallData}
            margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
            <XAxis
              dataKey="sector"
              angle={-45}
              textAnchor="end"
              height={80}
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              stroke="#475569"
            />
            <YAxis
              tickFormatter={(value) => `$${(value / 1_000_000).toFixed(0)}M`}
              tick={{ fill: '#94a3b8', fontSize: 12 }}
              stroke="#475569"
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(148, 163, 184, 0.1)' }} />
            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="circle"
              formatter={(value) => <span className="text-slate-300 text-sm">{value}</span>}
            />
            
            {/* Invisible bar for start position */}
            <Bar
              dataKey="start"
              stackId="stack"
              fill="transparent"
              isAnimationActive={false}
            />
            
            {/* Visible bar for loss amount */}
            <Bar
              dataKey="loss"
              stackId="stack"
              name="Sector Loss"
              radius={[8, 8, 0, 0]}
              animationDuration={300}
              animationEasing="ease-in-out"
            >
              {waterfallData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getSectorColor(entry.loss, entry.isTotal)}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Legend */}
      <div className="mt-6 flex items-center justify-center gap-6 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <span className="text-slate-400">Low Impact (&lt;10%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-500" />
          <span className="text-slate-400">Medium Impact (10-25%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-slate-400">High Impact (&gt;25%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-cyan-500" />
          <span className="text-slate-400">Total</span>
        </div>
      </div>
    </motion.div>
    </AnimatePresence>
  )
}
