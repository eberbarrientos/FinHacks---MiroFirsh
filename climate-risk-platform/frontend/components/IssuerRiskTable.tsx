/**
 * IssuerRiskTable Component
 * 
 * Displays issuer-level risk metrics with sortable columns and filtering.
 * Features premium table styling with hover effects and glassmorphism.
 * 
 * Requirements: 8.1
 */

'use client'

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowUpDown, ArrowUp, ArrowDown, Filter } from 'lucide-react'
import { cn } from '@/lib/utils'
import { TableLoader } from './PremiumLoader'

export interface IssuerRiskData {
  issuer_name: string
  aggregated_loss: number
  combined_score: number
  holdings_count: number
}

interface IssuerRiskTableProps {
  data: IssuerRiskData[]
  className?: string
  isLoading?: boolean
}

type SortField = 'issuer_name' | 'aggregated_loss' | 'combined_score' | 'holdings_count'
type SortDirection = 'asc' | 'desc' | null

export function IssuerRiskTable({ data, className, isLoading = false }: IssuerRiskTableProps) {
  const [sortField, setSortField] = useState<SortField>('aggregated_loss')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  const [riskThreshold, setRiskThreshold] = useState<number>(0)

  // Show loading state
  if (isLoading) {
    return <TableLoader className={className} />
  }

  // Handle column sorting
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Toggle direction or reset
      if (sortDirection === 'asc') {
        setSortDirection('desc')
      } else if (sortDirection === 'desc') {
        setSortDirection(null)
        setSortField('aggregated_loss')
      } else {
        setSortDirection('asc')
      }
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  // Sort and filter data
  const processedData = useMemo(() => {
    let filtered = data.filter(item => item.combined_score >= riskThreshold)

    if (sortDirection) {
      filtered = [...filtered].sort((a, b) => {
        const aVal = a[sortField]
        const bVal = b[sortField]

        if (typeof aVal === 'string' && typeof bVal === 'string') {
          return sortDirection === 'asc' 
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal)
        }

        return sortDirection === 'asc' 
          ? (aVal as number) - (bVal as number)
          : (bVal as number) - (aVal as number)
      })
    }

    return filtered
  }, [data, sortField, sortDirection, riskThreshold])

  // Get risk level color
  const getRiskColor = (score: number) => {
    if (score < 40) return 'text-emerald-400'
    if (score < 70) return 'text-amber-400'
    return 'text-red-400'
  }

  const getRiskBg = (score: number) => {
    if (score < 40) return 'bg-emerald-500/10'
    if (score < 70) return 'bg-amber-500/10'
    return 'bg-red-500/10'
  }

  // Render sort icon
  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-4 h-4 opacity-40" />
    }
    if (sortDirection === 'asc') {
      return <ArrowUp className="w-4 h-4 text-cyan-400" />
    }
    if (sortDirection === 'desc') {
      return <ArrowDown className="w-4 h-4 text-cyan-400" />
    }
    return <ArrowUpDown className="w-4 h-4 opacity-40" />
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key="table-loaded"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className={cn('rounded-2xl bg-slate-800/40 backdrop-blur-xl border border-slate-700/50 p-6', className)}
      >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-slate-100">Issuer Risk Analysis</h3>
        
        {/* Filter controls */}
        <div className="flex items-center gap-3">
          <Filter className="w-4 h-4 text-slate-400" />
          <label className="text-sm text-slate-400">Min Risk Score:</label>
          <select
            value={riskThreshold}
            onChange={(e) => setRiskThreshold(Number(e.target.value))}
            className="bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
          >
            <option value={0}>All</option>
            <option value={40}>Low (40+)</option>
            <option value={70}>High (70+)</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="text-left py-3 px-4">
                <button
                  onClick={() => handleSort('issuer_name')}
                  className="flex items-center gap-2 text-sm font-semibold text-slate-300 hover:text-cyan-400 transition-colors"
                >
                  Issuer Name
                  <SortIcon field="issuer_name" />
                </button>
              </th>
              <th className="text-right py-3 px-4">
                <button
                  onClick={() => handleSort('aggregated_loss')}
                  className="flex items-center justify-end gap-2 text-sm font-semibold text-slate-300 hover:text-cyan-400 transition-colors ml-auto"
                >
                  Aggregated Loss
                  <SortIcon field="aggregated_loss" />
                </button>
              </th>
              <th className="text-center py-3 px-4">
                <button
                  onClick={() => handleSort('combined_score')}
                  className="flex items-center justify-center gap-2 text-sm font-semibold text-slate-300 hover:text-cyan-400 transition-colors mx-auto"
                >
                  Risk Score
                  <SortIcon field="combined_score" />
                </button>
              </th>
              <th className="text-center py-3 px-4">
                <button
                  onClick={() => handleSort('holdings_count')}
                  className="flex items-center justify-center gap-2 text-sm font-semibold text-slate-300 hover:text-cyan-400 transition-colors mx-auto"
                >
                  Holdings
                  <SortIcon field="holdings_count" />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {processedData.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center py-8 text-slate-400">
                  No issuers match the current filter
                </td>
              </tr>
            ) : (
              processedData.map((issuer, index) => (
                <motion.tr
                  key={issuer.issuer_name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.2, delay: index * 0.03 }}
                  className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                >
                  <td className="py-3 px-4 text-slate-200 font-medium">
                    {issuer.issuer_name}
                  </td>
                  <td className="py-3 px-4 text-right text-slate-200 font-mono">
                    ${(issuer.aggregated_loss / 1_000_000).toFixed(2)}M
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={cn(
                      'inline-flex items-center justify-center px-3 py-1 rounded-full text-sm font-semibold',
                      getRiskBg(issuer.combined_score),
                      getRiskColor(issuer.combined_score)
                    )}>
                      {issuer.combined_score.toFixed(1)}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center text-slate-300">
                    {issuer.holdings_count}
                  </td>
                </motion.tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-slate-700/50 text-sm text-slate-400">
        Showing {processedData.length} of {data.length} issuers
      </div>
    </motion.div>
    </AnimatePresence>
  )
}
