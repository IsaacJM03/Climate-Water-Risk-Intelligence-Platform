// All TypeScript interfaces matching the API shapes

export interface Organization {
  id: number
  name: string
  type: string
  created_at: string
}

export interface User {
  id: number
  email: string
  role: string
  organization_id: number
}

export interface DecodedToken {
  userId: string
  orgId: number
  role: string
}

export interface Region {
  id: number
  name: string
  population: number
  vulnerability_index: number
  organization_id: number
  boundary: unknown
}

export interface RegionRisk {
  id: number
  region_id: number
  calculated_risk: number
  flood_probability: number
  drought_probability: number
  confidence_score: number
  created_at: string
}

export interface RegionForecast {
  region_id: number
  flood_probability: number
  drought_probability: number
  confidence_score: number
  horizon_days: number
}

export interface Reading {
  id: number
  region_id: number
  latitude: number
  longitude: number
  rainfall: number
  temperature: number
  water_level: number
  created_at: string
}

export interface Alert {
  id: number
  region_id: number
  level: 'low' | 'medium' | 'high' | 'critical'
  message: string
  acknowledged: boolean
  organization_id: number
  created_at: string
}

export interface CreateRegionPayload {
  name: string
  population: number
  vulnerability_index: number
}

export interface CreateReadingPayload {
  latitude: number
  longitude: number
  rainfall: number
  temperature: number
  water_level: number
}

export interface RegisterOrgPayload {
  name: string
  type: string
}

export interface RegisterUserPayload {
  email: string
  password: string
  role: string
  organization_id: number
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export type AlertLevel = 'low' | 'medium' | 'high' | 'critical'

export interface WsMessage {
  type: 'risk_update' | 'alert' | 'pong' | string
  region_id?: number
  calculated_risk?: number
  flood_probability?: number
  drought_probability?: number
  level?: AlertLevel
  message?: string
  timestamp: string
}
