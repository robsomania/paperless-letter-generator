<template>
  <div>
    <div class="page-header">
      <h2>{{ title }}</h2>
      <div class="btn-group">
        <slot name="actions" />
      </div>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string }>()
</script>
