import { ref, onUnmounted } from 'vue'
import type { WSIncomingMessage, WSOutgoingMessage } from '@/types'
import { useAuthStore } from '@/stores/auth'

export function useWebSocket(url: string) {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 10
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  let intentionalClose = false

  function connect() {
    const auth = useAuthStore()
    if (!auth.accessToken) return

    intentionalClose = false
    const separator = url.includes('?') ? '&' : '?'
    const fullUrl = `${url}${separator}token=${auth.accessToken}`

    ws.value = new WebSocket(fullUrl)

    ws.value.onopen = () => {
      connected.value = true
      reconnectAttempts.value = 0
    }

    ws.value.onclose = () => {
      connected.value = false
      if (!intentionalClose && reconnectAttempts.value < maxReconnectAttempts) {
        const delay = Math.min(1000 * 2 ** reconnectAttempts.value, 30000)
        reconnectTimeout = setTimeout(() => {
          reconnectAttempts.value++
          connect()
        }, delay)
      }
    }

    ws.value.onerror = () => {
      ws.value?.close()
    }
  }

  function send(data: WSOutgoingMessage) {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify(data))
    }
  }

  function sendTyping(isTyping: boolean) {
    send({ type: 'typing', is_typing: isTyping })
  }

  function sendMessage(content: string) {
    send({ type: 'message', content })
  }

  function onMessage(callback: (data: WSIncomingMessage) => void) {
    if (!ws.value) return
    ws.value.onmessage = (event: MessageEvent) => {
      callback(JSON.parse(event.data))
    }
  }

  function disconnect() {
    intentionalClose = true
    if (reconnectTimeout) clearTimeout(reconnectTimeout)
    ws.value?.close()
  }

  onUnmounted(() => {
    disconnect()
  })

  return { ws, connected, connect, disconnect, send, sendTyping, sendMessage, onMessage }
}
