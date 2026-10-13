<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

function handlePointerMove(e: PointerEvent) {
  const x = (e.clientX / window.innerWidth - 0.5) * 2
  const y = (e.clientY / window.innerHeight - 0.5) * 2
  document.documentElement.style.setProperty('--mx', x.toFixed(3))
  document.documentElement.style.setProperty('--my', y.toFixed(3))
}

onMounted(() => {
  window.addEventListener('pointermove', handlePointerMove)
  document.documentElement.style.setProperty('--mx', '0')
  document.documentElement.style.setProperty('--my', '0')
})

onUnmounted(() => {
  window.removeEventListener('pointermove', handlePointerMove)
})
</script>

<template>
  <div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden" aria-hidden="true">
    <div
      class="blob-wrap blob-wrap-a"
      :style="{ transform: `translate(calc(var(--mx, 0) * 50px), calc(var(--my, 0) * 50px))` }"
    >
      <span class="blob blob-a"></span>
    </div>
    <div
      class="blob-wrap blob-wrap-b"
      :style="{ transform: `translate(calc(var(--mx, 0) * -70px), calc(var(--my, 0) * -70px))` }"
    >
      <span class="blob blob-b"></span>
    </div>
  </div>
  <RouterView />
</template>

<style scoped>
.blob-wrap {
  position: absolute;
  transition: transform 0.9s cubic-bezier(0.22, 1, 0.36, 1);
}
.blob-wrap-a { top: -25vmax; left: -25vmax; }
.blob-wrap-b { bottom: -25vmax; right: -25vmax; }
.blob {
  width: 60vmax;
  height: 60vmax;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.28;
  animation: floatBlob 22s ease-in-out infinite;
}
.blob-a { background: radial-gradient(circle, #eb459e, transparent 70%); }
.blob-b { background: radial-gradient(circle, #8b5cf6, transparent 70%); animation-delay: -11s; }
@keyframes floatBlob {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(6vmax, -4vmax) scale(1.06); }
  66% { transform: translate(-4vmax, 6vmax) scale(0.96); }
}
</style>