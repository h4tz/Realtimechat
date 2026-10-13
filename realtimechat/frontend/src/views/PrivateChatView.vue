<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { useWebSocket } from '@/composables/useWebSocket'
import { useTyping } from '@/composables/useTyping'
import AppHeader from '@/components/AppHeader.vue'
import MessageList from '@/components/MessageList.vue'
import MessageInput from '@/components/MessageInput.vue'
import TypingIndicator from '@/components/TypingIndicator.vue'
import type { WSIncomingMessage } from '@/types'

const route = useRoute()
const auth = useAuthStore()
const chatStore = useChatStore()

const targetUsername = ref(route.params.username as string)
const typingUsers = ref<Set<string>>(new Set())
const chatContainer = ref<HTMLElement | null>(null)

const wsUrl = `${import.meta.env.VITE_WS_URL}/ws/private/${encodeURIComponent(targetUsername.value)}/`
const { connected, connect, disconnect, sendMessage, sendTyping, onMessage } = useWebSocket(wsUrl)

const { start: startTyping, stop: stopTyping } = useTyping(
  () => sendTyping(true),
  () => sendTyping(false),
)

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function handleWsMessage(data: WSIncomingMessage) {
  switch (data.type) {
    case 'message':
      chatStore.addMessage({
        id: data.id!,
        user1: { id: 0, username: data.user! },
        user2: { id: 0, username: targetUsername.value },
        content: data.content!,
        timestamp: data.timestamp!,
        is_read: false,
        read_at: null,
      })
      typingUsers.value.delete(data.user!)
      scrollToBottom()
      break
    case 'typing':
      if (data.user !== auth.username && data.is_typing) {
        typingUsers.value.add(data.user!)
      } else {
        typingUsers.value.delete(data.user!)
      }
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

onMounted(async () => {
  await chatStore.fetchPrivateMessages(targetUsername.value)
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
  <div class="h-screen flex flex-col bg-[#313338] text-[#dcddde]">
    <AppHeader />

    <div class="bg-[#2b2d31] text-[#dcddde] px-4 py-2 text-sm font-semibold border-b border-[#1e1f22]">
      {{ targetUsername }}
    </div>

    <div ref="chatContainer" class="flex-1 overflow-y-auto">
      <div v-if="chatStore.loading" class="flex items-center justify-center h-full text-[#80848e] text-sm">
        Loading messages...
      </div>
      <MessageList v-else :messages="(chatStore.messages as any)" />
    </div>

    <div v-if="typingUsers.size > 0" class="px-4 py-1 text-[#80848e] text-xs italic">
      <TypingIndicator
        v-for="user in typingUsers"
        :key="user"
        :user="user"
      />
    </div>

    <div class="px-4 pb-6 pt-2 bg-[#313338]">
      <MessageInput @send="handleSend" @input="handleInput" />
    </div>
  </div>
</template>
