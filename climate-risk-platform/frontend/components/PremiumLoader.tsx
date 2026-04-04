"use client"

import { motion } from "framer-motion"
import { Skeleton } from "@/components/ui/skeleton"

interface PremiumLoaderProps {
  variant?: "dashboard" | "stats" | "table" | "chart" | "map" | "card"
  className?: string
}

export function PremiumLoader({ variant = "dashboard", className = "" }: PremiumLoaderProps) {
  if (variant === "dashboard") {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className={`space-y-6 ${className}`}
      >
        {/* Stats Row Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/50 rounded-2xl p-6"
            >
              <Skeleton className="h-4 w-24 mb-3" />
              <Skeleton className="h-8 w-32 mb-2" />
              <Skeleton className="h-3 w-16" />
            </div>
          ))}
        </div>

        {/* Map and Charts Grid Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Map Skeleton */}
          <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/50 rounded-2xl p-6">
            <Skeleton className="h-6 w-32 mb-4" />
            <Skeleton className="h-[400px] w-full rounded-xl" />
          </div>

          {/* Chart Skeleton */}
          <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/50 rounded-2xl p-6">
            <Skeleton className="h-6 w-40 mb-4" />
            <Skeleton className="h-[400px] w-full rounded-xl" />
          </div>
        </div>

        {/* Table Skeleton */}
        <div className="bg-slate-900/40 backdrop-blur-sm border border-slate-800/50 rounded-2xl p-6">
          <Skeleton className="h-6 w-48 mb-4" />
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </div>
      </motion.div>
    )
  }

  if (variant === "stats") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
        className={`bg-slate-900/40 backdrop-blur-sm border border-slate-800/50 rounded-2xl p-6 ${className}`}
      >
        <Skeleton className="h-4 w-24 mb-3" />
        <Skeleton className="h-8 w-32 mb-2" />
        <Skeleton className="h-3 w-16" />
      </motion.div>
    )
  }

  if (variant === "table") {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className={`bg-slate-900/40 backdrop-blur-sm border border-slate-800/50 rounded-2xl p-6 ${className}`}
      >
        <Skeleton className="h-6 w-48 mb-4" />
        <div className="space-y-3">
          {/* Table Header */}
          <div className="flex gap-4 pb-3 border-b border-slate-800/50">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-4 w-20" />
          </div>
          {/* Table Rows */}
          {[...Array(8)].map((_, i) => (
            <div key={i} className="flex gap-4 items-center">
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-28" />
              <Skeleton className="h-10 w-20" />
            </div>
          ))}
        </div>
      </motion.div>
    )
  }

  if (variant === "chart") {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.3 }}
        className={`bg-slate-900/40 backdrop-blur-sm border border-slate-800/50 rounded-2xl p-6 ${className}`}
      >
        <Skeleton className="h-6 w-40 mb-4" />
        <Skeleton className="h-[300px] w-full rounded-xl" />
        <div className="flex gap-4 mt-4 justify-center">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-20" />
        </div>
      </motion.div>
    )
  }

  if (variant === "map") {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className={`bg-slate-900/40 backdrop-blur-sm border border-slate-800/50 rounded-2xl p-6 ${className}`}
      >
        <div className="flex justify-between items-center mb-4">
          <Skeleton className="h-6 w-32" />
          <div className="flex gap-2">
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-8 w-24" />
          </div>
        </div>
        <Skeleton className="h-[500px] w-full rounded-xl" />
        <div className="flex gap-4 mt-4">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-32" />
        </div>
      </motion.div>
    )
  }

  if (variant === "card") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3 }}
        className={`bg-slate-900/40 backdrop-blur-sm border border-slate-800/50 rounded-2xl p-6 ${className}`}
      >
        <Skeleton className="h-5 w-3/4 mb-3" />
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-5/6" />
      </motion.div>
    )
  }

  return null
}

// Specific loader components for common use cases
export function StatsRowLoader() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
      {[...Array(5)].map((_, i) => (
        <PremiumLoader key={i} variant="stats" />
      ))}
    </div>
  )
}

export function MapLoader() {
  return <PremiumLoader variant="map" />
}

export function TableLoader() {
  return <PremiumLoader variant="table" />
}

export function ChartLoader() {
  return <PremiumLoader variant="chart" />
}

export function DashboardLoader() {
  return <PremiumLoader variant="dashboard" />
}
