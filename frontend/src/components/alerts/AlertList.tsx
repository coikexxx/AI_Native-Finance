import { useEffect } from 'react'
import { useAlertStore } from '../../store/alertStore'
import { alertsApi } from '../../api/alerts'
import { ALERT_TYPE_LABELS } from '../../types/alert'
import clsx from 'clsx'

export function AlertList() {
  const { alerts, load, toggle, remove } = useAlertStore()

  useEffect(() => { load() }, [load])

  if (!alerts.length) {
    return (
      <div className="card text-center py-8">
        <p className="text-slate-500">暂无提醒 No alerts set</p>
        <p className="text-slate-600 text-xs mt-1">Create an alert above to get started</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="section-title mb-3">活跃提醒 Active Alerts ({alerts.filter(a => a.is_active).length})</h2>
      <div className="space-y-2">
        {alerts.map(alert => (
          <div
            key={alert.id}
            className={clsx(
              'p-3 rounded-lg border transition-opacity',
              alert.is_active
                ? 'bg-slate-800/60 border-slate-700'
                : 'bg-slate-900/40 border-slate-800 opacity-60',
            )}
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-mono font-bold text-sky-400">{alert.ticker}</span>
                <span className="badge bg-slate-700 text-slate-300 text-xs">
                  {ALERT_TYPE_LABELS[alert.alert_type]}
                </span>
                {!alert.is_active && (
                  <span className="badge bg-slate-800 text-slate-500 text-xs">已停用 Disabled</span>
                )}
              </div>
              <div className="flex items-center gap-1">
                {/* Toggle */}
                <button
                  onClick={() => toggle(alert.id)}
                  className={clsx(
                    'relative inline-flex h-5 w-9 items-center rounded-full transition-colors',
                    alert.is_active ? 'bg-sky-600' : 'bg-slate-700',
                  )}
                  title={alert.is_active ? '停用 Disable' : '启用 Enable'}
                >
                  <span className={clsx(
                    'inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform',
                    alert.is_active ? 'translate-x-4' : 'translate-x-0.5',
                  )} />
                </button>
                {/* Delete */}
                <button
                  onClick={async () => {
                    try {
                      await alertsApi.delete(alert.id)
                      remove(alert.id)
                    } catch {
                      alert('删除失败 Failed to delete alert. Please try again.')
                    }
                  }}
                  className="text-slate-600 hover:text-red-400 ml-1 p-0.5 transition-colors"
                  title="删除 Delete"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="mt-1.5 text-xs text-slate-400">
              {alert.target_price && `目标价: $${alert.target_price.toFixed(2)}`}
              {alert.event_description && alert.event_description}
              {alert.cron_expression && `定期分析 | ${alert.cron_expression}`}
            </div>

            <div className="mt-1 text-xs text-slate-600">
              触发次数: {alert.trigger_count} |
              {alert.last_triggered_at
                ? ` 最近触发: ${new Date(alert.last_triggered_at).toLocaleDateString()}`
                : ' 从未触发'}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
