import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getRoomMessages, getPrivateMessages } from '@/api/messages'
import type { Message, PrivateMessage } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<(Message | PrivateMessage)[]>([])
  const loading = ref(false)
  const hasMore = ref(true)
  const currentPage = ref(1)
  const totalPages = ref(1)

  function reset() {
    messages.value = []
    hasMore.value = true
    currentPage.value = 1
    totalPages.value = 1
  }

  async function fetchRoomMessages(room: string, page: number = 1) {
    loading.value = true
    try {
      const data = await getRoomMessages(room, page)
      if (page === 1) {
        messages.value = data.messages
      } else {
        messages.value = [...data.messages, ...messages.value]
      }
      hasMore.value = data.has_previous
      currentPage.value = data.current_page
      totalPages.value = data.total_pages
    } finally {
      loading.value = false
    }
  }

  async function fetchPrivateMessages(username: string, page: number = 1) {
    loading.value = true
    try {
      const data = await getPrivateMessages(username, page)
      if (page === 1) {
        messages.value = data.messages
      } else {
        messages.value = [...data.messages, ...messages.value]
      }
      hasMore.value = data.has_previous
      currentPage.value = data.current_page
      totalPages.value = data.total_pages
    } finally {
      loading.value = false
    }
  }

  function addMessage(msg: Message | PrivateMessage) {
    messages.value.push(msg)
  }

  return {
    messages,
    loading,
    hasMore,
    currentPage,
    totalPages,
    reset,
    fetchRoomMessages,
    fetchPrivateMessages,
    addMessage,
  }
})
