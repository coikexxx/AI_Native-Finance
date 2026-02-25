import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { analysisApi } from '../api/analysis'
import { useAnalysisStore } from '../store/analysisStore'

export function useAnalysis() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { setCurrentJob, initAgents, reset } = useAnalysisStore()

  const startAnalysis = useCallback(async (ticker: string) => {
    setLoading(true)
    setError(null)
    reset()
    initAgents()

    try {
      const job = await analysisApi.start(ticker.trim().toUpperCase())
      setCurrentJob({
        job_id: job.job_id,
        ticker: job.ticker,
        status: 'running',
        created_at: job.created_at,
      })
      navigate(`/analysis/${job.job_id}`)
    } catch (e: unknown) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }, [navigate, setCurrentJob, initAgents, reset])

  return { startAnalysis, loading, error }
}
