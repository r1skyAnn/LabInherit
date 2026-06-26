import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface MemberOut {
  id: number
  display_name: string
  email: string
  role: string
  status: string
  enrollment_year: number | null
  graduation_year: number | null
  research_direction: string | null
  current_affiliation: string | null
  bio: string | null
  last_login_at: string | null
  created_at: string
}

export interface MemberListResponse {
  items: MemberOut[]
  total: number
}

export const membersApi = {
  list(params?: {
    page?: number
    page_size?: number
    search?: string
  }): AxiosPromise<MemberListResponse> {
    return apiClient.get('/members', { params })
  },
}
