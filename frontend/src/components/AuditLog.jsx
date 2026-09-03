import { useState } from 'react'

export default function AuditLog({ events }) {
  const [expanded, setExpanded] = useState(null)

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Audit Trail</h2>
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/50 text-slate-400 text-left">
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
              <>
                <tr
                  key={entry.event_id}
                  onClick={() =>
                    setExpanded(expanded === entry.event_id ? null : entry.event_id)
                  }
                  className="border-t border-slate-800 hover:bg-slate-800/30 cursor-pointer"
                >
                  <td className="px-4 py-2 font-mono text-slate-400">{entry.event_id}</td>
                  <td className="px-4 py-2 capitalize">
                    {entry.diagnosis.predicted_cause.replace(/_/g, ' ')}
                  </td>
                  <td className="px-4 py-2 text-slate-400">
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
                  <tr className="border-t border-slate-800 bg-slate-800/20">
                    <td colSpan={5} className="px-4 py-3 text-slate-400">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <div className="text-xs text-slate-500 mb-1">Reasoning</div>
                          <p className="text-sm">{entry.diagnosis.reasoning}</p>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500 mb-1">Signals</div>
                          <pre className="text-xs bg-slate-950 rounded p-2 overflow-x-auto">
                            {JSON.stringify(entry.signals, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
