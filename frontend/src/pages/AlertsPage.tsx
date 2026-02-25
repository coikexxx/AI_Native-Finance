import { AlertForm } from '../components/alerts/AlertForm'
import { AlertList } from '../components/alerts/AlertList'

export function AlertsPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">提醒管理 Alerts</h1>
        <p className="text-slate-500 text-sm mt-1">
          设置价格提醒、财报日提醒，或定期触发重新分析
        </p>
      </div>
      <AlertForm />
      <AlertList />
    </div>
  )
}
