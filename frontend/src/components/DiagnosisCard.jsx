const CAUSE_COLORS = {
  issuer_decline: 'border-l-orange-500',
  network_timeout: 'border-l-sky-500',
  expired_instrument: 'border-l-amber-500',
  insufficient_funds: 'border-l-purple-500',
  acquirer_outage: 'border-l-red-500',
  fraud_hold: 'border-l-rose-600',
  ambiguous: 'border-l-slate-500',
}

const OUTCOME_STYLES = {
  recovered: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  not_recovered: 'bg-red-500/10 text-red-400 border-red-500/30',
  pending_manual_action: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
}

export default function DiagnosisCard({ entry }) {
  const borderColor = CAUSE_COLORS[entry.diagnosis.predicted_cause] || 'border-l-slate-500'
  const outcomeStyle = OUTCOME_STYLES[entry.outcome] || ''

  return (
    <div className={`bg-slate-900 border border-slate-800 border-l-4 ${borderColor} rounded-lg p-4 mb-3`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="text-sm font-mono text-slate-400">{entry.event_id}</span>
          <span className="mx-2 text-slate-600">·</span>
          <span className="text-sm text-slate-300">{entry.customer_id}</span>
        </div>
        <span className="text-sm font-semibold">
          ₹{entry.amount.toLocaleString('en-IN')}
        </span>
      </div>

      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="text-sm font-medium capitalize">
          {entry.diagnosis.predicted_cause.replace(/_/g, ' ')}
        </span>
        <ConfidenceBadge confidence={entry.diagnosis.confidence} />
        {entry.diagnosis.source && entry.diagnosis.source !== 'rule_engine' && (
          <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
            {entry.diagnosis.source === 'gemini' ? 'Gemini-assisted' : entry.diagnosis.source}
          </span>
        )}
      </div>

      <p className="text-sm text-slate-400 mb-3">{entry.diagnosis.reasoning}</p>

      <div className="flex justify-between items-center text-sm">
        <span className="text-slate-500">
          Action: <span className="text-slate-300">{entry.action.action.replace(/_/g, ' ')}</span>
        </span>
        <span className={`text-xs px-2 py-1 rounded border ${outcomeStyle}`}>
          {entry.outcome.replace(/_/g, ' ')}
        </span>
      </div>
    </div>
  )
}

function ConfidenceBadge({ confidence }) {
  const styles = {
    high: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    medium: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    low: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${styles[confidence] || styles.low}`}>
      {confidence} confidence
    </span>
  )
}
