<script setup lang="ts">
defineProps<{
  user: string
}>()
</script>

<template>
  <div class="px-4 py-1 text-[#80848e] text-xs italic flex items-center gap-1">
    <span>{{ user }} is typing</span>
    <span class="inline-flex gap-0.5">
      <span class="w-1 h-1 bg-[#80848e] rounded-full animate-bounce" style="animation-delay: 0ms"></span>
      <span class="w-1 h-1 bg-[#80848e] rounded-full animate-bounce" style="animation-delay: 150ms"></span>
      <span class="w-1 h-1 bg-[#80848e] rounded-full animate-bounce" style="animation-delay: 300ms"></span>
    </span>
  </div>
</template>