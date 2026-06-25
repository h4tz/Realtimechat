import axios from 'axios'
import api from './client'
import type { TokenResponse } from '@/types'

export async function login(username: string, password: string): Promise<TokenResponse> {
  const { data } = await api.post('/api/token/', { username, password })
  return data
}

export async function refreshToken(refresh: string): Promise<TokenResponse> {
  const { data } = await axios.post(
    `${import.meta.env.VITE_API_URL}/api/token/refresh/`,
    { refresh },
  )
  return data
}
