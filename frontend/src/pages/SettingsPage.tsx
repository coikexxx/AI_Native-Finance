import { useEffect, useState } from 'react'
import { useSettingsStore } from '../store/settingsStore'
import { AVAILABLE_MODELS } from '../types/settings'

export function SettingsPage() {
  const { settings, loading, saving, testing, saveResult, testResult, load, save, testConnection, clearFeedback } =
    useSettingsStore()

  const [modelName, setModelName] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [maxTokens, setMaxTokens] = useState(8192)
  const [showKey, setShowKey] = useState(false)

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (settings) {
      setModelName(settings.model_name)
      setMaxTokens(settings.max_tokens)
    }
  }, [settings])

  const handleSave = async () => {
    clearFeedback()
    await save({ model_name: modelName, api_key: apiKey, max_tokens: maxTokens })
    setApiKey('')  // Clear the field after save
  }

  const handleTest = async () => {
    clearFeedback()
    await testConnection()
  }

  if (loading && !settings) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">加载中 Loading...</div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">设置 Settings</h1>
        <p className="text-slate-500 text-sm mt-1">配置 AI 模型和 API 密钥 Configure AI model and API credentials</p>
      </div>

      {/* Model Selection */}
      <div className="card space-y-4">
        <h2 className="text-base font-semibold text-slate-200">模型选择 Model</h2>

        <div className="space-y-1">
          <label className="text-sm text-slate-400">AI 模型</label>
          <select
            value={modelName}
            onChange={e => setModelName(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-sky-500"
          >
            {AVAILABLE_MODELS.map(m => (
              <option key={m.id} value={m.id}>{m.label}</option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-sm text-slate-400">最大 Token 数 Max Tokens</label>
          <input
            type="number"
            min={1024}
            max={32768}
            step={1024}
            value={maxTokens}
            onChange={e => setMaxTokens(Number(e.target.value))}
            className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-sky-500"
          />
          <p className="text-xs text-slate-600">建议 8192，最大 32768 / Recommended 8192, max 32768</p>
        </div>
      </div>

      {/* API Key */}
      <div className="card space-y-4">
        <h2 className="text-base font-semibold text-slate-200">API 密钥 API Key</h2>
        {settings?.api_key_set && (
          <div className="flex items-center gap-2 text-sm text-emerald-400">
            <span>✓</span>
            <span>已配置自定义 API 密钥 Custom API key is set</span>
          </div>
        )}
        <div className="space-y-1">
          <label className="text-sm text-slate-400">
            {settings?.api_key_set ? '更新 API 密钥（留空保持不变）Update API Key (leave blank to keep current)' : 'Anthropic API Key'}
          </label>
          <div className="flex gap-2">
            <input
              type={showKey ? 'text' : 'password'}
              value={apiKey}
              onChange={e => setApiKey(e.target.value)}
              placeholder={settings?.api_key_set ? '••••••••（不变）' : 'sk-ant-...'}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-sky-500 font-mono"
            />
            <button
              onClick={() => setShowKey(v => !v)}
              className="btn-ghost text-xs px-3"
            >
              {showKey ? '隐藏' : '显示'}
            </button>
          </div>
          <p className="text-xs text-slate-600">
            密钥保存在本地数据库中，从不在接口中返回 / Key stored in local DB, never returned via API
          </p>
        </div>
      </div>

      {/* Action Row */}
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={handleSave}
          disabled={saving || !modelName}
          className="btn-primary"
        >
          {saving ? '保存中...' : '保存设置 Save'}
        </button>

        <button
          onClick={handleTest}
          disabled={testing}
          className="btn-ghost"
        >
          {testing ? '测试中...' : '测试连接 Test Connection'}
        </button>

        {/* Save feedback */}
        {saveResult === 'success' && (
          <span className="text-sm text-emerald-400">✓ 已保存 Saved</span>
        )}
        {saveResult === 'error' && (
          <span className="text-sm text-red-400">✗ 保存失败 Save failed</span>
        )}
      </div>

      {/* Test Connection Result */}
      {testResult && (
        <div className={`card border ${testResult.ok ? 'border-emerald-800 bg-emerald-900/20' : 'border-red-800 bg-red-900/20'}`}>
          {testResult.ok ? (
            <div className="text-sm text-emerald-300">
              ✓ 连接成功 Connection OK — 模型: {testResult.model}
            </div>
          ) : (
            <div className="text-sm text-red-300">
              ✗ 连接失败 Connection failed: {testResult.error}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
