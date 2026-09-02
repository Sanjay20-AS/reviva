import { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE}/api/metrics`)
      .then((res) => {
        if (!res.ok) throw new Error(`API returned ${res.status}`)
        return res.json()
      })
      .then(setMetrics)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <h1 className="text-3xl font-bold mb-2">Reviva</h1>
      <p className="text-slate-400 mb-8">
        Payment degradation → root cause → recovery
      </p>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300">
          Couldn't reach the backend: {error}. Make sure the FastAPI server
          is running on {API_BASE}.
        </div>
      )}

      {!error && !metrics && (
        <p className="text-slate-500">Loading metrics…</p>
      )}

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Recovery rate" value={`${metrics.recovery_rate_pct}%`} />
          <MetricCard
            label="Amount recovered"
            value={`₹${metrics.total_amount_recovered.toLocaleString('en-IN')}`}
          />
          <MetricCard
            label="Diagnosis accuracy"
            value={`${metrics.diagnosis_accuracy_pct}%`}
          />
          <MetricCard label="Total events" value={metrics.total_events} />
        </div>
      )}

      {/* Full dashboard components (event stream, diagnosis cards,
          audit log view) come next — this is the connectivity-verified
          scaffold. */}
    </div>
  )
}

function MetricCard({ label, value }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="text-slate-400 text-sm mb-1">{label}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  )
}
