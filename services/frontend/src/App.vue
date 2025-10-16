<template>
  <n-config-provider :theme="theme">
    <n-layout>
      <n-layout-header bordered class="header">
        <div class="header-content">
          <div class="logo">
            <h1>🤖 EmoRobCare</h1>
          </div>
          <div class="nav">
            <n-button-group>
              <n-button
                v-for="route in routes"
                :key="route.name"
                :type="$route.name === route.name ? 'primary' : 'default'"
                @click="$router.push(route.path)"
                size="small"
              >
                <template #icon>
                  <n-icon :component="route.icon" />
                </template>
                {{ route.label }}
              </n-button>
            </n-button-group>
          </div>
          <div class="settings">
            <n-button circle @click="toggleTheme" size="small">
              <template #icon>
                <n-icon :component="themeIcon" />
              </template>
            </n-button>
            <n-button circle @click="toggleLanguage" size="small">
              <template #icon>
                <span>{{ language === 'es' ? '🇪🇸' : '🇬🇧' }}</span>
              </template>
            </n-button>
          </div>
        </div>
      </n-layout-header>

      <n-layout-content content-style="padding: 24px;">
        <router-view />
      </n-layout-content>

      <n-layout-footer bordered class="footer">
        <div class="footer-content">
          <p>🤖 EmoRobCare - Conversational AI for children with TEA2</p>
          <p class="status" :class="{ connected: isConnected, disconnected: !isConnected }">
            {{ connectionStatus }}
          </p>
        </div>
      </n-layout-footer>
    </n-layout>
  </n-config-provider>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  NConfigProvider, NLayout, NLayoutHeader, NLayoutContent, NLayoutFooter,
  NButton, NButtonGroup, NIcon, darkTheme, useMessage
} from 'naive-ui'
import {
  HomeOutline, ChatbubbleOutline, PersonOutline, TimeOutline,
  SunnyOutline, MoonOutline
} from '@vicons/ionicons5'
import { useAppStore } from './stores/app'
import { useApiStore } from './stores/api'

const appStore = useAppStore()
const apiStore = useApiStore()
const message = useMessage()

const routes = [
  { name: 'Home', path: '/', label: 'Home', icon: HomeOutline },
  { name: 'Conversation', path: '/conversation', label: 'Chat', icon: ChatbubbleOutline },
  { name: 'Profile', path: '/profile', label: 'Profile', icon: PersonOutline },
  { name: 'History', path: '/history', label: 'History', icon: TimeOutline }
]

const theme = computed(() => appStore.isDark ? darkTheme : null)
const themeIcon = computed(() => appStore.isDark ? SunnyOutline : MoonOutline)
const language = computed(() => appStore.language)
const isConnected = computed(() => apiStore.isConnected)
const connectionStatus = computed(() =>
  isConnected.value ? '🟢 Connected' : '🔴 Disconnected'
)

const toggleTheme = () => {
  appStore.toggleTheme()
}

const toggleLanguage = () => {
  appStore.toggleLanguage()
  message.info(appStore.language === 'es' ? 'Idioma cambiado' : 'Language changed')
}

onMounted(async () => {
  await apiStore.checkHealth()
})
</script>

<style scoped>
.header {
  height: 64px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.logo h1 {
  margin: 0;
  font-size: 1.5rem;
  color: #2080f0;
}

.nav {
  flex: 1;
  text-align: center;
}

.settings {
  display: flex;
  gap: 8px;
}

.footer {
  text-align: center;
  padding: 16px 24px;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
}

.footer-content p {
  margin: 0;
  opacity: 0.7;
}

.status {
  font-weight: bold;
  margin-top: 4px;
}

.status.connected {
  color: #52c41a;
}

.status.disconnected {
  color: #ff4d4f;
}

@media (max-width: 768px) {
  .header-content {
    padding: 0 16px;
  }

  .logo h1 {
    font-size: 1.2rem;
  }

  .nav .n-button {
    font-size: 0.8rem;
    padding: 0 8px;
  }
}
</style>