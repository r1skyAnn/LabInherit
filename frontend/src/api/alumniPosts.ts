import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface AlumniPostCreate {
  type: string  // referral | tech | resource
  title: string
  content?: string | null
  company?: string | null
  position?: string | null
  contact_info?: string | null
  tags?: string | null
}

export interface AlumniPostUpdate {
  type?: string
  title?: string
  content?: string | null
  company?: string | null
  position?: string | null
  contact_info?: string | null
  tags?: string | null
}

export interface AlumniPostOut {
  id: number
  author_id: number
  author_display_name: string | null
  type: string
  title: string
  content: string | null
  company: string | null
  position: string | null
  contact_info: string | null
  tags: string | null
  created_at: string
  updated_at: string
}

export interface AlumniPostListResponse {
  items: AlumniPostOut[]
  total: number
}

export const alumniPostsApi = {
  create(data: AlumniPostCreate): AxiosPromise<AlumniPostOut> {
    return apiClient.post('/alumni-posts', data)
  },

  list(params?: {
    type?: string
    page?: number
    page_size?: number
  }): AxiosPromise<AlumniPostListResponse> {
    return apiClient.get('/alumni-posts', { params })
  },

  get(id: number): AxiosPromise<AlumniPostOut> {
    return apiClient.get(`/alumni-posts/${id}`)
  },

  update(id: number, data: AlumniPostUpdate): AxiosPromise<AlumniPostOut> {
    return apiClient.patch(`/alumni-posts/${id}`, data)
  },

  remove(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/alumni-posts/${id}`)
  },
}
