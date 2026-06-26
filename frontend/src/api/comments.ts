import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface CommentOut {
  id: number
  target_type: string
  target_id: number
  parent_id: number | null
  author_id: number
  content: string
  is_ask: boolean
  status: string
  created_at: string
  updated_at: string
  author_name: string
  author_email: string
}

export interface CommentCreate {
  content: string
  parent_id?: number | null
  is_ask?: boolean
  status?: string | null
}

export interface CommentUpdate {
  content?: string | null
  status?: string | null
  is_ask?: boolean | null
}

export interface CommentListResponse {
  items: CommentOut[]
  total: number
}

export const commentsApi = {
  list(noteId: number, params?: { page?: number; page_size?: number }): AxiosPromise<CommentListResponse> {
    return apiClient.get(`/comments/notes/${noteId}`, { params })
  },

  create(noteId: number, data: CommentCreate): AxiosPromise<CommentOut> {
    return apiClient.post(`/comments/notes/${noteId}`, data)
  },

  update(id: number, data: CommentUpdate): AxiosPromise<CommentOut> {
    return apiClient.patch(`/comments/${id}`, data)
  },

  remove(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/comments/${id}`)
  },

  listProjectAsks(projectId: number, params?: { page?: number; page_size?: number }): AxiosPromise<CommentListResponse> {
    return apiClient.get(`/comments/projects/${projectId}`, { params })
  },
}
