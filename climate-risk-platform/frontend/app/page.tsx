'use client'

import { useRef, useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import Hero from '@/components/ui/animated-shader-hero'
import { SectionScroll } from '@/components/ui/section-scroll-animation'
import { CascadeSimulationPanel } from '@/components/CascadeSimulationPanel'
import { portfolioApi } from '@/lib/portfolio-api'

interface Portfolio {
  id: string
  name: string
  base_currency: string
  holdings_count: number
  total_value: number
}

export default function Home() {
  const dashboardRef = useRef<HTMLDivElement>(null)
  const [portfolios, setPortfolios] = useState<Portfolio[]>([])
  const [selectedPortfolio, setSelectedPortfolio] = useState<Portfolio | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadPortfolios()
  }, [])

  const loadPortfolios = async () => {
    try {
      const data = await portfolioApi.listPortfolios()
      const withSummary = await Promise.all(
        data.map(async (p) => {
          try {
            return await portfolioApi.getPortfolio(p.id)
          } catch {
            return { ...p, holdings_count: 0, total_value: 0 }
          }
        })
      )
      setPortfolios(withSummary)
      if (withSummary.length > 0) setSelectedPortfolio(withSummary[0])
    } catch {
      setError('Failed to load portfolios')
    }
  }

  const scrollToDashboard = useCallback(() => {
    dashboardRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [])

  return (
    <div className="min-h-screen relative" style={{ zIndex: 1 }}>
      {/* ===== SECTION 1: Shader Hero ===== */}
      <Hero
        trustBadge={{
          text: 'MiroFish-powered Agent Cascade Simulation',
          icons: ['⚡'],
        }}
        headline={{
          line1: 'Climate Risk',
          line2: 'Intelligence',
        }}
        subtitle="Assess and visualize how climate events cascade through your portfolio's company network — powered by AI agents that model systemic financial risk in real time."
        buttons={{
          primary: {
            text: 'Launch Dashboard',
            onClick: scrollToDashboard,
          },
          secondary: {
            text: 'Learn More',
            onClick: () => {
              document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
            },
          },
        }}
      />

      {/* ===== SECTION 2: Features ===== */}
      <section
        id="features"
        className="relative py-24 px-6"
      >
        <div className="max-w-6xl mx-auto">
          <SectionScroll
            titleComponent={
              <>
                <p className="text-sm font-medium text-cyan-400 uppercase tracking-widest mb-3">
                  Platform Capabilities
                </p>
                <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
                  Systemic Risk, <span className="text-cyan-400">Visualized</span>
                </h2>
                <p className="text-slate-400 text-lg max-w-2xl mx-auto">
                  62 AI agents model real-world company dependencies to reveal hidden cascade risks across your portfolio.
                </p>
              </>
            }
          >
            <div className="grid md:grid-cols-3 gap-6">
              {[
                { icon: '🌀', title: 'Cascade Simulation', desc: 'Describe any climate event and watch AI agents propagate impacts through supply chains and financial dependencies.' },
                { icon: '🔗', title: 'Agent Network', desc: '62 interconnected agents with 136 cascade links model real company relationships across sectors and regions.' },
                { icon: '📊', title: 'Loss Quantification', desc: 'Real-time calculation of direct losses, cascaded losses, and amplification factors across your holdings.' },
                { icon: '⏱️', title: 'Timeline Analysis', desc: 'Track how events propagate round by round through the network with detailed cascade timelines.' },
                { icon: '📝', title: 'AI Narratives', desc: 'Auto-generated narrative explanations of cascade dynamics and systemic risk patterns.' },
                { icon: '💡', title: 'Action Recommendations', desc: 'Actionable portfolio optimization suggestions based on identified vulnerabilities.' },
              ].map((feature, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 40, scale: 0.95 }}
                  whileInView={{ opacity: 1, y: 0, scale: 1 }}
                  viewport={{ once: true, margin: '-40px' }}
                  transition={{
                    duration: 0.55,
                    delay: (i % 3) * 0.1,
                    ease: [0.22, 1, 0.36, 1],
                  }}
                  whileHover={{ y: -6, scale: 1.02, transition: { duration: 0.2 } }}
                  className="rounded-2xl bg-black/30 backdrop-blur-md border border-white/10 p-6 hover:bg-black/40 hover:border-cyan-500/30 transition-colors duration-300 group cursor-default"
                >
                  <div className="text-3xl mb-4">{feature.icon}</div>
                  <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-cyan-400 transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{feature.desc}</p>
                </motion.div>
              ))}
            </div>
          </SectionScroll>
        </div>
      </section>

      {/* ===== SECTION 3: Dashboard — the simulation panel, inline ===== */}
      <div
        ref={dashboardRef}
        className="relative"
      >
        {/* Sticky nav bar for the dashboard section */}
        <motion.nav
          initial={{ opacity: 0, y: -20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="sticky top-0 z-50 border-b border-white/10 bg-black/30 backdrop-blur-xl"
        >
          <div className="max-w-7xl mx-auto px-6 py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-base font-bold text-slate-100">Climate Risk Intelligence</h1>
                  <p className="text-[10px] text-slate-500">MiroFish-powered Agent Cascade Simulation</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {portfolios.length > 0 && (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500">Portfolio:</span>
                    <select
                      value={selectedPortfolio?.id || ''}
                      onChange={e => {
                        const p = portfolios.find(x => x.id === e.target.value)
                        if (p) setSelectedPortfolio(p)
                      }}
                      className="px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                    >
                      {portfolios.map(p => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                  </div>
                )}
                {selectedPortfolio && (
                  <div className="text-xs text-slate-500 px-3 py-1.5 bg-slate-800/30 rounded-lg border border-slate-700/30">
                    {selectedPortfolio.holdings_count} holdings · ${(selectedPortfolio.total_value / 1e6).toFixed(0)}M
                  </div>
                )}
              </div>
            </div>
          </div>
        </motion.nav>

        {/* Dashboard content */}
        <div className="p-6">
          {error && (
            <div className="max-w-7xl mx-auto mb-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4 text-amber-400 text-sm">
              {error}
            </div>
          )}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            className="max-w-7xl mx-auto"
          >
            {selectedPortfolio ? (
              <CascadeSimulationPanel portfolioId={selectedPortfolio.id} />
            ) : (
              <CascadeSimulationPanel portfolioId="default" />
            )}
          </motion.div>
        </div>
      </div>
    </div>
  )
}
