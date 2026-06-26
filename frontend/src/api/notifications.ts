import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface NotificationOut {
  id: number
  user_id: number
  type: string
  payload_json: string | null
  read_at: string | null
  created_at: string
}

export interface NotificationListResponse {
  items: NotificationOut[]
  total: number
  unread_count: number
}

export const notificationsApi = {
  list(params?: {
    unread_only?: boolean
    page?: number
    page_size?: number
  }): AxiosPromise<NotificationListResponse> {
    return apiClient.get('/notifications', { params })
  },

  unreadCount(): AxiosPromise<{ unread_count: number }> {
    return apiClient.get('/notifications/unread-count')
  },

  markRead(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.patch(`/notifications/${id}/read`)
  },

  readAll(): AxiosPromise<{ detail: string }> {
    return apiClient.post('/notifications/read-all')
  },
}
