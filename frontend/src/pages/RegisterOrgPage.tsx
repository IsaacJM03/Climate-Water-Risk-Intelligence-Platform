import { useState } from 'react'
import { Link } from 'react-router-dom'
import { registerOrg } from '../api/client'
import { CloudRain, CheckCircle } from 'lucide-react'

const ORG_TYPES = [
  { value: 'church', label: 'Church' },
  { value: 'ngo', label: 'NGO' },
  { value: 'government', label: 'Government' },
]

export default function RegisterOrgPage() {
  const [step, setStep] = useState<1 | 2>(1)
  const [orgName, setOrgName] = useState('')
  const [orgType, setOrgType] = useState('ngo')
  const [orgId, setOrgId] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const org = await registerOrg({ name: orgName, type: orgType })
      setOrgId(org.id)
      setStep(2)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Registration failed.'
      setError(String(msg))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 to-primary-700 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="bg-primary-100 rounded-full p-3 mb-3">
            <CloudRain className="w-7 h-7 text-primary-700" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Register Organization</h1>
          <p className="text-sm text-gray-500 mt-1">Climate Risk Intelligence Platform</p>
        </div>

        {step === 1 ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Organization Name
              </label>
              <input
                type="text"
                required
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                placeholder="e.g. Riverside NGO"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Organization Type
              </label>
              <select
                value={orgType}
                onChange={(e) => setOrgType(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 bg-white"
              >
                {ORG_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white font-medium py-2 rounded-lg transition-colors text-sm"
            >
              {loading ? 'Creating…' : 'Create Organization'}
            </button>
          </form>
        ) : (
          <div className="text-center space-y-4">
            <div className="flex justify-center">
              <CheckCircle className="w-14 h-14 text-green-500" />
            </div>
            <h2 className="text-lg font-semibold text-gray-800">Organization Created!</h2>
            <div className="bg-gray-50 rounded-lg p-4 text-left text-sm space-y-1">
              <p className="text-gray-600">
                <span className="font-medium">Organization ID:</span>{' '}
                <span className="font-mono text-primary-700 text-base">{orgId}</span>
              </p>
              <p className="text-gray-500 text-xs mt-2">
                Keep this ID safe. Your system administrator needs it to create user accounts.
              </p>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700 text-left">
              <p className="font-medium mb-1">Next steps:</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>
                  Have your admin call{' '}
                  <code className="bg-blue-100 px-1 rounded">POST /api/v1/auth/register-user</code>{' '}
                  with organization_id: {orgId}
                </li>
                <li>
                  Or use the interactive API docs at{' '}
                  <a
                    href="http://localhost:8000/api/docs"
                    target="_blank"
                    rel="noreferrer"
                    className="underline"
                  >
                    /api/docs
                  </a>
                </li>
              </ol>
            </div>
          </div>
        )}

        <p className="text-center text-sm text-gray-500 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-primary-600 hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
