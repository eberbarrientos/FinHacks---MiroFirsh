export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="glass-card p-8 max-w-2xl">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">
          Climate Risk Intelligence Platform
        </h1>
        <p className="text-muted-foreground text-lg">
          Assess and visualize climate-related risks across investment portfolios
        </p>
        <div className="mt-8 space-y-2">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-400"></div>
            <span className="text-sm">Backend API Ready</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-400"></div>
            <span className="text-sm">Frontend Framework Initialized</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-amber-400"></div>
            <span className="text-sm">Database Setup Pending</span>
          </div>
        </div>
      </div>
    </main>
  )
}
