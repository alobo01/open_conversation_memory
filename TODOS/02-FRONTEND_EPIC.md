# 🖥️ Frontend Vue 3 Epic (UI)

## Overview
Complete the Vue 3 frontend interface with audio recording, conversation management, and bilingual support for children with TEA2.

## Tasks

### UI-001: Proyecto Vue 3 base ⏳ **MEDIUM PRIORITY**
**Status**: Partially implemented
**Estimated**: 8 hours
**Current State**: Basic Vue 3 structure exists
**Files to enhance**:
- `services/frontend/package.json` (optimize dependencies)
- `services/frontend/vite.config.js` (configure for port 81)
- `services/frontend/src/main.js` (setup complete)

#### Subtasks:
- [ ] **Dependency Optimization**: Review and optimize package dependencies
- [ ] **Build Configuration**: Ensure production-ready build setup
- [ ] **Environment Configuration**: Set up development/production environments
- [ ] **Performance Optimization**: Configure Vite for optimal performance
- [ ] **Error Boundaries**: Implement error handling for Vue components
- [ ] **Code Splitting**: Optimize bundle size with code splitting

#### Acceptance Criteria:
- [ ] `npm run dev` works correctly on port 81
- [ ] Build size < 2MB for production
- [ ] Hot reload works in development mode
- [ ] Error boundaries prevent app crashes
- [ ] Code splitting reduces initial load time

---

### UI-002: Componente conversación ⏳ **HIGH PRIORITY**
**Status**: Basic structure exists
**Estimated**: 16 hours
**Dependencies**: UI-001
**Files to implement**:
- `services/frontend/src/components/ConversationInterface.vue` (enhance)
- `services/frontend/src/components/MessageBubble.vue` (new)
- `services/frontend/src/components/EmotionRenderer.vue` (new)
- `services/frontend/src/stores/conversation.js` (enhance)

#### Subtasks:
- [ ] **Message Display**: Render conversation messages with proper formatting
- [ ] **Emotion Markup**: Render `**positive**`, `__calm__`, neutral formatting
- [ ] **Real-time Updates**: WebSocket or polling for real-time conversation updates
- [ ] **Message Input**: Child-friendly input interface with validation
- [ ] **Conversation History**: Display conversation history with navigation
- [ ] **Accessibility**: WCAG 2.1 AA compliance for children with TEA2
- [ ] **Responsive Design**: Mobile and desktop responsive layout

#### Implementation Details:
```vue
<!-- MessageBubble.vue -->
<template>
  <div class="message-bubble" :class="messageClass">
    <div class="message-content" v-html="formattedContent"></div>
    <div class="message-meta">
      <span class="timestamp">{{ formattedTime }}</span>
      <span class="emotion-indicator" v-if="emotion">{{ emotion }}</span>
    </div>
  </div>
</template>
```

#### Acceptance Criteria:
- [ ] Messages display with proper emotion markup formatting
- [ ] Real-time conversation updates work smoothly
- [ ] Interface is intuitive for children 5-13 years old
- [ ] Accessibility features support screen readers
- [ ] Mobile interface works correctly on tablets and phones

---

### UI-003: Grabación de audio ⏳ **HIGH PRIORITY**
**Status**: Pending implementation
**Estimated**: 20 hours
**Dependencies**: UI-002, ASR-003 ✅
**Files to implement**:
- `services/frontend/src/components/AudioRecorder.vue` (new)
- `services/frontend/src/services/audioService.js` (new)
- `services/frontend/src/utils/webRTCUtils.js` (new)
- `services/frontend/src/components/AudioPlayer.vue` (new)

