import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { AetherParticleBackground } from "@/components/ui/aether-flow-hero"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Climate Risk Intelligence Platform",
  description: "Assess and visualize climate-related risks across investment portfolios",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        {/* Fixed particle canvas — renders behind all page content, no scroll breaks */}
        <AetherParticleBackground />
        {/* Page content sits above the canvas */}
        <div className="relative" style={{ zIndex: 1 }}>
          {children}
        </div>
      </body>
    </html>
  )
}
