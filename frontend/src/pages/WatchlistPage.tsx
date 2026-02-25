import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { useAnalysis } from '../hooks/useAnalysis'

interface WatchlistItem {
  id: string
  ticker: string
  added_at: string
  current_price?: number
  notes?: string
}

export function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([])
  const [newTicker, setNewTicker] = useState('')
  const { startAnalysis } = useAnalysis()

  const load = () => {
    axios.get('/api/v1/watchlist').then(r => setItems(r.data)).catch(() => {})
  }

  useEffect(() => { load() }, [])

  const add = async () => {
    const t = newTicker.trim().toUpperCase()
    if (!t) return
    try {
      await axios.post('/api/v1/watchlist', { ticker: t })
      setNewTicker('')
      load()
    } catch {}
  }

  const remove = async (ticker: string) => {
    await axios.delete(`/api/v1/watchlist/${ticker}`)
    load()
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">自选股 Watchlist</h1>
        <p className="text-slate-500 text-sm mt-1">跟踪股票，一键触发分析</p>
      </div>

      {/* Add ticker */}
      <div className="card">
        <div className="flex gap-3">
          <input
            type="text"
            value={newTicker}
            onChange={e => setNewTicker(e.target.value.toUpperCase())}
            placeholder="添加股票代码 e.g. NVDA"
            className="input flex-1 font-mono"
            maxLength={10}
            onKeyDown={e => e.key === 'Enter' && add()}
          />
          <button onClick={add} className="btn-primary px-5">添加 Add</button>
        </div>
      </div>

      {/* Watchlist */}
      {items.length === 0 ? (
        <div className="card text-center py-8 text-slate-500">
          自选股为空 Watchlist is empty
        </div>
      ) : (
        <div className="card">
          <div className="space-y-1">
            {items.map(item => (
              <div key={item.id}
                className="flex items-center justify-between py-2.5 border-b border-slate-800 last:border-0">
                <div className="flex items-center gap-3">
                  <Link to={`/`} className="font-mono font-bold text-sky-400 text-lg hover:text-sky-300">
                    {item.ticker}
                  </Link>
                  {item.current_price && (
                    <span className="text-slate-300">${item.current_price.toFixed(2)}</span>
                  )}
                  <span className="text-slate-600 text-xs">{new Date(item.added_at).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => startAnalysis(item.ticker)}
                    className="btn-ghost text-xs border border-slate-700"
                  >
                    分析 Analyze
                  </button>
                  <button onClick={() => remove(item.ticker)}
                    className="text-slate-600 hover:text-red-400 transition-colors">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
