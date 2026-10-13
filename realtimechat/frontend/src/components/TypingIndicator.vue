<script setup lang="ts">
defineProps<{
  user: string
}>()
</script>

<template>
  <div class="px-4 py-1 text-[#80848e] text-xs italic">
    {{ user }} is typing...
  </div>
</template>
