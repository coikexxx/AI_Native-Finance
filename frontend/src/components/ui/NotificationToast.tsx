import { useAnalysisStore } from '../../store/analysisStore'
import clsx from 'clsx'

export function NotificationToast() {
  const { notifications, dismissNotification } = useAnalysisStore()

  if (!notifications.length) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2">
      {notifications.map(n => (
        <div
          key={n.id}
          className={clsx(
            'flex items-start gap-3 p-3 rounded-lg shadow-lg border max-w-sm text-sm',
            n.type === 'error'
              ? 'bg-red-900 border-red-700 text-red-200'
              : 'bg-sky-900 border-sky-700 text-sky-200',
          )}
        >
          <span className="flex-1">{n.message}</span>
          <button onClick={() => dismissNotification(n.id)} className="text-current opacity-60 hover:opacity-100">
            ×
          </button>
        </div>
      ))}
    </div>
  )
}
