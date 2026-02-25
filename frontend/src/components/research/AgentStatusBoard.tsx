import { useAnalysisStore } from '../../store/analysisStore'
import { AGENT_DISPLAY_NAMES } from '../../types/analysis'
import clsx from 'clsx'

const statusIcon = {
  pending: (
    <svg className="w-4 h-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <circle cx="12" cy="12" r="10" strokeWidth="2" />
    </svg>
  ),
  running: (
    <svg className="w-4 h-4 text-sky-400 animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  ),
  complete: (
    <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  failed: (
    <svg className="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
}

export function AgentStatusBoard() {
  const { agentStatuses, streamingPhase } = useAnalysisStore()
  const agents = Object.values(agentStatuses)

  const completed = agents.filter(a => a.status === 'complete').length
  const total = agents.length

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h2 className="section-title">分析进行中 Analysis in Progress</h2>
        <span className="text-sm text-slate-400">{completed}/{total} 完成</span>
      </div>

      {streamingPhase && (
        <div className="mb-3 text-xs text-sky-400 flex items-center gap-1.5">
          <svg className="w-3 h-3 animate-pulse" fill="currentColor" viewBox="0 0 8 8">
            <circle cx="4" cy="4" r="3" />
          </svg>
          {streamingPhase}
        </div>
      )}

      {/* Overall progress bar */}
      <div className="h-1.5 bg-slate-800 rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-sky-500 rounded-full transition-all duration-500"
          style={{ width: `${(completed / total) * 100}%` }}
        />
      </div>

      <div className="grid grid-cols-1 gap-2">
        {agents.map(agent => (
          <div
            key={agent.agent_name}
            className={clsx(
              'flex items-center gap-3 p-2.5 rounded-lg transition-colors',
              agent.status === 'running' && 'bg-sky-900/20 border border-sky-800/40',
              agent.status === 'complete' && 'bg-emerald-900/10',
              agent.status === 'failed' && 'bg-red-900/10',
              agent.status === 'pending' && 'opacity-50',
            )}
          >
            <div className="flex-shrink-0">{statusIcon[agent.status]}</div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-slate-200 truncate">
                {agent.display_name || AGENT_DISPLAY_NAMES[agent.agent_name] || agent.agent_name}
              </div>
              {agent.message && agent.status === 'running' && (
                <div className="text-xs text-slate-400 truncate mt-0.5">{agent.message}</div>
              )}
            </div>
            {agent.status === 'running' && (
              <div className="text-xs text-sky-400 font-mono">{agent.progress_pct}%</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
