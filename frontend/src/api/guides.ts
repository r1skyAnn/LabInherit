import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface GuideOut {
  id: number
  title: string
  slug: string
  content: string
  tag: string
  related_projects: string | null
  sort_order: number
  is_pinned: boolean
  author_id: number
  author_name: string
  created_at: string
  updated_at: string
}

export interface GuideCreate {
  title: string
  slug: string
  content?: string
  tag?: string
  related_projects?: string | null
  sort_order?: number
  is_pinned?: boolean
}

export interface GuideUpdate {
  title?: string | null
  content?: string | null
  tag?: string | null
  related_projects?: string | null
  sort_order?: number | null
  is_pinned?: boolean | null
}

export interface GuideListResponse {
  items: GuideOut[]
  total: number
}

export const guidesApi = {
  list(params?: { tag?: string }): AxiosPromise<GuideListResponse> {
    return apiClient.get('/guides', { params })
  },

  get(slug: string): AxiosPromise<GuideOut> {
    return apiClient.get(`/guides/${slug}`)
  },

  create(data: GuideCreate): AxiosPromise<GuideOut> {
    return apiClient.post('/guides', data)
  },

  update(id: number, data: GuideUpdate): AxiosPromise<GuideOut> {
    return apiClient.patch(`/guides/${id}`, data)
  },

  remove(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/guides/${id}`)
  },
}
