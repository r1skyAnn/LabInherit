import type { AxiosPromise } from 'axios'
import apiClient from './client'

export interface CategoryOut {
  id: number
  parent_id: number | null
  name: string
  slug: string
  path: string
  sort_order: number
  created_by: number
  creator_display_name: string | null
  created_at: string
  updated_at: string
  children: CategoryOut[]
}

export interface CategoryCreate {
  name: string
  parent_id?: number | null
  sort_order?: number
}

export interface CategoryUpdate {
  name?: string | null
  parent_id?: number | null
  sort_order?: number | null
}

export interface CategoryListResponse {
  items: CategoryOut[]
  total: number
}

export const categoriesApi = {
  create(data: CategoryCreate): AxiosPromise<CategoryOut> {
    return apiClient.post('/categories', data)
  },

  list(): AxiosPromise<CategoryListResponse> {
    return apiClient.get('/categories')
  },

  get(id: number): AxiosPromise<CategoryOut> {
    return apiClient.get(`/categories/${id}`)
  },

  update(id: number, data: CategoryUpdate): AxiosPromise<CategoryOut> {
    return apiClient.patch(`/categories/${id}`, data)
  },

  remove(id: number): AxiosPromise<{ detail: string }> {
    return apiClient.delete(`/categories/${id}`)
  },
}
