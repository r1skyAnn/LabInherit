import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface AnnouncementCreate {
  title: string
  content: string
  is_pinned?: boolean
}

export interface AnnouncementUpdate {
  title?: string
  content?: string
  is_pinned?: boolean
}

export interface AnnouncementOut {
  id: number
  title: string
  content: string
  author_id: number
  author_display_name: string | null
  is_pinned: boolean
  created_at: string
  updated_at: string
}

export interface AnnouncementListResponse {
  items: AnnouncementOut[]
  total: number
}

export const announcementsApi = {
  create(data: AnnouncementCreate): AxiosPromise<AnnouncementOut> {
    return apiClient.post('/announcements', data)
  },

  list(params?: {
    page?: number
    page_size?: number
  }): AxiosPromise<AnnouncementListResponse> {
    return apiClient.get('/announcements', { params })
  },

  get(id: number): AxiosPromise<AnnouncementOut> {
    return apiClient.get(`/announcements/${id}`)
  },

  update(id: number, data: AnnouncementUpdate): AxiosPromise<AnnouncementOut> {
    return apiClient.patch(`/announcements/${id}`, data)
  },

  remove(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/announcements/${id}`)
  },
}
