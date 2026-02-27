import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useShallow } from 'zustand/react/shallow'
import { useSSE } from '../hooks/useSSE'
import { useAnalysisStore } from '../store/analysisStore'
import { analysisApi } from '../api/analysis'
import { AgentStatusBoard } from '../components/research/AgentStatusBoard'
import { DecisionBadge } from '../components/research/DecisionBadge'
import { Scorecard } from '../components/research/Scorecard'
import { InvestmentMemo } from '../components/research/InvestmentMemo'
import { EvidencePack } from '../components/research/EvidencePack'
import { AlertForm } from '../components/alerts/AlertForm'
import type { StreamEvent, Scorecard as ScorecardType } from '../types/analysis'

export function AnalysisPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const [isStreaming, setIsStreaming] = useState(true)

  const currentJob = useAnalysisStore(state => state.currentJob)
  const { updateJobResult, updateAgentStatus, setPhase, setCurrentJob } = useAnalysisStore(
    useShallow(state => ({
      updateJobResult: state.updateJobResult,
      updateAgentStatus: state.updateAgentStatus,
      setPhase: state.setPhase,
      setCurrentJob: state.setCurrentJob,
    }))
  )

  const handleStreamEvent = useCallback((event: StreamEvent) => {
    const { event_type, agent_name, payload } = event

    switch (event_type) {
      case 'phase_start':
        setPhase((payload.message as string) || '')
        break
      case 'agent_start':
        if (agent_name) {
          updateAgentStatus(agent_name, {
            status: 'running',
            display_name: (payload.display_name as string) || agent_name,
          })
        }
        break
      case 'agent_progress':
        if (agent_name) {
          updateAgentStatus(agent_name, {
            progress_pct: (payload.progress_pct as number) || 0,
            message: (payload.message as string) || undefined,
          })
        }
        break
      case 'agent_complete':
        if (agent_name) {
          updateAgentStatus(agent_name, { status: 'complete', progress_pct: 100 })
        }
        break
      case 'agent_error':
        if (agent_name) {
          updateAgentStatus(agent_name, { status: 'failed' })
        }
        break
      case 'complete':
        setIsStreaming(false)
        setPhase('')
        updateJobResult({
          status: 'complete',
          decision: payload.decision as 'Buy' | 'Hold' | 'Watch' | 'No',
          scorecard: payload.scorecard as ScorecardType,
          decision_rationale: payload.decision_rationale as string,
        })
        if (jobId) {
          analysisApi.get(jobId).then(job => setCurrentJob(job)).catch(() => {})
        }
        break
      case 'error':
        setIsStreaming(false)
        updateJobResult({ status: 'failed', error_message: payload.message as string })
        break
    }
  }, [jobId, setCurrentJob, setPhase, updateAgentStatus, updateJobResult])

  // Load existing analysis if navigating directly to URL
  useEffect(() => {
    if (!jobId) return
    analysisApi.get(jobId).then(job => {
      setCurrentJob(job)
      if (job.status === 'complete' || job.status === 'failed') {
        setIsStreaming(false)
      }
    }).catch(() => {})
  }, [jobId, setCurrentJob])

  // SSE stream for live updates
  useSSE(
    jobId && isStreaming ? `/api/v1/analysis/${jobId}/stream` : '',
    {
      enabled: isStreaming && !!jobId,
      onMessage: (e) => {
        try {
          const event: StreamEvent = JSON.parse(e.data)
          handleStreamEvent(event)
        } catch {}
      },
      onError: () => {},
    }
  )

  if (!currentJob) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-400">加载中 Loading...</div>
      </div>
    )
  }

  const isComplete = currentJob.status === 'complete'
  const isFailed = currentJob.status === 'failed'

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 font-mono">{currentJob.ticker}</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {isComplete ? '分析完成 Analysis Complete' :
             isFailed ? '分析失败 Analysis Failed' :
             '分析进行中 Analysis in Progress...'}
          </p>
        </div>
        {isComplete && (
          <button
            onClick={() => {
              const ticker = currentJob.ticker
              window.location.href = `/`
              sessionStorage.setItem('prefill_ticker', ticker)
            }}
            className="btn-ghost text-xs"
          >
            新分析 New Analysis →
          </button>
        )}
      </div>

      {isFailed && (
        <div className="card border border-red-800 bg-red-900/20">
          <p className="text-red-300">分析失败: {currentJob.error_message}</p>
        </div>
      )}

      {(currentJob.status === 'running' || currentJob.status === 'pending') && (
        <AgentStatusBoard />
      )}

      {isComplete && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="space-y-4">
            {currentJob.decision && (
              <DecisionBadge
                decision={currentJob.decision}
                rationale={currentJob.decision_rationale}
              />
            )}
            {currentJob.scorecard && (
              <Scorecard scorecard={currentJob.scorecard} />
            )}
            <AlertForm defaultTicker={currentJob.ticker} />
          </div>

          <div className="lg:col-span-2 space-y-4">
            {currentJob.investment_memo_md && (
              <InvestmentMemo
                memoMd={currentJob.investment_memo_md}
                ticker={currentJob.ticker}
              />
            )}
            {currentJob.evidence_items && currentJob.evidence_items.length > 0 && (
              <EvidencePack evidence={currentJob.evidence_items} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}
