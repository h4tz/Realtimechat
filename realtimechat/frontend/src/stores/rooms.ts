import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getRooms, searchRooms, createRoom } from '@/api/rooms'
import type { Room } from '@/types'

export const useRoomsStore = defineStore('rooms', () => {
  const rooms = ref<Room[]>([])
  const searchResults = ref<string[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchRooms() {
    loading.value = true
    error.value = null
    try {
      rooms.value = await getRooms()
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to load rooms'
    } finally {
      loading.value = false
    }
  }

  async function search(query: string) {
    if (!query.trim()) {
      searchResults.value = []
      return
    }
    try {
      const data = await searchRooms(query)
      searchResults.value = data.rooms
    } catch {
      searchResults.value = []
    }
  }

  async function create(name: string) {
    error.value = null
    try {
      const data = await createRoom({ room_name: name })
      return data
    } catch (e: any) {
      error.value = e.response?.data?.error || 'Failed to create room'
      throw e
    }
  }

  return { rooms, searchResults, loading, error, fetchRooms, search, create }
})
