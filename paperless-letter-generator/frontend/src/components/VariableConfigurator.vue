<template>
  <div class="card">
    <h3 style="margin-bottom: 0.75rem;">Variablen konfigurieren</h3>
    <div class="variable-row" style="font-weight: 600; font-size: 0.8rem; color: var(--text-muted);">
      <span class="var-name">Variable</span>
      <div class="var-controls">
        <span style="flex: 2;">Label</span>
        <span style="flex: 1;">Typ</span>
        <span style="flex: 0 0 60px;">Pflicht</span>
      </div>
    </div>
    <div v-for="(v, i) in modelValue" :key="v.name" class="variable-row">
      <span class="var-name">{{ v.name }}</span>
      <div class="var-controls">
        <input :value="v.label" @input="update(i, 'label', ($event.target as HTMLInputElement).value)" placeholder="Label" style="flex: 2;" />
        <select :value="v.type" @change="update(i, 'type', ($event.target as HTMLSelectElement).value)" style="flex: 1;">
          <option value="text">Text</option>
          <option value="textarea">Textarea</option>
          <option value="date">Datum</option>
        </select>
        <input type="checkbox" :checked="v.required" @change="update(i, 'required', ($event.target as HTMLInputElement).checked)" style="flex: 0 0 60px;" />
      </div>
    </div>
    <div v-if="modelValue.length === 0" style="color: var(--text-muted); padding: 0.5rem; font-size: 0.9rem;">
      Keine Variablen gefunden. Verwende <code v-pre>{{ var_name }}</code> im LaTeX-Quelltext.
    </div>
  </div>
</template>

<script setup lang="ts">
export interface VariableItem {
  name: string
  label: string
  type: string
  required: boolean
}

const props = defineProps<{ modelValue: VariableItem[] }>()
const emit = defineEmits<{ 'update:modelValue': [items: VariableItem[]] }>()

function update(index: number, field: 'label' | 'type' | 'required', value: string | boolean) {
  const copy = props.modelValue.map(v => ({ ...v }))
  ;(copy[index] as any)[field] = value
  emit('update:modelValue', copy)
}
</script>