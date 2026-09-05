import { useEffect, useState } from 'react'
import Sidebar from './components/Sidebar'
import MetricsPanel from './components/MetricsPanel'
import Charts from './components/Charts'
import EventStream from './components/EventStream'
import AuditLog from './components/AuditLog'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const TAB_TITLES = {
  stream: 'Event Stream',
  audit: 'Audit Trail',
  about: 'About Reviva',
}

export default function App() {
  const [metrics, setMetrics] = useState(null)
  const [events, setEvents] = useState(null)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('stream')

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/api/metrics`).then((r) => {
        if (!r.ok) throw new Error(`Metrics API returned ${r.status}`)
        return r.json()
      }),
      fetch(`${API_BASE}/api/events`).then((r) => {
        if (!r.ok) throw new Error(`Events API returned ${r.status}`)
        return r.json()
      }),
    ])
      .then(([metricsData, eventsData]) => {
        setMetrics(metricsData)
        setEvents(eventsData.events)
      })
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar active={tab} onNavigate={setTab} />

      <div className="flex-1 min-w-0">
        <header className="border-b border-border px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-zinc-100">{TAB_TITLES[tab]}</h1>
            <p className="text-xs text-muted">
              Payment degradation → root cause → recovery
            </p>
          </div>
          {metrics && (
            <div className="text-xs text-muted">
              {metrics.total_events} events · {metrics.recovery_rate_pct}% recovered
            </div>
          )}
        </header>

        <main className="p-8 max-w-6xl">
          {error && (
            <div className="card border-red-500/30 bg-red-500/5 p-4 text-red-300 text-sm mb-6">
              Couldn't reach the backend: {error}. Make sure the FastAPI
              server is running on {API_BASE}.
            </div>
          )}

          {!error && !metrics && <p className="text-muted text-sm">Loading…</p>}

          {tab !== 'about' && metrics && <MetricsPanel metrics={metrics} />}
          {tab === 'stream' && events && <Charts events={events} />}

          {tab === 'stream' && events && <EventStream events={events} />}
          {tab === 'audit' && events && <AuditLog events={events} />}
          {tab === 'about' && <AboutPanel />}
        </main>
      </div>
    </div>
  )
}

function AboutPanel() {
  return (
    <div className="card p-6 max-w-2xl">
      <h2 className="text-base font-semibold text-zinc-100 mb-2">
        Reviva — AI Revenue Recovery
      </h2>
      <p className="text-sm text-muted leading-relaxed">
        Built for the Razorpay AI Buildathon, Track 03. Reviva detects
        degrading payments, diagnoses the likely root cause using a
        two-layer rule + clustering engine (with Gemini assisting on
        genuinely ambiguous cases), and executes a bounded, compliant
        recovery action — with a full audit trail and honest, measured
        results rather than cherry-picked wins.
      </p>
    </div>
  )
}
