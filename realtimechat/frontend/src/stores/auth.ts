import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const username = ref<string | null>(localStorage.getItem('username'))

  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function setUsername(name: string) {
    username.value = name
    localStorage.setItem('username', name)
  }

  async function login(user: string, password: string) {
    const data = await apiLogin(user, password)
    setTokens(data.access, data.refresh)
    setUsername(user)
  }

  function logout() {
    accessToken.value = null
    refreshToken.value = null
    username.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
  }

  return { accessToken, refreshToken, username, isAuthenticated, setTokens, setUsername, login, logout }
})
