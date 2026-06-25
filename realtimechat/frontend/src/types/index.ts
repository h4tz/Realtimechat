export interface User {
  id: number
  username: string
}

export interface TokenResponse {
  access: string
  refresh: string
}

export interface Room {
  room: string
  message_count: number
  last_message: string
}

export interface RoomSearchResult {
  rooms: string[]
}

export interface RoomCreateRequest {
  room_name: string
}

export interface Message {
  id: string
  room: string
  user: User
  content: string
  timestamp: string
  is_edited: boolean
  edited_at: string | null
}

export interface PrivateMessage {
  id: string
  user1: User
  user2: User
  content: string
  timestamp: string
  is_read: boolean
  read_at: string | null
}

export interface PaginatedMessages {
  messages: Message[]
  has_next: boolean
  has_previous: boolean
  current_page: number
  total_pages: number
  total_messages: number
}

export interface PaginatedPrivateMessages {
  messages: PrivateMessage[]
  has_next: boolean
  has_previous: boolean
  current_page: number
  total_pages: number
  total_messages: number
}

export interface WSIncomingMessage {
  type: 'message' | 'typing' | 'user_joined' | 'user_left' | 'error'
  user?: string
  content?: string
  timestamp?: string
  id?: string
  is_typing?: boolean
  message?: string
}

export interface WSOutgoingMessage {
  type: 'message' | 'typing'
  content?: string
  is_typing?: boolean
}
