import { useState, FormEvent } from 'react'
import { useAnalysis } from '../../hooks/useAnalysis'

export function TickerInput() {
  const [ticker, setTicker] = useState('')
  const { startAnalysis, loading, error } = useAnalysis()

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const t = ticker.trim().toUpperCase()
    if (!t) return
    startAnalysis(t)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-slate-100 mb-2">
          AI 投研助手
        </h1>
        <p className="text-slate-400 text-base">
          A股 / 港股 / BTC 全面投研分析
        </p>
        <p className="text-slate-500 text-sm mt-1">
          支持 A股（沪市6开头，深市0/3开头）、港股、比特币 · AI 自动完成行业、财务、估值、风险研究
        </p>
      </div>

      <form onSubmit={handleSubmit} className="relative">
        <div className="flex gap-3">
          <input
            type="text"
            value={ticker}
            onChange={e => setTicker(e.target.value.toUpperCase())}
            placeholder="输入代码 e.g. 600519, 0700, BTC"
            className="input flex-1 text-lg h-14 px-5 font-mono tracking-wider"
            maxLength={10}
            autoFocus
            disabled={loading}
            aria-label="Stock ticker input"
          />
          <button
            type="submit"
            disabled={loading || !ticker.trim()}
            className="btn-primary h-14 px-8 text-base"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                启动中...
              </span>
            ) : (
              '开始分析 Analyze →'
            )}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-3 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="mt-4 flex gap-2 flex-wrap">
        {['600519', '000858', '0700', '9988', 'BTC'].map(t => (
          <button
            key={t}
            onClick={() => setTicker(t)}
            className="btn-ghost text-xs py-1 px-2 border border-slate-700"
          >
            {t}
          </button>
        ))}
      </div>
    </div>
  )
}
