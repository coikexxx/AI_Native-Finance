import clsx from 'clsx'

const DECISION_CONFIG = {
  Buy: {
    bg: 'bg-emerald-500/20 border-emerald-500/40',
    text: 'text-emerald-300',
    icon: '▲',
    label: 'BUY / 买入',
    description: '具有吸引力的买入机会',
  },
  Hold: {
    bg: 'bg-amber-500/20 border-amber-500/40',
    text: 'text-amber-300',
    icon: '◆',
    label: 'HOLD / 持有',
    description: '合理估值，持有等待',
  },
  Watch: {
    bg: 'bg-sky-500/20 border-sky-500/40',
    text: 'text-sky-300',
    icon: '◉',
    label: 'WATCH / 观察',
    description: '关注但等待更好时机',
  },
  No: {
    bg: 'bg-red-500/20 border-red-500/40',
    text: 'text-red-300',
    icon: '▼',
    label: 'NO / 不投资',
    description: '估值过高或质量不足',
  },
}

interface Props {
  decision: 'Buy' | 'Hold' | 'Watch' | 'No'
  rationale?: string
  className?: string
}

export function DecisionBadge({ decision, rationale, className }: Props) {
  const config = DECISION_CONFIG[decision] || DECISION_CONFIG.Watch

  return (
    <div className={clsx('card border', config.bg, className)}>
      <div className="flex items-center gap-4">
        <div className={clsx('text-5xl font-bold', config.text)}>{config.icon}</div>
        <div>
          <div className={clsx('text-2xl font-bold tracking-wide', config.text)}>
            {config.label}
          </div>
          <div className="text-slate-400 text-sm mt-0.5">{config.description}</div>
        </div>
      </div>
      {rationale && (
        <p className="mt-4 text-slate-300 text-sm leading-relaxed border-t border-slate-700/50 pt-4">
          {rationale}
        </p>
      )}
    </div>
  )
}
