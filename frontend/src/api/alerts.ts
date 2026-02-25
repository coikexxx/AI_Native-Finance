import client from './client'
import type { Alert, AlertCreate, AlertTrigger } from '../types/alert'

export const alertsApi = {
  list: () => client.get<Alert[]>('/alerts').then(r => r.data),
  create: (payload: AlertCreate) => client.post<Alert>('/alerts', payload).then(r => r.data),
  update: (id: string, payload: Partial<Alert>) =>
    client.put<Alert>(`/alerts/${id}`, payload).then(r => r.data),
  delete: (id: string) => client.delete(`/alerts/${id}`),
  history: (id: string) =>
    client.get<AlertTrigger[]>(`/alerts/${id}/history`).then(r => r.data),
}
