<template>
  <AppLayout :title="title">
    <template #actions>
      <button class="btn btn-primary" @click="generatePdf" :disabled="!selectedTemplate || generating">
        {{ generating ? 'Generiere...' : 'Vorschau' }}
      </button>
      <button class="btn btn-primary" @click="sendToPaperless" :disabled="letterStatus !== 'generated' || sending">
        {{ sending ? 'Sende...' : 'An Paperless senden' }}
      </button>
    </template>

    <div class="two-col">
      <div>
        <div class="form-group">
          <label>Template</label>
          <select v-model="selectedTemplate" @change="onTemplateChange">
            <option :value="null">-- Template wählen --</option>
            <option v-for="t in templates" :key="t.id" :value="t">{{ t.name }}</option>
          </select>
        </div>

        <div class="form-group">
          <label>Empfänger</label>
          <select v-model="selectedCorrespondent" @change="onCorrespondentChange">
            <option :value="null">-- Korrespondent wählen --</option>
            <option :value="MANUAL">-- Manuelle Eingabe --</option>
            <optgroup v-if="localProfiles.length > 0" label="Eigene Kontakte">
              <option v-for="p in localProfiles" :key="'lp-' + p.id" :value="p">{{ p.name }}</option>
            </optgroup>
            <optgroup label="Paperless">
              <option v-for="c in correspondents" :key="'pl-' + c.id" :value="c">{{ c.name }}</option>
            </optgroup>
          </select>
          <div v-if="selectedCorrespondent === MANUAL" class="manual-fields">
            <input v-model="fieldValues['recipient_name']" placeholder="Name" />
            <input v-model="fieldValues['recipient_street']" placeholder="Straße" />
            <input v-model="fieldValues['recipient_zip_city']" placeholder="PLZ Ort" />
            <input v-model="fieldValues['recipient_country']" placeholder="Land" />
          </div>
        </div>

        <div class="form-group">
          <label>Absender</label>
          <select v-model="selectedSender" @change="onSenderChange">
            <option :value="null">-- Absender wählen --</option>
            <option :value="MANUAL">-- Manuelle Eingabe --</option>
            <option v-for="s in senderProfiles" :key="s.id" :value="s">{{ s.name }}</option>
          </select>
          <div v-if="selectedSender === MANUAL" class="manual-fields">
            <input v-model="fieldValues['sender_name']" placeholder="Name" />
            <input v-model="fieldValues['sender_street']" placeholder="Straße" />
            <input v-model="fieldValues['sender_zip_city']" placeholder="PLZ Ort" />
            <input v-model="fieldValues['sender_country']" placeholder="Land" />
            <input v-model="fieldValues['sender_email']" placeholder="E-Mail" />
            <input v-model="fieldValues['sender_phone']" placeholder="Telefon" />
          </div>
        </div>

        <div class="form-group">
          <label style="display: flex; justify-content: space-between; align-items: center;">
            <span>Falzmarken</span>
            <input type="checkbox" v-model="foldmarks" style="margin: 0;" />
          </label>
        </div>

        <div class="form-group">
          <label>Quell-Dokument ID (für Antwort)</label>
          <input v-model.number="sourceDocumentId" type="number" placeholder="z.B. 123" />
          <button v-if="sourceDocumentId" class="btn btn-sm" @click="fetchSourceDoc" style="margin-top: 0.3rem;">
            Dokument laden
          </button>
        </div>

        <template v-if="sourceDoc">
          <div class="card" style="font-size: 0.9rem;">
            <strong>Quell-Dokument:</strong> {{ sourceDoc.title }}<br />
            <span style="color: var(--text-muted);">vom {{ formatDate(sourceDoc.created) }}</span>
          </div>
        </template>

        <div v-if="!profile && selectedCorrespondent && selectedCorrespondent !== MANUAL && addressFormVisible" class="card">
          <h3 style="margin-bottom: 0.75rem;">Adresse für {{ (selectedCorrespondent as PaperlessCorrespondent).name }}</h3>
          <div class="form-group">
            <label>Name</label>
            <input v-model="addressForm.name" :placeholder="(selectedCorrespondent as PaperlessCorrespondent).name" />
          </div>
          <div class="form-group">
            <label>Anrede (e/r)</label>
            <input v-model="addressForm.salutation" placeholder="r oder e" />
          </div>
          <div class="form-group">
            <label>Firma</label>
            <input v-model="addressForm.company" />
          </div>
          <div class="form-group">
            <label>Straße</label>
            <input v-model="addressForm.street" />
          </div>
          <div class="form-group">
            <label>PLZ Ort</label>
            <input v-model="addressForm.zip_city" />
          </div>
          <button class="btn btn-sm btn-primary" @click="saveAddress">Adresse speichern</button>
        </div>

        <hr style="margin: 1rem 0; border: none; border-top: 1px solid var(--border);" />

        <div v-for="field in formFields" :key="field.name" class="form-group">
          <label :title="field.name">
            {{ field.label }}
            <span v-if="field.required" style="color: var(--danger);">*</span>
          </label>
          <textarea v-if="field.type === 'textarea'" v-model="fieldValues[field.name]" :placeholder="field.label" rows="4"></textarea>
          <input v-else :type="field.type === 'date' ? 'date' : 'text'" v-model="fieldValues[field.name]" :placeholder="field.label" />
        </div>
      </div>

      <div>
        <PdfPreview :pdfUrl="pdfUrl" :loading="generating" :error="pdfError" />
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, onBeforeRouteUpdate } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import PdfPreview from '@/components/PdfPreview.vue'
import { templatesApi, type LaTeXTemplate, type DiscoveredVariable } from '@/api/templates'
import { lettersApi } from '@/api/letters'
import { paperlessApi, type PaperlessCorrespondent, type PaperlessDocument } from '@/api/paperless'
import { correspondentsApi, type CorrespondentProfile } from '@/api/correspondents'

