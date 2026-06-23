<template>
  <AppLayout :title="isNew ? 'Neues Template' : 'Template bearbeiten'">
    <template #actions>
      <button class="btn btn-primary" @click="save">Speichern</button>
      <router-link to="/templates" class="btn">Abbrechen</router-link>
    </template>

    <div class="two-col">
      <div>
        <div class="form-group">
          <label>Name</label>
          <input v-model="form.name" placeholder="z.B. Formeller Geschäftsbrief" />
        </div>
        <div class="form-group">
          <label>Beschreibung</label>
          <input v-model="form.description" placeholder="Kurze Beschreibung" />
        </div>
        <div class="form-group full-height-textarea">
          <label>LaTeX Quelltext</label>
          <textarea ref="textareaRef" v-model="form.latex_source" class="code" placeholder="% LaTeX mit {{ var_name }} Platzhaltern" @input="onSourceChange"></textarea>
        </div>
      </div>
      <div>
        <div class="known-vars">
          <h4>Verfügbare Variablen</h4>
          <div class="var-chips">
            <button v-for="v in knownVariables" :key="v.name" class="var-chip" @click="insertVariable(v.name)" :title="v.label">
              <code v-text="'{{ ' + v.name + ' }}'"></code>
              <span class="var-chip-label">{{ v.label }}</span>
            </button>
          </div>
        </div>
        <hr style="margin: 1rem 0;" />
        <VariableConfigurator v-model="variables" />
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import VariableConfigurator, { type VariableItem } from '@/components/VariableConfigurator.vue'
import { templatesApi, type VariableConfig } from '@/api/templates'

const route = useRoute()
const router = useRouter()
const isNew = ref(true)

const form = reactive({
  name: '',
  description: '',
  latex_source: '',
})
const variables = ref<VariableItem[]>([])
const templateId = ref<number | null>(null)
const knownVariables = ref<{ name: string; label: string; type: string; required: boolean }[]>([])
const textareaRef = ref<HTMLTextAreaElement | null>(null)

onMounted(async () => {
  try {
    const res = await templatesApi.knownVariables()
    knownVariables.value = Object.entries(res.data).map(([name, c]: [string, VariableConfig]) => ({
      name, label: c.label, type: c.type, required: c.required,
    }))
  } catch { knownVariables.value = [] }

  if (route.params.id && route.params.id !== 'new') {
    isNew.value = false
    templateId.value = Number(route.params.id)
    try {
      const res = await templatesApi.get(templateId.value)
      form.name = res.data.name
      form.description = res.data.description
      form.latex_source = res.data.latex_source
      const cfg = res.data.variable_config || {}
      const configured = new Map(Object.entries(cfg))
      variables.value = [...configured.entries()].map(([name, c]) => ({
        name, label: c.label || name, type: c.type || 'text', required: c.required || false,
      }))
      const discovered = [...new Set(
        [...form.latex_source.matchAll(/\{\{\s*(\w+)\s*\}\}/g)].map(m => m[1])
      )]
      for (const name of discovered) {
        if (!configured.has(name)) {
          variables.value.push({ name, label: name, type: 'text', required: false })
        }
      }
    } catch {
      router.push('/templates')
    }
  }
})

let discoverTimer: ReturnType<typeof setTimeout> | null = null

function onSourceChange() {
  if (templateId.value) return
  if (discoverTimer) clearTimeout(discoverTimer)
  discoverTimer = setTimeout(() => {
    const discovered = new Set(
      [...form.latex_source.matchAll(/\{\{\s*(\w+)\s*\}\}/g)].map(m => m[1])
    )
    variables.value = variables.value.filter(v => discovered.has(v.name))
    for (const name of discovered) {
      if (!variables.value.find(v => v.name === name)) {
        variables.value.push({ name, label: name, type: 'text', required: false })
      }
    }
  }, 400)
}

function insertVariable(name: string) {
  const ta = textareaRef.value
  if (!ta) return
  const start = ta.selectionStart
  const end = ta.selectionEnd
  const insertion = `{{ ${name} }}`
  form.latex_source = form.latex_source.substring(0, start) + insertion + form.latex_source.substring(end)
  requestAnimationFrame(() => {
    ta.focus()
    const pos = start + insertion.length
    ta.setSelectionRange(pos, pos)
  })
}

async function save() {
  const variableConfig: Record<string, any> = {}
  for (const v of variables.value) {
    variableConfig[v.name] = { label: v.label, type: v.type, required: v.required }
  }
  const payload = { ...form, variable_config: variableConfig }
  try {
    if (isNew.value) {
      await templatesApi.create(payload)
    } else if (templateId.value) {
      await templatesApi.update(templateId.value, payload)
    }
    router.push('/templates')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || 'Fehler beim Speichern'
    alert(msg)
  }
}
</script>

<style scoped>
.known-vars h4 {
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
  color: var(--text-muted);
}
.var-chips {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  max-height: 50vh;
  overflow-y: auto;
}
.var-chip {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.35rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--surface);
  cursor: pointer;
  text-align: left;
  font-size: 0.85rem;
  transition: background 0.15s;
}
.var-chip:hover {
  background: var(--bg-secondary);
}
.var-chip code {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.8rem;
  color: var(--primary);
  white-space: nowrap;
}
.var-chip-label {
  color: var(--text-muted);
  font-size: 0.8rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
