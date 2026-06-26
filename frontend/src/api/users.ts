import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface UserProfileOut {
  enrollment_year: number | null
  graduation_year: number | null
  research_direction: string | null
  current_affiliation: string | null
  bio: string | null
  avatar_url: string | null
  gender: string | null
}

export interface UserOut {
  id: number
  email: string
  display_name: string
  status: string
  role: string
  last_login_at: string | null
  profile: UserProfileOut | null
  created_at: string
}

export interface UserUpdate {
  display_name?: string
  enrollment_year?: number | null
  graduation_year?: number | null
  research_direction?: string | null
  current_affiliation?: string | null
  bio?: string | null
  avatar_url?: string | null
  gender?: string | null
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export const usersApi = {
  getMe(): AxiosPromise<UserOut> {
    return apiClient.get('/users/me')
  },

  updateMe(data: UserUpdate): AxiosPromise<UserOut> {
    return apiClient.patch('/users/me', data)
  },

  changePassword(data: ChangePasswordRequest): AxiosPromise<{ detail: string }> {
    return apiClient.post('/users/me/change-password', data)
  },
}
