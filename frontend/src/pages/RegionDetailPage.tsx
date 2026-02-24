import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { ArrowLeft, Plus } from 'lucide-react'
import {
  getRegion,
  getRegionRisk,
  getRegionForecast,
  getReadings,
  createReading,
} from '../api/client'
import RiskGauge from '../components/RiskGauge'
import type { CreateReadingPayload } from '../types'

const HORIZONS = [7, 14, 30]

function ProgressBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-2.5">
        <div
          className="h-2.5 rounded-full"
          style={{ width: `${Math.min(100, value * 100).toFixed(1)}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-medium text-gray-700 w-10 text-right">
        {(value * 100).toFixed(1)}%
      </span>
    </div>
  )
}

function AddReadingForm({
  regionId,
  onDone,
}: {
  regionId: number
  onDone: () => void
}) {
  const qc = useQueryClient()
  const [form, setForm] = useState<Record<string, string>>({
    latitude: '',
    longitude: '',
    rainfall: '',
    temperature: '',
    water_level: '',
  })
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: (payload: CreateReadingPayload) => createReading(regionId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['readings', regionId] })
      onDone()
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to submit reading.'
      setError(String(msg))
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    mutation.mutate({
      latitude: Number(form.latitude),
      longitude: Number(form.longitude),
      rainfall: Number(form.rainfall),
      temperature: Number(form.temperature),
      water_level: Number(form.water_level),
    })
  }

  const fields: Array<{ key: string; label: string; placeholder: string }> = [
    { key: 'latitude', label: 'Latitude', placeholder: '0.0000' },
    { key: 'longitude', label: 'Longitude', placeholder: '0.0000' },
    { key: 'rainfall', label: 'Rainfall (mm)', placeholder: '0' },
    { key: 'temperature', label: 'Temperature (°C)', placeholder: '25' },
    { key: 'water_level', label: 'Water Level (m)', placeholder: '0' },
  ]

  return (
    <form onSubmit={handleSubmit} className="bg-blue-50 border border-blue-200 rounded-xl p-4 space-y-3">
      <h4 className="font-semibold text-gray-800 text-sm">Add Reading</h4>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {fields.map(({ key, label, placeholder }) => (
          <div key={key}>
            <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
            <input
              required
              type="number"
              step="any"
              placeholder={placeholder}
              value={form[key]}
              onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        ))}
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={mutation.isPending}
          className="bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded-lg"
        >
          {mutation.isPending ? 'Submitting…' : 'Submit'}
        </button>
        <button
          type="button"
          onClick={onDone}
          className="text-sm text-gray-500 px-4 py-1.5 rounded-lg border border-gray-300"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default function RegionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const regionId = Number(id)
  const [horizon, setHorizon] = useState(7)
  const [showReadingForm, setShowReadingForm] = useState(false)

  const { data: region, isLoading: loadingRegion } = useQuery({
    queryKey: ['region', regionId],
    queryFn: () => getRegion(regionId),
  })

  const { data: risk } = useQuery({
    queryKey: ['regionRisk', regionId],
    queryFn: () => getRegionRisk(regionId),
    refetchInterval: 30_000,
  })

  const { data: forecast } = useQuery({
    queryKey: ['regionForecast', regionId, horizon],
    queryFn: () => getRegionForecast(regionId, horizon),
  })

  const { data: readings = [] } = useQuery({
    queryKey: ['readings', regionId],
    queryFn: () => getReadings({ region_id: regionId, page_size: 20 }),
  })

  if (loadingRegion) return <p className="text-sm text-gray-500">Loading…</p>
  if (!region) return <p className="text-sm text-red-600">Region not found.</p>

  const forecastData = forecast
    ? [
        {
          name: `${horizon}d forecast`,
          'Flood Prob.': +(forecast.flood_probability * 100).toFixed(1),
          'Drought Prob.': +(forecast.drought_probability * 100).toFixed(1),
        },
      ]
    : []

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <button
          onClick={() => navigate('/regions')}
          className="text-gray-400 hover:text-gray-700 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h2 className="text-xl font-bold text-gray-900">{region.name}</h2>
          <p className="text-sm text-gray-500">
            Population: {region.population.toLocaleString()} · Vulnerability:{' '}
            {(region.vulnerability_index * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Assessment */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-800 mb-4">Risk Assessment</h3>
          {risk ? (
            <div className="flex items-center gap-6">
              <RiskGauge value={risk.calculated_risk} />
              <div className="flex-1 space-y-3">
                <div>
                  <p className="text-xs font-medium text-gray-600 mb-1">Flood Probability</p>
                  <ProgressBar value={risk.flood_probability} color="#3b82f6" />
                </div>
                <div>
                  <p className="text-xs font-medium text-gray-600 mb-1">Drought Probability</p>
                  <ProgressBar value={risk.drought_probability} color="#f59e0b" />
                </div>
                <p className="text-xs text-gray-400">
                  Confidence: {(risk.confidence_score * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-400">No risk data available.</p>
          )}
        </div>

        {/* Forecast */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">Forecast</h3>
            <div className="flex gap-1">
              {HORIZONS.map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    horizon === h
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {h}d
                </button>
              ))}
            </div>
          </div>
          {forecastData.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={forecastData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis unit="%" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip formatter={(v: number) => `${v}%`} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="Flood Prob." fill="#3b82f6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Drought Prob." fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-sm text-gray-400">No forecast data.</p>
          )}
        </div>
      </div>

      {/* Readings */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-800">Recent Readings</h3>
          <button
            onClick={() => setShowReadingForm((v) => !v)}
            className="flex items-center gap-1.5 text-sm bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Reading
          </button>
        </div>

        {showReadingForm && (
          <div className="mb-4">
            <AddReadingForm regionId={regionId} onDone={() => setShowReadingForm(false)} />
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-500 border-b border-gray-100">
                <th className="pb-2 font-medium">Lat</th>
                <th className="pb-2 font-medium">Lng</th>
                <th className="pb-2 font-medium">Rainfall</th>
                <th className="pb-2 font-medium">Temp</th>
                <th className="pb-2 font-medium">Water Level</th>
                <th className="pb-2 font-medium">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {readings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-gray-400">
                    No readings yet.
                  </td>
                </tr>
              ) : (
                readings.map((r) => (
                  <tr key={r.id} className="text-gray-700">
                    <td className="py-2">{r.latitude}</td>
                    <td className="py-2">{r.longitude}</td>
                    <td className="py-2">{r.rainfall} mm</td>
                    <td className="py-2">{r.temperature}°C</td>
                    <td className="py-2">{r.water_level} m</td>
                    <td className="py-2 text-gray-400 text-xs">
                      {new Date(r.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
