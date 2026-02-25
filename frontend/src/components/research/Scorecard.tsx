import {
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ResponsiveContainer, Tooltip,
} from 'recharts'
import type { Scorecard as ScorecardType } from '../../types/analysis'

interface Props {
  scorecard: ScorecardType
}

export function Scorecard({ scorecard }: Props) {
  const data = [
    { subject: '财务质量\nFinancial', value: scorecard.financial_quality_score, fullMark: 10 },
    { subject: '护城河\nMoat', value: scorecard.moat_score, fullMark: 10 },
    { subject: '估值\nValuation', value: scorecard.valuation_score, fullMark: 10 },
    { subject: '低风险\nLow Risk', value: 10 - scorecard.risk_score + 1, fullMark: 10 },
  ]

  const getScoreColor = (score: number) => {
    if (score >= 7.5) return 'text-emerald-400'
    if (score >= 5) return 'text-amber-400'
    return 'text-red-400'
  }

  return (
    <div className="card">
      <h2 className="section-title mb-4">评分卡 Scorecard</h2>

      {/* Radar chart */}
      <div className="h-52">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 20 }}>
            <PolarGrid stroke="#334155" />
            <PolarAngleAxis
              dataKey="subject"
              tick={{ fill: '#94a3b8', fontSize: 10 }}
            />
            <Radar
              name="Score"
              dataKey="value"
              stroke="#0ea5e9"
              fill="#0ea5e9"
              fillOpacity={0.2}
              strokeWidth={2}
            />
            <Tooltip
              contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
              labelStyle={{ color: '#e2e8f0' }}
              itemStyle={{ color: '#0ea5e9' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Score breakdown */}
      <div className="mt-2 grid grid-cols-2 gap-3">
        {[
          { label: '财务质量', en: 'Financial Quality', value: scorecard.financial_quality_score },
          { label: '护城河', en: 'Economic Moat', value: scorecard.moat_score },
          { label: '估值吸引力', en: 'Valuation', value: scorecard.valuation_score },
          { label: '风险评分', en: 'Risk Score', value: scorecard.risk_score, inverted: true },
        ].map(item => (
          <div key={item.label} className="bg-slate-800/50 rounded-lg p-3">
            <div className="text-xs text-slate-500">{item.en}</div>
            <div className="text-xs text-slate-400">{item.label}</div>
            <div className={`text-2xl font-bold mt-1 ${getScoreColor(item.inverted ? 11 - item.value : item.value)}`}>
              {item.value.toFixed(1)}
              <span className="text-sm text-slate-500">/10</span>
            </div>
          </div>
        ))}
      </div>

      {/* Overall */}
      <div className="mt-3 p-3 bg-slate-800 rounded-lg flex justify-between items-center">
        <span className="text-slate-400 font-medium">综合评分 Overall</span>
        <span className={`text-3xl font-bold ${getScoreColor(scorecard.overall_score)}`}>
          {scorecard.overall_score.toFixed(1)}
          <span className="text-sm text-slate-500">/10</span>
        </span>
      </div>
    </div>
  )
}