type CorrespondentOption = PaperlessCorrespondent | CorrespondentProfile | typeof MANUAL | null
import { sendersApi, type SenderProfile } from '@/api/senders'

const MANUAL = '__manual__'
const route = useRoute()

const editSourceId = ref<number | null>(null)
const editVersionGroupId = ref<number | null>(null)
const title = computed(() => editSourceId.value
  ? `Neue Version von Brief #${editSourceId.value}`
  : 'Neuen Brief erstellen')

const templates = ref<LaTeXTemplate[]>([])
const selectedTemplate = ref<LaTeXTemplate | null>(null)
const selectedCorrespondent = ref<CorrespondentOption>(null)
const correspondents = ref<PaperlessCorrespondent[]>([])
const localProfiles = ref<CorrespondentProfile[]>([])
const senderProfiles = ref<SenderProfile[]>([])
const selectedSender = ref<SenderProfile | typeof MANUAL | null>(null)
const foldmarks = ref(true)
const sourceDocumentId = ref<number | null>(null)
const sourceDoc = ref<PaperlessDocument | null>(null)
const profile = ref<CorrespondentProfile | null>(null)
const addressFormVisible = ref(false)
const addressForm = reactive({ name: '', salutation: '', company: '', street: '', zip_city: '', country: '' })
const formFields = ref<DiscoveredVariable[]>([])
const fieldValues = reactive<Record<string, string>>({})
const letterId = ref<number | null>(null)
const letterStatus = ref<'draft' | 'generated' | 'sent' | ''>('')
const generating = ref(false)
const sending = ref(false)
const pdfUrl = ref<string | null>(null)
const pdfError = ref<string | null>(null)

onMounted(async () => {
  try {
    const tRes = await templatesApi.list()
    templates.value = tRes.data
  } catch { templates.value = [] }

  try {
    const cRes = await paperlessApi.listCorrespondents()
    correspondents.value = cRes.data
  } catch { correspondents.value = [] }

  try {
    const lpRes = await correspondentsApi.list()
    localProfiles.value = lpRes.data
  } catch { localProfiles.value = [] }

  try {
    const sRes = await sendersApi.list()
    senderProfiles.value = sRes.data
  } catch { senderProfiles.value = [] }

  await handleRouteQuery()
})

onBeforeRouteUpdate(async (to, from) => {
  if (to.query.edit !== from.query.edit || to.query.template !== from.query.template) {
    await handleRouteQuery(to.query)
  }
})

async function handleRouteQuery(query?: Record<string, any>) {
  const q = query || route.query
  await resetToNew()
  if (q.edit) {
    await loadEditLetter(Number(q.edit), q.newGroup === '1')
  } else if (q.template) {
    const t = templates.value.find(t => t.id === Number(q.template))
    if (t) selectedTemplate.value = t
    await onTemplateChange()
  }
}

