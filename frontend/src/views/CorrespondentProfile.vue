<template>
  <AppLayout title="Kontakte (Adressbuch)">
    <div v-if="loading">Lade...</div>

    <div v-else>
      <div class="form-group" style="max-width: 400px;">
        <label>Paperless-Korrespondent übernehmen</label>
        <div style="display: flex; gap: 0.5rem;">
          <select v-model="selectedPaperlessId" @change="onSelectPaperless" style="flex: 1;">
            <option :value="null">-- Korrespondent wählen --</option>
            <option v-for="c in paperlessCorrespondents" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <button class="btn btn-sm" @click="newStandalone">+ Neuer Kontakt</button>
        </div>
      </div>

        <div v-if="editing || isStandalone" class="card" style="max-width: 600px;">
        <h3 style="margin-bottom: 0.75rem;">
          {{ editingLocalId ? 'Kontakt bearbeiten' : (isStandalone ? 'Neuen Kontakt anlegen' : 'Adresse für ' + editingName) }}
        </h3>
        <div class="form-group">
          <label>Name *</label>
          <input v-model="form.name" />
        </div>
        <div class="form-group">
          <label>Anrede (e/r)</label>
          <input v-model="form.salutation" placeholder="r oder e" />
        </div>
        <div class="form-group">
          <label>Firma</label>
          <input v-model="form.company" />
        </div>
        <div class="form-group">
          <label>Straße</label>
          <input v-model="form.street" />
        </div>
        <div class="form-group">
          <label>PLZ Ort</label>
          <input v-model="form.zip_city" />
        </div>
        <div class="form-group">
          <label>Land</label>
          <input v-model="form.country" />
        </div>
        <div class="btn-group">
          <button class="btn btn-primary" @click="save">Speichern</button>
          <button v-if="editingLocalId" class="btn btn-danger" @click="remove">Löschen</button>
          <button class="btn" @click="cancelEdit">Abbrechen</button>
        </div>
      </div>

      <hr style="margin: 1.5rem 0; border: none; border-top: 1px solid var(--border);" />

      <table v-if="localProfiles.length > 0">
        <thead>
          <tr>
            <th>Name</th>
            <th>Typ</th>
            <th>Anrede</th>
            <th>Firma</th>
            <th>Adresse</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in localProfiles" :key="p.id">
            <td>{{ p.name }}</td>
            <td><span class="badge" :class="p.paperless_id ? 'badge-pl' : 'badge-local'">{{ p.paperless_id ? 'Paperless' : 'Lokal' }}</span></td>
            <td>{{ p.salutation }}</td>
            <td>{{ p.company }}</td>
            <td>{{ p.street }}, {{ p.zip_city }}</td>
            <td>
              <button class="btn btn-sm" @click="editProfile(p)">Bearbeiten</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty-state">
        <p>Keine Kontakte gespeichert.</p>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { paperlessApi, type PaperlessCorrespondent } from '@/api/paperless'
import { correspondentsApi, type CorrespondentProfile } from '@/api/correspondents'

const loading = ref(true)
const paperlessCorrespondents = ref<PaperlessCorrespondent[]>([])
const localProfiles = ref<CorrespondentProfile[]>([])
const selectedPaperlessId = ref<number | null>(null)
const editing = ref<PaperlessCorrespondent | CorrespondentProfile | null>(null)
const editingLocalId = ref<number | null>(null)
const isStandalone = ref(false)
const editingName = ref('')
const form = reactive({ name: '', salutation: '', company: '', street: '', zip_city: '', country: '' })

onMounted(async () => {
  try {
    const [cRes, lRes] = await Promise.all([
      paperlessApi.listCorrespondents(),
      correspondentsApi.list(),
    ])
    paperlessCorrespondents.value = cRes.data
    localProfiles.value = lRes.data
  } catch {} finally {
    loading.value = false
  }
})

function onSelectPaperless() {
  isStandalone.value = false
  editingLocalId.value = null
  if (!selectedPaperlessId.value) {
    editing.value = null
    return
  }
  const c = paperlessCorrespondents.value.find(x => x.id === selectedPaperlessId.value)
  if (!c) return
  editing.value = c
  editingName.value = c.name
  const existing = localProfiles.value.find(p => p.paperless_id === c.id)
  if (existing) {
    editingLocalId.value = existing.id
    form.name = existing.name
    form.salutation = existing.salutation
    form.company = existing.company
    form.street = existing.street
    form.zip_city = existing.zip_city
    form.country = existing.country
  } else {
    form.name = c.name
    form.salutation = ''
    form.company = ''
    form.street = ''
    form.zip_city = ''
    form.country = ''
  }
}

function newStandalone() {
  isStandalone.value = true
  selectedPaperlessId.value = null
  editing.value = null
  editingLocalId.value = null
  editingName.value = ''
  form.name = ''
  form.salutation = ''
  form.company = ''
  form.street = ''
  form.zip_city = ''
  form.country = ''
}

async function save() {
  if (!form.name) { alert('Name ist erforderlich'); return }
  try {
    if (editingLocalId.value) {
      const res = await correspondentsApi.update(editingLocalId.value, { ...form })
      const idx = localProfiles.value.findIndex(p => p.id === editingLocalId.value)
      if (idx !== -1) localProfiles.value[idx] = res.data
    } else if (isStandalone.value) {
      const res = await correspondentsApi.create({ paperless_id: null, ...form })
      localProfiles.value.push(res.data)
    } else if (editing.value) {
      const res = await correspondentsApi.create({
        paperless_id: editing.value.id,
        name: form.name || editing.value.name,
        salutation: form.salutation,
        company: form.company,
        street: form.street,
        zip_city: form.zip_city,
        country: form.country,
      })
      localProfiles.value.push(res.data)
    }
    cancelEdit()
  } catch (e: any) {
    alert('Fehler: ' + (e?.response?.data?.detail || e.message))
  }
}

async function remove() {
  if (!editingLocalId.value || !confirm('Kontakt löschen?')) return
  try {
    await correspondentsApi.delete(editingLocalId.value)
    localProfiles.value = localProfiles.value.filter(p => p.id !== editingLocalId.value)
    cancelEdit()
  } catch { alert('Löschen fehlgeschlagen') }
}

function editProfile(p: CorrespondentProfile) {
  isStandalone.value = false
  editingLocalId.value = p.id
  editing.value = p
  editingName.value = p.name
  selectedPaperlessId.value = p.paperless_id
  form.name = p.name
  form.salutation = p.salutation
  form.company = p.company
  form.street = p.street
  form.zip_city = p.zip_city
  form.country = p.country
}

function cancelEdit() {
  editing.value = null
  editingLocalId.value = null
  isStandalone.value = false
  selectedPaperlessId.value = null
  form.name = ''
  form.salutation = ''
  form.company = ''
  form.street = ''
  form.zip_city = ''
  form.country = ''
}
</script>

<style scoped>
.badge {
  display: inline-block;
  font-size: 0.7rem;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  vertical-align: middle;
}
.badge-local {
  background: var(--primary);
  color: #fff;
}
.badge-pl {
  background: #6c757d;
  color: #fff;
}
</style>