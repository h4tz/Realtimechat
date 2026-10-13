<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useRoomsStore } from '@/stores/rooms'
import { useChatStore } from '@/stores/chat'
import { useWebSocket } from '@/composables/useWebSocket'
import { useTyping } from '@/composables/useTyping'
import MessageList from '@/components/MessageList.vue'
import MessageInput from '@/components/MessageInput.vue'
import TypingIndicator from '@/components/TypingIndicator.vue'
import type { WSIncomingMessage } from '@/types'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const roomsStore = useRoomsStore()
const chatStore = useChatStore()

const roomName = ref(route.params.room as string)
const typingUsers = ref<Set<string>>(new Set())
const chatContainer = ref<HTMLElement | null>(null)
const showScrollButton = ref(false)

const wsUrl = `${import.meta.env.VITE_WS_URL}/ws/chat/${encodeURIComponent(roomName.value)}/`
const { connected, connect, disconnect, sendMessage, sendTyping, onMessage } = useWebSocket(wsUrl)

const { start: startTyping, stop: stopTyping } = useTyping(
  () => sendTyping(true),
  () => sendTyping(false)
)

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function onScroll() {
  if (!chatContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = chatContainer.value
  showScrollButton.value = scrollHeight - scrollTop - clientHeight > 80
}

function scrollDown() {
  scrollToBottom()
}

function handleWsMessage(data: WSIncomingMessage) {
  switch (data.type) {
    case 'message':
      chatStore.addMessage({
        id: data.id!,
        room: roomName.value,
        user: { id: 0, username: data.user! },
        content: data.content!,
        timestamp: data.timestamp!,
        is_edited: false,
        edited_at: null,
      })
      typingUsers.value.delete(data.user as string)
      scrollToBottom()
      break
    case 'typing':
      if (data.user !== auth.username && data.is_typing) {
        typingUsers.value.add(data.user as string)
      } else {
        typingUsers.value.delete(data.user as string)
      }
      break
    case 'user_joined':
    case 'user_left':
      break
  }
}

function handleSend(content: string) {
  sendMessage(content)
  stopTyping()
}

function handleInput() {
  startTyping()
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(async () => {
  await roomsStore.fetchRooms()
  await chatStore.fetchRoomMessages(roomName.value)
  scrollToBottom()
  connect()
  onMessage(handleWsMessage)
})

onUnmounted(() => {
  disconnect()
})

watch(
  () => chatStore.messages.length,
  () => scrollToBottom(),
)
</script>

<template>
  <div class="h-screen flex bg-[#313338] text-[#dcddde]">
    <!-- Server rail -->
    <aside class="w-[72px] bg-[#1e1f22] flex flex-col items-center py-3 gap-2 flex-shrink-0">
      <router-link to="/" class="w-12 h-12 rounded-full bg-[#eb459e] flex items-center justify-center text-white font-bold">C</router-link>
    </aside>

    <!-- Channel sidebar -->
    <aside class="w-60 bg-[#2b2d31] flex flex-col flex-shrink-0">
      <div class="h-12 px-4 flex items-center font-semibold border-b border-[#1e1f22]">Chat</div>
      <div class="flex-1 overflow-y-auto p-2">
        <div class="text-xs uppercase text-[#80848e] font-semibold mb-1 px-2">Text Channels</div>
        <button
          v-for="r in roomsStore.rooms"
          :key="r.room"
          @click="router.push(`/chat/${encodeURIComponent(r.room)}`)"
          class="w-full text-left px-2 py-1.5 rounded hover:bg-[#35373c] text-[#b5bac1] hover:text-white text-sm flex items-center gap-1"
          :class="r.room === roomName ? 'bg-[#404249] text-white' : ''"
        >
          <span class="text-[#80848e]">#</span>{{ r.room }}
        </button>
      </div>
      <div class="h-14 bg-[#232428] px-2 flex items-center gap-2 border-t border-[#1e1f22]">
        <div class="w-8 h-8 rounded-full bg-[#eb459e] flex items-center justify-center text-xs font-semibold">{{ auth.username?.[0]?.toUpperCase() }}</div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium truncate">{{ auth.username }}</div>
        </div>
        <button @click="logout" class="text-[#80848e] hover:text-white text-xs">Logout</button>
      </div>
    </aside>

    <!-- Chat area -->
    <main class="flex-1 flex flex-col min-w-0">
      <div class="h-12 px-4 flex items-center font-semibold border-b border-[#1e1f22] bg-[#313338]">
        <span class="text-[#80848e] mr-1">#</span>{{ roomName }}
      </div>

      <div ref="chatContainer" class="flex-1 overflow-y-auto px-2 relative" @scroll="onScroll">
        <div v-if="chatStore.loading" class="flex items-center justify-center h-full text-[#80848e] text-sm">
          Loading messages...
        </div>
        <MessageList v-else :messages="chatStore.messages" />
        <button
          v-if="showScrollButton"
          @click="scrollDown"
          class="absolute bottom-4 right-6 bg-[#eb459e] text-white text-xs px-3 py-1.5 rounded-full shadow-lg hover:bg-[#d946a6] transition"
        >
          New messages ↓
        </button>
      </div>

      <div v-if="typingUsers.size > 0" class="px-4 py-1 text-[#80848e] text-xs italic">
        <TypingIndicator v-for="user in typingUsers" :key="user" :user="user" />
      </div>

      <div class="px-4 pb-6 pt-2 bg-[#313338]">
        <MessageInput @send="handleSend" @input="handleInput" />
      </div>
    </main>
  </div>
</template>