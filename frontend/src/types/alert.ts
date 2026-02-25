export type AlertType = 'price_above' | 'price_below' | 'earnings_date' | 're_analyze' | 'custom'

export interface Alert {
  id: string
  ticker: string
  alert_type: AlertType
  target_price?: number
  cron_expression?: string
  event_description?: string
  is_active: boolean
  created_at: string
  last_triggered_at?: string
  trigger_count: number
}

export interface AlertCreate {
  ticker: string
  alert_type: AlertType
  target_price?: number
  cron_expression?: string
  event_description?: string
}

export interface AlertTrigger {
  id: string
  alert_id: string
  triggered_at: string
  trigger_value: string
  action_taken: string
}

export const ALERT_TYPE_LABELS: Record<AlertType, string> = {
  price_above: '价格突破上限 Price Above',
  price_below: '价格跌破下限 Price Below',
  earnings_date: '财报日提醒 Earnings Date',
  re_analyze: '定期重新分析 Re-analyze',
  custom: '自定义事件 Custom',
}

export const FREQUENCY_OPTIONS = [
  { value: '0 8 * * 1', label: '每周一 Weekly (Monday)' },
  { value: '0 8 * * *', label: '每日 Daily' },
  { value: '0 8 1 * *', label: '每月1日 Monthly' },
]
