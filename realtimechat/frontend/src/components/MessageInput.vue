<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  send: [content: string]
}>()

const input = ref('')

function handleSend() {
  const trimmed = input.value.trim()
  if (!trimmed) return
  emit('send', trimmed)
  input.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="flex items-center gap-2 p-4 bg-white border-t border-slate-200">
    <input
      v-model="input"
      @keydown="handleKeydown"
      type="text"
      placeholder="Type a message..."
      class="flex-1 px-4 py-2.5 rounded-full border border-slate-300 text-sm outline-none focus:border-blue-500 transition-colors"
      autocomplete="off"
    />
    <button
      @click="handleSend"
      :disabled="!input.trim()"
      class="px-5 py-2.5 bg-blue-500 text-white text-sm font-medium rounded-full hover:bg-blue-600 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
    >
      Send
    </button>
  </div>
</template>
