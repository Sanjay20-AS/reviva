import { useState, Fragment } from 'react'

export default function AuditLog({ events }) {
  const [expanded, setExpanded] = useState(null)

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Audit Trail</h2>
      <div className="card rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900/60 text-muted text-left">
            <tr>
              <th className="px-4 py-2 font-medium">Event</th>
              <th className="px-4 py-2 font-medium">Cause</th>
              <th className="px-4 py-2 font-medium">Action</th>
              <th className="px-4 py-2 font-medium">Outcome</th>
              <th className="px-4 py-2 font-medium">Correct?</th>
            </tr>
          </thead>
          <tbody>
            {events.map((entry) => (
              <Fragment key={entry.event_id}>
                <tr
                  onClick={() =>
                    setExpanded(expanded === entry.event_id ? null : entry.event_id)
                  }
                  className="border-t border-border hover:bg-zinc-900/40 cursor-pointer"
                >
                  <td className="px-4 py-2 font-mono text-muted">{entry.event_id}</td>
                  <td className="px-4 py-2 capitalize">
                    {entry.diagnosis.predicted_cause.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-2 text-muted">
                    {entry.action.action.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-2">{entry.outcome.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-2">
                    {entry.diagnosis_correct ? (
                      <span className="text-emerald-400">✓</span>
                    ) : (
                      <span className="text-red-400">✗</span>
                    )}
                  </td>
                </tr>
                {expanded === entry.event_id && (
                  <tr className="border-t border-border bg-zinc-900/30">
                    <td colSpan={5} className="px-4 py-3 text-muted">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-xs text-muted mb-1">Reasoning</div>
                          <p className="text-sm">{entry.diagnosis.reasoning}</p>
                        </div>
                        <div>
                          <div className="text-xs text-muted mb-1">Signals</div>
                          <pre className="text-xs bg-black rounded p-2 overflow-x-auto">
                            {JSON.stringify(entry.signals, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}