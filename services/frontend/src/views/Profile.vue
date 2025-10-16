<template>
  <div class="profile">
    <n-card class="profile-card">
      <h2>Perfil del Niño</h2>

      <!-- Child Selection -->
      <div class="form-section">
        <n-form-item label="Seleccionar niño">
          <n-select
            v-model:value="selectedChildId"
            :options="childOptions"
            placeholder="Selecciona un niño"
            @update:value="loadChildProfile"
          />
        </n-form-item>
      </div>

      <!-- Profile Form -->
      <n-form v-if="currentProfile" :model="currentProfile">
        <div class="form-grid">
          <n-form-item label="Nombre">
            <n-input v-model:value="currentProfile.name" />
          </n-form-item>

          <n-form-item label="Edad">
            <n-input-number
              v-model:value="currentProfile.age"
              :min="5"
              :max="13"
            />
          </n-form-item>

          <n-form-item label="Idioma">
            <n-select
              v-model:value="currentProfile.language"
              :options="languageOptions"
            />
          </n-form-item>

          <n-form-item label="Nivel conversacional">
            <n-slider
              v-model:value="currentProfile.level"
              :min="1"
              :max="5"
              :marks="levelMarks"
              :step="1"
            />
          </n-form-item>

          <n-form-item label="Sensibilidad">
            <n-select
              v-model:value="currentProfile.sensitivity"
              :options="sensitivityOptions"
            />
          </n-form-item>
        </div>

        <!-- Topics -->
        <div class="form-section">
          <h3>Temas preferidos</h3>
          <n-checkbox-group v-model:value="currentProfile.preferred_topics">
            <n-space>
              <n-checkbox
                v-for="topic in topicOptions"
                :key="topic.value"
                :value="topic.value"
                :label="topic.label"
              />
            </n-space>
          </n-checkbox-group>
        </div>

        <div class="form-section">
          <h3>Temas a evitar</h3>
          <n-checkbox-group v-model:value="currentProfile.avoid_topics">
            <n-space>
              <n-checkbox
                v-for="topic in topicOptions"
                :key="topic.value"
                :value="topic.value"
                :label="topic.label"
              />
            </n-space>
          </n-checkbox-group>
        </div>

        <!-- Actions -->
        <div class="form-actions">
          <n-button type="primary" @click="saveProfile" :loading="isLoading">
            Guardar perfil
          </n-button>
          <n-button @click="createNewProfile">
            Crear nuevo perfil
          </n-button>
        </div>
      </n-form>

      <!-- Create New Profile Form -->
      <n-form v-else-if="showCreateForm" :model="newProfile">
        <h3>Crear Nuevo Perfil</h3>
        <div class="form-grid">
          <n-form-item label="Nombre">
            <n-input v-model:value="newProfile.name" />
          </n-form-item>

          <n-form-item label="Edad">
            <n-input-number
              v-model:value="newProfile.age"
              :min="5"
              :max="13"
            />
          </n-form-item>

          <n-form-item label="Idioma">
            <n-select
              v-model:value="newProfile.language"
              :options="languageOptions"
            />
          </n-form-item>
        </div>

        <div class="form-actions">
          <n-button type="primary" @click="createProfile" :loading="isLoading">
            Crear perfil
          </n-button>
          <n-button @click="showCreateForm = false">
            Cancelar
          </n-button>
        </div>
      </n-form>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <p>No hay perfiles configurados</p>
        <n-button type="primary" @click="showCreateForm = true">
          Crear primer perfil
        </n-button>
      </div>
    </n-card>

    <!-- Statistics -->
    <n-card v-if="currentProfile && stats" class="stats-card">
      <h3>Estadísticas</h3>
      <n-grid :cols="2" :x-gap="16" :y-gap="16">
        <n-gi>
          <n-statistic label="Conversaciones totales" :value="stats.total_conversations" />
        </n-gi>
        <n-gi>
          <n-statistic label="Mensajes totales" :value="stats.total_messages" />
        </n-gi>
        <n-gi>
          <n-statistic label="Duración promedio" :value="stats.avg_conversation_length" suffix="msg" />
        </n-gi>
        <n-gi>
          <n-statistic label="Temas favoritos" :value="stats.favorite_topic" />
        </n-gi>
      </n-grid>
    </n-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  NCard, NForm, NFormItem, NInput, NInputNumber, NSelect, NButton,
  NCheckboxGroup, NCheckbox, NSpace, NSlider, NGrid, NGi,
  NStatistic, useMessage, useLoadingBar
} from 'naive-ui'
import { useAppStore } from '../stores/app'
import { useApiStore } from '../stores/api'

const appStore = useAppStore()
const apiStore = useApiStore()
const message = useMessage()
const loadingBar = useLoadingBar()

