import { ref, onUnmounted } from 'vue'

export function useTyping(onStart: () => void, onStop: () => void, timeout: number = 1000) {
  const isTyping = ref(false)
  let typingTimeout: ReturnType<typeof setTimeout> | null = null

  function start() {
    if (!isTyping.value) {
      isTyping.value = true
      onStart()
    }
    if (typingTimeout) clearTimeout(typingTimeout)
    typingTimeout = setTimeout(() => {
      isTyping.value = false
      onStop()
    }, timeout)
  }

  function stop() {
    if (typingTimeout) clearTimeout(typingTimeout)
    if (isTyping.value) {
      isTyping.value = false
      onStop()
    }
  }

  onUnmounted(() => {
    if (typingTimeout) clearTimeout(typingTimeout)
  })

  return { isTyping, start, stop }
}
