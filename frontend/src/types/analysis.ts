export interface Scorecard {
  financial_quality_score: number
  moat_score: number
  valuation_score: number
  risk_score: number
  overall_score: number
}

export interface EvidenceReference {
  citation_key: string
  agent_name: string
  source_label: string
  source_type: string
  excerpt: string
  source_url?: string
}

export interface ScenarioResult {
  scenario_name: string
  probability_pct: number
  intrinsic_value: number
  return_pct: number
}

export interface AnalysisJob {
  job_id: string
  ticker: string
  status: 'pending' | 'running' | 'complete' | 'failed'
  created_at: string
  completed_at?: string
  error_message?: string
  scorecard?: Scorecard
  decision?: 'Buy' | 'Hold' | 'Watch' | 'No'
  decision_rationale?: string
  investment_memo_md?: string
  evidence_items?: EvidenceReference[]
  scenario_outputs?: ScenarioResult[]
}

export interface AgentStatus {
  agent_name: string
  display_name?: string
  status: 'pending' | 'running' | 'complete' | 'failed'
  progress_pct: number
  message?: string
}

export interface StreamEvent {
  event_type: string
  agent_name?: string
  payload: Record<string, unknown>
}

// Map display names
export const AGENT_DISPLAY_NAMES: Record<string, string> = {
  IndustryAgent: '行业结构 Industry',
  FinancialQualityAgent: '财务质量 Financial',
  ManagementAgent: '管理层 Management',
  BusinessModelAgent: '商业模式 Biz Model',
  MoatAgent: '护城河 Moat',
  ValuationAgent: '估值 Valuation',
  RiskAgent: '风险 Risk',
  ThesisAgent: '投资论点 Thesis',
  MonitoringAgent: '监控 Monitoring',
}

export const ALL_AGENTS = Object.keys(AGENT_DISPLAY_NAMES)