// Data
const selectedChildId = ref(null)
const currentProfile = ref(null)
const newProfile = ref({
  name: '',
  age: 8,
  language: 'es'
})
const showCreateForm = ref(false)
const isLoading = ref(false)
const stats = ref(null)

const childOptions = ref([
  { label: 'Ana', value: 'ana' },
  { label: 'Carlos', value: 'carlos' },
  { label: 'Sofía', value: 'sofia' }
])

const languageOptions = [
  { label: 'Español', value: 'es' },
  { label: 'English', value: 'en' }
]

const sensitivityOptions = [
  { label: 'Baja', value: 'low' },
  { label: 'Media', value: 'medium' },
  { label: 'Alta', value: 'high' }
]

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

const levelMarks = {
  1: '1',
  2: '2',
  3: '3',
  4: '4',
  5: '5'
}

// Methods
const loadChildProfile = async (childId) => {
  // Mock profile data - in real app, this would come from API
  const mockProfiles = {
    ana: {
      child_id: 'ana',
      name: 'Ana',
      age: 7,
      language: 'es',
      level: 3,
      sensitivity: 'medium',
      preferred_topics: ['school', 'friends', 'animals'],
      avoid_topics: []
    },
    carlos: {
      child_id: 'carlos',
      name: 'Carlos',
      age: 9,
      language: 'es',
      level: 4,
      sensitivity: 'low',
      preferred_topics: ['sports', 'hobbies', 'food'],
      avoid_topics: ['family']
    },
    sofia: {
      child_id: 'sofia',
      name: 'Sofía',
      age: 6,
      language: 'es',
      level: 2,
      sensitivity: 'high',
      preferred_topics: ['animals', 'holidays', 'food'],
      avoid_topics: []
    }
  }

  currentProfile.value = mockProfiles[childId] || null
  await loadChildStats(childId)
}

const loadChildStats = async (childId) => {
  // Mock stats - in real app, this would come from API
  const mockStats = {
    ana: {
      total_conversations: 15,
      total_messages: 127,
      avg_conversation_length: 8.5,
      favorite_topic: 'school'
    },
    carlos: {
      total_conversations: 22,
      total_messages: 198,
      avg_conversation_length: 9.0,
      favorite_topic: 'sports'
    },
    sofia: {
      total_conversations: 8,
      total_messages: 52,
      avg_conversation_length: 6.5,
      favorite_topic: 'animals'
    }
  }

  stats.value = mockStats[childId] || null
}

const saveProfile = async () => {
  try {
    isLoading.value = true
    loadingBar.start()

    // Mock API call - in real app, this would save to backend
    await new Promise(resolve => setTimeout(resolve, 1000))

    message.success('Perfil guardado exitosamente')

  } catch (error) {
    console.error('Error saving profile:', error)
    message.error('No se pudo guardar el perfil')
  } finally {
    isLoading.value = false
    loadingBar.finish()
  }
}

const createProfile = async () => {
  if (!newProfile.value.name.trim()) {
    message.warning('Por favor ingresa un nombre')
    return
  }

  try {
    isLoading.value = true
    loadingBar.start()

    // Mock API call
    const childId = newProfile.value.name.toLowerCase().replace(/\s+/g, '_')
    const profileData = {
      child_id: childId,
      name: newProfile.value.name,
      age: newProfile.value.age,
      language: newProfile.value.language,
      level: 3,
      sensitivity: 'medium',
      preferred_topics: [],
      avoid_topics: []
    }

    // Add to options
    childOptions.value.push({
      label: profileData.name,
      value: profileData.child_id
    })

    // Select the new profile
    selectedChildId.value = profileData.child_id
    await loadChildProfile(profileData.child_id)

    // Reset form
    newProfile.value = {
      name: '',
      age: 8,
      language: 'es'
    }
    showCreateForm.value = false

    message.success('Perfil creado exitosamente')

  } catch (error) {
    console.error('Error creating profile:', error)
    message.error('No se pudo crear el perfil')
  } finally {
    isLoading.value = false
    loadingBar.finish()
  }
}

const createNewProfile = () => {
  showCreateForm.value = true
  currentProfile.value = null
}

onMounted(() => {
  if (childOptions.value.length > 0) {
    selectedChildId.value = childOptions.value[0].value
    loadChildProfile(selectedChildId.value)
  }
})
</script>

<style scoped>
.profile {
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
  margin-bottom: 24px;
}

.profile-card h2 {
  color: #333;
  margin-bottom: 24px;
}

.form-section {
  margin: 24px 0;
}

.form-section h3 {
  color: #333;
  margin-bottom: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #666;
}

.empty-state p {
  margin-bottom: 16px;
}

.stats-card h3 {
  color: #333;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }
}
</style>