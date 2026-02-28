export interface ModelSettings {
  model_name: string
  api_key_set: boolean
  max_tokens: number
}

export interface SettingsUpdate {
  model_name: string
  api_key: string
  max_tokens: number
}

export interface TestConnectionResult {
  ok: boolean
  model?: string
  error?: string
}

export const AVAILABLE_MODELS = [
  { id: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6（推荐）' },
  { id: 'claude-opus-4-6', label: 'Claude Opus 4.6（最强）' },
  { id: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5（最快）' },
]
