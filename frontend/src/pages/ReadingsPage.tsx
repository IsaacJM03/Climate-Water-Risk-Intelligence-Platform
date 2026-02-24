import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getReadings, getRegions } from '../api/client'

const PAGE_SIZE = 20

export default function ReadingsPage() {
  const [regionId, setRegionId] = useState<number | undefined>(undefined)
  const [page, setPage] = useState(1)

  const { data: regions = [] } = useQuery({
    queryKey: ['regions'],
    queryFn: getRegions,
  })

  const { data: readings = [], isLoading, error } = useQuery({
    queryKey: ['readings', regionId, page],
    queryFn: () => getReadings({ region_id: regionId, page, page_size: PAGE_SIZE }),
  })

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-gray-900">Readings</h2>

      {/* Filter */}
      <div>
        <select
          value={regionId ?? ''}
          onChange={(e) => {
            setRegionId(e.target.value ? Number(e.target.value) : undefined)
            setPage(1)
          }}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
        >
          <option value="">All regions</option>
          {regions.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
      </div>

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {error && <p className="text-sm text-red-600">Failed to load readings.</p>}

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 bg-gray-50 border-b border-gray-100">
                <th className="px-4 py-3 font-medium">Region</th>
                <th className="px-4 py-3 font-medium">Latitude</th>
                <th className="px-4 py-3 font-medium">Longitude</th>
                <th className="px-4 py-3 font-medium">Rainfall (mm)</th>
                <th className="px-4 py-3 font-medium">Temp (°C)</th>
                <th className="px-4 py-3 font-medium">Water Level (m)</th>
                <th className="px-4 py-3 font-medium">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {readings.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                    No readings found.
                  </td>
                </tr>
              ) : (
                readings.map((r) => (
                  <tr key={r.id} className="hover:bg-gray-50 text-gray-700">
                    <td className="px-4 py-2.5">#{r.region_id}</td>
                    <td className="px-4 py-2.5">{r.latitude}</td>
                    <td className="px-4 py-2.5">{r.longitude}</td>
                    <td className="px-4 py-2.5">{r.rainfall}</td>
                    <td className="px-4 py-2.5">{r.temperature}</td>
                    <td className="px-4 py-2.5">{r.water_level}</td>
                    <td className="px-4 py-2.5 text-gray-400 text-xs">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
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
          disabled={readings.length < PAGE_SIZE}
          onClick={() => setPage((p) => p + 1)}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 disabled:opacity-40 hover:bg-gray-50"
        >
          Next
        </button>
      </div>
    </div>
  )
}
