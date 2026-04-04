"use client"

import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface InteractiveCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode
  className?: string
  hoverScale?: number
  hoverGlow?: boolean
}

export function InteractiveCard({
  children,
  className,
  hoverScale = 1.02,
  hoverGlow = true,
  ...props
}: InteractiveCardProps) {
  return (
    <motion.div
      whileHover={{
        scale: hoverScale,
        transition: { duration: 0.2, ease: "easeOut" },
      }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "relative overflow-hidden rounded-2xl cursor-pointer",
        "bg-gradient-to-br from-slate-800/40 to-slate-900/40",
        "backdrop-blur-xl border border-slate-700/50",
        "transition-all duration-300",
        hoverGlow && "hover:border-slate-600/70 hover:shadow-lg hover:shadow-cyan-500/10",
        className
      )}
      {...props}
    >
      {hoverGlow && (
        <motion.div
          className="absolute inset-0 bg-gradient-to-br from-cyan-500/0 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300"
          initial={{ opacity: 0 }}
          whileHover={{ opacity: 0.1 }}
        />
      )}
      <div className="relative z-10">{children}</div>
    </motion.div>
  )
}
