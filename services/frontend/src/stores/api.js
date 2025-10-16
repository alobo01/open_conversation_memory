import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const ASR_URL = import.meta.env.VITE_ASR_URL || 'http://localhost:8001'

export const useApiStore = defineStore('api', () => {
  const isConnected = ref(false)
  const isLoading = ref(false)
  const error = ref(null)

  const api = axios.create({
    baseURL: API_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  const asrApi = axios.create({
    baseURL: ASR_URL,
    timeout: 30000, // Longer timeout for audio processing
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  // Response interceptor for error handling
  api.interceptors.response.use(
    response => response,
    async (error) => {
      console.error('API Error:', error)
      isConnected.value = false
      throw error
    }
  )

  asrApi.interceptors.response.use(
    response => response,
    async (error) => {
      console.error('ASR Error:', error)
      throw error
    }
  )

  const checkHealth = async () => {
    try {
      const response = await api.get('/health')
      isConnected.value = response.data.status === 'healthy'
      return response.data
    } catch (err) {
      isConnected.value = false
      throw err
    }
  }

  const startConversation = async (child, topic, level) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await api.post('/conv/start', {
        child,
        topic,
        level
      })

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to start conversation'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const continueConversation = async (conversationId, userSentence, end = false) => {
    try {
      isLoading.value = true
      error.value = null

      const response = await api.post('/conv/next', {
        conversation_id: conversationId,
        user_sentence: userSentence,
        end
      })

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to continue conversation'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const getConversation = async (conversationId) => {
    try {
      const response = await api.get(`/conv/${conversationId}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to get conversation'
      throw err
    }
  }

  const getChildConversations = async (childId, limit = 10) => {
    try {
      const response = await api.get(`/conv/child/${childId}?limit=${limit}`)
      return response.data.conversations
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to get conversations'
      throw err
    }
  }

  const transcribeAudio = async (audioFile, tier = 'balanced', language = null) => {
    try {
      isLoading.value = true
      error.value = null

      const formData = new FormData()
      formData.append('audio', audioFile)

      const params = new URLSearchParams()
      params.append('tier', tier)
      if (language) {
        params.append('language', language)
      }

      const response = await asrApi.post(`/transcribe?${params}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to transcribe audio'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const testTranscription = async (text, tier = 'balanced', language = 'es') => {
    try {
      const response = await asrApi.post(`/test?text=${encodeURIComponent(text)}&tier=${tier}&language=${language}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to test transcription'
      throw err
    }
  }

  const insertKnowledge = async (sparqlUpdate) => {
    try {
      const response = await api.post('/kg/insert', {
        sparql_update: sparqlUpdate
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to insert knowledge'
      throw err
    }
  }

  const retrieveKnowledge = async (sparqlSelect, limit = 100) => {
    try {
      const response = await api.post('/kg/retrieve', {
        sparql_select: sparqlSelect,
        limit
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to retrieve knowledge'
      throw err
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    isConnected,
    isLoading,
    error,
    checkHealth,
    startConversation,
    continueConversation,
    getConversation,
    getChildConversations,
    transcribeAudio,
    testTranscription,
    insertKnowledge,
    retrieveKnowledge,
    clearError
  }
})