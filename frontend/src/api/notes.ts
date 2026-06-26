import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface NoteOut {
  id: number
  project_id: number
  category_id: number | null
  author_id: number
  title: string
  content: string
  author_display_name: string
  author_email: string
  author_enrollment_year: number | null
  author_graduation_year: number | null
  is_pinned: boolean
  like_count: number
  comment_count: number
  liked: boolean
  created_at: string
  updated_at: string
  category_name: string | null
  project_title: string | null
}

export interface NoteCreate {
  project_id: number
  category_id?: number | null
  title: string
  content: string
}

export interface NoteUpdate {
  title?: string | null
  content?: string | null
  category_id?: number | null
  is_pinned?: boolean | null
}

export interface NoteListResponse {
  items: NoteOut[]
  total: number
}

export const notesApi = {
  create(data: NoteCreate): AxiosPromise<NoteOut> {
    return apiClient.post('/notes', data)
  },

  list(params?: {
    project_id?: number
    category_id?: number
    author_id?: number
    q?: string
    page?: number
    page_size?: number
  }): AxiosPromise<NoteListResponse> {
    return apiClient.get('/notes', { params })
  },

  get(id: number): AxiosPromise<NoteOut> {
    return apiClient.get(`/notes/${id}`)
  },

  update(id: number, data: NoteUpdate): AxiosPromise<NoteOut> {
    return apiClient.patch(`/notes/${id}`, data)
  },

  remove(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/notes/${id}`)
  },

  like(id: number): AxiosPromise<NoteOut> {
    return apiClient.post(`/notes/${id}/like`)
  },

  unlike(id: number): AxiosPromise<NoteOut> {
    return apiClient.delete(`/notes/${id}/like`)
  },
}
