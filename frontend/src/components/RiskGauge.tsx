import { RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts'

interface RiskGaugeProps {
  value: number // 0–100
}

function riskColor(value: number): string {
  if (value < 30) return '#22c55e'  // green
  if (value < 60) return '#eab308'  // yellow
  if (value < 85) return '#f97316'  // orange
  return '#ef4444'                   // red
}

function riskLabel(value: number): string {
  if (value < 30) return 'Low'
  if (value < 60) return 'Moderate'
  if (value < 85) return 'High'
  return 'Critical'
}

export default function RiskGauge({ value }: RiskGaugeProps) {
  const safeValue = Math.min(100, Math.max(0, Math.round(value)))
  const color = riskColor(safeValue)
  const data = [{ name: 'risk', value: safeValue, fill: color }]

  return (
    <div className="relative flex flex-col items-center">
      <RadialBarChart
        width={180}
        height={180}
        cx={90}
        cy={90}
        innerRadius={60}
        outerRadius={80}
        barSize={14}
        data={data}
        startAngle={210}
        endAngle={-30}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar background dataKey="value" cornerRadius={6} angleAxisId={0} />
      </RadialBarChart>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-2xl font-bold" style={{ color }}>{safeValue}</span>
        <span className="text-xs font-medium text-gray-500">{riskLabel(safeValue)}</span>
      </div>
    </div>
  )
}
