import { Wifi, WifiOff, Activity, Bell, TrendingUp } from 'lucide-react'
import type { WsMessage } from '../types'
import AlertBadge from './AlertBadge'
import type { AlertLevel } from '../types'

interface LiveFeedProps {
  messages: WsMessage[]
  isConnected: boolean
}

function EventIcon({ type }: { type: string }) {
  if (type === 'alert') return <Bell className="w-4 h-4 text-orange-500" />
  if (type === 'risk_update') return <TrendingUp className="w-4 h-4 text-blue-500" />
  return <Activity className="w-4 h-4 text-gray-400" />
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString()
  } catch {
    return iso
  }
}

export default function LiveFeed({ messages, isConnected }: LiveFeedProps) {
  const displayed = messages.slice(0, 10)

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h3 className="font-semibold text-gray-800">Live Feed</h3>
        <div className="flex items-center gap-1.5 text-xs">
          {isConnected ? (
            <>
              <Wifi className="w-3.5 h-3.5 text-green-500" />
              <span className="text-green-600 font-medium">Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="w-3.5 h-3.5 text-gray-400" />
              <span className="text-gray-500">Disconnected</span>
            </>
          )}
        </div>
      </div>

      <div className="divide-y divide-gray-50 max-h-80 overflow-y-auto">
        {displayed.length === 0 ? (
          <p className="text-sm text-gray-400 text-center py-8">No events yet</p>
        ) : (
          displayed.map((msg, i) => (
            <div key={i} className="flex items-start gap-3 px-4 py-2.5">
              <EventIcon type={msg.type} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-gray-700 capitalize">
                    {msg.type.replace('_', ' ')}
                  </span>
                  {msg.type === 'alert' && msg.level && (
                    <AlertBadge level={msg.level as AlertLevel} />
                  )}
                  {msg.region_id !== undefined && (
                    <span className="text-xs text-gray-400">Region #{msg.region_id}</span>
                  )}
                </div>
                {msg.message && (
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{msg.message}</p>
                )}
                {msg.calculated_risk !== undefined && (
                  <p className="text-xs text-gray-500 mt-0.5">
                    Risk: {Math.round(msg.calculated_risk)}
                  </p>
                )}
              </div>
              <span className="text-xs text-gray-400 shrink-0">{formatTime(msg.timestamp)}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
