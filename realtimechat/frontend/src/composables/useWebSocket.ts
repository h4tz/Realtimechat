import { ref, onUnmounted } from 'vue'
import type { WSIncomingMessage, WSOutgoingMessage } from '@/types'
import { useAuthStore } from '@/stores/auth'

export function useWebSocket(url: string) {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const authenticated = ref(false)
  const reconnectAttempts = ref(0)
  const maxReconnectAttempts = 10
  let reconnectTimeout: ReturnType<typeof setTimeout> | null = null
  let intentionalClose = false

  function connect() {
    const auth = useAuthStore()
    if (!auth.accessToken) return

    intentionalClose = false
    authenticated.value = false

    ws.value = new WebSocket(url)

    ws.value.onopen = () => {
      // Send auth message as first message (token not in URL)
      ws.value?.send(JSON.stringify({
        type: 'auth',
        token: auth.accessToken,
      }))
      connected.value = true
      authenticated.value = true
      reconnectAttempts.value = 0
    }

    ws.value.onclose = () => {
      connected.value = false
      authenticated.value = false
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
    if (ws.value?.readyState === WebSocket.OPEN && authenticated.value) {
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
      try {
        const data = JSON.parse(event.data)
        callback(data)
      } catch {
        // Ignore malformed messages
      }
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

  return { ws, connected, authenticated, connect, disconnect, send, sendTyping, sendMessage, onMessage }
}
