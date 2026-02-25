import { useState, FormEvent } from 'react'
import { alertsApi } from '../../api/alerts'
import { useAlertStore } from '../../store/alertStore'
import { ALERT_TYPE_LABELS, FREQUENCY_OPTIONS } from '../../types/alert'
import type { AlertType, AlertCreate } from '../../types/alert'

export function AlertForm({ defaultTicker = '' }: { defaultTicker?: string }) {
  const [ticker, setTicker] = useState(defaultTicker)
  const [type, setType] = useState<AlertType>('price_above')
  const [targetPrice, setTargetPrice] = useState('')
  const [frequency, setFrequency] = useState(FREQUENCY_OPTIONS[0].value)
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const { add } = useAlertStore()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    const payload: AlertCreate = {
      ticker: ticker.trim().toUpperCase(),
      alert_type: type,
      ...(type === 'price_above' || type === 'price_below'
        ? { target_price: parseFloat(targetPrice) }
        : {}),
      ...(type === 're_analyze' ? { cron_expression: frequency } : {}),
      ...(type === 'custom' ? { event_description: description } : {}),
    }

    try {
      const alert = await alertsApi.create(payload)
      add(alert)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
      // Reset
      setTargetPrice('')
      setDescription('')
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2 className="section-title mb-4">新建提醒 New Alert</h2>

      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="label">股票代码 Ticker</label>
          <input
            type="text"
            value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
            className="input font-mono"
            placeholder="e.g. AAPL"
            required
            maxLength={10}
          />
        </div>

        <div>
          <label className="label">提醒类型 Alert Type</label>
          <select
            value={type}
            onChange={e => setType(e.target.value as AlertType)}
            className="input"
          >
            {Object.entries(ALERT_TYPE_LABELS).map(([val, label]) => (
              <option key={val} value={val}>{label}</option>
            ))}
          </select>
        </div>

        {/* Conditional fields */}
        {(type === 'price_above' || type === 'price_below') && (
          <div>
            <label className="label">
              {type === 'price_above' ? '价格上限 Target Price (above)' : '价格下限 Target Price (below)'}
            </label>
            <div className="relative">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
              <input
                type="number"
                value={targetPrice}
                onChange={e => setTargetPrice(e.target.value)}
                className="input pl-7"
                placeholder="0.00"
                step="0.01"
                min="0"
                required
              />
            </div>
          </div>
        )}

        {type === 're_analyze' && (
          <div>
            <label className="label">分析频率 Frequency</label>
            <select value={frequency} onChange={e => setFrequency(e.target.value)} className="input">
              {FREQUENCY_OPTIONS.map(o => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
        )}

        {type === 'custom' && (
          <div>
            <label className="label">事件描述 Event Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="input h-20 resize-none"
              placeholder="描述你希望监控的事件..."
              required
            />
          </div>
        )}

        {error && (
          <div className="text-red-400 text-sm">{error}</div>
        )}
        {success && (
          <div className="text-emerald-400 text-sm">✓ 提醒已创建 Alert created!</div>
        )}

        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? '保存中...' : '保存提醒 Save Alert'}
        </button>
      </form>
    </div>
  )
}
