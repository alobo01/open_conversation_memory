import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from services.api.services.safety_service import (
    SafetyService, SafetyViolationType, SafetyViolation, SafetyCheckResult
)
from services.api.models.schemas import EmotionType, Language


class TestSafetyService:
    """Comprehensive test suite for SafetyService"""

    @pytest.fixture
    def safety_service(self):
        """Create a SafetyService instance for testing"""
        return SafetyService()

    @pytest.fixture
    def sample_child_profile(self):
        """Sample child profile for testing"""
        return {
            "child_id": "test_child_123",
            "name": "Test Child",
            "age": 8,
            "preferred_topics": ["juegos", "escuela"],
            "avoid_topics": ["miedo", "oscuridad"],
            "blocked_topics": ["violencia", "muerte"],
            "sensitive_topics": ["separación", "accidentes"],
            "level": 3,
            "sensitivity": "medium",
            "language": "es"
        }

    @pytest.fixture
    def sample_context(self):
        """Sample conversation context"""
        return {
            "conversation_id": "conv_123",
            "topic": "juegos",
            "level": 3,
            "history": [
                {"role": "user", "text": "me gustan los juegos"},
                {"role": "assistant", "text": "**¡Genial!** ¿qué juegos te gustan?"}
            ]
        }


class TestInappropriateContentDetection:
    """Test detection of inappropriate content"""

    @pytest.mark.asyncio
    async def test_detect_violence_content(self, safety_service, sample_child_profile, sample_context):
        """Test detection of violent content"""
        violent_content = "quiero matar al monstruo y golpearlo fuerte"

        result = await safety_service.check_content_safety(
            content=violent_content,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.VIOLENCE for v in result.violations)
        assert any(v.violation_type == SafetyViolationType.INAPPROPRIATE_CONTENT for v in result.violations)

    @pytest.mark.asyncio
    async def test_detect_inappropriate_words(self, safety_service, sample_child_profile, sample_context):
        """Test detection of inappropriate words"""
        inappropriate_content = "estúpido idiota, esto es una mierda"

        result = await safety_service.check_content_safety(
            content=inappropriate_content,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert len(result.violations) >= 2  # Should detect multiple violations

    @pytest.mark.asyncio
    async def test_detect_scary_topics(self, safety_service, sample_child_profile, sample_context):
        """Test detection of scary topics for young children"""
        scary_content = "hay monstruos bajo mi cama y fantasmas en el armario"

        result = await safety_service.check_content_safety(
            content=scary_content,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.SCARY_TOPIC for v in result.violations)

    @pytest.mark.asyncio
    async def test_scary_topics_age_sensitivity(self, safety_service, sample_context):
        """Test that scary topic detection is age-sensitive"""
        scary_content = "vi un fantasma en el cine"

        # Test with young child (should be blocked)
        young_child = {
            "child_id": "young_child",
            "age": 5,
            "level": 1,
            "sensitivity": "high",
            "language": "es"
        }

        result = await safety_service.check_content_safety(
            content=scary_content,
            child_profile=young_child,
            context=sample_context,
            language="es"
        )
        assert not result.is_safe

        # Test with older child (might be allowed with lower severity)
        older_child = {
            "child_id": "older_child",
            "age": 12,
            "level": 4,
            "sensitivity": "low",
            "language": "es"
        }

        result = await safety_service.check_content_safety(
            content=scary_content,
            child_profile=older_child,
            context=sample_context,
            language="es"
        )
        # Should either be safe or have lower severity violations
        if not result.is_safe:
            assert all(v.severity in ["low", "medium"] for v in result.violations)


class TestPersonalInformationProtection:
    """Test detection of personal information"""

    @pytest.mark.asyncio
    async def test_detect_phone_numbers(self, safety_service, sample_child_profile, sample_context):
        """Test detection of phone numbers"""
        content_with_phone = "mi número es 1234567890, llámame"

        result = await safety_service.check_content_safety(
            content=content_with_phone,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.PERSONAL_INFO for v in result.violations)
        assert any(v.severity == "critical" for v in result.violations)

    @pytest.mark.asyncio
    async def test_detect_email_addresses(self, safety_service, sample_child_profile, sample_context):
        """Test detection of email addresses"""
        content_with_email = "mi email es niño@ejemplo.com"

        result = await safety_service.check_content_safety(
            content=content_with_email,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.PERSONAL_INFO for v in result.violations)

    @pytest.mark.asyncio
    async def test_detect_home_address(self, safety_service, sample_child_profile, sample_context):
        """Test detection of home addresses"""
        content_with_address = "vivo en 123 calle principal"

        result = await safety_service.check_content_safety(
            content=content_with_address,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.PERSONAL_INFO for v in result.violations)


class TestBlockedTopicsValidation:
    """Test validation of blocked topics for specific children"""

    @pytest.mark.asyncio
    async def test_blocked_topics_detection(self, safety_service, sample_child_profile, sample_context):
        """Test detection of topics specifically blocked for a child"""
        content_with_blocked_topic = "me gusta hablar de violencia y muerte"

        result = await safety_service.check_content_safety(
            content=content_with_blocked_topic,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.BLOCKED_TOPIC for v in result.violations)

    @pytest.mark.asyncio
    async def test_sensitive_topics_detection(self, safety_service, sample_child_profile, sample_context):
        """Test detection of sensitive topics for a child"""
        content_with_sensitive_topic = "tengo miedo de la separación de mis padres"

        result = await safety_service.check_content_safety(
            content=content_with_sensitive_topic,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        # Should detect as blocked topic (sensitive_topics included in blocked topics check)


class TestLanguageComplexityValidation:
    """Test validation of language complexity for different ages"""

    @pytest.mark.asyncio
    async def test_complex_language_for_young_child(self, safety_service, sample_context):
        """Test that complex language is flagged for young children"""
        complex_content = "La experimentación científica demuestra que los compuestos químicos reaccionan de manera diferente bajo diversas condiciones ambientales"

        young_child = {
            "child_id": "young_child",
            "age": 5,
            "level": 1,
            "language": "es"
        }

        result = await safety_service.check_content_safety(
            content=complex_content,
            child_profile=young_child,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.LANGUAGE_COMPLEXITY for v in result.violations)

    @pytest.mark.asyncio
    async def test_appropriate_language_for_older_child(self, safety_service, sample_child_profile, sample_context):
        """Test that age-appropriate language passes validation"""
        appropriate_content = "me gusta aprender sobre ciencia y hacer experimentos divertidos"

        result = await safety_service.check_content_safety(
            content=appropriate_content,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        # Should be safe (no complexity violations)
        complexity_violations = [
            v for v in result.violations
            if v.violation_type == SafetyViolationType.LANGUAGE_COMPLEXITY
        ]
        assert len(complexity_violations) == 0


class TestEmotionalAppropriateness:
    """Test validation of emotional appropriateness"""

    @pytest.mark.asyncio
    async def test_negative_content_for_sensitive_child(self, safety_service, sample_context):
        """Test that overly negative content is flagged for sensitive children"""
        negative_content = "todo es malo, feo y terrible, siempre me equivoco y todo sale mal"

        sensitive_child = {
            "child_id": "sensitive_child",
            "age": 6,
            "level": 2,
            "sensitivity": "high",
            "language": "es"
        }

        result = await safety_service.check_content_safety(
            content=negative_content,
            child_profile=sensitive_child,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.EMOTIONAL_INAPPROPRIATE for v in result.violations)

    @pytest.mark.asyncio
    async def test_overstimulation_for_young_child(self, safety_service, sample_context):
        """Test that overly exciting content is flagged for very young children"""
        overstimulating_content = "**¡EXCITADO!** **¡MUY!** **¡INCREÍBLE!** **¡FANTÁSTICO!** **¡PERFECTO!** **¡GENIAL!**"

        very_young_child = {
            "child_id": "toddler",
            "age": 5,
            "level": 1,
            "sensitivity": "medium",
            "language": "es"
        }

        result = await safety_service.check_content_safety(
            content=overstimulating_content,
            child_profile=very_young_child,
            context=sample_context,
            language="es"
        )

        # Should flag for overstimulation
        emotional_violations = [
            v for v in result.violations
            if v.violation_type == SafetyViolationType.EMOTIONAL_INAPPROPRIATE
        ]
        assert len(emotional_violations) > 0


class TestContentFiltering:
    """Test content filtering capabilities"""

    @pytest.mark.asyncio
    async def test_inappropriate_content_filtering(self, safety_service, sample_child_profile, sample_context):
        """Test that inappropriate content is properly filtered"""
        inappropriate_content = "quiero matar al monstruo malo"

        result = await safety_service.check_content_safety(
            content=inappropriate_content,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert result.filtered_content is not None
        assert "matar" not in result.filtered_content.lower()
        assert result.filtered_content != inappropriate_content

    @pytest.mark.asyncio
    async def test_personal_info_filtering(self, safety_service, sample_child_profile, sample_context):
        """Test that personal information is properly filtered"""
        content_with_personal_info = "mi email es niño@ejemplo.com y mi teléfono es 1234567890"

        result = await safety_service.check_content_safety(
            content=content_with_personal_info,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        assert not result.is_safe
        assert result.filtered_content is not None
        assert "niño@ejemplo.com" not in result.filtered_content
        assert "1234567890" not in result.filtered_content


class TestSafeTopicAlternatives:
    """Test generation of safe alternative topics"""

    @pytest.mark.asyncio
    async def test_safe_alternative_topic_generation(self, safety_service, sample_child_profile):
        """Test generation of safe alternative topics"""
        blocked_topic = "violencia"

        alternative = await safety_service.get_safe_alternative_topic(
            blocked_topic=blocked_topic,
            child_profile=sample_child_profile,
            language="es"
        )

        assert alternative is not None
        assert alternative != blocked_topic
        assert alternative in safety_service.appropriate_topics_by_age[(8, 10)]

    @pytest.mark.asyncio
    async def test_age_appropriate_alternatives(self, safety_service):
        """Test that alternatives are age-appropriate"""
        blocked_topic = "miedo"

        # Test for different ages
        ages_to_test = [5, 8, 12]

        for age in ages_to_test:
            child_profile = {
                "child_id": f"child_{age}",
                "age": age,
                "level": 3,
                "language": "es"
            }

            alternative = await safety_service.get_safe_alternative_topic(
                blocked_topic=blocked_topic,
                child_profile=child_profile,
                language="es"
            )

            assert alternative is not None
            # Verify it's in the appropriate age range topics
            found_appropriate = False
            for age_range, topics in safety_service.appropriate_topics_by_age.items():
                if age_range[0] <= age <= age_range[1]:
                    if alternative in topics:
                        found_appropriate = True
                        break
            assert found_appropriate, f"Alternative '{alternative}' not appropriate for age {age}"


class TestProfileValidation:
    """Test child profile safety validation"""

    @pytest.mark.asyncio
    async def test_sensitive_child_profile_validation(self, safety_service):
        """Test validation of sensitive child profiles"""
        young_sensitive_child = {
            "child_id": "young_sensitive",
            "age": 6,
            "level": 2,
            "sensitivity": "high",
            "blocked_topics": [],  # Empty blocklist - should trigger warning
            "language": "es"
        }

        result = await safety_service.validate_child_profile_safety(young_sensitive_child)

        assert not result.is_safe
        assert len(result.violations) > 0
        assert any(v.violation_type == SafetyViolationType.BLOCKED_TOPIC for v in result.violations)

    @pytest.mark.asyncio
    async def test_adequate_child_profile_validation(self, safety_service):
        """Test validation of adequate child profiles"""
        adequate_child = {
            "child_id": "adequate_child",
            "age": 8,
            "level": 3,
            "sensitivity": "medium",
            "blocked_topics": ["violencia", "miedo", "muerte"],
            "language": "es"
        }

        result = await safety_service.validate_child_profile_safety(adequate_child)

        assert result.is_safe
        assert len(result.violations) == 0


class TestSafetyStatistics:
    """Test safety monitoring and statistics"""

    @pytest.mark.asyncio
    async def test_safety_statistics_empty(self, safety_service):
        """Test statistics with no safety checks performed"""
        stats = await safety_service.get_safety_statistics()

        assert stats["total_safety_checks"] == 0
        assert stats["safety_rate"] == 0
        assert stats["safe_checks"] == 0
        assert stats["unsafe_checks"] == 0

    @pytest.mark.asyncio
    async def test_safety_statistics_with_data(self, safety_service, sample_child_profile, sample_context):
        """Test statistics after performing safety checks"""
        # Perform some safety checks
        safe_content = "me gusta jugar en el parque"
        unsafe_content = "quiero matar al monstruo"

        # Safe check
        await safety_service.check_content_safety(
            content=safe_content,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        # Unsafe check
        await safety_service.check_content_safety(
            content=unsafe_content,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        stats = await safety_service.get_safety_statistics()

        assert stats["total_safety_checks"] == 2
        assert stats["safe_checks"] == 1
        assert stats["unsafe_checks"] == 1
        assert stats["safety_rate"] == 0.5
        assert len(stats["violation_counts"]) > 0


class TestServiceStatus:
    """Test safety service status reporting"""

    def test_service_status(self, safety_service):
        """Test service status reporting"""
        status = safety_service.get_service_status()

        assert status["status"] == "active"
        assert "features" in status
        assert status["features"]["inappropriate_content_detection"] is True
        assert status["features"]["violence_detection"] is True
        assert status["features"]["personal_info_protection"] is True
        assert "supported_languages" in status
        assert "es" in status["supported_languages"]
        assert "en" in status["supported_languages"]


class TestMultiLanguageSupport:
    """Test safety validation across different languages"""

    @pytest.mark.asyncio
    async def test_english_content_validation(self, safety_service, sample_context):
        """Test safety validation with English content"""
        english_child = {
            "child_id": "english_child",
            "age": 8,
            "level": 3,
            "language": "en"
        }

        violent_content = "I want to kill the monster and hit him hard"

        result = await safety_service.check_content_safety(
            content=violent_content,
            child_profile=english_child,
            context=sample_context,
            language="en"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.VIOLENCE for v in result.violations)

    @pytest.mark.asyncio
    async def test_english_inappropriate_content(self, safety_service, sample_context):
        """Test detection of inappropriate English content"""
        english_child = {
            "child_id": "english_child",
            "age": 8,
            "level": 3,
            "language": "en"
        }

        inappropriate_content = "stupid idiot, this is shit"

        result = await safety_service.check_content_safety(
            content=inappropriate_content,
            child_profile=english_child,
            context=sample_context,
            language="en"
        )

        assert not result.is_safe
        assert any(v.violation_type == SafetyViolationType.INAPPROPRIATE_CONTENT for v in result.violations)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_empty_content(self, safety_service, sample_child_profile, sample_context):
        """Test safety check with empty content"""
        result = await safety_service.check_content_safety(
            content="",
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        # Empty content should be safe
        assert result.is_safe
        assert len(result.violations) == 0

    @pytest.mark.asyncio
    async def test_very_long_content(self, safety_service, sample_child_profile, sample_context):
        """Test safety check with very long content"""
        long_content = "palabra " * 1000  # Very long repetitive content

        result = await safety_service.check_content_safety(
            content=long_content,
            child_profile=sample_child_profile,
            context=sample_context,
            language="es"
        )

        # Should handle long content without crashing
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_missing_child_profile(self, safety_service, sample_context):
        """Test safety check with missing child profile"""
        result = await safety_service.check_content_safety(
            content="me gusta jugar",
            child_profile={},
            context=sample_context,
            language="es"
        )

        # Should use defaults and not crash
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_unsupported_language(self, safety_service, sample_child_profile, sample_context):
        """Test safety check with unsupported language"""
        result = await safety_service.check_content_safety(
            content="violence content",
            child_profile=sample_child_profile,
            context=sample_context,
            language="fr"  # French (not explicitly supported)
        )

        # Should default to Spanish patterns
        assert result is not None
        assert isinstance(result, SafetyCheckResult)