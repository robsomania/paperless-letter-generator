<template>
  <AppLayout title="Dashboard">
    <template #actions>
      <router-link to="/letters/compose" class="btn btn-primary">Neuer Brief</router-link>
      <router-link to="/templates/new" class="btn">Neues Template</router-link>
    </template>

    <div class="status-bar">
      <div class="status-item">Templates: <strong>{{ templateCount }}</strong></div>
      <div class="status-item">Briefe (Entwurf): <strong>{{ draftCount }}</strong></div>
      <div class="status-item">Briefe (gesendet): <strong>{{ sentCount }}</strong></div>
    </div>

    <div class="card" v-if="connectionStatus !== null">
      <h3 style="margin-bottom: 0.5rem;">Paperless-ngx Verbindung</h3>
      <p v-if="connectionStatus" style="color: var(--success);">Verbunden mit {{ paperlessUrl }}</p>
      <p v-else style="color: var(--danger);">Keine Verbindung. Prüfe PAPERLESS_API_URL und Token.</p>
    </div>

    <h3 style="margin: 1.5rem 0 0.75rem;">Letzte Briefe</h3>
    <div v-if="recentLetters.length === 0" class="empty-state">
      <p>Noch keine Briefe erstellt.</p>
      <router-link to="/letters/compose" class="btn btn-primary">Ersten Brief erstellen</router-link>
    </div>
    <table v-else>
      <thead>
        <tr>
          <th>Template</th>
          <th>Empfänger</th>
          <th>Status</th>
          <th>Erstellt</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="g in recentLetters" :key="g.latest.id">
          <td>{{ g.latest.template_name }}</td>
          <td>{{ g.latest.correspondent_name || '-' }}</td>
          <td><span :class="'badge badge-' + g.latest.status">{{ statusLabel(g.latest.status) }}</span></td>
          <td>{{ formatDate(g.latest.created_at) }}</td>
          <td><span v-if="g.count > 1" class="version-count">{{ g.count }} Versionen</span></td>
        </tr>
      </tbody>
    </table>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { templatesApi } from '@/api/templates'
import { lettersApi, type Letter } from '@/api/letters'
import { paperlessApi } from '@/api/paperless'

const templateCount = ref(0)
const draftCount = ref(0)
const sentCount = ref(0)
const allLetters = ref<Letter[]>([])
const recentLetters = computed(() => {
  const map = new Map<number, { latest: Letter; count: number }>()
  for (const l of allLetters.value) {
    const gid = l.version_group_id || l.id
    const cur = map.get(gid)
    if (!cur) {
      map.set(gid, { latest: l, count: 1 })
    } else {
      cur.count++
      if (new Date(l.created_at) > new Date(cur.latest.created_at)) cur.latest = l
    }
  }
  return [...map.values()]
    .sort((a, b) => new Date(b.latest.created_at).getTime() - new Date(a.latest.created_at).getTime())
    .slice(0, 10)
})
const connectionStatus = ref<boolean | null>(null)
const paperlessUrl = ref('')

onMounted(async () => {
  try {
    const tRes = await templatesApi.list()
    templateCount.value = tRes.data.length
  } catch { templateCount.value = 0 }

  try {
    const lRes = await lettersApi.list()
    allLetters.value = lRes.data
    draftCount.value = lRes.data.filter(l => l.status === 'draft').length
    sentCount.value = lRes.data.filter(l => l.status === 'sent').length
  } catch { allLetters.value = [] }

  try {
    const cRes = await paperlessApi.me()
    connectionStatus.value = true
    paperlessUrl.value = cRes.data.url
  } catch { connectionStatus.value = false }
})

function statusLabel(s: string) {
  const labels: Record<string, string> = { draft: 'Entwurf', generated: 'Generiert', sent: 'Gesendet' }
  return labels[s] || s
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('de-DE')
}
</script>

<style scoped>
.version-count {
  font-size: 0.8rem;
  color: var(--text-muted);
  background: var(--bg);
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  white-space: nowrap;
}
</style>
