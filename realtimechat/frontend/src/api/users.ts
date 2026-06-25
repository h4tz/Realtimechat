import api from './client'
import type { User } from '@/types'

export async function getUsers(): Promise<User[]> {
  const { data } = await api.get('/api/users/')
  return data
}
