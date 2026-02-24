import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Plus, MapPin, Trash2 } from 'lucide-react'
import { getRegions, createRegion, deleteRegion } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import type { CreateRegionPayload } from '../types'

const ALLOWED_ROLES = ['admin', 'analyst']

function AddRegionForm({ onDone }: { onDone: () => void }) {
  const qc = useQueryClient()
  const [name, setName] = useState('')
  const [population, setPopulation] = useState('')
  const [vulnerability, setVulnerability] = useState('')
  const [error, setError] = useState('')

  const mutation = useMutation({
    mutationFn: (payload: CreateRegionPayload) => createRegion(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['regions'] })
      onDone()
    },
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to create region.'
      setError(String(msg))
    },
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    mutation.mutate({
      name,
      population: Number(population),
      vulnerability_index: Number(vulnerability),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-4 space-y-3">
      <h4 className="font-semibold text-gray-800 text-sm">Add New Region</h4>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <input
          required
          placeholder="Region name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <input
          required
          type="number"
          min={0}
          placeholder="Population"
          value={population}
          onChange={(e) => setPopulation(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <input
          required
          type="number"
          min={0}
          max={1}
          step={0.01}
          placeholder="Vulnerability index (0–1)"
          value={vulnerability}
          onChange={(e) => setVulnerability(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={mutation.isPending}
          className="bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors"
        >
          {mutation.isPending ? 'Saving…' : 'Save'}
        </button>
        <button
          type="button"
          onClick={onDone}
          className="text-sm text-gray-500 hover:text-gray-700 px-4 py-1.5 rounded-lg border border-gray-300"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}

export default function RegionsPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)

  const { data: regions = [], isLoading, error } = useQuery({
    queryKey: ['regions'],
    queryFn: getRegions,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteRegion(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['regions'] }),
  })

  const canEdit = ALLOWED_ROLES.includes(user?.role ?? '')

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900">Regions</h2>
        {canEdit && (
          <button
            onClick={() => setShowForm((v) => !v)}
            className="flex items-center gap-1.5 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Region
          </button>
        )}
      </div>

      {showForm && <AddRegionForm onDone={() => setShowForm(false)} />}

      {isLoading && <p className="text-sm text-gray-500">Loading…</p>}
      {error && <p className="text-sm text-red-600">Failed to load regions.</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {regions.map((region) => (
          <div
            key={region.id}
            className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => navigate(`/regions/${region.id}`)}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-primary-600 shrink-0 mt-0.5" />
                <h3 className="font-semibold text-gray-900">{region.name}</h3>
              </div>
              {canEdit && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteMutation.mutate(region.id)
                  }}
                  className="text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
            <div className="mt-3 space-y-1 text-sm text-gray-600">
              <p>
                Population:{' '}
                <span className="font-medium text-gray-800">
                  {region.population.toLocaleString()}
                </span>
              </p>
              <p>
                Vulnerability:{' '}
                <span className="font-medium text-gray-800">
                  {(region.vulnerability_index * 100).toFixed(0)}%
                </span>
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
