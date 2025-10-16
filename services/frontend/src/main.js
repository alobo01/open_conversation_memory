import { createApp } from 'vue'
import { createPinia } from 'pinia'
import naive from 'naive-ui'
import { createRouter, createWebHistory } from 'vue-router'
import { autoAnimatePlugin } from '@formkit/auto-animate/vue'

import App from './App.vue'
import Home from './views/Home.vue'
import Conversation from './views/Conversation.vue'
import Profile from './views/Profile.vue'
import History from './views/History.vue'

import './style.css'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/conversation', name: 'Conversation', component: Conversation },
  { path: '/profile', name: 'Profile', component: Profile },
  { path: '/history', name: 'History', component: History }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)

app.use(createPinia())
app.use(naive)
app.use(router)
app.use(autoAnimatePlugin)

app.mount('#app')