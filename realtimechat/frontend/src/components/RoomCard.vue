<script setup lang="ts">
import type { Room } from '@/types'

defineProps<{
  room: Room
}>()

defineEmits<{
  click: [roomName: string]
}>()

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <button
    @click="$emit('click', room.room)"
    class="w-full flex items-center justify-between p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors text-left"
  >
    <div>
      <div class="font-medium text-slate-800 text-sm">#{{ room.room }}</div>
      <div class="text-xs text-slate-500 mt-0.5">{{ formatTime(room.last_message) }}</div>
    </div>
    <span class="bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full">
      {{ room.message_count }}
    </span>
  </button>
</template>
