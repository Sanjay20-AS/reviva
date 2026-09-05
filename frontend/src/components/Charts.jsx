import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Cell,
} from 'recharts'

const CAUSE_COLORS = {
  issuer_decline: '#f97316',
  network_timeout: '#0ea5e9',
  expired_instrument: '#eab308',
  insufficient_funds: '#a855f7',
  acquirer_outage: '#ef4444',
  fraud_hold: '#e11d48',
  ambiguous: '#71717a',
}

export default function Charts({ events }) {
  const byCause = computeRecoveryByCause(events)
  const timeline = computeRecoveryTimeline(events)

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
      <div className="card p-5">
        <div className="text-sm font-medium text-zinc-200 mb-1">
          Recovery rate by cause
        </div>
        <div className="text-xs text-muted mb-4">
          Which failure types recover most reliably
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={byCause} margin={{ left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis
              dataKey="cause"
              tick={{ fill: '#71717a', fontSize: 11 }}
              tickFormatter={(v) => v.replace(/_/g, ' ')}
              interval={0}
              angle={-25}
              textAnchor="end"
              height={60}
            />
            <YAxis tick={{ fill: '#71717a', fontSize: 11 }} unit="%" />
            <Tooltip
              contentStyle={{
                background: '#0f0f16',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(value) => [`${value}%`, 'Recovery rate']}
              labelFormatter={(label) => label.replace(/_/g, ' ')}
            />
            <Bar dataKey="recoveryRate" radius={[4, 4, 0, 0]}>
              {byCause.map((entry) => (
                <Cell key={entry.cause} fill={CAUSE_COLORS[entry.cause] || '#71717a'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card p-5">
        <div className="text-sm font-medium text-zinc-200 mb-1">
          Cumulative amount recovered
        </div>
        <div className="text-xs text-muted mb-4">
          Running total across the processed batch, in event order
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={timeline} margin={{ left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis
              dataKey="index"
              tick={{ fill: '#71717a', fontSize: 11 }}
              label={{ value: 'Event #', position: 'insideBottom', offset: -5, fill: '#71717a', fontSize: 11 }}
            />
            <YAxis
              tick={{ fill: '#71717a', fontSize: 11 }}
              tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              contentStyle={{
                background: '#0f0f16',
                border: '1px solid rgba(255,255,255,0.08)',
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(value) => [`₹${value.toLocaleString('en-IN')}`, 'Recovered']}
            />
            <Line
              type="monotone"
              dataKey="cumulative"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

function computeRecoveryByCause(events) {
  const byCause = {}
  for (const e of events) {
    const cause = e.diagnosis.predicted_cause
    if (!byCause[cause]) byCause[cause] = { total: 0, recovered: 0 }
    byCause[cause].total += 1
    if (e.outcome === 'recovered') byCause[cause].recovered += 1
  }
  return Object.entries(byCause).map(([cause, stats]) => ({
    cause,
    recoveryRate: Math.round((100 * stats.recovered) / stats.total),
  }))
}

function computeRecoveryTimeline(events) {
  // Events already come sorted by original_event_timestamp from the backend
  let cumulative = 0
  return events.map((e, i) => {
    cumulative += e.amount_recovered
    return { index: i + 1, cumulative: Math.round(cumulative) }
  })
}
