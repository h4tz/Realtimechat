<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useRoomsStore } from '@/stores/rooms'
import AppHeader from '@/components/AppHeader.vue'
import RoomCard from '@/components/RoomCard.vue'

const router = useRouter()
const roomsStore = useRoomsStore()

const roomInput = ref('')
const searchQuery = ref('')
const showCreateError = ref(false)

const filteredRooms = computed(() => {
  if (!searchQuery.value.trim()) return roomsStore.rooms
  const q = searchQuery.value.toLowerCase()
  return roomsStore.rooms.filter((r) => r.room.toLowerCase().includes(q))
})

const searchSuggestions = computed(() => roomsStore.searchResults)

let searchTimeout: ReturnType<typeof setTimeout> | null = null

function onSearchInput() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    roomsStore.search(searchQuery.value)
  }, 300)
}

function joinRoom(roomName: string) {
  if (!/^[a-zA-Z0-9_-]+$/.test(roomName)) return
  router.push(`/chat/${encodeURIComponent(roomName)}`)
}

async function createAndJoin() {
  const name = roomInput.value.trim()
  if (!name) return
  try {
    await roomsStore.create(name)
    roomInput.value = ''
    joinRoom(name)
  } catch {
    showCreateError.value = true
    setTimeout(() => (showCreateError.value = false), 3000)
  }
}

function handleRoomKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') createAndJoin()
}

function openPrivateChat(username: string) {
  router.push(`/private/${encodeURIComponent(username)}`)
}

onMounted(() => {
  roomsStore.fetchRooms()
})
</script>

<template>
  <div class="min-h-screen bg-slate-100">
    <AppHeader />

    <div class="max-w-lg mx-auto px-4 py-8">
      <div class="bg-white rounded-2xl shadow-sm p-6 mb-6">
        <h2 class="text-lg font-semibold text-slate-800 mb-4">Join a Room</h2>

        <div class="flex gap-2 mb-3">
          <input
            v-model="roomInput"
            @keydown="handleRoomKeydown"
            type="text"
            placeholder="Enter room name..."
            class="flex-1 px-4 py-2.5 rounded-full border border-slate-300 text-sm outline-none focus:border-blue-500 transition-colors"
          />
          <button
            @click="createAndJoin"
            class="px-5 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-full hover:bg-blue-600 transition-colors"
          >
            Join
          </button>
        </div>

        <p v-if="roomsStore.error || showCreateError" class="text-xs text-red-500 mt-2">
          {{ roomsStore.error || 'Failed to create room' }}
        </p>

        <div class="mt-4">
          <input
            v-model="searchQuery"
            @input="onSearchInput"
            type="text"
            placeholder="Search rooms..."
            class="w-full px-4 py-2.5 rounded-full border border-slate-200 text-sm outline-none focus:border-blue-400 transition-colors"
          />
          <div v-if="searchSuggestions.length && searchQuery.trim()" class="mt-2 flex flex-wrap gap-1">
            <button
              v-for="room in searchSuggestions"
              :key="room"
              @click="joinRoom(room)"
              class="text-xs bg-slate-100 hover:bg-slate-200 px-3 py-1 rounded-full transition-colors"
            >
              #{{ room }}
            </button>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-2xl shadow-sm p-6">
        <h2 class="text-lg font-semibold text-slate-800 mb-4">Your Rooms</h2>

        <div v-if="roomsStore.loading" class="text-center py-8 text-slate-400 text-sm">
          Loading rooms...
        </div>

        <div v-else-if="filteredRooms.length" class="space-y-2">
          <RoomCard
            v-for="room in filteredRooms"
            :key="room.room"
            :room="room"
            @click="joinRoom"
          />
        </div>

        <div v-else class="text-center py-8 text-slate-400 text-sm">
          No rooms yet. Create one above!
        </div>
      </div>
    </div>
  </div>
</template>
