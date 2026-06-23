<template>
  <div>
    <div v-if="loading" style="text-align: center; padding: 2rem; color: var(--text-muted);">
      Generiere PDF...
    </div>
    <div v-else-if="error" style="color: var(--danger); white-space: pre-wrap; font-family: monospace; font-size: 0.85rem; background: #fef2f2; padding: 1rem; border-radius: var(--radius);">
      {{ error }}
    </div>
    <iframe v-else-if="pdfUrl" :src="pdfUrl" style="width: 100%; height: 500px; border: 1px solid var(--border); border-radius: var(--radius);"></iframe>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ pdfUrl: string | null, loading: boolean, error: string | null }>()
</script>
