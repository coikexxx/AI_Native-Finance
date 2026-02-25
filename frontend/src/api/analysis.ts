import client from './client'
import type { AnalysisJob } from '../types/analysis'

export const analysisApi = {
  start: (ticker: string) =>
    client.post<{ job_id: string; status: string; ticker: string; created_at: string }>(
      '/analysis',
      { ticker }
    ).then(r => r.data),

  get: (jobId: string) =>
    client.get<AnalysisJob>(`/analysis/${jobId}`).then(r => r.data),

  history: (limit = 20) =>
    client.get<AnalysisJob[]>('/analysis/history', { params: { limit } }).then(r => r.data),
}