#### Subtasks:
- [ ] **WebRTC Integration**: Implement audio recording using WebRTC API
- [ ] **Audio Format Support**: Support multiple audio formats (WAV, MP3, WebM)
- [ ] **Recording Controls**: Start/stop/pause recording with visual feedback
- [ ] **Audio Preview**: Play back recorded audio before sending
- [ ] **ASR Integration**: Send audio to ASR service with tier selection
- [ ] **Visual Feedback**: Recording level indicators and audio visualization
- [ ] **Error Handling**: Handle microphone permissions and recording errors
- [ ] **Audio Quality Settings**: Allow selection of recording quality

#### Implementation Details:
```javascript
// audioService.js
class AudioService {
  async startRecording(options = { sampleRate: 16000, channels: 1 }) {
    // Start WebRTC recording
  }

  async stopRecording() {
    // Stop recording and return audio blob
  }

  async transcribeAudio(audioBlob, tier = 'balanced') {
    // Send to ASR service
    return fetch('/api/asr/transcribe', {
      method: 'POST',
      body: formData
    });
  }
}
```

#### Acceptance Criteria:
- [ ] Audio recording works on all modern browsers
- [ ] Recorded audio quality is clear for ASR processing
- [ ] Visual feedback shows recording status and levels
- [ ] Error handling gracefully manages microphone permissions
- [ ] Audio can be previewed before sending to ASR
- [ ] Integration with ASR service works seamlessly

---

### UI-004: Navegación niños/temas ⏳ **MEDIUM PRIORITY**
**Status**: Pending implementation
**Estimated**: 12 hours
**Dependencies**: UI-003
**Files to implement**:
- `services/frontend/src/views/ChildProfile.vue` (new)
- `services/frontend/src/views/TopicSelection.vue` (new)
- `services/frontend/src/components/ConversationHistory.vue` (new)
- `services/frontend/src/stores/profile.js` (new)

#### Subtasks:
- [ ] **Child Profiles**: Interface to select and manage child profiles
- [ ] **Topic Selection**: Visual topic selection (school, hobbies, holidays, food, friends)
- [ ] **Conversation History**: Browse past conversations by child and topic
- [ ] **Profile Management**: Create/edit child profiles with preferences
- [ ] **Topic Preferences**: Set preferred and avoided topics per child
- [ ] **Conversation Statistics**: Display basic conversation metrics
- [ ] **Search & Filter**: Search conversations by date, topic, or content

#### Implementation Details:
```vue
<!-- TopicSelection.vue -->
<template>
  <div class="topic-selection">
    <h2>{{ $t('topics.select_topic') }}</h2>
    <div class="topic-grid">
      <div v-for="topic in availableTopics"
           :key="topic.id"
           class="topic-card"
           :class="{ active: selectedTopic === topic.id }"
           @click="selectTopic(topic.id)">
        <img :src="topic.icon" :alt="topic.name">
        <h3>{{ $t(`topics.${topic.id}`) }}</h3>
      </div>
    </div>
  </div>
</template>
```

#### Acceptance Criteria:
- [ ] Child profile selection works correctly
- [ ] Topic selection interface is intuitive and child-friendly
- [ ] Conversation history displays with proper filtering
- [ ] Profile management allows basic customization
- [ ] Search functionality finds conversations effectively

---

### UI-005: Bilingüe ES/EN ⏳ **LOW PRIORITY**
**Status**: Pending implementation
**Estimated**: 8 hours
**Dependencies**: UI-004
**Files to implement**:
- `services/frontend/src/i18n/index.js` (new)
- `services/frontend/src/locales/es.json` (new)
- `services/frontend/src/locales/en.json` (new)
- `services/frontend/src/components/LanguageSwitch.vue` (new)

#### Subtasks:
- [ ] **i18n Setup**: Implement Vue I18n for internationalization
- [ ] **Language Switching**: Add language toggle in interface
- [ ] **Content Translation**: Translate all UI text to Spanish and English
- [ ] **Persistent Language**: Remember language preference in localStorage
- [ ] **RTL Support**: Ensure proper text direction for both languages
- [ ] **Date/Time Formatting**: Localize date and time displays
- [ ] **Number Formatting**: Localize numbers and measurements

