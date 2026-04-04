/**
 * RecommendationsPanel Component
 * 
 * Displays prioritized portfolio optimization recommendations with filtering and sorting.
 * Features priority badges with color coding and glassmorphism styling.
 * 
 * Requirements: 6.1, 6.6
 */

'use client'

import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { 
  AlertTriangle, 
  TrendingUp, 
  Shield, 
  Eye, 
  Target,
  Filter,
  ArrowUpDown,
  ArrowUp,
  ArrowDown
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Recommendation } from '@/lib/recommendation-api'

interface RecommendationsPanelProps {
  recommendations: Recommendation[]
  className?: string
  onRecommendationClick?: (recommendation: Recommendation) => void
}

type SortField = 'priority' | 'potential_impact'
type SortDirection = 'asc' | 'desc'

const RECOMMENDATION_TYPE_CONFIG = {
  rebalance: {
    icon: TrendingUp,
    label: 'Rebalance',
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/10',
    border: 'border-cyan-500/30',
  },
  diversify: {
    icon: Target,
    label: 'Diversify',
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/30',
  },
  hedge: {
    icon: Shield,
    label: 'Hedge',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
  },
  watchlist: {
    icon: Eye,
    label: 'Watchlist',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10',
    border: 'border-amber-500/30',
  },
  insurance_review: {
    icon: Shield,
    label: 'Insurance Review',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
  },
}

const PRIORITY_CONFIG = {
  critical: {
    label: 'Critical',
    color: 'text-red-400',
    bg: 'bg-red-500/20',
    border: 'border-red-500/50',
    icon: AlertTriangle,
  },
  high: {
    label: 'High',
    color: 'text-amber-400',
    bg: 'bg-amber-500/20',
    border: 'border-amber-500/50',
    icon: AlertTriangle,
  },
  medium: {
    label: 'Medium',
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/20',
    border: 'border-yellow-500/50',
    icon: AlertTriangle,
  },
  low: {
    label: 'Low',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/20',
    border: 'border-emerald-500/50',
    icon: AlertTriangle,
  },
}

