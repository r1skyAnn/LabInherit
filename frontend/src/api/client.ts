import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

/**
 * Centralized axios client. All API modules import this and use typed methods.
 *
 * baseURL is read from VITE_API_BASE; in dev Vite proxies /api to the backend.
 * In production, VITE_API_BASE should be the full backend URL (e.g., http://localhost:8000/api/v1).
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: (() => {
    const envBase = import.meta.env.VITE_API_BASE
    if (envBase) {
      // 如果配置了绝对 URL（生产环境）或相对路径（开发环境）
      return envBase.startsWith('http')
        ? envBase  // 生产：完整 URL
        : envBase  // 开发：相对路径，Vite proxy 会处理
    }
    return '/api/v1'  // 默认相对路径
  })(),
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
      // Show a friendly toast on auth failure — covers login errors, expired
      // tokens, and any API call that rejects a stale session.
      ElMessage.error(message || '邮箱或密码错误，请重试')
      // Only redirect if not already on an auth page
      if (!router.currentRoute.value.path.startsWith('/auth')) {
        router.push('/auth/login')
      }
    } else if (status === 403) {
      ElMessage.error(message || '权限不足')
    } else {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  },
)

export default apiClient