#### Acceptance Criteria:
- [ ] Language switching works instantly without page reload
- [ ] All UI text is properly translated
- [ ] Language preference persists across sessions
- [ ] Interface layout adapts correctly to both languages
- [ ] No untranslated text remains in production

---

## Cross-Cutting Features

### Accessibility (WCAG 2.1 AA)
- [ ] **Keyboard Navigation**: All features accessible via keyboard
- [ ] **Screen Reader Support**: Proper ARIA labels and semantic HTML
- [ ] **High Contrast Mode**: Support for high contrast themes
- [ ] **Focus Management**: Clear focus indicators and logical tab order
- [ ] **Text Scaling**: Interface scales properly up to 200%

### Child-Friendly Design
- [ ] **Visual Design**: Bright, engaging colors appropriate for children
- [ ] **Large Touch Targets**: Minimum 44x44px touch targets
- [ ] **Simple Language**: Clear, simple instructions and labels
- [ ] **Consistent Navigation**: Predictable interface patterns
- [ ] **Error Messages**: Child-friendly error messages and guidance

### Performance Optimization
- [ ] **Bundle Size**: Keep initial bundle under 2MB
- [ ] **Load Time**: Page load time < 3 seconds
- [ ] **Interaction Response**: UI interactions respond within 100ms
- [ ] **Memory Usage**: Monitor and optimize memory consumption
- [ ] **Network Optimization**: Efficient API calls and caching

---

## Testing Requirements

### Unit Tests
- [ ] **Component Tests**: Test each Vue component independently
- [ ] **Store Tests**: Test Pinia store actions and state
- [ ] **Service Tests**: Test audio service and API integration
- [ ] **Utility Tests**: Test helper functions and utilities

### Integration Tests
- [ ] **Audio Integration**: Test complete audio recording to ASR flow
- [ ] **Conversation Flow**: Test complete conversation workflow
- [ ] **API Integration**: Test frontend-backend API integration
- [ ] **Cross-browser Testing**: Test on Chrome, Firefox, Safari, Edge

### User Experience Tests
- [ ] **Usability Testing**: Test with actual users (children with TEA2)
- [ ] **Accessibility Testing**: Screen reader and keyboard navigation tests
- [ ] **Performance Testing**: Load time and interaction speed tests
- [ ] **Mobile Testing**: Responsive design on various devices

---

## Success Metrics

### User Experience Metrics
- [ ] **Task Completion Rate**: > 90% of children can complete conversations
- [ ] **Error Rate**: < 5% of users encounter interface errors
- [ ] **Satisfaction Score**: > 4.0/5.0 satisfaction rating from users

### Technical Metrics
- [ ] **Performance Targets**: All performance targets met
- [ ] **Browser Compatibility**: Works on 95%+ of target browsers
- [ ] **Accessibility Score**: 100% WCAG 2.1 AA compliance
- [ ] **Bug Rate**: < 1 critical bug per release

---

## Implementation Timeline

### Week 1
1. Complete UI-001: Vue 3 base optimization
2. Start UI-002: Conversation interface development
3. Implement basic accessibility features

### Week 2
1. Complete UI-002: Conversation interface
2. Implement UI-003: Audio recording (major feature)
3. Start UI-004: Navigation and profiles

### Week 3
1. Complete UI-003: Audio recording integration
2. Complete UI-004: Navigation and profiles
3. Implement UI-005: Bilingual support
4. Comprehensive testing and bug fixes

---

## Related Files & References

- `services/frontend/src/App.vue` - Main application component
- `services/frontend/src/stores/conversation.js` - Conversation state management
- `services/frontend/package.json` - Dependencies and scripts
- `services/api/routers/conversation.py` - Backend conversation API
- `services/api/routers/asr.py` - Backend ASR API integration
- `docs/frontend_development.md` - Frontend development guidelines