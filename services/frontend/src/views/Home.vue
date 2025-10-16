<template>
  <div class="home">
    <n-card class="welcome-card">
      <div class="welcome-content">
        <h1>{{ t('welcome') }}</h1>
        <p class="description">{{ t('description') }}</p>
      </div>
    </n-card>

    <n-card class="setup-card">
      <h2>{{ t('start_conversation') }}</h2>

      <!-- Child Profile Selection -->
      <div class="form-section">
        <n-form-item label="Nombre del niño">
          <n-input
            v-model:value="childName"
            placeholder="Escribe el nombre del niño"
            @keyup.enter="startConversation"
          />
        </n-form-item>
      </div>

      <!-- Topic Selection -->
      <div class="form-section">
        <h3>{{ t('select_topic') }}</h3>
        <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen">
          <n-gi v-for="topic in topics" :key="topic.id">
            <div
              class="topic-card"
              :class="{ selected: selectedTopic === topic.id }"
              @click="selectedTopic = topic.id"
            >
              <div class="topic-icon">{{ topic.icon }}</div>
              <div class="topic-name">{{ t(`topics.${topic.id}`) }}</div>
            </div>
          </n-gi>
        </n-grid>
      </div>

      <!-- Level Selection -->
      <div class="form-section">
        <h3>{{ t('select_level') }}</h3>
        <div class="level-selector">
          <div
            v-for="level in 5"
            :key="level"
            class="level-option"
            :class="{ selected: selectedLevel === level }"
            @click="selectedLevel = level"
          >
            <div class="level-number">{{ level }}</div>
            <div class="level-description">{{ t(`levels.${level}`) }}</div>
          </div>
        </div>
      </div>

      <!-- Start Button -->
      <div class="form-section">
        <n-button
          type="primary"
          size="large"
          :disabled="!canStart"
          :loading="isLoading"
          @click="startConversation"
          block
        >
          {{ t('start_conversation') }}
        </n-button>
      </div>
    </n-card>

    <!-- Recent Conversations -->
    <n-card v-if="recentConversations.length > 0" class="recent-card">
      <h3>Conversaciones recientes</h3>
      <n-list>
        <n-list-item v-for="conv in recentConversations" :key="conv.conversation_id">
          <div class="recent-item">
            <div class="recent-info">
              <strong>{{ conv.child_id }}</strong>
              <span class="recent-topic">{{ t(`topics.${conv.topic}`) }}</span>
              <span class="recent-time">{{ formatTime(conv.created_at) }}</span>
            </div>
            <n-button size="small" @click="resumeConversation(conv)">
              Reanudar
            </n-button>
          </div>
        </n-list-item>
      </n-list>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NForm, NFormItem, NInput, NButton, NGrid, NGi,
  NList, NListItem, useMessage, useLoadingBar
} from 'naive-ui'
import { useAppStore } from '../stores/app'
import { useApiStore } from '../stores/api'

const router = useRouter()
const appStore = useAppStore()
const apiStore = useApiStore()
const message = useMessage()
const loadingBar = useLoadingBar()

const childName = ref('')
const selectedTopic = ref(null)
const selectedLevel = ref(3)
const recentConversations = ref([])

const topics = [
  { id: 'school', icon: '🏫' },
  { id: 'hobbies', icon: '🎮' },
  { id: 'holidays', icon: '✈️' },
  { id: 'food', icon: '🍕' },
  { id: 'friends', icon: '👥' },
  { id: 'family', icon: '👨‍👩‍👧‍👦' },
  { id: 'animals', icon: '🐾' },
  { id: 'sports', icon: '⚽' }
]

const canStart = computed(() => {
  return childName.value.trim() && selectedTopic.value && selectedLevel.value
})

const isLoading = computed(() => apiStore.isLoading)

const startConversation = async () => {
  if (!canStart.value) return

  try {
    loadingBar.start()
    const result = await apiStore.startConversation(
      childName.value.trim(),
      selectedTopic.value,
      selectedLevel.value
    )

    // Store conversation data for the conversation view
    localStorage.setItem('currentConversation', JSON.stringify({
      conversationId: result.conversation_id,
      childName: childName.value.trim(),
      topic: selectedTopic.value,
      level: selectedLevel.value,
      startingSentence: result.starting_sentence
    }))

    message.success('Conversación iniciada')
    router.push('/conversation')

  } catch (error) {
    console.error('Error starting conversation:', error)
    message.error('No se pudo iniciar la conversación')
  } finally {
    loadingBar.finish()
  }
}

const resumeConversation = async (conversation) => {
  try {
    loadingBar.start()
    const result = await apiStore.getConversation(conversation.conversation_id)

    localStorage.setItem('currentConversation', JSON.stringify({
      conversationId: conversation.conversation_id,
      childName: conversation.child_id,
      topic: conversation.topic,
      level: conversation.level,
      messages: result.messages
    }))

    router.push('/conversation')

  } catch (error) {
    console.error('Error resuming conversation:', error)
    message.error('No se pudo reanudar la conversación')
  } finally {
    loadingBar.finish()
  }
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return 'Hace un momento'
  if (diff < 3600000) return `Hace ${Math.floor(diff / 60000)} minutos`
  if (diff < 86400000) return `Hace ${Math.floor(diff / 3600000)} horas`
  return date.toLocaleDateString()
}

const t = (key) => appStore.t(key)

onMounted(async () => {
  // Load recent conversations (mock data for now)
  recentConversations.value = [
    {
      conversation_id: 'conv_001',
      child_id: 'Ana',
      topic: 'school',
      level: 3,
      created_at: new Date(Date.now() - 3600000).toISOString()
    },
    {
      conversation_id: 'conv_002',
      child_id: 'Carlos',
      topic: 'hobbies',
      level: 2,
      created_at: new Date(Date.now() - 7200000).toISOString()
    }
  ]
})
</script>

<style scoped>
.home {
  max-width: 800px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 24px;
  text-align: center;
}

.welcome-content h1 {
  color: #2080f0;
  margin-bottom: 8px;
}

.description {
  color: #666;
  font-size: 1.1rem;
}

.setup-card {
  margin-bottom: 24px;
}

.setup-card h2 {
  color: #333;
  margin-bottom: 24px;
}

.form-section {
  margin-bottom: 32px;
}

.form-section h3 {
  color: #333;
  margin-bottom: 16px;
}

.recent-card h3 {
  color: #333;
  margin-bottom: 16px;
}

.recent-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recent-topic {
  color: #666;
  font-size: 0.9rem;
}

.recent-time {
  color: #999;
  font-size: 0.8rem;
}

@media (max-width: 768px) {
  .level-selector {
    flex-direction: column;
  }

  .recent-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>