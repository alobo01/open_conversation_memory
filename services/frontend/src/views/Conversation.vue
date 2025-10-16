<template>
  <div class="conversation">
    <n-card class="conversation-card">
      <!-- Conversation Header -->
      <div class="conversation-header">
        <div class="conversation-info">
          <h2>Conversación con {{ conversationData.childName }}</h2>
          <div class="conversation-meta">
            <n-tag type="info">{{ t(`topics.${conversationData.topic}`) }}</n-tag>
            <n-tag type="success">Nivel {{ conversationData.level }}</n-tag>
          </div>
        </div>
        <div class="conversation-actions">
          <n-button @click="endConversation" type="warning" size="small">
            Finalizar
          </n-button>
        </div>
      </div>

      <!-- Messages -->
      <div class="messages-container" ref="messagesContainer">
        <div
          v-for="message in messages"
          :key="message.timestamp"
          class="message"
          :class="{ 'message-user': message.role === 'user', 'message-assistant': message.role === 'assistant' }"
        >
          <div class="message-content">
            <div class="message-text" v-html="formatMessage(message.text)"></div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            <div v-if="message.asr_confidence" class="message-confidence">
              confianza: {{ Math.round(message.asr_confidence * 100) }}%
            </div>
          </div>
          <div class="message-avatar">
            <span>{{ message.role === 'user' ? '👦' : '🤖' }}</span>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="isLoading" class="message message-assistant">
          <div class="message-content">
            <div class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
          <div class="message-avatar">
            <span>🤖</span>
          </div>
        </div>
      </div>

      <!-- Input Area -->
      <div class="input-area">
        <div class="conversation-input">
          <n-input
            v-model:value="userMessage"
            :placeholder="t('type_message')"
            @keyup.enter="sendMessage"
            :disabled="isLoading || conversationEnded"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 3 }"
            ref="messageInput"
          />
          <div class="input-actions">
            <button
              class="recording-button"
              :class="{ recording: isRecording }"
              @click="toggleRecording"
              :disabled="isLoading || conversationEnded"
              v-if="isAudioSupported"
            >
              {{ isRecording ? '🔴' : '🎤' }}
            </button>
            <n-button
              type="primary"
              @click="sendMessage"
              :disabled="!userMessage.trim() || isLoading || conversationEnded"
              :loading="isLoading"
            >
              {{ t('send_message') }}
            </n-button>
          </div>
        </div>
        <div v-if="isRecording" class="recording-status">
          {{ t('recording') }}... {{ recordingTime }}s
        </div>
      </div>
    </n-card>

    <!-- Suggestions -->
    <n-card v-if="suggestions.length > 0" class="suggestions-card">
      <h3>Sugerencias:</h3>
      <div class="suggestions">
        <n-button
          v-for="suggestion in suggestions"
          :key="suggestion"
          size="small"
          @click="userMessage = suggestion"
          class="suggestion-button"
        >
          {{ suggestion }}
        </n-button>
      </div>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard, NButton, NTag, NInput, useMessage, useLoadingBar
} from 'naive-ui'
import { useAppStore } from '../stores/app'
import { useApiStore } from '../stores/api'

const router = useRouter()
const appStore = useAppStore()
const apiStore = useApiStore()
const message = useMessage()
const loadingBar = useLoadingBar()

// Data
const conversationData = ref({
  conversationId: '',
  childName: '',
  topic: '',
  level: 3
})

const messages = ref([])
const userMessage = ref('')
const isLoading = ref(false)
const conversationEnded = ref(false)
const suggestions = ref([])

// Audio recording
const isRecording = ref(false)
const recordingTime = ref(0)
const recordingTimer = ref(null)
const audioStream = ref(null)
const mediaRecorder = ref(null)
const audioChunks = ref([])

// Refs
const messagesContainer = ref(null)
const messageInput = ref(null)

// Computed
const isAudioSupported = computed(() => {
  return navigator.mediaDevices && navigator.mediaDevices.getUserMedia
})

