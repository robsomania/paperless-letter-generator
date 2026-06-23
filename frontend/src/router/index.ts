import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '@/views/Dashboard.vue'
import TemplateList from '@/views/TemplateList.vue'
import TemplateEditor from '@/views/TemplateEditor.vue'
import LetterCompose from '@/views/LetterCompose.vue'
import LetterList from '@/views/LetterList.vue'
import CorrespondentProfile from '@/views/CorrespondentProfile.vue'
import SenderProfiles from '@/views/SenderProfiles.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/templates', name: 'TemplateList', component: TemplateList },
  { path: '/templates/new', name: 'TemplateCreate', component: TemplateEditor },
  { path: '/templates/:id', name: 'TemplateEdit', component: TemplateEditor },
  { path: '/letters/compose', name: 'LetterCompose', component: LetterCompose },
  { path: '/letters', name: 'LetterList', component: LetterList },
  { path: '/correspondents', name: 'CorrespondentProfiles', component: CorrespondentProfile },
  { path: '/senders', name: 'SenderProfiles', component: SenderProfiles },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
