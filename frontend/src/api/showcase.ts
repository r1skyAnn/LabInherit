import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface ShowcaseOut {
  id: number
  author_id: number
  type: string
  title: string
  description: string | null
  image_url: string | null
  pdf_url: string | null
  contact_info: string | null
  experience: string | null
  created_at: string
  updated_at: string
  author_name: string
  author_email: string
  author_enrollment_year: number | null
  author_graduation_year: number | null
}

export interface ShowcaseCreate {
  type: string
  title: string
  description?: string | null
  image_url?: string | null
  pdf_url?: string | null
  contact_info?: string | null
  experience?: string | null
}

export interface ShowcaseUpdate {
  title?: string | null
  description?: string | null
  image_url?: string | null
  pdf_url?: string | null
  contact_info?: string | null
  experience?: string | null
}

export interface ShowcaseListResponse {
  items: ShowcaseOut[]
  total: number
}

export const showcaseApi = {
  list(params?: { type?: string; page?: number; page_size?: number }): AxiosPromise<ShowcaseListResponse> {
    return apiClient.get('/showcase', { params })
  },

  create(data: ShowcaseCreate): AxiosPromise<ShowcaseOut> {
    return apiClient.post('/showcase', data)
  },

  update(id: number, data: ShowcaseUpdate): AxiosPromise<ShowcaseOut> {
    return apiClient.patch(`/showcase/${id}`, data)
  },

  remove(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/showcase/${id}`)
  },
}
