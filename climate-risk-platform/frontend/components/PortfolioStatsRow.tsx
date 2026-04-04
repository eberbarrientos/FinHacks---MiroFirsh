/**
 * PortfolioStatsRow Component
 * 
 * Displays key portfolio metrics with animated counter effects and glassmorphism styling.
 * Metrics animate from 0 to final value over 1 second using Framer Motion.
 * 
 * Requirements: 8.1, 8.2, 13.2, 13.3, 13.4
 */

'use client'

import { useEffect, useState } from 'react'
import { motion, useSpring, useTransform, AnimatePresence } from 'framer-motion'
import { TrendingUp, TrendingDown, MapPin, Building2, DollarSign } from 'lucide-react'
import { cn } from '@/lib/utils'
import { StatsRowLoader } from './PremiumLoader'

interface PortfolioStatsRowProps {
  portfolioValue: number
  climateVar: number
  stressedDrawdown: number
  topHotspot: string
  topSectorRisk: string
  className?: string
  isLoading?: boolean
}

interface StatCardProps {
  label: string
  value: number | string
  icon: React.ReactNode
  format?: 'currency' | 'percentage' | 'text'
  riskLevel?: 'low' | 'medium' | 'high'
  animate?: boolean
}

function AnimatedNumber({ value, format = 'currency' }: { value: number; format?: 'currency' | 'percentage' }) {
  const spring = useSpring(0, { duration: 1000 })
  const display = useTransform(spring, (latest) => {
    if (format === 'currency') {
      return `$${(latest / 1_000_000).toFixed(1)}M`
    } else if (format === 'percentage') {
      return `${latest.toFixed(2)}%`
    }
    return latest.toFixed(0)
  })

  const [displayValue, setDisplayValue] = useState('$0.0M')

  useEffect(() => {
    spring.set(value)
  }, [spring, value])

  useEffect(() => {
    const unsubscribe = display.on('change', (latest) => {
      setDisplayValue(latest)
    })
    return () => unsubscribe()
  }, [display])

  return <span>{displayValue}</span>
}

function StatCard({ label, value, icon, format = 'text', riskLevel, animate = true }: StatCardProps) {
  // Determine risk level color
  const getRiskColor = () => {
    if (!riskLevel) return 'text-cyan-400'
    
    switch (riskLevel) {
      case 'low':
        return 'text-emerald-400'
      case 'medium':
        return 'text-amber-400'
      case 'high':
        return 'text-red-400'
      default:
        return 'text-cyan-400'
    }
  }

  const getRiskBgGlow = () => {
    if (!riskLevel) return 'from-cyan-500/10'
    
    switch (riskLevel) {
      case 'low':
        return 'from-emerald-500/10'
      case 'medium':
        return 'from-amber-500/10'
      case 'high':
        return 'from-red-500/10'
      default:
        return 'from-cyan-500/10'
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        'relative overflow-hidden rounded-2xl',
        'bg-gradient-to-br from-slate-800/40 to-slate-900/40',
        'backdrop-blur-xl border border-slate-700/50',
        'p-6 hover:border-slate-600/50 transition-all duration-300',
        'shadow-lg hover:shadow-xl'
      )}
    >
      {/* Glow effect */}
      <div className={cn(
        'absolute inset-0 bg-gradient-to-br opacity-0 hover:opacity-100 transition-opacity duration-300',
        getRiskBgGlow(),
        'to-transparent'
      )} />

      <div className="relative z-10">
        {/* Icon */}
        <div className={cn('mb-3', getRiskColor())}>
          {icon}
        </div>

        {/* Label */}
        <p className="text-sm text-slate-400 mb-2 font-medium">
          {label}
        </p>

        {/* Value */}
        <div className={cn('text-2xl font-bold', getRiskColor())}>
          {animate && typeof value === 'number' ? (
            <AnimatedNumber value={value} format={format as 'currency' | 'percentage'} />
          ) : (
            <span>
              {format === 'currency' && typeof value === 'number'
                ? `$${(value / 1_000_000).toFixed(1)}M`
                : format === 'percentage' && typeof value === 'number'
                ? `${value.toFixed(2)}%`
                : value}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export function PortfolioStatsRow({
  portfolioValue,
  climateVar,
  stressedDrawdown,
  topHotspot,
  topSectorRisk,
  className,
  isLoading = false,
}: PortfolioStatsRowProps) {
  // Show loading state
  if (isLoading) {
    return <StatsRowLoader />
  }

  // Determine risk levels based on values
  const getDrawdownRiskLevel = (drawdown: number): 'low' | 'medium' | 'high' => {
    if (drawdown < 5) return 'low'
    if (drawdown < 15) return 'medium'
    return 'high'
  }

  const getVarRiskLevel = (climateVar: number, portfolioValue: number): 'low' | 'medium' | 'high' => {
    const varPercentage = (climateVar / portfolioValue) * 100
    if (varPercentage < 5) return 'low'
    if (varPercentage < 15) return 'medium'
    return 'high'
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key="stats-loaded"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4', className)}
      >
        <StatCard
          label="Portfolio Value"
          value={portfolioValue}
          icon={<DollarSign className="w-6 h-6" />}
          format="currency"
          riskLevel="low"
        />

        <StatCard
          label="Climate VaR"
          value={climateVar}
          icon={<TrendingDown className="w-6 h-6" />}
          format="currency"
          riskLevel={getVarRiskLevel(climateVar, portfolioValue)}
        />

        <StatCard
          label="Stressed Drawdown"
          value={stressedDrawdown}
          icon={<TrendingDown className="w-6 h-6" />}
          format="percentage"
          riskLevel={getDrawdownRiskLevel(stressedDrawdown)}
        />

        <StatCard
          label="Top Hotspot"
          value={topHotspot}
          icon={<MapPin className="w-6 h-6" />}
          format="text"
          riskLevel="medium"
          animate={false}
        />

        <StatCard
          label="Top Sector Risk"
          value={topSectorRisk}
          icon={<Building2 className="w-6 h-6" />}
          format="text"
          riskLevel="medium"
          animate={false}
        />
      </motion.div>
    </AnimatePresence>
  )
}
