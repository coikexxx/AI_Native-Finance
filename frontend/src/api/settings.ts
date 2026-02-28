import client from './client'
import type { ModelSettings, SettingsUpdate, TestConnectionResult } from '../types/settings'

export const settingsApi = {
  get: () =>
    client.get<ModelSettings>('/settings').then(r => r.data),

  update: (payload: SettingsUpdate) =>
    client.put<ModelSettings>('/settings', payload).then(r => r.data),

  testConnection: () =>
    client.post<TestConnectionResult>('/settings/test-connection').then(r => r.data),
}
