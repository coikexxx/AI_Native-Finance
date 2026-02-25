import { useState } from 'react'
import type { EvidenceReference } from '../../types/analysis'
import clsx from 'clsx'

const SOURCE_TYPE_COLORS: Record<string, string> = {
  filing: 'bg-purple-900/40 text-purple-300',
  price_data: 'bg-sky-900/40 text-sky-300',
  news: 'bg-amber-900/40 text-amber-300',
  earnings_call: 'bg-emerald-900/40 text-emerald-300',
  macro: 'bg-red-900/40 text-red-300',
  company_info: 'bg-slate-700 text-slate-300',
}

interface Props {
  evidence: EvidenceReference[]
}

export function EvidencePack({ evidence }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [filter, setFilter] = useState<string>('all')

  const sourceTypes = ['all', ...Array.from(new Set(evidence.map(e => e.source_type)))]
  const filtered = filter === 'all' ? evidence : evidence.filter(e => e.source_type === filter)

  return (
    <div className="card">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <h2 className="section-title">证据包 Evidence Pack</h2>
          <span className="badge bg-slate-700 text-slate-300">{evidence.length}</span>
        </div>
        <svg
          className={clsx('w-5 h-5 text-slate-400 transition-transform', expanded && 'rotate-180')}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="mt-4">
          {/* Source type filter */}
          <div className="flex gap-1.5 flex-wrap mb-3">
            {sourceTypes.map(type => (
              <button
                key={type}
                onClick={() => setFilter(type)}
                className={clsx(
                  'badge cursor-pointer transition-colors',
                  filter === type
                    ? 'bg-sky-600 text-white'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700',
                )}
              >
                {type === 'all' ? `全部 All (${evidence.length})` : type}
              </button>
            ))}
          </div>

          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {filtered.map((e, idx) => (
              <div key={idx} id={e.citation_key.replace('[', '').replace(']', '')}
                className="p-3 bg-slate-800/60 rounded-lg border border-slate-700/50">
                <div className="flex items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs text-sky-400 font-bold">{e.citation_key}</span>
                    <span className={clsx('badge text-xs', SOURCE_TYPE_COLORS[e.source_type] || 'bg-slate-700 text-slate-300')}>
                      {e.source_type}
                    </span>
                  </div>
                  <span className="text-xs text-slate-500 flex-shrink-0">{e.agent_name}</span>
                </div>
                <div className="text-xs text-slate-400 font-medium mb-1">{e.source_label}</div>
                <p className="text-xs text-slate-300 leading-relaxed line-clamp-3">{e.excerpt}</p>
                {e.source_url && (
                  <a href={e.source_url} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-sky-500 hover:text-sky-400 mt-1 block truncate">
                    {e.source_url}
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