// Methods
const formatMessage = (text) => {
  // Apply emotional markup styling
  let formatted = text
    .replace(/\*\*(.*?)\*\*/g, '<span class="positive">$1</span>')
    .replace(/__(.*?)__/g, '<span class="calm">$1</span>')

  return formatted
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const sendMessage = async () => {
  if (!userMessage.value.trim() || isLoading.value || conversationEnded.value) return

  const messageText = userMessage.value.trim()
  userMessage.value = ''

  // Add user message
  messages.value.push({
    role: 'user',
    text: messageText,
    timestamp: new Date().toISOString()
  })

  scrollToBottom()

  try {
    isLoading.value = true
    loadingBar.start()

    const response = await apiStore.continueConversation(
      conversationData.value.conversationId,
      messageText,
      false
    )

    // Add assistant message
    messages.value.push({
      role: 'assistant',
      text: response.reply,
      emotion: response.emotion,
      timestamp: response.timestamp
    })

    suggestions.value = response.suggestions || []

    scrollToBottom()

  } catch (error) {
    console.error('Error sending message:', error)
    message.error('No se pudo enviar el mensaje')
  } finally {
    isLoading.value = false
    loadingBar.finish()
  }
}

const endConversation = async () => {
  if (messages.value.length > 0) {
    try {
      await apiStore.continueConversation(
        conversationData.value.conversationId,
        conversationEnded.value ? 'Conversation ended' : 'end_conversation',
        true
      )
    } catch (error) {
      console.error('Error ending conversation:', error)
    }
  }

  conversationEnded.value = true
  message.info('Conversación finalizada')

  setTimeout(() => {
    router.push('/')
  }, 2000)
}

const toggleRecording = async () => {
  if (isRecording.value) {
    stopRecording()
  } else {
    await startRecording()
  }
}

const startRecording = async () => {
  try {
    audioStream.value = await navigator.mediaDevices.getUserMedia({ audio: true })
    mediaRecorder.value = new MediaRecorder(audioStream.value)
    audioChunks.value = []

    mediaRecorder.value.ondataavailable = (event) => {
      audioChunks.value.push(event.data)
    }

    mediaRecorder.value.onstop = async () => {
      const audioBlob = new Blob(audioChunks.value, { type: 'audio/wav' })
      await transcribeAudio(audioBlob)
    }

    mediaRecorder.value.start()
    isRecording.value = true

    // Start recording timer
    recordingTimer.value = setInterval(() => {
      recordingTime.value += 1
      if (recordingTime.value >= 30) {
        stopRecording()
      }
    }, 1000)

  } catch (error) {
    console.error('Error starting recording:', error)
    message.error('No se pudo iniciar la grabación')
  }
}

const stopRecording = () => {
  if (mediaRecorder.value && isRecording.value) {
    mediaRecorder.value.stop()
  }

  if (audioStream.value) {
    audioStream.value.getTracks().forEach(track => track.stop())
  }

  if (recordingTimer.value) {
    clearInterval(recordingTimer.value)
  }

  isRecording.value = false
  recordingTime.value = 0
  audioChunks.value = []
}

const transcribeAudio = async (audioBlob) => {
  try {
    isLoading.value = true
    loadingBar.start()

    const result = await apiStore.transcribeAudio(
      audioBlob,
      'balanced',
      appStore.language
    )

    userMessage.value = result.text
    messageInput.value?.focus()

  } catch (error) {
    console.error('Error transcribing audio:', error)
    message.error('No se pudo transcribir el audio')
  } finally {
    isLoading.value = false
    loadingBar.finish()
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const t = (key) => appStore.t(key)

// Lifecycle
onMounted(() => {
  // Load conversation data from localStorage
  const savedConversation = localStorage.getItem('currentConversation')
  if (savedConversation) {
    const data = JSON.parse(savedConversation)
    conversationData.value = {
      conversationId: data.conversationId,
      childName: data.childName,
      topic: data.topic,
      level: data.level
    }

    // Load existing messages
    if (data.messages) {
      messages.value = data.messages
    } else if (data.startingSentence) {
      // Add starting sentence
      messages.value.push({
        role: 'assistant',
        text: data.startingSentence,
        emotion: 'neutral',
        timestamp: new Date().toISOString()
      })
    }

    scrollToBottom()
  } else {
    // No conversation data, redirect to home
    router.push('/')
  }
})

onUnmounted(() => {
  if (isRecording.value) {
    stopRecording()
  }
})

watch(userMessage, () => {
  suggestions.value = []
})
</script>

<style scoped>
.conversation {
  max-width: 800px;
  margin: 0 auto;
}

.conversation-card {
  height: calc(100vh - 200px);
  display: flex;
  flex-direction: column;
}

.conversation-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.conversation-info h2 {
  margin: 0 0 8px 0;
  color: #333;
}

.conversation-meta {
  display: flex;
  gap: 8px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  max-height: calc(100vh - 400px);
}

.message {
  display: flex;
  margin-bottom: 16px;
  gap: 12px;
}

.message-user {
  flex-direction: row-reverse;
}

.message-content {
  flex: 1;
  max-width: 70%;
}

.message-user .message-content {
  text-align: right;
}

.message-text {
  background: #f0f0f0;
  padding: 12px 16px;
  border-radius: 12px;
  margin-bottom: 4px;
  word-wrap: break-word;
}

.message-assistant .message-text {
  background: #e3f2fd;
  color: #1976d2;
}

.message-time {
  font-size: 0.8rem;
  color: #999;
}

.message-confidence {
  font-size: 0.8rem;
  color: #666;
}

.message-avatar {
  font-size: 1.5rem;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-area {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.conversation-input {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.recording-status {
  margin-top: 8px;
  color: #e74c3c;
  font-size: 0.9rem;
}

.suggestions-card {
  margin-top: 16px;
}

.suggestions-card h3 {
  margin: 0 0 12px 0;
  color: #333;
}

.suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-button {
  margin: 0;
}

.loading-dots {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #1976d2;
  animation: loading-dot 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes loading-dot {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .conversation-card {
    height: calc(100vh - 150px);
  }

  .message-content {
    max-width: 85%;
  }

  .conversation-input {
    flex-direction: column;
    gap: 8px;
  }

  .input-actions {
    justify-content: space-between;
  }

  .suggestions {
    flex-direction: column;
  }

  .suggestion-button {
    width: 100%;
  }
}
</style>