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

function isOwn(msg: Message): boolean {
  return msg.user.username === auth.username
}
</script>

<template>
  <div class="flex-1 overflow-y-auto px-2 py-2 space-y-0.5">
    <div
      v-for="msg in messages"
      :key="msg.id"
      class="group flex items-start gap-3 px-2 py-0.5 rounded hover:bg-[#2e3035] transition-colors"
    >
      <div class="mt-0.5 flex-shrink-0 w-9 h-9 rounded-full bg-[#5865f2] flex items-center justify-center text-white text-sm font-semibold">
        {{ (msg.user.username?.[0] || '?').toUpperCase() }}
      </div>
      <div class="min-w-0 flex-1">
        <div class="flex items-baseline gap-2">
          <span
            class="text-sm font-medium"
            :class="isOwn(msg) ? 'text-[#5865f2]' : 'text-white'"
          >
            {{ msg.user.username }}
          </span>
          <span class="text-[10px] text-[#80848e]">{{ formatTime(msg.timestamp) }}</span>
        </div>
        <div class="text-sm text-[#dcddde] leading-relaxed break-words whitespace-pre-wrap">{{ msg.content }}</div>
      </div>
    </div>
  </div>
</template>