export function RecommendationsPanel({ 
  recommendations, 
  className,
  onRecommendationClick 
}: RecommendationsPanelProps) {
  const [filterType, setFilterType] = useState<string>('all')
  const [sortField, setSortField] = useState<SortField>('priority')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  // Handle sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection(field === 'priority' ? 'asc' : 'desc')
    }
  }

  // Process recommendations (filter and sort)
  const processedRecommendations = useMemo(() => {
    let filtered = recommendations

    // Filter by type
    if (filterType !== 'all') {
      filtered = filtered.filter(rec => rec.recommendation_type === filterType)
    }

    // Sort
    const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
    
    return [...filtered].sort((a, b) => {
      if (sortField === 'priority') {
        const aOrder = priorityOrder[a.priority]
        const bOrder = priorityOrder[b.priority]
        return sortDirection === 'asc' ? aOrder - bOrder : bOrder - aOrder
      } else {
        // Sort by potential_impact
        const aImpact = a.potential_impact || 0
        const bImpact = b.potential_impact || 0
        return sortDirection === 'asc' ? aImpact - bImpact : bImpact - aImpact
      }
    })
  }, [recommendations, filterType, sortField, sortDirection])

  // Get unique recommendation types for filter
  const recommendationTypes = useMemo(() => {
    const types = new Set(recommendations.map(r => r.recommendation_type))
    return Array.from(types)
  }, [recommendations])

  // Render sort icon
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-4 h-4 opacity-40" />
    }
    return sortDirection === 'asc' 
      ? <ArrowUp className="w-4 h-4 text-cyan-400" />
      : <ArrowDown className="w-4 h-4 text-cyan-400" />
  }

  return (
    <div className={cn(
      'rounded-2xl bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 p-6',
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-slate-100">Recommendations</h3>
          <p className="text-sm text-slate-400 mt-1">
            {processedRecommendations.length} actionable suggestions
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-4">
          {/* Filter by type */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
            >
              <option value="all">All Types</option>
              {recommendationTypes.map(type => (
                <option key={type} value={type}>
                  {RECOMMENDATION_TYPE_CONFIG[type as keyof typeof RECOMMENDATION_TYPE_CONFIG].label}
                </option>
              ))}
            </select>
          </div>

          {/* Sort controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleSort('priority')}
              className={cn(
                'flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors',
                sortField === 'priority'
                  ? 'bg-cyan-500/20 text-cyan-400'
                  : 'bg-slate-900/50 text-slate-400 hover:text-slate-200'
              )}
            >
              Priority
              <SortIcon field="priority" />
            </button>
            <button
              onClick={() => handleSort('potential_impact')}
              className={cn(
                'flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm transition-colors',
                sortField === 'potential_impact'
                  ? 'bg-cyan-500/20 text-cyan-400'
                  : 'bg-slate-900/50 text-slate-400 hover:text-slate-200'
              )}
            >
              Impact
              <SortIcon field="potential_impact" />
            </button>
          </div>
        </div>
      </div>

      {/* Recommendations list */}
      <div className="space-y-3">
        {processedRecommendations.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <Target className="w-12 h-12 mx-auto mb-3 opacity-40" />
            <p>No recommendations match the current filter</p>
          </div>
        ) : (
          processedRecommendations.map((recommendation, index) => {
            const typeConfig = RECOMMENDATION_TYPE_CONFIG[recommendation.recommendation_type]
            const priorityConfig = PRIORITY_CONFIG[recommendation.priority]
            const TypeIcon = typeConfig.icon
            const PriorityIcon = priorityConfig.icon

            return (
              <motion.div
                key={recommendation.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
                onClick={() => onRecommendationClick?.(recommendation)}
                className={cn(
                  'relative overflow-hidden rounded-xl',
                  'bg-gradient-to-br from-slate-800/60 to-slate-900/60',
                  'backdrop-blur-sm border',
                  typeConfig.border,
                  'p-4 hover:border-slate-600/50 transition-all duration-300',
                  'cursor-pointer hover:shadow-lg',
                  onRecommendationClick && 'hover:scale-[1.01]'
                )}
              >
                {/* Glow effect */}
                <div className={cn(
                  'absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300',
                  typeConfig.bg
                )} />

                <div className="relative z-10">
                  {/* Header row */}
                  <div className="flex items-start justify-between mb-3">
                    {/* Type badge */}
                    <div className={cn(
                      'flex items-center gap-2 px-3 py-1.5 rounded-lg',
                      typeConfig.bg,
                      'border',
                      typeConfig.border
                    )}>
                      <TypeIcon className={cn('w-4 h-4', typeConfig.color)} />
                      <span className={cn('text-sm font-semibold', typeConfig.color)}>
                        {typeConfig.label}
                      </span>
                    </div>

                    {/* Priority badge */}
                    <div className={cn(
                      'flex items-center gap-1.5 px-3 py-1.5 rounded-lg',
                      priorityConfig.bg,
                      'border',
                      priorityConfig.border
                    )}>
                      <PriorityIcon className={cn('w-4 h-4', priorityConfig.color)} />
                      <span className={cn('text-sm font-bold uppercase tracking-wide', priorityConfig.color)}>
                        {priorityConfig.label}
                      </span>
                    </div>
                  </div>

                  {/* Message */}
                  <p className="text-slate-200 leading-relaxed mb-3">
                    {recommendation.message}
                  </p>

                  {/* Footer metrics */}
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4">
                      {recommendation.affected_holdings && recommendation.affected_holdings.length > 0 && (
                        <div className="text-slate-400">
                          <span className="font-semibold text-slate-300">
                            {recommendation.affected_holdings.length}
                          </span>
                          {' '}affected holdings
                        </div>
                      )}
                    </div>

                    {recommendation.potential_impact && recommendation.potential_impact > 0 && (
                      <div className="text-right">
                        <div className="text-xs text-slate-400 mb-0.5">Potential Loss Reduction</div>
                        <div className="font-mono font-bold text-emerald-400">
                          ${(recommendation.potential_impact / 1_000_000).toFixed(2)}M
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )
          })
        )}
      </div>

      {/* Summary footer */}
      {processedRecommendations.length > 0 && (
        <div className="mt-6 pt-4 border-t border-slate-700/50">
          <div className="grid grid-cols-4 gap-4 text-center">
            {(['critical', 'high', 'medium', 'low'] as const).map(priority => {
              const count = processedRecommendations.filter(r => r.priority === priority).length
              const config = PRIORITY_CONFIG[priority]
              
              return (
                <div key={priority} className="space-y-1">
                  <div className={cn('text-2xl font-bold', config.color)}>
                    {count}
                  </div>
                  <div className="text-xs text-slate-400 uppercase tracking-wide">
                    {config.label}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
