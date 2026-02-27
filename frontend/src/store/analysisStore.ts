import { create } from 'zustand'
import type { AnalysisJob, AgentStatus, ALL_AGENTS } from '../types/analysis'
import { AGENT_DISPLAY_NAMES } from '../types/analysis'

interface AnalysisState {
  currentJob: AnalysisJob | null
  agentStatuses: Record<string, AgentStatus>
  streamingPhase: string
  notifications: { id: string; message: string; type: string }[]

  setCurrentJob: (job: AnalysisJob) => void
  updateAgentStatus: (name: string, updates: Partial<AgentStatus>) => void
  setPhase: (phase: string) => void
  initAgents: () => void
  updateJobResult: (data: Partial<AnalysisJob>) => void
  addNotification: (msg: string, type?: string) => void
  dismissNotification: (id: string) => void
  reset: () => void
}

const defaultAgentStatuses = (): Record<string, AgentStatus> =>
  Object.keys(AGENT_DISPLAY_NAMES).reduce((acc, name) => {
    acc[name] = {
      agent_name: name,
      display_name: AGENT_DISPLAY_NAMES[name],
      status: 'pending',
      progress_pct: 0,
    }
    return acc
  }, {} as Record<string, AgentStatus>)

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  currentJob: null,
  agentStatuses: defaultAgentStatuses(),
  streamingPhase: '',
  notifications: [],

  setCurrentJob: (job) => set({ currentJob: job }),

  updateAgentStatus: (name, updates) =>
    set(state => {
      const current = state.agentStatuses[name]
      if (!current) return state
      const next = { ...current, ...updates }

      if (
        current.status === next.status &&
        current.progress_pct === next.progress_pct &&
        current.message === next.message &&
        current.display_name === next.display_name
      ) {
        return state
      }

      return {
        agentStatuses: {
          ...state.agentStatuses,
          [name]: next,
        },
      }
    }),

  setPhase: (phase) => set({ streamingPhase: phase }),

  initAgents: () => set({ agentStatuses: defaultAgentStatuses() }),

  updateJobResult: (data) =>
    set(state => ({
      currentJob: state.currentJob ? { ...state.currentJob, ...data } : null,
    })),

  addNotification: (message, type = 'info') =>
    set(state => ({
      notifications: [
        ...state.notifications,
        { id: Date.now().toString(), message, type },
      ].slice(-5), // Keep last 5
    })),

  dismissNotification: (id) =>
    set(state => ({
      notifications: state.notifications.filter(n => n.id !== id),
    })),

  reset: () => set({ currentJob: null, agentStatuses: defaultAgentStatuses(), streamingPhase: '' }),
}))
