<template>
  <div class="history">
    <n-card class="history-card">
      <div class="history-header">
        <h2>Historial de Conversaciones</h2>
        <div class="history-filters">
          <n-select
            v-model:value="selectedChild"
            :options="childOptions"
            placeholder="Todos los niños"
            clearable
            @update:value="loadConversations"
          />
          <n-select
            v-model:value="selectedTopic"
            :options="topicOptions"
            placeholder="Todos los temas"
            clearable
            @update:value="loadConversations"
          />
          <n-date-picker
            v-model:value="dateRange"
            type="daterange"
            clearable
            @update:value="loadConversations"
          />
        </div>
      </div>

      <!-- Conversation List -->
      <div class="conversation-list">
        <div v-if="filteredConversations.length === 0" class="empty-state">
          <p>No hay conversaciones que coincidan con los filtros</p>
        </div>

        <div
          v-for="conversation in filteredConversations"
          :key="conversation.conversation_id"
          class="conversation-item"
          @click="openConversation(conversation)"
        >
          <div class="conversation-main">
            <div class="conversation-info">
              <h3>{{ conversation.child_name }}</h3>
              <div class="conversation-meta">
                <n-tag :type="getTopicColor(conversation.topic)">
                  {{ t(`topics.${conversation.topic}`) }}
                </n-tag>
                <span class="conversation-level">Nivel {{ conversation.level }}</span>
                <span class="conversation-date">{{ formatDate(conversation.created_at) }}</span>
              </div>
            </div>
            <div class="conversation-stats">
              <span class="message-count">{{ conversation.message_count }} mensajes</span>
              <span class="conversation-duration">{{ formatDuration(conversation.duration) }}</span>
            </div>
          </div>
          <div class="conversation-preview">
            <p>{{ getPreviewText(conversation) }}</p>
          </div>
          <div class="conversation-actions">
            <n-button size="small" @click.stop="resumeConversation(conversation)">
              Reanudar
            </n-button>
            <n-button size="small" type="error" @click.stop="deleteConversation(conversation)">
              Eliminar
            </n-button>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="pagination" v-if="totalPages > 1">
        <n-pagination
          v-model:page="currentPage"
          :page-count="totalPages"
          @update:page="loadConversations"
        />
      </div>
    </n-card>

    <!-- Conversation Details Modal -->
    <n-modal v-model:show="showDetails" preset="card" style="width: 800px;">
      <template #header>
        Detalles de Conversación
      </template>
      <div v-if="selectedConversation">
        <div class="detail-header">
          <h3>{{ selectedConversation.child_name }}</h3>
          <div class="detail-meta">
            <n-tag :type="getTopicColor(selectedConversation.topic)">
              {{ t(`topics.${selectedConversation.topic}`) }}
            </n-tag>
            <span>Nivel {{ selectedConversation.level }}</span>
            <span>{{ formatDate(selectedConversation.created_at) }}</span>
          </div>
        </div>

        <div class="messages-preview">
          <div
            v-for="message in selectedConversation.messages"
            :key="message.timestamp"
            class="message-preview"
            :class="{ 'message-user': message.role === 'user' }"
          >
            <div class="message-content">
              <strong>{{ message.role === 'user' ? 'Niño' : 'Asistente' }}:</strong>
              <span v-html="formatMessage(message.text)"></span>
            </div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NSelect, NDatePicker, NTag, NButton, NPagination, NModal,
  useMessage, useDialog
} from 'naive-ui'
import { useAppStore } from '../stores/app'
import { useApiStore } from '../stores/api'

const router = useRouter()
const appStore = useAppStore()
const apiStore = useApiStore()
const message = useMessage()
const dialog = useDialog()

// Data
const conversations = ref([])
const selectedChild = ref(null)
const selectedTopic = ref(null)
const dateRange = ref(null)
const currentPage = ref(1)
const pageSize = ref(10)
const showDetails = ref(false)
const selectedConversation = ref(null)

const childOptions = ref([
  { label: 'Ana', value: 'ana' },
  { label: 'Carlos', value: 'carlos' },
  { label: 'Sofía', value: 'sofia' }
])

const topicOptions = [
  { label: 'Escuela', value: 'school' },
  { label: 'Hobbies', value: 'hobbies' },
  { label: 'Vacaciones', value: 'holidays' },
  { label: 'Comida', value: 'food' },
  { label: 'Amigos', value: 'friends' },
  { label: 'Familia', value: 'family' },
  { label: 'Animales', value: 'animals' },
  { label: 'Deportes', value: 'sports' }
]

// Computed
const filteredConversations = computed(() => {
  let filtered = [...conversations.value]

  if (selectedChild.value) {
    filtered = filtered.filter(conv => conv.child_id === selectedChild.value)
  }

  if (selectedTopic.value) {
    filtered = filtered.filter(conv => conv.topic === selectedTopic.value)
  }

  if (dateRange.value && dateRange.value.length === 2) {
    const [start, end] = dateRange.value
    filtered = filtered.filter(conv => {
      const convDate = new Date(conv.created_at)
      return convDate >= start && convDate <= end
    })
  }

  return filtered
})

const totalPages = computed(() => {
  return Math.ceil(filteredConversations.value.length / pageSize.value)
})

