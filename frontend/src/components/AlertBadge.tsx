import type { AlertLevel } from '../types'

interface AlertBadgeProps {
  level: AlertLevel
}

const config: Record<AlertLevel, { label: string; classes: string }> = {
  low: { label: 'Low', classes: 'bg-blue-100 text-blue-800' },
  medium: { label: 'Medium', classes: 'bg-yellow-100 text-yellow-800' },
  high: { label: 'High', classes: 'bg-orange-100 text-orange-800' },
  critical: { label: 'Critical', classes: 'bg-red-100 text-red-800' },
}

export default function AlertBadge({ level }: AlertBadgeProps) {
  const { label, classes } = config[level] ?? config.low
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${classes}`}>
      {label}
    </span>
  )
}
