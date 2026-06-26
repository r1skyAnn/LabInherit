import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface InviteCreateRequest {
  max_uses?: number
  expires_at?: string | null
  note?: string | null
}

export interface InviteOut {
  id: number
  code: string
  max_uses: number
  used_count: number
  expires_at: string | null
  note: string | null
  revoked_at: string | null
  created_at: string
}

export interface RedeemRequest {
  code: string
  email: string
  password: string
  display_name: string
  enrollment_year?: number | null
  research_direction?: string | null
  gender?: string | null
}

export interface RegisterRequest {
  email: string
  password: string
  display_name: string
  enrollment_year?: number | null
  research_direction?: string | null
  gender?: string | null
}

export const invitesApi = {
  create(data: InviteCreateRequest): AxiosPromise<InviteOut> {
    return apiClient.post('/invites', data)
  },

  list(include_revoked = false): AxiosPromise<InviteOut[]> {
    return apiClient.get('/invites', { params: { include_revoked } })
  },

  revoke(id: number): AxiosPromise<InviteOut> {
    return apiClient.post(`/invites/${id}/revoke`)
  },

  redeem(data: RedeemRequest): AxiosPromise<{ detail: string; submitted_email: string }> {
    return apiClient.post('/invites/redeem', data)
  },

  register(data: RegisterRequest): AxiosPromise<{ detail: string; submitted_email: string }> {
    return apiClient.post('/invites/register', data)
  },
}
