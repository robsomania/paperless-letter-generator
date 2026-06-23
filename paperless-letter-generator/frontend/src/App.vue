<template>
  <div class="layout">
    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <div class="sidebar-header">
        <h1>Letter Generator</h1>
        <button class="hamburger" @click="sidebarOpen = !sidebarOpen" aria-label="Menü">&#9776;</button>
      </div>
      <nav @click="sidebarOpen = false">
        <router-link to="/">Dashboard</router-link>
        <router-link to="/templates">Templates</router-link>
        <router-link to="/letters/compose">Neuer Brief</router-link>
        <router-link to="/letters">Briefe</router-link>
        <router-link to="/correspondents">Kontakte</router-link>
        <router-link to="/senders">Absender</router-link>
      </nav>
    </aside>
    <div v-if="sidebarOpen" class="sidebar-backdrop" @click="sidebarOpen = false" />
    <main class="main">
      <button class="hamburger mobile-menu-btn" @click="sidebarOpen = !sidebarOpen" aria-label="Menü">&#9776;</button>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const sidebarOpen = ref(false)
</script>
