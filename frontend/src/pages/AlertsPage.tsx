import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle } from 'lucide-react'
import { getAlerts, acknowledgeAlert } from '../api/client'
import AlertBadge from '../components/AlertBadge'
import type { AlertLevel } from '../types'

const LEVELS: Array<{ value: string; label: string }> = [
  { value: '', label: 'All levels' },
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
]

const PAGE_SIZE = 20

export default function AlertsPage() {
  const qc = useQueryClient()
  const [level, setLevel] = useState('')
  const [unackedOnly, setUnackedOnly] = useState(false)
  const [page, setPage] = useState(1)

  const { data: alerts = [], isLoading, error } = useQuery({
    queryKey: ['alerts', level, unackedOnly, page],
    queryFn: () =>
      getAlerts({
        level: level || undefined,
        unacknowledged_only: unackedOnly,
        page,
        page_size: PAGE_SIZE,
      }),
  })

  const ackMutation = useMutation({
    mutationFn: (id: number) => acknowledgeAlert(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  })

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900">Alerts</h2>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <select
          value={level}
          onChange={(e) => { setLevel(e.target.value); setPage(1) }}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
        >
          {LEVELS.map((l) => (
            <option key={l.value} value={l.value}>
              {l.label}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input
            type="checkbox"
            checked={unackedOnly}
            onChange={(e) => { setUnackedOnly(e.target.checked); setPage(1) }}
            className="rounded accent-primary-600"
          />
          Unacknowledged only
        </label>
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {error && <p className="text-sm text-red-600">Failed to load alerts.</p>}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 bg-gray-50 border-b border-gray-100">
              <th className="px-4 py-3 font-medium">Level</th>
              <th className="px-4 py-3 font-medium">Message</th>
              <th className="px-4 py-3 font-medium">Region</th>
              <th className="px-4 py-3 font-medium">Time</th>
              <th className="px-4 py-3 font-medium">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {alerts.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  No alerts found.
                </td>
              </tr>
            ) : (
              alerts.map((alert) => (
                <tr key={alert.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <AlertBadge level={alert.level as AlertLevel} />
                  </td>
                  <td className="px-4 py-3 text-gray-700 max-w-xs truncate">{alert.message}</td>
                  <td className="px-4 py-3 text-gray-500">#{alert.region_id}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {new Date(alert.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    {alert.acknowledged ? (
                      <span className="flex items-center gap-1 text-xs text-green-600">
                        <CheckCircle className="w-3.5 h-3.5" />
                        Acked
                      </span>
                    ) : (
                      <button
                        onClick={() => ackMutation.mutate(alert.id)}
                        disabled={ackMutation.isPending}
                        className="text-xs text-primary-600 hover:text-primary-800 font-medium disabled:opacity-50"
                      >
                        Acknowledge
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center gap-3 justify-end">
        <button
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
        >
          Previous
        </button>
        <span className="text-sm text-gray-600">Page {page}</span>
        <button
          disabled={alerts.length < PAGE_SIZE}
          onClick={() => setPage((p) => p + 1)}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  )
}