async function loadEditLetter(id: number, newGroup: boolean = false) {
  editSourceId.value = id
  try {
    const letterRes = await lettersApi.get(id)
    const letter = letterRes.data
    editVersionGroupId.value = newGroup ? null : (letter.version_group_id || id)

    const t = templates.value.find(t => t.id === letter.template_id)
    if (t) {
      selectedTemplate.value = t
      await onTemplateChange()
    }

    for (const [k, v] of Object.entries(letter.field_values)) {
      fieldValues[k] = v
    }
    if ('_foldmarks' in (letter.field_values || {})) {
      foldmarks.value = letter.field_values['_foldmarks'] === 'true'
    }

    if (letter.correspondent_profile_id) {
      try {
        const cRes = await correspondentsApi.get(letter.correspondent_profile_id)
        profile.value = cRes.data
        if (profile.value.paperless_id) {
          const c = correspondents.value.find(c => c.id === profile.value?.paperless_id)
          if (c) {
            selectedCorrespondent.value = c
            applyProfile()
          }
        } else {
          selectedCorrespondent.value = profile.value
          applyProfile()
        }
      } catch {}
    } else if (letter.field_values?.recipient_name) {
      selectedCorrespondent.value = MANUAL
    }

    if (letter.sender_profile_id) {
      try {
        const sRes = await sendersApi.get(letter.sender_profile_id)
        selectedSender.value = sRes.data
        applySenderProfile()
      } catch {}
    } else if (letter.field_values?.sender_name) {
      selectedSender.value = MANUAL
    }

    if (letter.source_document_id) {
      sourceDocumentId.value = letter.source_document_id
      try {
        const docRes = await paperlessApi.getDocument(letter.source_document_id)
        sourceDoc.value = docRes.data
      } catch {}
    }

    try {
      const pdfRes = await lettersApi.download(id)
      pdfUrl.value = URL.createObjectURL(pdfRes.data as Blob)
    } catch {}
  } catch {
    editSourceId.value = null
  }
}

async function resetToNew() {
  editSourceId.value = null
  editVersionGroupId.value = null
  selectedTemplate.value = null
  selectedCorrespondent.value = null
  selectedSender.value = senderProfiles.value.find(s => s.is_default) || null
  profile.value = null
  sourceDocumentId.value = null
  sourceDoc.value = null
  letterId.value = null
  letterStatus.value = ''
  pdfUrl.value = null
  pdfError.value = null
  formFields.value = []
  foldmarks.value = true
  for (const k of Object.keys(fieldValues)) delete fieldValues[k]
}

async function onTemplateChange() {
  formFields.value = []
  for (const k of Object.keys(fieldValues)) delete fieldValues[k]
  pdfUrl.value = null
  pdfError.value = null
  letterStatus.value = ''

  if (!selectedTemplate.value) return
  try {
    const res = await templatesApi.variables(selectedTemplate.value.id)
    formFields.value = res.data
    for (const f of formFields.value) {
      fieldValues[f.name] = ''
    }
  } catch { formFields.value = [] }
  if (selectedSender.value && selectedSender.value !== MANUAL) applySenderProfile()
}

function isPaperlessCorrespondent(v: CorrespondentOption): v is PaperlessCorrespondent {
  return v !== null && v !== MANUAL && 'last_correspondence' in v
}

function isLocalProfile(v: CorrespondentOption): v is CorrespondentProfile {
  return v !== null && v !== MANUAL && 'paperless_id' in v
}

async function onCorrespondentChange() {
  profile.value = null
  addressFormVisible.value = false
  if (!selectedCorrespondent.value) return
  if (selectedCorrespondent.value === MANUAL) return
  if (isLocalProfile(selectedCorrespondent.value)) {
    profile.value = selectedCorrespondent.value
    applyProfile()
    return
  }
  if (!isPaperlessCorrespondent(selectedCorrespondent.value)) return
  try {
    const res = await correspondentsApi.getByPaperless(selectedCorrespondent.value.id)
    profile.value = res.data
    applyProfile()
  } catch {
    addressForm.name = selectedCorrespondent.value.name
    addressForm.salutation = ''
    addressForm.company = ''
    addressForm.street = ''
    addressForm.zip_city = ''
    addressForm.country = ''
    addressFormVisible.value = true
  }
}

