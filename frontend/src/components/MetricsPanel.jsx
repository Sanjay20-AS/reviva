export default function MetricsPanel({ metrics }) {
  if (!metrics) return null

  return (
    <div className="mb-8">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <MetricCard
          label="Recovery rate"
          value={`${metrics.recovery_rate_pct}%`}
          accent="text-emerald-400"
        />
        <MetricCard
          label="Amount recovered"
          value={`₹${metrics.total_amount_recovered.toLocaleString('en-IN')}`}
          accent="text-emerald-400"
          sub={`of ₹${metrics.total_amount_at_risk.toLocaleString('en-IN')} at risk`}
        />
        <MetricCard
          label="Diagnosis accuracy"
          value={`${metrics.diagnosis_accuracy_pct}%`}
          accent="text-sky-400"
        />
        <MetricCard label="Total events" value={metrics.total_events} />
      </div>

      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatusChip label="Recovered" count={metrics.recovered_count} color="bg-emerald-500" />
        <StatusChip label="Not recovered" count={metrics.not_recovered_count} color="bg-red-500" />
        <StatusChip label="Pending manual action" count={metrics.pending_manual_count} color="bg-amber-500" />
      </div>

      {metrics.exceptions?.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">
            Exceptions — honest reporting, not cherry-picked
          </h3>
          <div className="max-h-48 overflow-y-auto space-y-1">
            {metrics.exceptions.map((e) => (
              <div
                key={e.event_id}
                className="flex justify-between text-sm text-slate-400 py-1 border-b border-slate-800/50 last:border-0"
              >
                <span>{e.event_id}</span>
                <span className="text-slate-500">{e.predicted_cause}</span>
                <span>₹{e.amount.toLocaleString('en-IN')}</span>
                <span
                  className={
                    e.outcome === 'not_recovered' ? 'text-red-400' : 'text-amber-400'
                  }
                >
                  {e.outcome.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function MetricCard({ label, value, accent = 'text-slate-100', sub }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="text-slate-400 text-sm mb-1">{label}</div>
      <div className={`text-2xl font-semibold ${accent}`}>{value}</div>
      {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
    </div>
  )
}

function StatusChip({ label, count, color }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-3">
      <span className={`w-2.5 h-2.5 rounded-full ${color}`} />
      <span className="text-slate-300 text-sm">{label}</span>
      <span className="ml-auto font-semibold">{count}</span>
    </div>
  )
}
