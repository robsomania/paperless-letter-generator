<template>
  <AppLayout title="Absender (Familie)">
    <template #actions>
      <button class="btn btn-primary" @click="showForm = true; editingId = null; resetForm()">+ Neuer Absender</button>
    </template>

    <div v-if="showForm" class="card" style="max-width: 600px;">
      <h3 style="margin-bottom: 0.75rem;">{{ editingId ? 'Absender bearbeiten' : 'Neuen Absender anlegen' }}</h3>
      <div class="form-group">
        <label>Name *</label>
        <input v-model="form.name" placeholder="z.B. Max Mustermann" />
      </div>
      <div class="form-group">
        <label>Straße</label>
        <input v-model="form.street" placeholder="Musterstr. 1" />
      </div>
      <div class="form-group">
        <label>PLZ Ort</label>
        <input v-model="form.zip_city" placeholder="12345 Musterstadt" />
      </div>
      <div class="form-group">
        <label>Land</label>
        <input v-model="form.country" placeholder="Deutschland" />
      </div>
      <div class="form-group">
        <label>E-Mail</label>
        <input v-model="form.email" placeholder="max@example.com" />
      </div>
      <div class="form-group">
        <label>Telefon</label>
        <input v-model="form.phone" placeholder="0123 456789" />
      </div>
      <div class="form-group">
        <label>
          <input type="checkbox" v-model="form.is_default" />
          Standard-Absender (vorausgewählt bei neuen Briefen)
        </label>
      </div>
      <div class="btn-group">
        <button class="btn btn-primary" @click="save">Speichern</button>
        <button class="btn" @click="showForm = false">Abbrechen</button>
        <button v-if="editingId" class="btn btn-danger" @click="remove">Löschen</button>
      </div>
    </div>

    <table v-if="senders.length > 0" style="margin-top: 1rem;">
      <thead>
        <tr>
          <th>Name</th>
          <th>Adresse</th>
          <th>E-Mail</th>
          <th>Telefon</th>
          <th>Standard</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in senders" :key="s.id">
          <td>{{ s.name }}</td>
          <td>{{ s.street }}, {{ s.zip_city }}</td>
          <td>{{ s.email || '-' }}</td>
          <td>{{ s.phone || '-' }}</td>
          <td>{{ s.is_default ? 'Ja' : '' }}</td>
          <td>
            <button class="btn btn-sm" @click="edit(s)">Bearbeiten</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty-state" style="margin-top: 1rem;">
      <p>Keine Absender angelegt.</p>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { sendersApi, type SenderProfile } from '@/api/senders'

const senders = ref<SenderProfile[]>([])
const showForm = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ name: '', street: '', zip_city: '', country: '', email: '', phone: '', is_default: false })

onMounted(async () => {
  try {
    const res = await sendersApi.list()
    senders.value = res.data
  } catch { senders.value = [] }
})

function resetForm() {
  form.name = ''
  form.street = ''
  form.zip_city = ''
  form.country = ''
  form.email = ''
  form.phone = ''
  form.is_default = false
}

function edit(s: SenderProfile) {
  editingId.value = s.id
  form.name = s.name
  form.street = s.street
  form.zip_city = s.zip_city
  form.country = s.country
  form.email = s.email
  form.phone = s.phone
  form.is_default = s.is_default
  showForm.value = true
}

async function save() {
  if (!form.name.trim()) { alert('Name ist erforderlich'); return }
  try {
    if (editingId.value) {
      const res = await sendersApi.update(editingId.value, { ...form })
      const idx = senders.value.findIndex(s => s.id === editingId.value)
      if (idx !== -1) senders.value[idx] = res.data
    } else {
      const res = await sendersApi.create({ ...form })
      senders.value.push(res.data)
    }
    showForm.value = false
  } catch (e: any) {
    alert('Fehler: ' + (e?.response?.data?.detail || e.message))
  }
}

async function remove() {
  if (!editingId.value || !confirm('Absender wirklich löschen?')) return
  try {
    await sendersApi.delete(editingId.value)
    senders.value = senders.value.filter(s => s.id !== editingId.value)
    showForm.value = false
    editingId.value = null
  } catch { alert('Löschen fehlgeschlagen') }
}
</script>