// Methods
const loadConversations = async () => {
  try {
    // Mock conversations data - in real app, this would come from API
    const mockConversations = [
      {
        conversation_id: 'conv_001',
        child_id: 'ana',
        child_name: 'Ana',
        topic: 'school',
        level: 3,
        created_at: new Date(Date.now() - 3600000).toISOString(),
        message_count: 12,
        duration: 480, // seconds
        messages: [
          { role: 'assistant', text: '__Hola__ Ana, ¿cómo fue tu día en el colegio?', timestamp: new Date(Date.now() - 3600000).toISOString() },
          { role: 'user', text: 'Bien, jugué con mis amigos', timestamp: new Date(Date.now() - 3540000).toISOString() },
          { role: 'assistant', text: '**¡Qué bien!** ¿Con qué jugaste?', timestamp: new Date(Date.now() - 3480000).toISOString() }
        ]
      },
      {
        conversation_id: 'conv_002',
        child_id: 'carlos',
        child_name: 'Carlos',
        topic: 'sports',
        level: 4,
        created_at: new Date(Date.now() - 7200000).toISOString(),
        message_count: 18,
        duration: 720,
        messages: [
          { role: 'assistant', text: '__Hola__ Carlos, ¿te gustan los deportes?', timestamp: new Date(Date.now() - 7200000).toISOString() },
          { role: 'user', text: 'Sí, me encanta el fútbol', timestamp: new Date(Date.now() - 7140000).toISOString() },
          { role: 'assistant', text: '**¡Genial!** ¿Cuál es tu equipo favorito?', timestamp: new Date(Date.now() - 7080000).toISOString() }
        ]
      },
      {
        conversation_id: 'conv_003',
        child_id: 'sofia',
        child_name: 'Sofía',
        topic: 'animals',
        level: 2,
        created_at: new Date(Date.now() - 86400000).toISOString(),
        message_count: 8,
        duration: 300,
        messages: [
          { role: 'assistant', text: '__Hola__ Sofía, ¿te gustan los animales?', timestamp: new Date(Date.now() - 86400000).toISOString() },
          { role: 'user', text: 'Sí, los perros', timestamp: new Date(Date.now() - 85800000).toISOString() },
          { role: 'assistant', text: '**¡Qué bien!** ¿Tienes un perro?', timestamp: new Date(Date.now() - 85200000).toISOString() }
        ]
      }
    ]

    conversations.value = mockConversations

  } catch (error) {
    console.error('Error loading conversations:', error)
    message.error('No se pudieron cargar las conversaciones')
  }
}

const openConversation = (conversation) => {
  selectedConversation.value = conversation
  showDetails.value = true
}

const resumeConversation = async (conversation) => {
  try {
    // Store conversation data for the conversation view
    localStorage.setItem('currentConversation', JSON.stringify({
      conversationId: conversation.conversation_id,
      childName: conversation.child_name,
      topic: conversation.topic,
      level: conversation.level,
      messages: conversation.messages
    }))

    router.push('/conversation')

  } catch (error) {
    console.error('Error resuming conversation:', error)
    message.error('No se pudo reanudar la conversación')
  }
}

const deleteConversation = (conversation) => {
  dialog.warning({
    title: 'Eliminar conversación',
    content: '¿Estás seguro de que quieres eliminar esta conversación? Esta acción no se puede deshacer.',
    positiveText: 'Eliminar',
    negativeText: 'Cancelar',
    onPositiveClick: () => {
      conversations.value = conversations.value.filter(
        conv => conv.conversation_id !== conversation.conversation_id
      )
      message.success('Conversación eliminada')
    }
  })
}

const getTopicColor = (topic) => {
  const colors = {
    school: 'info',
    hobbies: 'success',
    holidays: 'warning',
    food: 'error',
    friends: 'default',
    family: 'info',
    animals: 'success',
    sports: 'warning'
  }
  return colors[topic] || 'default'
}

const formatDate = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const getPreviewText = (conversation) => {
  if (conversation.messages && conversation.messages.length > 0) {
    const firstUserMessage = conversation.messages.find(msg => msg.role === 'user')
    if (firstUserMessage) {
      return firstUserMessage.text
    }
  }
  return 'Sin mensajes del usuario'
}

const formatMessage = (text) => {
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<span class="positive">$1</span>')
    .replace(/__(.*?)__/g, '<span class="calm">$1</span>')
  return formatted
}

const t = (key) => appStore.t(key)

onMounted(() => {
  loadConversations()
})
</script>

<style scoped>
.history {
  max-width: 1000px;
  margin: 0 auto;
}

.history-card {
  margin-bottom: 24px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.history-header h2 {
  color: #333;
  margin: 0;
}

.history-filters {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.conversation-list {
  min-height: 400px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #666;
}

.conversation-item {
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.conversation-item:hover {
  border-color: #2080f0;
  box-shadow: 0 2px 8px rgba(32, 128, 240, 0.1);
}

.conversation-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.conversation-info h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.conversation-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.conversation-level {
  font-size: 0.8rem;
  color: #666;
}

.conversation-date {
  font-size: 0.8rem;
  color: #999;
}

.conversation-stats {
  text-align: right;
  font-size: 0.9rem;
  color: #666;
}

.message-count,
.conversation-duration {
  display: block;
  margin-bottom: 4px;
}

.conversation-preview {
  margin-bottom: 12px;
}

.conversation-preview p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-actions {
  display: flex;
  gap: 8px;
}

.pagination {
  margin-top: 24px;
  text-align: center;
}

.detail-header {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-header h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.detail-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  color: #666;
}

.messages-preview {
  max-height: 400px;
  overflow-y: auto;
}

.message-preview {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  background: #f9f9f9;
}

.message-preview.message-user {
  background: #e3f2fd;
  margin-left: 20px;
}

.message-content {
  margin-bottom: 4px;
  line-height: 1.4;
}

.message-time {
  font-size: 0.8rem;
  color: #999;
}

@media (max-width: 768px) {
  .history-header {
    flex-direction: column;
    align-items: stretch;
  }

  .history-filters {
    flex-direction: column;
  }

  .conversation-main {
    flex-direction: column;
    gap: 8px;
  }

  .conversation-stats {
    text-align: left;
  }

  .conversation-actions {
    flex-direction: column;
  }
}
</style>