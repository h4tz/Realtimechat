<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value.trim() || !password.value.trim()) {
    error.value = 'Please fill in all fields'
    return
  }

  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.error || 'Login failed'
  } finally {
    loading.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') handleLogin()
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600 px-4">
    <div class="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
      <h1 class="text-2xl font-light text-slate-800 text-center mb-6 tracking-wide">Sign In</h1>

      <div class="space-y-4">
        <input
          v-model="username"
          @keydown="handleKeydown"
          type="text"
          placeholder="Username"
          autocomplete="username"
          class="w-full px-4 py-3 rounded-full border-2 border-slate-200 text-sm outline-none focus:border-blue-500 transition-colors"
        />
        <input
          v-model="password"
          @keydown="handleKeydown"
          type="password"
          placeholder="Password"
          autocomplete="current-password"
          class="w-full px-4 py-3 rounded-full border-2 border-slate-200 text-sm outline-none focus:border-blue-500 transition-colors"
        />
        <button
          @click="handleLogin"
          :disabled="loading"
          class="w-full py-3 bg-blue-500 text-white rounded-full font-medium hover:bg-blue-600 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
        >
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </div>

      <p v-if="error" class="mt-4 text-sm text-red-500 text-center">{{ error }}</p>
    </div>
  </div>
</template>
