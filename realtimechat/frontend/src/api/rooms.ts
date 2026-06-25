import api from './client'
import type { Room, RoomSearchResult, RoomCreateRequest } from '@/types'

export async function getRooms(): Promise<Room[]> {
  const { data } = await api.get('/api/rooms/')
  return data
}

export async function searchRooms(q: string): Promise<RoomSearchResult> {
  const { data } = await api.get('/api/rooms/search/', { params: { q } })
  return data
}

export async function createRoom(payload: RoomCreateRequest) {
  const { data } = await api.post('/api/rooms/create/', payload)
  return data
}
