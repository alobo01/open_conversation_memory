import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from ..models.schemas import EmotionType

logger = logging.getLogger(__name__)

class EmotionService:
    """Service for managing emotional responses and sentiment analysis"""

    def __init__(self):
        self.emotion_patterns = self._init_emotion_patterns()
        self.response_templates = self._init_response_templates()

    def _init_emotion_patterns(self) -> Dict[str, List[str]]:
        """Initialize emotion detection patterns"""
        return {
            "positive": [
                r"¡(qué|quién|cuándo|dónde|cómo) (bien|genial|fantástico|increíble|perfecto|maravilloso)",
                r"(me encanta|me gusta|amo|adoro|quiero)",
                r"(feliz|alegre contento|emocionado|entusiasmado)",
                r"(siempre|todo|mejor|favorito)"
            ],
            "calm": [
                r"(tranquilo|calma|respira|paciencia|lento)",
                r"(está bien|no te preocupes|todo está bien)",
                r"(relájate|descansa|paz|serenidad)",
                r"__(.*?)__"  # Whisper markup
            ],
            "neutral": [
                r"(entiendo|comprendo|vale|ok|de acuerdo)",
                r"(¿qué|cómo|cuándo|dónde|por qué)",
                r"(dime más|cuéntame|explícame)"
            ]
        }

    def _init_response_templates(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize response templates by emotion and language"""
        return {
            "es": {
                "positive": [
                    "**¡Qué bien!** {}",
                    "**¡Genial!** {}",
                    "**¡Fantástico!** {}",
                    "**¡Perfecto!** {}",
                    "**¡Increíble!** {}"
                ],
                "calm": [
                    "__Tranquilo__, {}",
                    "__Respira profundo__, {}",
                    "__Todo está bien__, {}",
                    "__No te preocupes__, {}",
                    "__Con calma__, {}"
                ],
                "neutral": [
                    "Entiendo. {}",
                    "Vale. {}",
                    "Comprendo. {}",
                    "De acuerdo. {}",
                    "Entendido. {}"
                ]
            },
            "en": {
                "positive": [
                    "**Great!** {}",
                    "**Wonderful!** {}",
                    **Fantastic!** {}",
                    "**Perfect!** {}",
                    "**Amazing!** {}"
                ],
                "calm": [
                    "__Calm down__, {}",
                    "__Take a deep breath__, {}",
                    "__It's okay__, {}",
                    "__Don't worry__, {}",
                    "__Relax__, {}"
                ],
                "neutral": [
                    "I understand. {}",
                    "Okay. {}",
                    "I see. {}",
                    "Alright. {}",
                    "Got it. {}"
                ]
            }
        }

    def detect_emotion(self, text: str, language: str = "es") -> EmotionType:
        """Detect emotion in text"""
        text_lower = text.lower()

        # Check for emotion patterns
        for emotion, patterns in self.emotion_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    if emotion == "positive":
                        return EmotionType.POSITIVE
                    elif emotion == "calm":
                        return EmotionType.CALM

        return EmotionType.NEUTRAL

    def apply_emotion_markup(
        self,
        text: str,
        emotion: EmotionType,
        language: str = "es"
    ) -> str:
        """Apply emotional markup to text"""
        if emotion == EmotionType.POSITIVE:
            return self._apply_positive_markup(text, language)
        elif emotion == EmotionType.CALM:
            return self._apply_calm_markup(text, language)
        else:
            return text  # Neutral text has no markup

    def _apply_positive_markup(self, text: str, language: str) -> str:
        """Apply positive emotion markup"""
        # Add enthusiastic words and bold markup
        positive_words = {
            "es": ["¡muy bien!", "¡excelente!", "¡fantástico!", "¡genial!"],
            "en": ["very good!", "excellent!", "fantastic!", "great!"]
        }

        words = positive_words.get(language, positive_words["es"])
        import random
        word = random.choice(words)

        # Apply bold markup to the entire response or key phrases
        if not text.startswith("**"):
            # Add bold to the beginning or key phrases
            sentences = text.split(".")
            if sentences:
                sentences[0] = f"**{sentences[0].strip()}**"
                text = ". ".join(sentences)

        return text

    def _apply_calm_markup(self, text: str, language: str) -> str:
        """Apply calm emotion markup"""
        # Add calming words and whisper markup
        calm_words = {
            "es": ["tranquilo", "con calma", "sin prisa", "paciencia"],
            "en": ["calm", "gently", "slowly", "patience"]
        }

        words = calm_words.get(language, calm_words["es"])
        import random
        word = random.choice(words)

        # Apply whisper markup to calming phrases
        if "__" not in text:
            # Add whisper markup to calming phrases
            text = f"__{word}__, {text}"

        return text

    def generate_emotional_response(
        self,
        base_response: str,
        emotion: EmotionType,
        language: str = "es",
        child_age: int = 8,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate an emotionally appropriate response"""
        try:
            # Get appropriate template
            templates = self.response_templates.get(language, self.response_templates["es"])
            emotion_templates = templates.get(emotion.value, templates["neutral"])

            # Select template based on child's age and context
            if child_age <= 6:
                template = emotion_templates[0]  # Simpler templates for younger kids
            elif child_age <= 10:
                template = emotion_templates[1] if len(emotion_templates) > 1 else emotion_templates[0]
            else:
                template = emotion_templates[-1]  # More complex for older kids

            # Format template with base response
            formatted_response = template.format(base_response)

            # Apply additional markup based on emotion
            final_response = self.apply_emotion_markup(formatted_response, emotion, language)

            return final_response

        except Exception as e:
            logger.error(f"Error generating emotional response: {e}")
            return base_response

    def analyze_conversation_emotions(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze emotions throughout a conversation"""
        try:
            emotion_counts = {emotion.value: 0 for emotion in EmotionType}
            emotion_sequence = []
            language = "es"  # Default

            for message in messages:
                if message.get("role") == "assistant":
                    text = message.get("text", "")
                    emotion = self.detect_emotion(text, language)
                    emotion_counts[emotion.value] += 1
                    emotion_sequence.append({
                        "message": text,
                        "emotion": emotion.value,
                        "timestamp": message.get("timestamp")
                    })

            # Calculate emotion distribution
            total_messages = sum(emotion_counts.values())
            emotion_distribution = {
                emotion: count / total_messages if total_messages > 0 else 0
                for emotion, count in emotion_counts.items()
            }

            # Determine dominant emotion
            dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]

            # Analyze emotion changes
            emotion_changes = self._analyze_emotion_changes(emotion_sequence)

            return {
                "emotion_counts": emotion_counts,
                "emotion_distribution": emotion_distribution,
                "dominant_emotion": dominant_emotion,
                "emotion_sequence": emotion_sequence,
                "emotion_changes": emotion_changes,
                "total_messages": total_messages
            }

        except Exception as e:
            logger.error(f"Error analyzing conversation emotions: {e}")
            return {}

    def _analyze_emotion_changes(self, emotion_sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze changes in emotions throughout conversation"""
        changes = []

        for i in range(1, len(emotion_sequence)):
            prev_emotion = emotion_sequence[i-1]["emotion"]
            curr_emotion = emotion_sequence[i]["emotion"]

            if prev_emotion != curr_emotion:
                changes.append({
                    "from": prev_emotion,
                    "to": curr_emotion,
                    "position": i,
                    "timestamp": emotion_sequence[i]["timestamp"]
                })

        return changes

    def get_emotion_appropriate_topics(
        self,
        emotion: EmotionType,
        child_age: int = 8,
        language: str = "es"
    ) -> List[str]:
        """Get topics appropriate for current emotional state"""
        topics = {
            EmotionType.POSITIVE: {
                "es": ["logros", "cosas que te hacen feliz", "amigos", "juegos favoritos"],
                "en": ["achievements", "things that make you happy", "friends", "favorite games"]
            },
            EmotionType.CALM: {
                "es": ["actividades relajantes", "naturaleza", "música", "cuentos tranquilos"],
                "en": ["relaxing activities", "nature", "music", "calm stories"]
            },
            EmotionType.NEUTRAL: {
                "es": ["cotidiano", "escuela", "familia", "actividades normales"],
                "en": ["daily life", "school", "family", "normal activities"]
            }
        }

        age_appropriate_topics = {
            (5, 7): {
                EmotionType.POSITIVE: ["juegos", "dibujos", "canciones", "juguetes"],
                EmotionType.CALM: ["cuentos", "dormir", "mimos", "abrazos"],
                EmotionType.NEUTRAL: ["comida", "casa", "cole", "familia"]
            },
            (8, 10): {
                EmotionType.POSITIVE: ["amigos", "deportes", "hobbies", "logros"],
                EmotionType.CALM: ["lectura", "música", "naturaleza", "paseos"],
                EmotionType.NEUTRAL: ["escuela", "tareas", "familia", "rutinas"]
            },
            (11, 13): {
                EmotionType.POSITIVE: ["pasiones", "talentos", "éxitos", "aspiraciones"],
                EmotionType.CALM: ["meditación", "reflexión", "creatividad", "arte"],
                EmotionType.NEUTRAL: ["futuro", "decisiones", "relaciones", "desafíos"]
            }
        }

        # Select appropriate topics based on age
        for age_range, age_topics in age_appropriate_topics.items():
            if age_range[0] <= child_age <= age_range[1]:
                return age_topics.get(emotion, [])

        # Default topics
        return topics.get(emotion, {}).get(language, [])

    def get_emotion_transition_suggestions(
        self,
        current_emotion: EmotionType,
        target_emotion: EmotionType,
        language: str = "es"
    ) -> List[str]:
        """Get suggestions to transition from one emotion to another"""
        transitions = {
            ("neutral", "positive"): {
                "es": [
                    "¿Qué te ha hecho feliz hoy?",
                    "Háblame de algo bueno que te haya pasado",
                    "¿Cuál es tu cosa favorita del día?"
                ],
                "en": [
                    "What made you happy today?",
                    "Tell me about something good that happened",
                    "What's your favorite thing about today?"
                ]
            },
            ("neutral", "calm"): {
                "es": [
                    "Respira hondo y cuéntame cómo te sientes",
                    "¿Te gustaría hablar de algo tranquilo?",
                    "Tomémonos un momento para relajarnos"
                ],
                "en": [
                    "Take a deep breath and tell me how you feel",
                    "Would you like to talk about something calm?",
                    "Let's take a moment to relax"
                ]
            },
            ("positive", "calm"): {
                "es": [
                    "Qué bien que te sientas así. Disfrutemos este momento",
                    "Mantengamos esta energía positiva pero tranquila",
                    "Es genial sentirse así, ¿verdad?"
                ],
                "en": [
                    "It's great that you feel this way. Let's enjoy this moment",
                    "Let's keep this positive but calm energy",
                    "It's wonderful to feel this way, right?"
                ]
            }
        }

        return transitions.get((current_emotion.value, target_emotion.value), {}).get(language, [])

    def get_service_status(self) -> Dict[str, Any]:
        """Get emotion service status"""
        return {
            "status": "active",
            "supported_emotions": [emotion.value for emotion in EmotionType],
            "supported_languages": list(self.response_templates.keys()),
            "emotion_patterns_count": sum(len(patterns) for patterns in self.emotion_patterns.values()),
            "response_templates_count": sum(
                len(templates) for lang_templates in self.response_templates.values()
                for templates in lang_templates.values()
            )
        }