import { useState, useMemo } from 'react'
import DiagnosisCard from './DiagnosisCard'

const CAUSES = [
  'all',
  'issuer_decline',
  'network_timeout',
  'expired_instrument',
  'insufficient_funds',
  'acquirer_outage',
  'fraud_hold',
  'ambiguous',
]

export default function EventStream({ events }) {
  const [filter, setFilter] = useState('all')

  const filtered = useMemo(() => {
    if (filter === 'all') return events
    return events.filter((e) => e.diagnosis.predicted_cause === filter)
  }, [events, filter])

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Event Stream</h2>
        <span className="text-sm text-muted">
          {filtered.length} of {events.length} events
        </span>
      </div>

      <div className="flex gap-2 mb-4 flex-wrap">
        {CAUSES.map((cause) => (
          <button
            key={cause}
            onClick={() => setFilter(cause)}
            className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
              filter === cause
                ? 'bg-zinc-100 text-zinc-900 border-zinc-100'
                : 'card text-muted hover:border-zinc-600'
            }`}
          >
            {cause === 'all' ? 'All' : cause.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      <div className="max-h-[600px] overflow-y-auto pr-1">
        {filtered.map((entry) => (
          <DiagnosisCard key={entry.event_id} entry={entry} />
        ))}
        {filtered.length === 0 && (
          <p className="text-muted text-sm py-8 text-center">
            No events match this filter.
          </p>
        )}
      </div>
    </div>
  )
}
