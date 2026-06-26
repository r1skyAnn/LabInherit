import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

/**
 * Centralized axios client. All API modules import this and use typed methods.
 *
 * baseURL is read from VITE_API_BASE; in dev Vite proxies /api to the backend.
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE ?? '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor — attach auth token when present
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('labinherit_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — uniform error handling + 401 redirect
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const message =
      error?.response?.data?.error?.message ?? error?.message ?? '请求失败，请稍后再试'

    if (status === 401) {
      localStorage.removeItem('labinherit_token')
      localStorage.removeItem('labinherit_user')
      // Only redirect if not already on an auth page
      if (!router.currentRoute.value.path.startsWith('/auth')) {
        router.push('/auth/login')
      }
    } else if (status === 403) {
      ElMessage.error(message || '权限不足')
    } else if (status !== 401) {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  },
)

export default apiClient
