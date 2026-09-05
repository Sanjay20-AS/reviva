import { Clock, Wifi, CreditCard, Wallet, ShieldAlert, ServerCrash, HelpCircle } from 'lucide-react'

const CAUSE_META = {
  issuer_decline: { color: 'border-l-orange-500', icon: CreditCard, iconColor: 'text-orange-400' },
  network_timeout: { color: 'border-l-sky-500', icon: Wifi, iconColor: 'text-sky-400' },
  expired_instrument: { color: 'border-l-amber-500', icon: Clock, iconColor: 'text-amber-400' },
  insufficient_funds: { color: 'border-l-purple-500', icon: Wallet, iconColor: 'text-purple-400' },
  acquirer_outage: { color: 'border-l-red-500', icon: ServerCrash, iconColor: 'text-red-400' },
  fraud_hold: { color: 'border-l-rose-600', icon: ShieldAlert, iconColor: 'text-rose-400' },
  ambiguous: { color: 'border-l-zinc-500', icon: HelpCircle, iconColor: 'text-zinc-400' },
}

const OUTCOME_STYLES = {
  recovered: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  not_recovered: 'bg-red-500/10 text-red-400 border-red-500/30',
  pending_manual_action: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
}

export default function DiagnosisCard({ entry }) {
  const meta = CAUSE_META[entry.diagnosis.predicted_cause] || CAUSE_META.ambiguous
  const Icon = meta.icon
  const outcomeStyle = OUTCOME_STYLES[entry.outcome] || ''

  return (
    <div className={`card border-l-4 ${meta.color} p-4 mb-3 transition-colors hover:border-zinc-700`}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="text-sm font-mono text-muted">{entry.event_id}</span>
          <span className="mx-2 text-zinc-600">·</span>
          <span className="text-sm text-zinc-300">{entry.customer_id}</span>
        </div>
        <span className="text-sm font-semibold">
          ₹{entry.amount.toLocaleString('en-IN')}
        </span>
      </div>

      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <Icon size={15} className={meta.iconColor} />
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

      <p className="text-sm text-muted mb-3">{entry.diagnosis.reasoning}</p>

      <div className="flex justify-between items-center text-sm">
        <span className="text-muted">
          Action: <span className="text-zinc-300">{entry.action.action.replace(/_/g, ' ')}</span>
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
    low: 'bg-zinc-500/10 text-muted border-zinc-500/30',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${styles[confidence] || styles.low}`}>
      {confidence} confidence
    </span>
  )
}
