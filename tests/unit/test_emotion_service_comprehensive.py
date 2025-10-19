import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from datetime import datetime

from services.api.services.emotion_service import EmotionService
from services.api.models.schemas import EmotionType


class TestEmotionServiceComprehensive:
    """Comprehensive tests for EmotionService with mocked dependencies"""

    @pytest.fixture
    def emotion_service(self):
        """Create emotion service instance"""
        return EmotionService()

    @pytest.fixture
    def mock_conversation_history(self):
        """Mock conversation history for testing"""
        return [
            {"role": "user", "text": "hola", "timestamp": "2024-01-01T10:00:00"},
            {"role": "assistant", "text": "**¡Hola!** ¿cómo estás?", "timestamp": "2024-01-01T10:00:01"},
            {"role": "user", "text": "estoy feliz", "timestamp": "2024-01-01T10:00:02"},
            {"role": "assistant", "text": "__Qué bien__ que estés feliz", "timestamp": "2024-01-01T10:00:03"}
        ]

    # ==================== NORMAL CASES ====================

    def test_detect_positive_emotion_normal_case(self, emotion_service):
        """Test normal positive emotion detection"""
        # Arrange
        text = "¡qué bien! me encanta jugar, es fantástico"

        # Act
        emotion = emotion_service.detect_emotion(text, "es")

        # Assert
        assert emotion == EmotionType.POSITIVE

    def test_detect_calm_emotion_normal_case(self, emotion_service):
        """Test normal calm emotion detection"""
        # Arrange
        text = "__tranquilo__, respira profundo, todo está bien"

        # Act
        emotion = emotion_service.detect_emotion(text, "es")

        # Assert
        assert emotion == EmotionType.CALM

    def test_generate_emotional_response_normal_case(self, emotion_service):
        """Test normal emotional response generation"""
        # Arrange
        base_response = "me gusta jugar"
        emotion = EmotionType.POSITIVE

        # Act
        response = emotion_service.generate_emotional_response(
            base_response, emotion, "es", child_age=8
        )

        # Assert
        assert response is not None
        assert len(response) > 0
        assert "**" in response  # Should contain positive markup

    def test_analyze_conversation_emotions_normal_case(self, emotion_service, mock_conversation_history):
        """Test normal conversation emotion analysis"""
        # Act
        analysis = emotion_service.analyze_conversation_emotions(mock_conversation_history)

        # Assert
        assert "emotion_counts" in analysis
        assert "emotion_distribution" in analysis
        assert "dominant_emotion" in analysis
        assert analysis["total_messages"] == 2  # Only assistant messages counted

    def test_get_emotion_appropriate_topics_normal_case(self, emotion_service):
        """Test normal topic suggestion"""
        # Act
        topics = emotion_service.get_emotion_appropriate_topics(
            EmotionType.POSITIVE, child_age=8, language="es"
        )

        # Assert
        assert isinstance(topics, list)
        assert len(topics) > 0

    # ==================== FAILURE CASES ====================

    def test_detect_emotion_failure_empty_text(self, emotion_service):
        """Test emotion detection failure with empty text"""
        # Arrange
        text = ""

        # Act
        emotion = emotion_service.detect_emotion(text, "es")

        # Assert
        assert emotion == EmotionType.NEUTRAL  # Default fallback

    def test_detect_emotion_failure_none_text(self, emotion_service):
        """Test emotion detection failure with None text"""
        # Act & Assert
        with pytest.raises(AttributeError):
            emotion_service.detect_emotion(None, "es")

    def test_generate_emotional_response_failure_invalid_template(self, emotion_service):
        """Test response generation failure with invalid template"""
        # Arrange
        original_templates = emotion_service.response_templates
        emotion_service.response_templates = {"es": {"positive": ["invalid {} format"]}}
        base_response = "test response"

        # Act
        response = emotion_service.generate_emotional_response(
            base_response, EmotionType.POSITIVE, "es", child_age=8
        )

        # Assert
        assert response == base_response  # Should return base response on error

        # Cleanup
        emotion_service.response_templates = original_templates

    def test_analyze_conversation_emotions_failure_invalid_messages(self, emotion_service):
        """Test conversation analysis failure with invalid messages"""
        # Arrange
        invalid_messages = [{"invalid": "structure"}]

        # Act
        analysis = emotion_service.analyze_conversation_emotions(invalid_messages)

        # Assert
        assert analysis == {}  # Should return empty dict on error

    def test_analyze_conversation_emotions_failure_none_input(self, emotion_service):
        """Test conversation analysis failure with None input"""
        # Act
        analysis = emotion_service.analyze_conversation_emotions(None)

        # Assert
        assert analysis == {}  # Should return empty dict

    def test_get_emotion_transition_suggestions_failure_unsupported_transition(self, emotion_service):
        """Test transition suggestions failure with unsupported transition"""
        # Act
        suggestions = emotion_service.get_emotion_transition_suggestions(
            EmotionType.CALM, EmotionType.POSITIVE, "es"
        )

        # Assert
        assert suggestions == []  # Should return empty list

    # ==================== EDGE CASES ====================

    def test_detect_emotion_edge_case_very_long_text(self, emotion_service):
        """Test emotion detection with very long text"""
        # Arrange
        long_text = "palabra " * 1000 + " ¡qué bien! "

        # Act
        emotion = emotion_service.detect_emotion(long_text, "es")

        # Assert
        assert emotion == EmotionType.POSITIVE

    def test_detect_emotion_edge_case_unicode_characters(self, emotion_service):
        """Test emotion detection with unicode characters"""
        # Arrange
        unicode_text = "¡Qué bien! 😊🎉 me encanta jugar ñáéíóú"

        # Act
        emotion = emotion_service.detect_emotion(unicode_text, "es")

        # Assert
        assert emotion == EmotionType.POSITIVE

    def test_detect_emotion_edge_case_mixed_case(self, emotion_service):
        """Test emotion detection with mixed case"""
        # Arrange
        mixed_case_text = "¡QuÉ BiEn! Me EnCaNtA JuGaR"

        # Act
        emotion = emotion_service.detect_emotion(mixed_case_text, "es")

        # Assert
        assert emotion == EmotionType.POSITIVE

    def test_detect_emotion_edge_case_whitespace_only(self, emotion_service):
        """Test emotion detection with whitespace only"""
        # Arrange
        whitespace_text = "   \n\t   "

        # Act
        emotion = emotion_service.detect_emotion(whitespace_text, "es")

        # Assert
        assert emotion == EmotionType.NEUTRAL

    def test_generate_emotional_response_edge_case_very_young_child(self, emotion_service):
        """Test response generation for very young child"""
        # Arrange
        base_response = "jugar"
        child_age = 3

        # Act
        response = emotion_service.generate_emotional_response(
            base_response, EmotionType.POSITIVE, "es", child_age=child_age
        )

        # Assert
        assert response is not None
        assert len(response) > 0

    def test_generate_emotional_response_edge_case_very_old_child(self, emotion_service):
        """Test response generation for very old child"""
        # Arrange
        base_response = "aprender cosas nuevas"
        child_age = 15

        # Act
        response = emotion_service.generate_emotional_response(
            base_response, EmotionType.POSITIVE, "es", child_age=child_age
        )

        # Assert
        assert response is not None
        assert len(response) > 0

    def test_analyze_conversation_emotions_edge_case_no_assistant_messages(self, emotion_service):
        """Test conversation analysis with no assistant messages"""
        # Arrange
        user_only_messages = [
            {"role": "user", "text": "hola"},
            {"role": "user", "text": "cómo estás"}
        ]

        # Act
        analysis = emotion_service.analyze_conversation_emotions(user_only_messages)

        # Assert
        assert analysis["total_messages"] == 0
        assert analysis["dominant_emotion"] == "neutral"

    def test_analyze_conversation_emotions_edge_case_single_message(self, emotion_service):
        """Test conversation analysis with single message"""
        # Arrange
        single_message = [
            {"role": "assistant", "text": "**¡Hola!**", "timestamp": "2024-01-01T10:00:00"}
        ]

        # Act
        analysis = emotion_service.analyze_conversation_emotions(single_message)

        # Assert
        assert analysis["total_messages"] == 1
        assert analysis["dominant_emotion"] == "positive"

    def test_get_emotion_appropriate_topics_edge_case_boundary_age(self, emotion_service):
        """Test topic suggestions at age boundaries"""
        # Test exact boundary ages
        for age in [5, 7, 8, 10, 11, 13]:
            # Act
            topics = emotion_service.get_emotion_appropriate_topics(
                EmotionType.POSITIVE, child_age=age, language="es"
            )

            # Assert
            assert isinstance(topics, list)
            assert len(topics) > 0

    def test_get_emotion_appropriate_topics_edge_case_unsupported_language(self, emotion_service):
        """Test topic suggestions with unsupported language"""
        # Act
        topics = emotion_service.get_emotion_appropriate_topics(
            EmotionType.POSITIVE, child_age=8, language="fr"
        )

        # Assert
        assert isinstance(topics, list)  # Should default to Spanish

    def test_apply_emotion_markup_edge_case_already_marked_text(self, emotion_service):
        """Test applying markup to already marked text"""
        # Arrange
        already_marked_text = "**¡Hola!** ¿cómo estás?"

        # Act
        marked_text = emotion_service.apply_emotion_markup(
            already_marked_text, EmotionType.POSITIVE, "es"
        )

        # Assert
        assert marked_text is not None
        assert "**" in marked_text

    def test_service_status_edge_case_all_attributes_present(self, emotion_service):
        """Test service status includes all expected attributes"""
        # Act
        status = emotion_service.get_service_status()

        # Assert
        required_attributes = [
            "status", "supported_emotions", "supported_languages",
            "emotion_patterns_count", "response_templates_count"
        ]

        for attr in required_attributes:
            assert attr in status

        assert status["status"] == "active"
        assert len(status["supported_emotions"]) == 3
        assert len(status["supported_languages"]) >= 2
        assert status["emotion_patterns_count"] > 0
        assert status["response_templates_count"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_emotion_detection(self, emotion_service):
        """Test concurrent emotion detection"""
        # Arrange
        texts = [
            "¡qué bien! me gusta",
            "tranquilo, está bien",
            "entiendo lo que dices",
            "¡fantástico! genial",
            "__respira__ con calma"
        ]

        # Act - Run detection concurrently
        async def detect_emotion_async(text):
            return emotion_service.detect_emotion(text, "es")

        tasks = [
            asyncio.create_task(detect_emotion_async(text))
            for text in texts
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        assert len(results) == len(texts)
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, EmotionType)

    def test_memory_leak_prevention_large_analysis(self, emotion_service):
        """Test that large conversation analysis doesn't cause memory issues"""
        # Arrange
        large_conversation = []
        for i in range(1000):
            large_conversation.append({
                "role": "assistant",
                "text": f"**¡Hola!** mensaje {i}",
                "timestamp": f"2024-01-01T10:{i%60:02d}:00"
            })

        # Act
        analysis = emotion_service.analyze_conversation_emotions(large_conversation)

        # Assert
        assert analysis is not None
        assert analysis["total_messages"] == 1000
        assert analysis["dominant_emotion"] == "positive"

    def test_regex_injection_safety(self, emotion_service):
        """Test that regex patterns are safe from injection attempts"""
        # Arrange - Malicious regex patterns
        malicious_texts = [
            ".*[a-zA-Z]*.*",  # Greedy regex pattern
            "^.*$",  # Full match pattern
            "(.*)",  # Capture group pattern
            "[a-z]+.*[0-9]+",  # Complex pattern
        ]

        # Act & Assert - Should not crash and should return neutral emotion
        for text in malicious_texts:
            emotion = emotion_service.detect_emotion(text, "es")
            assert emotion == EmotionType.NEUTRAL
