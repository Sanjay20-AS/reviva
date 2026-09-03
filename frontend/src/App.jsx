import { useEffect, useState } from 'react'
import MetricsPanel from './components/MetricsPanel'
import EventStream from './components/EventStream'
import AuditLog from './components/AuditLog'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

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
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 max-w-6xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold mb-1">Reviva</h1>
        <p className="text-slate-400">
          Payment degradation → root cause → recovery
        </p>
      </header>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300 mb-6">
          Couldn't reach the backend: {error}. Make sure the FastAPI server
          is running on {API_BASE}.
        </div>
      )}

      {!error && !metrics && (
        <p className="text-slate-500">Loading…</p>
      )}

      {metrics && <MetricsPanel metrics={metrics} />}

      {events && (
        <>
          <div className="flex gap-2 mb-6 border-b border-slate-800">
            <TabButton active={tab === 'stream'} onClick={() => setTab('stream')}>
              Event Stream
            </TabButton>
            <TabButton active={tab === 'audit'} onClick={() => setTab('audit')}>
              Audit Trail
            </TabButton>
          </div>

          {tab === 'stream' && <EventStream events={events} />}
          {tab === 'audit' && <AuditLog events={events} />}
        </>
      )}
    </div>
  )
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active
          ? 'border-slate-100 text-slate-100'
          : 'border-transparent text-slate-500 hover:text-slate-300'
      }`}
    >
      {children}
    </button>
  )
}