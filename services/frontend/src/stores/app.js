import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const isDark = ref(false)
  const language = ref('es')

  const toggleTheme = () => {
    isDark.value = !isDark.value
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  const toggleLanguage = () => {
    language.value = language.value === 'es' ? 'en' : 'es'
    localStorage.setItem('language', language.value)
  }

  const initializeFromStorage = () => {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme === 'dark') {
      isDark.value = true
    }

    const savedLanguage = localStorage.getItem('language')
    if (savedLanguage && ['es', 'en'].includes(savedLanguage)) {
      language.value = savedLanguage
    }
  }

  const translations = {
    es: {
      welcome: 'Bienvenido a EmoRobCare',
      description: 'Sistema conversacional para niños con TEA2',
      start_conversation: 'Iniciar Conversación',
      select_topic: 'Selecciona un tema',
      select_level: 'Selecciona el nivel',
      recording: 'Grabando...',
      stop_recording: 'Detener grabación',
      processing: 'Procesando...',
      send_message: 'Enviar mensaje',
      type_message: 'Escribe tu mensaje...',
      conversation_ended: 'Conversación finalizada',
      new_conversation: 'Nueva conversación',
      error_occurred: 'Ha ocurrido un error',
      connection_error: 'Error de conexión',
      topics: {
        school: 'Escuela',
        hobbies: 'Hobbies',
        holidays: 'Vacaciones',
        food: 'Comida',
        friends: 'Amigos',
        family: 'Familia',
        animals: 'Animales',
        sports: 'Deportes'
      },
      levels: {
        1: 'Frases muy simples',
        2: 'Frases cortas',
        3: 'Conversación básica',
        4: 'Conversación fluida',
        5: 'Conversación avanzada'
      }
    },
    en: {
      welcome: 'Welcome to EmoRobCare',
      description: 'Conversational system for children with TEA2',
      start_conversation: 'Start Conversation',
      select_topic: 'Select a topic',
      select_level: 'Select level',
      recording: 'Recording...',
      stop_recording: 'Stop recording',
      processing: 'Processing...',
      send_message: 'Send message',
      type_message: 'Type your message...',
      conversation_ended: 'Conversation ended',
      new_conversation: 'New conversation',
      error_occurred: 'An error occurred',
      connection_error: 'Connection error',
      topics: {
        school: 'School',
        hobbies: 'Hobbies',
        holidays: 'Holidays',
        food: 'Food',
        friends: 'Friends',
        family: 'Family',
        animals: 'Animals',
        sports: 'Sports'
      },
      levels: {
        1: 'Very simple phrases',
        2: 'Short phrases',
        3: 'Basic conversation',
        4: 'Fluent conversation',
        5: 'Advanced conversation'
      }
    }
  }

  const t = (key) => {
    const keys = key.split('.')
    let value = translations[language.value]
    for (const k of keys) {
      value = value?.[k]
    }
    return value || key
  }

  return {
    isDark,
    language,
    toggleTheme,
    toggleLanguage,
    initializeFromStorage,
    t
  }
})