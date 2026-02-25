import { create } from 'zustand'
import type { Alert } from '../types/alert'
import { alertsApi } from '../api/alerts'

interface AlertState {
  alerts: Alert[]
  loading: boolean
  error: string | null
  load: () => Promise<void>
  add: (a: Alert) => void
  remove: (id: string) => void
  toggle: (id: string) => Promise<void>
}

export const useAlertStore = create<AlertState>((set, get) => ({
  alerts: [],
  loading: false,
  error: null,

  load: async () => {
    set({ loading: true, error: null })
    try {
      const alerts = await alertsApi.list()
      set({ alerts, loading: false })
    } catch (e: unknown) {
      set({ error: e instanceof Error ? e.message : String(e), loading: false })
    }
  },

  add: (alert) => set(s => ({ alerts: [alert, ...s.alerts] })),

  remove: (id) => set(s => ({ alerts: s.alerts.filter(a => a.id !== id) })),

  toggle: async (id) => {
    const alert = get().alerts.find(a => a.id === id)
    if (!alert) return
    try {
      const updated = await alertsApi.update(id, { is_active: !alert.is_active })
      set(s => ({ alerts: s.alerts.map(a => a.id === id ? updated : a) }))
    } catch (e) {
      console.error('Failed to toggle alert:', e)
    }
  },
}))
