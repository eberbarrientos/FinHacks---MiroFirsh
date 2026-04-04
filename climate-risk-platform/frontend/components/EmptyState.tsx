"use client"

import { motion } from "framer-motion"
import { FileX, Upload, TrendingUp, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  variant?: "portfolio" | "holdings" | "risk-results" | "generic"
  title?: string
  description?: string
  actionLabel?: string
  onAction?: () => void
  className?: string
}

export function EmptyState({
  variant = "generic",
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  // Get variant-specific content
  const getContent = () => {
    switch (variant) {
      case "portfolio":
        return {
          icon: <Upload className="w-16 h-16" />,
          title: title || "No Portfolio Loaded",
          description: description || "Upload a portfolio to get started with climate risk analysis",
          actionLabel: actionLabel || "Upload Portfolio",
          iconColor: "text-cyan-400",
          bgGradient: "from-cyan-500/10 to-transparent",
        }
      case "holdings":
        return {
          icon: <FileX className="w-16 h-16" />,
          title: title || "No Holdings Found",
          description: description || "This portfolio doesn't have any holdings yet. Upload a CSV file with your portfolio holdings.",
          actionLabel: actionLabel || "Upload Holdings",
          iconColor: "text-teal-400",
          bgGradient: "from-teal-500/10 to-transparent",
        }
      case "risk-results":
        return {
          icon: <TrendingUp className="w-16 h-16" />,
          title: title || "No Risk Results Available",
          description: description || "Run a risk calculation to see climate risk analysis for your portfolio",
          actionLabel: actionLabel || "Calculate Risk",
          iconColor: "text-emerald-400",
          bgGradient: "from-emerald-500/10 to-transparent",
        }
      default:
        return {
          icon: <AlertCircle className="w-16 h-16" />,
          title: title || "No Data Available",
          description: description || "There's no data to display at the moment",
          actionLabel: actionLabel,
          iconColor: "text-slate-400",
          bgGradient: "from-slate-500/10 to-transparent",
        }
    }
  }

  const content = getContent()

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={cn(
        "relative overflow-hidden rounded-2xl",
        "bg-gradient-to-br from-slate-800/40 to-slate-900/40",
        "backdrop-blur-xl border border-slate-700/50",
        "p-12 text-center",
        className
      )}
    >
      {/* Background glow effect */}
      <div
        className={cn(
          "absolute inset-0 bg-gradient-to-br opacity-30",
          content.bgGradient
        )}
      />

      {/* Content */}
      <div className="relative z-10 max-w-md mx-auto">
        {/* Icon */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className={cn("mb-6 flex justify-center", content.iconColor)}
        >
          {content.icon}
        </motion.div>

        {/* Title */}
        <motion.h3
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-2xl font-bold text-slate-100 mb-3"
        >
          {content.title}
        </motion.h3>

        {/* Description */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="text-slate-400 mb-6 leading-relaxed"
        >
          {content.description}
        </motion.p>

        {/* Action button */}
        {content.actionLabel && onAction && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <Button
              onClick={onAction}
              className={cn(
                "bg-gradient-to-r from-cyan-500 to-teal-500",
                "hover:from-cyan-600 hover:to-teal-600",
                "text-white font-semibold px-6 py-2.5",
                "rounded-xl shadow-lg hover:shadow-xl",
                "transition-all duration-300"
              )}
            >
              {content.actionLabel}
            </Button>
          </motion.div>
        )}

        {/* Sample portfolio hint for portfolio variant */}
        {variant === "portfolio" && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="mt-4 text-sm text-slate-500"
          >
            Don't have a portfolio? Try our{" "}
            <button
              onClick={() => {
                // This would trigger loading a sample portfolio
                console.log("Load sample portfolio")
              }}
              className="text-cyan-400 hover:text-cyan-300 underline transition-colors"
            >
              sample portfolio
            </button>
          </motion.p>
        )}
      </div>
    </motion.div>
  )
}

// Specific empty state components for common use cases
export function PortfolioEmptyState({ onUpload }: { onUpload?: () => void }) {
  return <EmptyState variant="portfolio" onAction={onUpload} />
}

export function HoldingsEmptyState({ onUpload }: { onUpload?: () => void }) {
  return <EmptyState variant="holdings" onAction={onUpload} />
}

export function RiskResultsEmptyState({ onCalculate }: { onCalculate?: () => void }) {
  return <EmptyState variant="risk-results" onAction={onCalculate} />
}
