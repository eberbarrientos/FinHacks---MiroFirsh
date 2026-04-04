import Link from 'next/link'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-800/40 to-slate-900/40 backdrop-blur-xl border border-slate-700/50 p-12 max-w-2xl text-center">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-transparent" />
        <div className="relative z-10">
          <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
            Climate Risk Intelligence Platform
          </h1>
          <p className="text-slate-400 text-lg mb-8">
            Assess and visualize climate-related risks across investment portfolios
          </p>
          <div className="space-y-3 mb-8 text-left max-w-sm mx-auto">
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="text-sm text-slate-300">Backend API Running</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="text-sm text-slate-300">SQLite Database Ready</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="text-sm text-slate-300">Sample Portfolio Loaded (50 holdings)</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="text-sm text-slate-300">4 Climate Scenarios Available</span>
            </div>
          </div>
          <Link
            href="/dashboard"
            className="inline-flex items-center px-8 py-3 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
          >
            Open Dashboard →
          </Link>
        </div>
      </div>
    </main>
  )
}
