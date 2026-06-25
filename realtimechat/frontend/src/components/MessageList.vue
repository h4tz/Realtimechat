<script setup lang="ts">
import type { Message } from '@/types'
import { useAuthStore } from '@/stores/auth'

defineProps<{
  messages: Message[]
}>()

const auth = useAuthStore()

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
    <div
      v-for="msg in messages"
      :key="msg.id"
      :class="[
        'max-w-[70%] rounded-2xl px-4 py-2 animate-fade-in',
        msg.user.username === auth.username
          ? 'bg-blue-500 text-white ml-auto rounded-br-md'
          : 'bg-white text-slate-800 shadow-sm rounded-bl-md',
      ]"
    >
      <div class="text-xs font-semibold opacity-80 mb-0.5">{{ msg.user.username }}</div>
      <div class="text-sm leading-relaxed">{{ msg.content }}</div>
      <div class="text-[0.65rem] mt-0.5 opacity-60">{{ formatTime(msg.timestamp) }}</div>
    </div>
  </div>
</template>
