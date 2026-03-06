import axios from 'axios'
import type {
  LoginResponse,
  Organization,
  User,
  Region,
  RegionRisk,
  RegionForecast,
  Alert,
  Reading,
  CreateRegionPayload,
  CreateReadingPayload,
  RegisterOrgPayload,
  RegisterUserPayload,
} from '../types'

const TOKEN_KEY = 'cwrip_token'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// Auth
export async function login(email: string, password: string): Promise<LoginResponse> {
  const params = new URLSearchParams()
  params.append('username', email)
  params.append('password', password)
  const { data } = await apiClient.post<LoginResponse>('/api/v1/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export async function registerOrg(payload: RegisterOrgPayload): Promise<Organization> {
  const { data } = await apiClient.post<Organization>('/api/v1/auth/register', payload)
  return data
}

export async function registerUser(payload: RegisterUserPayload): Promise<User> {
  const { data } = await apiClient.post<User>('/api/v1/auth/register-user', payload)
  return data
}

// Regions
export async function getRegions(): Promise<Region[]> {
  const { data } = await apiClient.get<Region[]>('/api/v1/regions')
  return data
}

export async function createRegion(payload: CreateRegionPayload): Promise<Region> {
  const { data } = await apiClient.post<Region>('/api/v1/regions', payload)
  return data
}

export async function getRegion(id: number): Promise<Region> {
  const { data } = await apiClient.get<Region>(`/api/v1/regions/${id}`)
  return data
}

export async function getRegionRisk(id: number): Promise<RegionRisk> {
  const { data } = await apiClient.get<RegionRisk>(`/api/v1/regions/${id}/risk`)
  return data
}

export async function getRegionForecast(id: number, horizonDays = 7): Promise<RegionForecast> {
  const { data } = await apiClient.get<RegionForecast>(
    `/api/v1/regions/${id}/forecast?horizon_days=${horizonDays}`,
  )
  return data
}

export async function deleteRegion(id: number): Promise<void> {
  await apiClient.delete(`/api/v1/regions/${id}`)
}

// Alerts
export async function getAlerts(params?: {
  level?: string
  unacknowledged_only?: boolean
  page?: number
  page_size?: number
}): Promise<Alert[]> {
  const { data } = await apiClient.get<Alert[]>('/api/v1/alerts', { params })
  return data
}

export async function getAlert(id: number): Promise<Alert> {
  const { data } = await apiClient.get<Alert>(`/api/v1/alerts/${id}`)
  return data
}

export async function acknowledgeAlert(id: number): Promise<Alert> {
  const { data } = await apiClient.post<Alert>(`/api/v1/alerts/${id}/acknowledge`)
  return data
}

// Readings
export async function getReadings(params?: {
  region_id?: number
  page?: number
  page_size?: number
}): Promise<Reading[]> {
  const { data } = await apiClient.get<Reading[]>('/api/v1/readings', { params })
  return data
}

export async function createReading(
  regionId: number,
  payload: CreateReadingPayload,
): Promise<Reading> {
  const { data } = await apiClient.post<Reading>(
    `/api/v1/readings?region_id=${regionId}`,
    payload,
  )
  return data
}

export default apiClient
