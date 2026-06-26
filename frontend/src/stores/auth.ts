import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserOut } from '@/api/users'
import { usersApi } from '@/api/users'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('labinherit_token'))
  const user = ref<UserOut | null>(
    JSON.parse(localStorage.getItem('labinherit_user') ?? 'null'),
  )
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() =>
    user.value?.role === 'admin' || user.value?.role === 'owner',
  )
  const isOwner = computed(() => user.value?.role === 'owner')

  function setAuth(newToken: string, newUser: UserOut) {
    token.value = newToken
    user.value = newUser
    localStorage.setItem('labinherit_token', newToken)
    localStorage.setItem('labinherit_user', JSON.stringify(newUser))
  }

  function clearAuth() {
    token.value = null
    user.value = null
    localStorage.removeItem('labinherit_token')
    localStorage.removeItem('labinherit_user')
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const resp = await authApi.login({ email, password })
      const newToken = resp.data.access_token
      // Save token first so the interceptor picks it up for /users/me
      token.value = newToken
      localStorage.setItem('labinherit_token', newToken)
      const userResp = await usersApi.getMe()
      setAuth(newToken, userResp.data)
      return true
    } finally {
      loading.value = false
    }
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const resp = await usersApi.getMe()
      user.value = resp.data
      if (user.value) {
        localStorage.setItem('labinherit_user', JSON.stringify(user.value))
      }
    } catch {
      clearAuth()
    }
  }

  function logout() {
    clearAuth()
    router.push('/auth/login')
  }

  // Restore user on app start if token exists
  if (token.value) {
    fetchMe()
  }

  return {
    token,
    user,
    loading,
    isLoggedIn,
    isAdmin,
    isOwner,
    setAuth,
    clearAuth,
    login,
    fetchMe,
    logout,
  }
})
