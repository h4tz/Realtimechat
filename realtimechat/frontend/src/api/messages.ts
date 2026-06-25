import api from './client'
import type { PaginatedMessages, PaginatedPrivateMessages } from '@/types'

export async function getRoomMessages(
  room: string,
  page: number = 1,
): Promise<PaginatedMessages> {
  const { data } = await api.get(`/api/rooms/${encodeURIComponent(room)}/messages/`, {
    params: { page },
  })
  return data
}

export async function sendRoomMessage(room: string, content: string) {
  const { data } = await api.post(`/api/rooms/${encodeURIComponent(room)}/messages/`, {
    content,
  })
  return data
}

export async function getPrivateMessages(
  username: string,
  page: number = 1,
): Promise<PaginatedPrivateMessages> {
  const { data } = await api.get(
    `/api/private/${encodeURIComponent(username)}/messages/`,
    { params: { page } },
  )
  return data
}
