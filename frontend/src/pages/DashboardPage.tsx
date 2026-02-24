import { useQuery } from '@tanstack/react-query'
import { MapPin, Bell, AlertTriangle, Activity } from 'lucide-react'
import { getRegions, getAlerts } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import { useWebSocket } from '../hooks/useWebSocket'
import AlertBadge from '../components/AlertBadge'
import LiveFeed from '../components/LiveFeed'
import type { Alert } from '../types'

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string
  value: number | string
  icon: React.ElementType
  color: string
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex items-center gap-4">
      <div className={`rounded-full p-3 ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user, token } = useAuth()
  const { messages, isConnected } = useWebSocket(user?.orgId ?? null, token)

  const { data: regions = [] } = useQuery({
    queryKey: ['regions'],
    queryFn: getRegions,
    refetchInterval: 30_000,
  })

  const { data: allAlerts = [] } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => getAlerts({ page_size: 50 }),
    refetchInterval: 30_000,
  })

  const { data: unackedAlerts = [] } = useQuery({
    queryKey: ['alerts', 'unacked'],
    queryFn: () => getAlerts({ unacknowledged_only: true, page_size: 50 }),
    refetchInterval: 30_000,
  })

  const criticalAlerts = (allAlerts as Alert[]).filter((a) => a.level === 'critical')
  const recentAlerts = (allAlerts as Alert[]).slice(0, 5)

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">Dashboard</h2>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard
          label="Total Regions"
          value={regions.length}
          icon={MapPin}
          color="bg-blue-50 text-blue-600"
        />
        <StatCard
          label="Active Alerts"
          value={unackedAlerts.length}
          icon={Bell}
          color="bg-yellow-50 text-yellow-600"
        />
        <StatCard
          label="Critical Alerts"
          value={criticalAlerts.length}
          icon={AlertTriangle}
          color="bg-red-50 text-red-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent alerts */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
            <Activity className="w-4 h-4 text-gray-500" />
            <h3 className="font-semibold text-gray-800">Recent Alerts</h3>
          </div>
          <div className="divide-y divide-gray-50">
            {recentAlerts.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-8">No alerts</p>
            ) : (
              recentAlerts.map((alert) => (
                <div key={alert.id} className="px-5 py-3 flex items-start gap-3">
                  <AlertBadge level={alert.level} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-700 truncate">{alert.message}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Region #{alert.region_id} ·{' '}
                      {new Date(alert.created_at).toLocaleString()}
                    </p>
                  </div>
                  {alert.acknowledged && (
                    <span className="text-xs text-gray-400 shrink-0">Acked</span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Live feed */}
        <LiveFeed messages={messages} isConnected={isConnected} />
      </div>
    </div>
  )
}
