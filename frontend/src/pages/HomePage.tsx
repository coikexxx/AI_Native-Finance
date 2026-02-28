import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { TickerInput } from '../components/research/TickerInput'
import { analysisApi } from '../api/analysis'
import type { AnalysisJob } from '../types/analysis'

const DECISION_COLORS: Record<string, string> = {
  Buy: 'text-emerald-400',
  Hold: 'text-amber-400',
  Watch: 'text-sky-400',
  No: 'text-red-400',
}

export function HomePage() {
  const [history, setHistory] = useState<AnalysisJob[]>([])

  useEffect(() => {
    analysisApi.history(10).then(setHistory).catch(() => {})
  }, [])

  return (
    <div className="space-y-10">
      <div className="pt-10">
        <TickerInput />
      </div>

      {history.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-slate-400 mb-3">最近分析 Recent Analyses</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {history.map(job => (
              <Link
                key={job.job_id}
                to={`/analysis/${job.job_id}`}
                className="card hover:border-slate-600 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-mono font-bold text-sky-400 text-lg">{job.ticker}</span>
                  {job.decision && (
                    <span className={`font-bold ${DECISION_COLORS[job.decision] || ''}`}>
                      {job.decision}
                    </span>
                  )}
                  {job.status === 'running' && (
                    <span className="badge bg-sky-900 text-sky-300 animate-pulse">运行中</span>
                  )}
                  {job.status === 'failed' && (
                    <span className="badge bg-red-900 text-red-300">失败</span>
                  )}
                </div>
                {job.scorecard && (
                  <div className="flex gap-3 text-xs text-slate-500">
                    <span>财务 {job.scorecard?.financial_quality_score?.toFixed(1)}</span>
                    <span>护城河 {job.scorecard?.moat_score?.toFixed(1)}</span>
                    <span>估值 {job.scorecard?.valuation_score?.toFixed(1)}</span>
                  </div>
                )}
                <div className="text-xs text-slate-600 mt-1">
                  {new Date(job.created_at).toLocaleString()}
                </div>
                {(job.model_used || job.input_tokens || job.output_tokens) && (
                  <div className="flex gap-2 text-xs text-slate-700 mt-0.5">
                    {job.model_used && (
                      <span>{job.model_used.replace('claude-', '')}</span>
                    )}
                    {((job.input_tokens ?? 0) + (job.output_tokens ?? 0)) > 0 && (
                      <span>{(((job.input_tokens ?? 0) + (job.output_tokens ?? 0)) / 1000).toFixed(1)}K tokens</span>
                    )}
                  </div>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Quick tips */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-slate-500">
        {[
          { icon: '🤖', title: '9个专家智能体', desc: '行业、财务、估值、风险、护城河等全方位分析' },
          { icon: '📊', title: '可审计的投研报告', desc: '每个结论都附有来源引用，透明可追溯' },
          { icon: '🔔', title: '智能提醒机制', desc: '价格提醒、财报日提醒、定期重新分析' },
        ].map(item => (
          <div key={item.title} className="card text-center">
            <div className="text-2xl mb-2">{item.icon}</div>
            <div className="font-medium text-slate-300 mb-1">{item.title}</div>
            <div className="text-xs">{item.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
