import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
}

export const authApi = {
  login(data: LoginRequest): AxiosPromise<TokenResponse> {
    return apiClient.post('/auth/login', data)
  },

  forgotPassword(data: ForgotPasswordRequest): AxiosPromise<{ detail: string }> {
    return apiClient.post('/auth/forgot-password', data)
  },

  resetPassword(data: ResetPasswordRequest): AxiosPromise<{ detail: string }> {
    return apiClient.post('/auth/reset-password', data)
  },
}
