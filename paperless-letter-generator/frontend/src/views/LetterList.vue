<template>
  <AppLayout title="Briefe">
    <template #actions>
      <router-link to="/letters/compose" class="btn btn-primary">+ Neuer Brief</router-link>
    </template>

    <div v-if="groups.length === 0" class="empty-state">
      <p>Noch keine Briefe erstellt.</p>
      <router-link to="/letters/compose" class="btn btn-primary">Ersten Brief erstellen</router-link>
    </div>

    <div v-else class="letter-groups">
      <div v-for="g in groups" :key="g.groupId" class="letter-group">
        <div class="group-header" @click="toggleExpanded(g.groupId)" :class="{ clickable: g.versions.length > 1 }">
          <div class="group-info">
            <span class="group-title">{{ g.latest.template_name }}</span>
            <span class="group-meta">{{ g.latest.correspondent_name || '-' }} · {{ statusLabel(g.latest.status) }} · {{ formatDate(g.latest.created_at) }}</span>
          </div>
          <div class="group-actions">
            <span v-if="g.versions.length > 1" class="version-count">{{ g.versions.length }} Versionen</span>
            <router-link v-if="g.latest.status !== 'sent'" :to="`/letters/compose?edit=${g.latest.id}`" class="btn btn-sm" @click.stop>
              Bearbeiten
            </router-link>
            <router-link v-else :to="`/letters/compose?edit=${g.latest.id}&newGroup=1`" class="btn btn-sm" @click.stop>
              Neue Version
            </router-link>
            <button v-if="g.latest.status === 'generated'" class="btn btn-sm btn-primary" @click.stop="sendLetter(g.latest.id)">
              Senden
            </button>
            <a v-if="g.latest.paperless_document_id" :href="paperlessDocUrl(g.latest.paperless_document_id)" target="_blank" class="btn btn-sm" @click.stop>
              In Paperless
            </a>
            <span v-if="g.versions.length > 1" class="expand-icon" @click.stop="toggleExpanded(g.groupId)">{{ expanded[g.groupId] ? '▲' : '▼' }}</span>
          </div>
        </div>
        <table v-if="expanded[g.groupId]" class="version-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Erstellt</th>
              <th>Aktionen</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="l in g.versions" :key="l.id">
              <td>{{ l.id }}</td>
              <td><span :class="'badge badge-' + l.status">{{ statusLabel(l.status) }}</span></td>
              <td>{{ formatDate(l.created_at) }}</td>
              <td>
                <div class="btn-group">
                  <button v-if="l.status === 'draft'" class="btn btn-sm btn-primary" @click="regenerate(l.id)">
                    Generieren
                  </button>
                  <button v-if="l.status === 'generated'" class="btn btn-sm" @click="downloadPdf(l.id)">
                    PDF
                  </button>
                  <router-link v-if="l.status === 'generated' || l.status === 'draft'" :to="`/letters/compose?edit=${l.id}`" class="btn btn-sm">
                    Bearbeiten
                  </router-link>
                  <router-link v-else-if="l.status === 'sent'" :to="`/letters/compose?edit=${l.id}&newGroup=1`" class="btn btn-sm">
                    Neue Version
                  </router-link>
                  <button v-if="l.status === 'generated'" class="btn btn-sm btn-primary" @click="sendLetter(l.id)">
                    Senden
                  </button>
                  <a v-if="l.paperless_document_id" :href="paperlessDocUrl(l.paperless_document_id)" target="_blank" class="btn btn-sm">
                    In Paperless
                  </a>
                  <button class="btn btn-sm btn-danger" @click="deleteLetter(l.id)">Löschen</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { lettersApi, type Letter } from '@/api/letters'
import { paperlessApi } from '@/api/paperless'

interface LetterGroup {
  groupId: number
  latest: Letter
  versions: Letter[]
}

const letters = ref<Letter[]>([])
const paperlessUrl = ref('')
const expanded = reactive<Record<number, boolean>>({})

const groups = computed<LetterGroup[]>(() => {
  const map = new Map<number, Letter[]>()
  for (const l of letters.value) {
    const gid = l.version_group_id || l.id
    if (!map.has(gid)) map.set(gid, [])
    map.get(gid)!.push(l)
  }
  const result: LetterGroup[] = []
  for (const [gid, versions] of map) {
    versions.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    if (!(gid in expanded)) expanded[gid] = versions.length === 1
    result.push({
      groupId: gid,
      latest: versions[0],
      versions,
    })
  }
  result.sort((a, b) => new Date(b.latest.created_at).getTime() - new Date(a.latest.created_at).getTime())
  return result
})

onMounted(async () => {
  try {
    const res = await lettersApi.list()
    letters.value = res.data
  } catch { letters.value = [] }
  try {
    const cRes = await paperlessApi.me()
    paperlessUrl.value = cRes.data.url
  } catch {}
})

function toggleExpanded(id: number) { expanded[id] = !expanded[id] }

function statusLabel(s: string) {
  const labels: Record<string, string> = { draft: 'Entwurf', generated: 'Generiert', sent: 'Gesendet' }
  return labels[s] || s
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('de-DE')
}

async function regenerate(id: number) {
  try {
    await lettersApi.generate(id)
    const res = await lettersApi.list()
    letters.value = res.data
  } catch (e: any) {
    alert('Fehler: ' + (e?.response?.data?.detail || e.message))
  }
}

async function downloadPdf(id: number) {
  try {
    const res = await lettersApi.download(id)
    const url = URL.createObjectURL(res.data as Blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `letter-${id}.pdf`
    a.click()
  } catch { alert('Download fehlgeschlagen') }
}

async function sendLetter(id: number) {
  try {
    const l = letters.value.find(x => x.id === id)
    await lettersApi.send(id, {
      title: `Brief #${id}`,
      correspondent_id: l?.correspondent_profile_id || undefined,
    })
    const res = await lettersApi.list()
    letters.value = res.data
    alert('Brief gesendet!')
  } catch (e: any) {
    alert('Fehler: ' + (e?.response?.data?.detail || e.message))
  }
}

async function deleteLetter(id: number) {
  if (!confirm('Brief wirklich löschen?')) return
  try {
    await lettersApi.delete(id)
    letters.value = letters.value.filter(l => l.id !== id)
  } catch { alert('Löschen fehlgeschlagen') }
}

function paperlessDocUrl(docId: string) {
  return `${paperlessUrl.value}/documents/${docId}/details`
}
</script>

<style scoped>
.letter-groups {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.letter-group {
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: var(--bg-secondary);
  gap: 1rem;
}

.group-header.clickable {
  cursor: pointer;
}

.group-header.clickable:hover {
  background: var(--bg-hover);
}

.group-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.group-title {
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.group-meta {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.group-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.version-count {
  font-size: 0.8rem;
  color: var(--text-muted);
  background: var(--bg);
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  white-space: nowrap;
}

.expand-icon {
  font-size: 0.75rem;
  cursor: pointer;
  user-select: none;
  color: var(--text-muted);
}

.version-table {
  width: 100%;
  border-collapse: collapse;
  border: none;
}

.version-table th,
.version-table td {
  padding: 0.5rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.version-table th {
  font-size: 0.85rem;
  color: var(--text-muted);
  font-weight: 600;
  background: var(--bg);
}

.version-table tr:last-child td {
  border-bottom: none;
}

.version-table .btn-group {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .group-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  .group-actions {
    flex-wrap: wrap;
  }
}
</style>
