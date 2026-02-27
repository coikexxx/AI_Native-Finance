import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'

// ─── Types ────────────────────────────────────────────────────────────────────

interface PriceSnapshot {
  ticker: string
  price: number | null
  prev_close: number | null
  change_pct: number | null
  volume: number | null
  avg_volume: number | null
  volume_ratio: number | null
  last_checked_at: string | null
  market: string | null
  currency: string | null
}

interface NewsItem {
  ticker: string
  title: string
  summary: string
  link: string
  published: string
  published_ts: number | null
  significance: 'high' | 'medium' | 'low'
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtPct(v: number | null): string {
  if (v === null) return '—'
  const sign = v >= 0 ? '+' : ''
  return `${sign}${v.toFixed(2)}%`
}

function fmtPrice(v: number | null, currency = '$'): string {
  if (v === null) return '—'
  return `${currency}${v.toFixed(2)}`
}

function marketBadge(market: string | null) {
  if (market === 'a_share') return <span className="text-xs px-1.5 py-0.5 rounded bg-red-900/40 text-red-300 font-medium">A股</span>
  if (market === 'hk') return <span className="text-xs px-1.5 py-0.5 rounded bg-blue-900/40 text-blue-300 font-medium">港股</span>
  if (market === 'crypto') return <span className="text-xs px-1.5 py-0.5 rounded bg-amber-900/40 text-amber-300 font-medium">BTC</span>
  return null
}

function fmtVolRatio(v: number | null): string {
  if (v === null) return '—'
  return `${v.toFixed(1)}x`
}

function fmtVolume(v: number | null): string {
  if (v === null) return '—'
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`
  if (v >= 1_000) return `${(v / 1_000).toFixed(0)}K`
  return String(v)
}

function fmtAge(published: string): string {
  try {
    const d = new Date(published)
    const diff = Date.now() - d.getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    return `${Math.floor(hrs / 24)}d ago`
  } catch {
    return published
  }
}

function pctClass(v: number | null): string {
  if (v === null) return 'text-slate-500'
  if (v >= 2) return 'text-emerald-400 font-semibold'
  if (v > 0) return 'text-emerald-400'
  if (v <= -2) return 'text-red-400 font-semibold'
  if (v < 0) return 'text-red-400'
  return 'text-slate-400'
}

function pctIcon(v: number | null): string {
  if (v === null) return ''
  if (v >= 2) return '📈'
  if (v > 0) return '▲'
  if (v <= -2) return '📉'
  if (v < 0) return '▼'
  return '—'
}

function volIcon(ratio: number | null): string | null {
  if (ratio === null || ratio < 2) return null
  if (ratio >= 3) return '🔥'
  return '⚡'
}

function sigBadge(sig: 'high' | 'medium' | 'low') {
  if (sig === 'high') return (
    <span className="text-xs px-1.5 py-0.5 rounded bg-red-900/50 text-red-300 font-medium">重要</span>
  )
  if (sig === 'medium') return (
    <span className="text-xs px-1.5 py-0.5 rounded bg-amber-900/50 text-amber-300 font-medium">关注</span>
  )
  return null
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function PriceCard({ snap }: { snap: PriceSnapshot }) {
  const vi = volIcon(snap.volume_ratio)
  const currency = snap.currency || '$'
  return (
    <div className="bg-slate-800/60 border border-slate-700 rounded-xl p-4 flex flex-col gap-2 hover:border-slate-600 transition-colors">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              sessionStorage.setItem('prefill_ticker', snap.ticker)
              window.location.href = '/'
            }}
            className="font-mono font-bold text-sky-400 text-lg hover:text-sky-300 bg-transparent border-0 p-0 cursor-pointer"
          >
            {snap.ticker}
          </button>
          {marketBadge(snap.market)}
        </div>
        <span className="text-xs text-slate-600">
          {vi && <span className="mr-1">{vi}</span>}
          {snap.last_checked_at
            ? `${new Date(snap.last_checked_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })} checked`
            : 'live'}
        </span>
      </div>

      <div className="flex items-baseline gap-3">
        <span className="text-2xl font-mono text-slate-100">{fmtPrice(snap.price, currency)}</span>
        <span className={`text-sm font-mono ${pctClass(snap.change_pct)}`}>
          {pctIcon(snap.change_pct)} {fmtPct(snap.change_pct)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-x-4 text-xs text-slate-500 mt-1">
        <div>
          <span className="text-slate-600">前收盘</span>
          <span className="ml-1 text-slate-400">{fmtPrice(snap.prev_close, currency)}</span>
        </div>
        <div>
          <span className="text-slate-600">成交量</span>
          <span className={`ml-1 ${snap.volume_ratio && snap.volume_ratio >= 2 ? 'text-amber-400' : 'text-slate-400'}`}>
            {fmtVolume(snap.volume)}
            {snap.volume_ratio !== null && (
              <span className="ml-1 text-slate-500">({fmtVolRatio(snap.volume_ratio)})</span>
            )}
          </span>
        </div>
      </div>
    </div>
  )
}

function NewsRow({ item }: { item: NewsItem }) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-slate-800 last:border-0">
      <div className="flex-shrink-0 mt-0.5">
        <span className="font-mono text-xs font-bold text-sky-500 bg-sky-900/30 px-1.5 py-0.5 rounded">
          {item.ticker}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start gap-2 flex-wrap">
          {sigBadge(item.significance)}
          <a
            href={item.link}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-slate-200 hover:text-sky-300 transition-colors leading-snug line-clamp-2"
          >
            {item.title}
          </a>
        </div>
        {item.summary && (
          <p className="text-xs text-slate-500 mt-1 line-clamp-2">{item.summary}</p>
        )}
      </div>
      <div className="flex-shrink-0 text-xs text-slate-600 whitespace-nowrap mt-0.5">
        {fmtAge(item.published)}
      </div>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export function MonitorPage() {
  const [prices, setPrices] = useState<PriceSnapshot[]>([])
  const [news, setNews] = useState<NewsItem[]>([])
  const [loadingPrices, setLoadingPrices] = useState(true)
  const [loadingNews, setLoadingNews] = useState(true)
  const [checkTriggered, setCheckTriggered] = useState(false)
  const [newsFilter, setNewsFilter] = useState<'all' | 'high' | 'medium'>('all')
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const loadPrices = useCallback(async () => {
    setLoadingPrices(true)
    try {
      const r = await axios.get<PriceSnapshot[]>('/api/v1/monitor/prices')
      setPrices(r.data)
      setLastRefresh(new Date())
    } catch {
      // silent
    } finally {
      setLoadingPrices(false)
    }
  }, [])

  const loadNews = useCallback(async () => {
    setLoadingNews(true)
    try {
      const r = await axios.get<NewsItem[]>('/api/v1/monitor/news?max_per_ticker=8')
      setNews(r.data)
    } catch {
      // silent
    } finally {
      setLoadingNews(false)
    }
  }, [])

  useEffect(() => {
    loadPrices()
    loadNews()
  }, [loadPrices, loadNews])

  // Auto-refresh prices every 60 seconds
  useEffect(() => {
    const id = setInterval(loadPrices, 60_000)
    return () => clearInterval(id)
  }, [loadPrices])

  const triggerCheck = async () => {
    try {
      await axios.post('/api/v1/monitor/check-now')
      setCheckTriggered(true)
      setTimeout(() => setCheckTriggered(false), 3000)
    } catch {
      // silent
    }
  }

  const filteredNews = news.filter(n => {
    if (newsFilter === 'all') return true
    return n.significance === newsFilter
  })

  const isEmpty = !loadingPrices && prices.length === 0

  return (
    <div className="max-w-6xl mx-auto space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">行情监控 Monitor</h1>
          <p className="text-slate-500 text-sm mt-1">
            自动监控价格异动（±2%）和重要新闻 · 每5分钟检查价格，每30分钟检查新闻
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastRefresh && (
            <span className="text-xs text-slate-600">
              行情更新: {lastRefresh.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          )}
          <button
            onClick={loadPrices}
            className="btn-ghost text-xs border border-slate-700 px-3 py-1.5"
            disabled={loadingPrices}
          >
            {loadingPrices ? '刷新中…' : '刷新行情'}
          </button>
          <button
            onClick={triggerCheck}
            disabled={checkTriggered}
            className="btn-primary text-xs px-3 py-1.5"
          >
            {checkTriggered ? '✓ 检查已触发' : '立即检查异动'}
          </button>
        </div>
      </div>

      {isEmpty ? (
        /* Empty state */
        <div className="card text-center py-12 text-slate-500">
          <div className="text-4xl mb-3">📡</div>
          <p className="font-medium text-slate-400">暂无监控股票</p>
          <p className="text-sm mt-1">
            请先在{' '}
            <Link to="/watchlist" className="text-sky-400 hover:underline">自选股</Link>
            {' '}中添加股票代码
          </p>
        </div>
      ) : (
        <>
          {/* ── Price Grid ──────────────────────────────────────────────── */}
          <section>
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
              实时行情快照
            </h2>
            {loadingPrices && prices.length === 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="bg-slate-800/40 border border-slate-700 rounded-xl p-4 animate-pulse h-28" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {prices.map(snap => (
                  <PriceCard key={snap.ticker} snap={snap} />
                ))}
              </div>
            )}
          </section>

          {/* ── News Feed ───────────────────────────────────────────────── */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                新闻与舆情动态
              </h2>
              <div className="flex items-center gap-1">
                {(['all', 'high', 'medium'] as const).map(f => (
                  <button
                    key={f}
                    onClick={() => setNewsFilter(f)}
                    className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
                      newsFilter === f
                        ? 'bg-sky-900/50 text-sky-300'
                        : 'text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    {f === 'all' ? '全部' : f === 'high' ? '🔴 重要' : '🟡 关注'}
                  </button>
                ))}
                <button
                  onClick={loadNews}
                  className="text-xs text-slate-600 hover:text-slate-400 ml-2"
                  disabled={loadingNews}
                >
                  {loadingNews ? '…' : '刷新'}
                </button>
              </div>
            </div>

            <div className="card">
              {loadingNews && news.length === 0 ? (
                <div className="space-y-3 py-2">
                  {[...Array(5)].map((_, i) => (
                    <div key={i} className="flex gap-3 animate-pulse">
                      <div className="w-12 h-4 bg-slate-700 rounded" />
                      <div className="flex-1 h-4 bg-slate-700 rounded" />
                    </div>
                  ))}
                </div>
              ) : filteredNews.length === 0 ? (
                <p className="text-slate-500 text-center py-6 text-sm">
                  {newsFilter === 'all' ? '暂无新闻数据' : '当前筛选条件下无新闻'}
                </p>
              ) : (
                <div>
                  {filteredNews.map((item, i) => (
                    <NewsRow key={`${item.ticker}-${i}`} item={item} />
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* ── Monitor Status ──────────────────────────────────────────── */}
          <section className="card">
            <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
              监控配置
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <div>
                  <div className="text-slate-300 font-medium">价格异动监控</div>
                  <div className="text-slate-500 text-xs">触发阈值：±2% · A股 09:30–15:00 CST | 港股 09:30–16:00 HKT | BTC 24/7</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <div>
                  <div className="text-slate-300 font-medium">成交量异动</div>
                  <div className="text-slate-500 text-xs">触发阈值：成交量 ≥ 2× 三个月均值</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <div>
                  <div className="text-slate-300 font-medium">新闻与舆情</div>
                  <div className="text-slate-500 text-xs">每30分钟扫描：财报/监管/并购/分析师评级等</div>
                </div>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
