import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface ProjectCreate {
  title: string
  description?: string | null
  category_id?: number | null
  priority?: string
  tech_stack?: string | null
  repo_url?: string | null
  demo_url?: string | null
  zip_url?: string | null
  started_at?: string | null
  ended_at?: string | null
}

export interface ProjectUpdate {
  title?: string
  description?: string | null
  category_id?: number | null
  status?: string
  priority?: string
  tech_stack?: string | null
  repo_url?: string | null
  demo_url?: string | null
  zip_url?: string | null
  started_at?: string | null
  ended_at?: string | null
}

export interface ProjectOut {
  id: number
  title: string
  description: string | null
  category_id: number | null
  category_name: string | null
  status: string
  priority: string
  tech_stack: string | null
  repo_url: string | null
  demo_url: string | null
  zip_url: string | null
  started_at: string | null
  ended_at: string | null
  created_by: number
  creator_display_name: string | null
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  items: ProjectOut[]
  total: number
}

export const projectsApi = {
  create(data: ProjectCreate): AxiosPromise<ProjectOut> {
    return apiClient.post('/projects', data)
  },

  list(params?: {
    status?: string
    page?: number
    page_size?: number
  }): AxiosPromise<ProjectListResponse> {
    return apiClient.get('/projects', { params })
  },

  get(id: number): AxiosPromise<ProjectOut> {
    return apiClient.get(`/projects/${id}`)
  },

  update(id: number, data: ProjectUpdate): AxiosPromise<ProjectOut> {
    return apiClient.patch(`/projects/${id}`, data)
  },

  remove(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/projects/${id}`)
  },
}
