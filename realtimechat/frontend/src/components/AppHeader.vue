<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <header class="bg-[#2b2d31] text-white px-4 py-2.5 flex items-center justify-between border-b border-[#1e1f22]">
    <router-link to="/" class="text-sm font-semibold tracking-wide hover:text-[#dcddde] transition-colors">
      Chat
    </router-link>
    <div class="flex items-center gap-3">
      <span class="text-sm text-[#dcddde]">{{ auth.username }}</span>
      <button
        @click="logout"
        class="text-xs bg-[#383a40] hover:bg-[#404249] px-3 py-1.5 rounded transition-colors"
      >
        Logout
      </button>
    </div>
  </header>
</template>
