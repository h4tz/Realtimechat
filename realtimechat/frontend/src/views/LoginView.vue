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
const isRegister = ref(false)

async function handleSubmit() {
  if (!username.value.trim() || !password.value.trim()) {
    error.value = 'Please fill in all fields'
    return
  }

  loading.value = true
  error.value = ''
  try {
    if (isRegister.value) {
      await auth.register(username.value, password.value)
    } else {
      await auth.login(username.value, password.value)
    }
    router.push('/')
  } catch (e: any) {
    error.value = e.response?.data?.error || (isRegister.value ? 'Register failed' : 'Login failed')
  } finally {
    loading.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') handleLogin()
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-[#313338] px-4 py-12">
    <div class="max-w-md mx-auto w-full">
      <div class="bg-[#2b2d31] rounded-lg shadow-2xl p-8 w-full max-w-sm border border-[#1e1f22] animate-fade-in">
        <div class="flex items-center justify-center mb-6">
          <div class="w-12 h-12 rounded-xl bg-slate-700 flex items-center justify-center">
            <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16l-4-4 4-4m0 0l4 4-4 4m0-10l4 4-4 4m0 0l4-4-4-4m0 0l-4 4 4-4m0 6v12a6 6 0 0 0 6 6h6a6 6 0 0 0 6-6V16"/>
            </svg>
          </div>
        </div>
        
        <h1 class="text-3xl font-light text-slate-100 text-center mb-2 tracking-wide">Chat</h1>
        <p class="text-slate-400 text-center text-sm mb-8">Sign in to continue</p>

        <div class="space-y-4">
          <input
            v-model="username"
            @keydown="handleKeydown"
            type="text"
            placeholder="Username"
            autocomplete="username"
            class="w-full bg-slate-700 border border-slate-500 rounded-xl px-5 py-4 text-slate-100 outline-none focus:border-slate-400 transition-colors placeholder-slate-500"
          />
          <input
            v-model="password"
            @keydown="handleKeydown"
            type="password"
            placeholder="Password"
            autocomplete="current-password"
            class="w-full bg-slate-700 border border-slate-500 rounded-xl px-5 py-4 text-slate-100 outline-none focus:border-slate-400 transition-colors placeholder-slate-500"
          />
          <button
            @click="handleSubmit"
            :disabled="loading"
            class="w-full btn btn-primary rounded-xl py-4 rounded-xl font-medium text-lg hover:shadow-lg transition-all"
            :class="{ 'opacity-50 cursor-not-allowed': loading }"
          >
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </button>
        </div>

        <p v-if="error" class="mt-6 text-sm text-slate-400 text-center">{{ error }}</p>

        <p class="mt-8 text-xs text-slate-500 text-center">
          <a href="#" class="text-slate-400 hover-underline" @click.prevent="isRegister = !isRegister">
            {{ isRegister ? 'Already have an account? Sign in' : "Don't have an account? Register" }}
          </a>
        </p>
      </div>
    </div>
  </div>
</template>