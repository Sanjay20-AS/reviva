import { LayoutGrid, ScrollText, Info, Sparkles } from 'lucide-react'

const NAV_SECTIONS = [
  {
    label: 'Overview',
    items: [
      { key: 'stream', label: 'Event Stream', icon: LayoutGrid },
      { key: 'audit', label: 'Audit Trail', icon: ScrollText },
    ],
  },
  {
    label: 'Project',
    items: [
      { key: 'about', label: 'About Reviva', icon: Info },
    ],
  },
]

export default function Sidebar({ active, onNavigate }) {
  return (
    <aside className="w-64 shrink-0 border-r border-border bg-card/40 min-h-screen flex flex-col">
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Sparkles size={16} />
          </div>
          <div>
            <div className="text-sm font-semibold text-zinc-100">Reviva</div>
            <div className="text-xs text-muted">Razorpay Buildathon</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-6">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label}>
            <div className="text-xs font-medium text-muted px-3 mb-1.5 uppercase tracking-wide">
              {section.label}
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const Icon = item.icon
                return (
                  <button
                    key={item.key}
                    onClick={() => onNavigate(item.key)}
                    className={`w-full flex items-center gap-2.5 px-3 py-1.5 rounded-md text-sm transition-colors text-left ${
                      active === item.key
                        ? 'bg-zinc-800/70 text-zinc-100'
                        : 'text-muted hover:bg-zinc-800/40 hover:text-zinc-200'
                    }`}
                  >
                    <Icon size={15} className="shrink-0" />
                    {item.label}
                  </button>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-border flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-full bg-zinc-700 flex items-center justify-center text-xs font-medium">
          SA
        </div>
        <div className="text-xs">
          <div className="text-zinc-200">Sanjay A</div>
          <div className="text-muted">Track 03 submission</div>
        </div>
      </div>
    </aside>
  )
}
