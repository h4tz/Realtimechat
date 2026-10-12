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

function openPrivateChat(username: string) {
  router.push(`/private/${encodeURIComponent(username)}`)
}

onMounted(() => {
  roomsStore.fetchRooms()
})
</script>

<template>
  <div class="min-h-screen bg-slate-900">
    <AppHeader />

    <div class="max-w-lg mx-auto w-full px-4 py-8">
      <div class="bg-slate-800 rounded-2xl shadow-2xl p-6 border border-slate-700 mb-6 animate-slide-up">
        <h2 class="text-lg font-semibold text-slate-100 mb-4">Join a Room</h2>

        <div class="flex gap-2 mb-3">
          <input
            v-model="roomInput"
            @keydown="handleRoomKeydown"
            type="text"
            placeholder="Enter room name..."
            class="flex-1 bg-slate-700 border border-slate-500 rounded-xl px-5 py-4 text-slate-100 outline-none focus:border-primary transition-colors"
          />
          <button
            @click="createAndJoin"
            class="btn btn-primary rounded-xl px-5 py-2.5 font-medium hover:shadow-lg transition-all"
          >
            Join
          </button>
        </div>

        <p v-if="roomsStore.error || showCreateError" class="text-sm text-slate-400 mt-2">
          {{ roomsStore.error || 'Failed to create room' }}
        </p>

        <div class="mt-4">
          <input
            v-model="searchQuery"
            @input="onSearchInput"
            type="text"
            placeholder="Search rooms..."
            class="w-full bg-slate-700 border border-slate-500 rounded-xl px-5 py-4 text-slate-400 outline-none focus:border-primary transition-colors"
          />
          <div v-if="searchSuggestions.length && searchQuery.trim()" class="mt-2 flex flex-wrap gap-2">
            <button
              v-for="room in searchSuggestions"
              :key="room"
              @click="joinRoom(room)"
              class="inline-flex items-center rounded-full px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
            >
              #{{ room }}
            </button>
          </div>
        </div>
      </div>

      <div class="bg-slate-800 rounded-2xl shadow-2xl p-6 animate-slide-up">
        <h2 class="text-lg font-semibold text-slate-100 mb-4">Your Rooms</h2>

        <div v-if="roomsStore.loading" class="text-center py-8 text-slate-400 text-sm">
          Loading rooms...
        </div>

        <div v-else-if="filteredRooms.length" class="space-y-3">
          <RoomCard
            v-for="room in filteredRooms"
            :key="room.room"
            :room="room"
            @click="joinRoom"
          />
        </div>

        <div v-else class="py-8 text-center">
          <p class="text-slate-400">No rooms yet. <a href="#" class="text-slate-400 hover-underline focus-visible focus-visible-on-focus" @click.prevent="roomInput = 'new-room'">Create one</a> above!</p>
        </div>
      </div>
    </div>
  </div>
</template>