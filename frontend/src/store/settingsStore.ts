import { create } from 'zustand'
import { settingsApi } from '../api/settings'
import type { ModelSettings, SettingsUpdate, TestConnectionResult } from '../types/settings'

interface SettingsState {
  settings: ModelSettings | null
  loading: boolean
  saving: boolean
  testing: boolean
  saveResult: 'success' | 'error' | null
  testResult: TestConnectionResult | null

  load: () => Promise<void>
  save: (update: SettingsUpdate) => Promise<void>
  testConnection: () => Promise<void>
  clearFeedback: () => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: null,
  loading: false,
  saving: false,
  testing: false,
  saveResult: null,
  testResult: null,

  load: async () => {
    set({ loading: true })
    try {
      const data = await settingsApi.get()
      set({ settings: data, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  save: async (update: SettingsUpdate) => {
    set({ saving: true, saveResult: null })
    try {
      const data = await settingsApi.update(update)
      set({ settings: data, saving: false, saveResult: 'success' })
    } catch {
      set({ saving: false, saveResult: 'error' })
    }
  },

  testConnection: async () => {
    set({ testing: true, testResult: null })
    try {
      const result = await settingsApi.testConnection()
      set({ testResult: result, testing: false })
    } catch {
      set({ testResult: { ok: false, error: '请求失败 Request failed' }, testing: false })
    }
  },

  clearFeedback: () => set({ saveResult: null, testResult: null }),
}))
