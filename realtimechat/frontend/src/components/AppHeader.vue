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
  <header class="bg-slate-800 text-white px-4 py-3 flex items-center justify-between shadow-md">
    <router-link to="/" class="text-lg font-semibold tracking-wide hover:text-slate-200 transition-colors">
      Chat
    </router-link>
    <div class="flex items-center gap-4">
      <span class="text-sm text-slate-300">{{ auth.username }}</span>
      <button
        @click="logout"
        class="text-sm bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg transition-colors"
      >
        Logout
      </button>
    </div>
  </header>
</template>
