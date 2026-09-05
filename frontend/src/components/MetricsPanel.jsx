export default function MetricsPanel({ metrics }) {
  if (!metrics) return null

  return (
    <div className="mb-8">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <MetricCard
          label="Recovery rate"
          value={`${metrics.recovery_rate_pct}%`}
          delta="of total at-risk events"
        />
        <MetricCard
          label="Amount recovered"
          value={`₹${metrics.total_amount_recovered.toLocaleString('en-IN')}`}
          delta={`of ₹${metrics.total_amount_at_risk.toLocaleString('en-IN')} at risk`}
        />
        <MetricCard
          label="Diagnosis accuracy"
          value={`${metrics.diagnosis_accuracy_pct}%`}
          delta="vs. ground truth"
        />
        <MetricCard
          label="Total events"
          value={metrics.total_events}
          delta="processed in this batch"
        />
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <StatusCard label="Recovered" count={metrics.recovered_count} dot="bg-emerald-500" />
        <StatusCard label="Not recovered" count={metrics.not_recovered_count} dot="bg-red-500" />
        <StatusCard label="Pending manual action" count={metrics.pending_manual_count} dot="bg-amber-500" />
      </div>

      {metrics.exceptions?.length > 0 && (
        <div className="card p-5">
          <div className="text-sm font-medium text-zinc-200 mb-1">Exceptions</div>
          <div className="text-xs text-muted mb-3">
            Honest reporting — every unresolved case, not a cherry-picked subset
          </div>
          <div className="divide-y divide-border">
            {metrics.exceptions.slice(0, 8).map((e) => (
              <div key={e.event_id} className="flex items-center justify-between py-2 text-sm">
                <span className="font-mono text-muted">{e.event_id}</span>
                <span className="text-zinc-400 capitalize">
                  {e.predicted_cause.replace(/_/g, ' ')}
                </span>
                <span className="text-zinc-200">₹{e.amount.toLocaleString('en-IN')}</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full border ${
                    e.outcome === 'not_recovered'
                      ? 'text-red-400 border-red-500/30 bg-red-500/10'
                      : 'text-amber-400 border-amber-500/30 bg-amber-500/10'
                  }`}
                >
                  {e.outcome.replace(/_/g, ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function MetricCard({ label, value, delta }) {
  return (
    <div className="card p-5">
      <div className="text-sm text-muted mb-2">{label}</div>
      <div className="text-3xl font-semibold tracking-tight text-zinc-50 mb-1">{value}</div>
      <div className="text-xs text-muted">{delta}</div>
    </div>
  )
}

function StatusCard({ label, count, dot }) {
  return (
    <div className="card px-4 py-3 flex items-center gap-3">
      <span className={`w-2 h-2 rounded-full ${dot}`} />
      <span className="text-sm text-zinc-300">{label}</span>
      <span className="ml-auto text-sm font-semibold text-zinc-100">{count}</span>
    </div>
  )
}