function applyProfile() {
  if (!profile.value) return
  fieldValues['recipient_name'] = profile.value.name
  fieldValues['recipient_gender'] = profile.value.salutation
  fieldValues['recipient_company'] = profile.value.company
  fieldValues['recipient_street'] = profile.value.street
  fieldValues['recipient_zip_city'] = profile.value.zip_city
  fieldValues['recipient_country'] = profile.value.country
}

async function onSenderChange() {
  if (!selectedSender.value) return
  if (selectedSender.value === MANUAL) return
  applySenderProfile()
}

function applySenderProfile() {
  if (!selectedSender.value || selectedSender.value === MANUAL) return
  if (selectedSender.value.name) fieldValues['sender_name'] = selectedSender.value.name
  if (selectedSender.value.street) fieldValues['sender_street'] = selectedSender.value.street
  if (selectedSender.value.zip_city) fieldValues['sender_zip_city'] = selectedSender.value.zip_city
  if (selectedSender.value.country) fieldValues['sender_country'] = selectedSender.value.country
  if (selectedSender.value.email) fieldValues['sender_email'] = selectedSender.value.email
  if (selectedSender.value.phone) fieldValues['sender_phone'] = selectedSender.value.phone
}

async function saveAddress() {
  if (!selectedCorrespondent.value || selectedCorrespondent.value === MANUAL) return
  if (!isPaperlessCorrespondent(selectedCorrespondent.value)) return
  try {
    const payload = {
      paperless_id: selectedCorrespondent.value.id,
      name: addressForm.name || selectedCorrespondent.value.name,
      salutation: addressForm.salutation,
      company: addressForm.company,
      street: addressForm.street,
      zip_city: addressForm.zip_city,
      country: addressForm.country,
    }
    const res = await correspondentsApi.create(payload)
    localProfiles.value.push(res.data)
    profile.value = res.data
    addressFormVisible.value = false
    applyProfile()
  } catch (e: any) {
    alert('Fehler beim Speichern: ' + (e?.response?.data?.detail || e.message))
  }
}

async function fetchSourceDoc() {
  if (!sourceDocumentId.value) return
  try {
    const res = await paperlessApi.getDocument(sourceDocumentId.value)
    sourceDoc.value = res.data
    fieldValues['reference'] = `Ihr Schreiben vom ${formatDate(res.data.created)}, Betreff: ${res.data.title}`
    if (!selectedCorrespondent.value && res.data.correspondent) {
      const c = correspondents.value.find(c => c.id === res.data.correspondent)
      if (c) selectedCorrespondent.value = c
      await onCorrespondentChange()
    }
  } catch {
    alert('Dokument nicht gefunden')
  }
}

async function generatePdf() {
  if (!selectedTemplate.value) return
  generating.value = true
  pdfError.value = null
  pdfUrl.value = null
  try {
    const fv = { ...fieldValues, _foldmarks: foldmarks.value ? 'true' : 'false' }
    const res = await lettersApi.create({
      template_id: selectedTemplate.value.id,
      correspondent_profile_id: profile.value?.id || null,
      sender_profile_id: selectedSender.value && selectedSender.value !== MANUAL ? selectedSender.value.id : null,
      source_document_id: sourceDocumentId.value,
      field_values: fv,
      version_group_id: editVersionGroupId.value,
    })
    letterId.value = res.data.id
    const genRes = await lettersApi.generate(letterId.value)
    letterStatus.value = genRes.data.status
    const pdfRes = await lettersApi.download(letterId.value)
    pdfUrl.value = URL.createObjectURL(pdfRes.data as Blob)
  } catch (e: any) {
    pdfError.value = e?.response?.data?.detail || 'Fehler bei Generierung'
  } finally {
    generating.value = false
  }
}

async function sendToPaperless() {
  if (!letterId.value) return
  sending.value = true
  try {
    await lettersApi.send(letterId.value, {
      title: fieldValues['subject'] || `Brief #${letterId.value}`,
      correspondent_id: isPaperlessCorrespondent(selectedCorrespondent.value) ? selectedCorrespondent.value.id : undefined,
    })
    letterStatus.value = 'sent'
    alert('Brief wurde an Paperless gesendet!')
  } catch (e: any) {
    alert('Fehler beim Senden: ' + (e?.response?.data?.detail || e.message))
  } finally {
    sending.value = false
  }
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('de-DE')
}
</script>

<style scoped>
.manual-fields {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 0.5rem;
}
</style>
