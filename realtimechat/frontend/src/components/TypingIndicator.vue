<script setup lang="ts">
defineProps<{
  user: string
}>()
</script>

<template>
  <div class="px-4 py-2 bg-slate-100 text-slate-500 text-xs italic">
    {{ user }} is typing...
  </div>
</template>
