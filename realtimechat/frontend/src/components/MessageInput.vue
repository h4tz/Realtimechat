<script setup lang="ts">
import { ref, onMounted } from 'vue'

const emit = defineEmits<{
  send: [content: string]
}>()

const input = ref('')
const inputEl = ref<HTMLInputElement | null>(null)

onMounted(() => inputEl.value?.focus())

function handleSend() {
  const trimmed = input.value.trim()
  if (!trimmed) return
  emit('send', trimmed)
  input.value = ''
  inputEl.value?.focus()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="flex items-center gap-2">
    <input
      ref="inputEl"
      v-model="input"
      @keydown="handleKeydown"
      type="text"
      placeholder="Message..."
      class="flex-1 px-4 py-2.5 rounded-lg bg-[#383a40] text-[#dcddde] placeholder-[#6d6f78] text-sm outline-none focus:ring-0 border border-transparent focus:border-[#eb459e] transition-colors"
      autocomplete="off"
    />
    <button
      @click="handleSend"
      :disabled="!input.trim()"
      class="px-4 py-2.5 bg-[#eb459e] text-white text-sm font-medium rounded-lg hover:bg-[#d946a6] disabled:bg-[#383a40] disabled:text-[#6d6f78] disabled:cursor-not-allowed transition-colors"
    >
      Send
    </button>
  </div>
</template>