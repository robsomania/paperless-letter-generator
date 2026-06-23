<template>
  <AppLayout title="Templates">
    <template #actions>
      <router-link to="/templates/new" class="btn btn-primary">+ Neues Template</router-link>
    </template>

    <div v-if="templates.length === 0" class="empty-state">
      <p>Keine Templates vorhanden.</p>
      <router-link to="/templates/new" class="btn btn-primary">Erstes Template erstellen</router-link>
    </div>

    <div class="card-grid">
      <div v-for="t in templates" :key="t.id" class="card">
        <h3 style="margin-bottom: 0.25rem;">{{ t.name }}</h3>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.75rem;">
          {{ t.description || 'Keine Beschreibung' }}
        </p>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 1rem;">
          Variablen: {{ Object.keys(t.variable_config || {}).length }}
        </p>
        <div class="btn-group">
          <router-link :to="`/templates/${t.id}`" class="btn btn-sm">Bearbeiten</router-link>
          <router-link :to="`/letters/compose?template=${t.id}`" class="btn btn-sm btn-primary">Verwenden</router-link>
          <button class="btn btn-sm btn-danger" @click="confirmDelete(t)">Löschen</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { templatesApi, type LaTeXTemplate } from '@/api/templates'

const templates = ref<LaTeXTemplate[]>([])

onMounted(async () => {
  try {
    const res = await templatesApi.list()
    templates.value = res.data
  } catch { templates.value = [] }
})

async function confirmDelete(t: LaTeXTemplate) {
  if (!confirm(`Template "${t.name}" wirklich löschen?`)) return
  try {
    await templatesApi.delete(t.id)
    templates.value = templates.value.filter(x => x.id !== t.id)
  } catch { alert('Löschen fehlgeschlagen') }
}
</script>
