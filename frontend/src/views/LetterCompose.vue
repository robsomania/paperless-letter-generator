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

        <hr style="margin: 1rem 0; border: none; border-top: 1px solid var(--border);" />

        <div class="form-group">
          <label>Anlagen</label>
          <div class="attachments-list">
            <div v-for="(att, idx) in attachmentsRef" :key="idx" class="attachment-item">
              <input v-model="att.name" class="attachment-name" placeholder="Name der Anlage" />
              <span class="attachment-type-badge" :class="att.document_id ? 'badge-digital' : 'badge-manual'">
                {{ att.document_id ? 'PDF' : 'MAN' }}
              </span>
              <button class="btn btn-sm btn-danger" @click="removeAttachment(idx)">✕</button>
            </div>
          </div>
          <div class="btn-group" style="margin-top: 0.4rem;">
            <button class="btn btn-sm" @click="showAttachmentModal = true">+ Anlage hinzufügen</button>
          </div>
          <label class="checkbox-label" style="margin-top: 0.5rem; display: flex; align-items: center; gap: 0.4rem;">
            <input type="checkbox" v-model="attachmentWatermark" />
            Wasserzeichen auf Anlagen-Seiten (Anlage X von Y)
          </label>
        </div>
      </div>

      <div>
        <PdfPreview :pdfUrl="pdfUrl" :loading="generating" :error="pdfError" />
      </div>
    </div>

    <!-- Attachment Modal -->
    <div v-if="showAttachmentModal" class="modal-overlay" @click.self="showAttachmentModal = false">
      <div class="modal-content">
        <h3 style="margin-bottom: 0.75rem;">Dokument aus Paperless auswählen</h3>
        <div class="form-group">
          <input
            ref="searchInputRef"
            v-model="attachmentSearchQuery"
            placeholder="Suche in Paperless..."
            @input="onAttachmentSearch"
          />
        </div>
        <div class="modal-manual-row">
          <button class="btn btn-sm" @click="openManualAttachment">+ Manuelle Anlage (ohne PDF)</button>
        </div>
        <div v-if="attachmentSearchResults.length > 0" class="modal-results">
          <div
            v-for="doc in attachmentSearchResults"
            :key="doc.id"
            class="modal-result-item"
            @click="selectAttachment(doc)"
          >
            <strong>{{ doc.title }}</strong>
            <span class="result-meta">{{ doc.correspondent_name || '-' }} · {{ formatDate(doc.created) }}</span>
          </div>
        </div>
        <div v-else-if="attachmentSearchQuery && !attachmentSearching" class="empty-state">
          <p>Keine Dokumente gefunden.</p>
        </div>
        <div class="btn-group" style="margin-top: 0.75rem;">
          <button class="btn" @click="showAttachmentModal = false">Abbrechen</button>
        </div>
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
import { lettersApi, type AttachmentInfo } from '@/api/letters'
import { paperlessApi, type PaperlessCorrespondent, type PaperlessDocument, type PaperlessDocumentSearchResult } from '@/api/paperless'
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
const searchInputRef = ref<HTMLInputElement | null>(null)
const attachmentsRef = ref<AttachmentInfo[]>([])
const attachmentWatermark = ref(false)
const showAttachmentModal = ref(false)
const attachmentSearchQuery = ref('')
const attachmentSearchResults = ref<PaperlessDocumentSearchResult[]>([])
const attachmentSearching = ref(false)
let attachmentSearchTimer: ReturnType<typeof setTimeout> | null = null

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

    if (letter.attachments) {
      attachmentsRef.value = letter.attachments.filter(a => a.name || a.document_id)
    } else {
      attachmentsRef.value = []
    }
    attachmentWatermark.value = letter.attachment_watermark ?? false

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
  attachmentsRef.value = []
  attachmentWatermark.value = false
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
      attachments: attachmentsRef.value,
      attachment_watermark: attachmentWatermark.value,
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

function onAttachmentSearch() {
  if (attachmentSearchTimer) clearTimeout(attachmentSearchTimer)
  if (!attachmentSearchQuery.value.trim()) {
    attachmentSearchResults.value = []
    return
  }
  attachmentSearching.value = true
  attachmentSearchTimer = setTimeout(async () => {
    try {
      const res = await paperlessApi.searchDocuments(attachmentSearchQuery.value)
      attachmentSearchResults.value = res.data
    } catch {
      attachmentSearchResults.value = []
    } finally {
      attachmentSearching.value = false
    }
  }, 300)
}

function selectAttachment(doc: PaperlessDocumentSearchResult) {
  attachmentsRef.value.push({ document_id: doc.id, name: doc.title })
  closeAttachmentModal()
}

function openManualAttachment() {
  attachmentsRef.value.push({ document_id: null, name: '' })
  closeAttachmentModal()
}

function closeAttachmentModal() {
  showAttachmentModal.value = false
  attachmentSearchQuery.value = ''
  attachmentSearchResults.value = []
}

function removeAttachment(idx: number) {
  attachmentsRef.value.splice(idx, 1)
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

.attachments-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.attachment-name {
  flex: 1;
}

.attachment-type-badge {
  font-size: 0.65rem;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-weight: 600;
}

.badge-digital {
  background: var(--accent);
  color: #fff;
}

.badge-manual {
  background: var(--border);
  color: var(--text);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg);
  border-radius: 8px;
  padding: 1.25rem;
  min-width: 360px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}

.modal-manual-row {
  margin: 0.5rem 0;
}

.modal-results {
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-radius: 6px;
}

.modal-result-item {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.modal-result-item:hover {
  background: var(--bg-hover);
}

.modal-result-item:last-child {
  border-bottom: none;
}

.result-meta {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.empty-state {
  padding: 1rem;
  text-align: center;
  color: var(--text-secondary);
}
</style>
