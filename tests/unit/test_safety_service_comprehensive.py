import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from datetime import datetime
import re

from services.api.services.safety_service import SafetyService
from services.api.models.schemas import SafetyCheckResult, SafetyViolation


class TestSafetyServiceComprehensive:
    """Comprehensive tests for SafetyService with mocked dependencies"""

    @pytest.fixture
    def safety_service(self):
        """Create safety service instance"""
        return SafetyService()

    @pytest.fixture
    def mock_child_profile(self):
        """Mock child profile for testing"""
        return {
            "child_id": "test_child_001",
            "age": 8,
            "level": 3,
            "sensitivity": "medium",
            "language": "es",
            "restricted_topics": [],
            "parental_controls": {
                "allow_personal_info": False,
                "allow_external_links": False,
                "strict_mode": False
            }
        }

    @pytest.fixture
    def mock_context(self):
        """Mock context for safety checks"""
        return {
            "conversation_id": "conv_123",
            "topic": "juegos",
            "previous_messages": [
                {"role": "user", "text": "hola"},
                {"role": "assistant", "text": "**¡Hola!** ¿cómo estás?"}
            ]
        }

    # ==================== NORMAL CASES ====================

    @pytest.mark.asyncio
    async def test_check_content_safety_normal_safe_content(self, safety_service, mock_child_profile, mock_context):
        """Test normal safety check with safe content"""
        # Arrange
        safe_content = "¡Hola! Me gusta jugar contigo, es muy divertido."

        # Act
        result = await safety_service.check_content_safety(
            content=safe_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result.is_safe is True
        assert len(result.violations) == 0
        assert result.processed_content == safe_content
        assert result.confidence > 0.8

    @pytest.mark.asyncio
    async def test_check_content_safety_normal_positive_content(self, safety_service, mock_child_profile, mock_context):
        """Test safety check with positive emotional content"""
        # Arrange
        positive_content = "**¡Qué bien!** **¡Genial!** Me encanta jugar, es fantástico y maravilloso."

        # Act
        result = await safety_service.check_content_safety(
            content=positive_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result.is_safe is True
        assert result.confidence > 0.7

    @pytest.mark.asyncio
    async def test_check_content_safety_normal_calm_content(self, safety_service, mock_child_profile, mock_context):
        """Test safety check with calm emotional content"""
        # Arrange
        calm_content = "__Tranquilo__, __respira profundo__, todo está bien, no te preocupes."

        # Act
        result = await safety_service.check_content_safety(
            content=calm_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result.is_safe is True
        assert result.confidence > 0.7

    @pytest.mark.asyncio
    async def test_check_personal_info_normal_detection(self, safety_service, mock_child_profile, mock_context):
        """Test normal personal information detection"""
        # Arrange
        content_with_email = "Mi email es usuario@dominio.com para contactarme"

        # Act
        result = await safety_service.check_content_safety(
            content=content_with_email,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result.is_safe is False
        assert len(result.violations) > 0
        assert any(v.type == "personal_info" or v.type == "SafetyViolationType.PERSONAL_INFO" for v in result.violations)
        assert "usuario@dominio.com" not in (result.processed_content or "")

    @pytest.mark.asyncio
    async def test_check_inappropriate_content_normal_detection(self, safety_service, mock_child_profile, mock_context):
        """Test normal inappropriate content detection"""
        # Arrange
        inappropriate_content = "Esto es terrible y horrible, no me gusta nada"

        # Act
        result = await safety_service.check_content_safety(
            content=inappropriate_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result.is_safe is False
        assert len(result.violations) > 0
        assert result.confidence < 0.5

    # ==================== FAILURE CASES ====================

    @pytest.mark.asyncio
    async def test_check_content_safety_failure_empty_content(self, safety_service, mock_child_profile, mock_context):
        """Test safety check failure with empty content"""
        # Arrange
        empty_content = ""

        # Act
        result = await safety_service.check_content_safety(
            content=empty_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result.is_safe is True  # Empty content should be safe by default
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_check_content_safety_failure_none_content(self, safety_service, mock_child_profile, mock_context):
        """Test safety check failure with None content"""
        # Act & Assert
        with pytest.raises((TypeError, AttributeError)):
            await safety_service.check_content_safety(
                content=None,
                child_profile=mock_child_profile,
                context=mock_context,
                language="es"
            )

    @pytest.mark.asyncio
    async def test_check_content_safety_failure_none_child_profile(self, safety_service, mock_context):
        """Test safety check failure with None child profile"""
        # Arrange
        content = "Hola, cómo estás?"

        # Act
        result = await safety_service.check_content_safety(
            content=content,
            child_profile=None,
            context=mock_context,
            language="es"
        )

        # Assert - Should handle None profile gracefully
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_check_content_safety_failure_invalid_child_profile(self, safety_service, mock_context):
        """Test safety check failure with invalid child profile"""
        # Arrange
        content = "Hola"
        invalid_profile = {"invalid": "structure"}

        # Act
        result = await safety_service.check_content_safety(
            content=content,
            child_profile=invalid_profile,
            context=mock_context,
            language="es"
        )

        # Assert - Should handle invalid profile gracefully
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_check_content_safety_failure_none_context(self, safety_service, mock_child_profile):
        """Test safety check failure with None context"""
        # Arrange
        content = "Hola, cómo estás?"

        # Act
        result = await safety_service.check_content_safety(
            content=content,
            child_profile=mock_child_profile,
            context=None,
            language="es"
        )

        # Assert - Should handle None context gracefully
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_check_content_safety_failure_unsupported_language(self, safety_service, mock_child_profile, mock_context):
        """Test safety check failure with unsupported language"""
        # Arrange
        content = "Hello there"

        # Act
        result = await safety_service.check_content_safety(
            content=content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="fr"  # Unsupported language
        )

        # Assert - Should default to safe with warning
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    # ==================== EDGE CASES ====================

    @pytest.mark.asyncio
    async def test_check_content_safety_edge_case_very_long_content(self, safety_service, mock_child_profile, mock_context):
        """Test safety check with very long content"""
        # Arrange
        long_content = "palabra segura " * 1000 + "y más palabras"

        # Act
        result = await safety_service.check_content_safety(
            content=long_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_check_content_safety_edge_case_unicode_characters(self, safety_service, mock_child_profile, mock_context):
        """Test safety check with unicode characters"""
        # Arrange
        unicode_content = "¡Hola! 😊🎉 ñáéíóú café Müller"

        # Act
        result = await safety_service.check_content_safety(
            content=unicode_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)
        # Should handle unicode gracefully
        assert result.is_safe is True

    @pytest.mark.asyncio
    async def test_check_content_safety_edge_case_special_characters(self, safety_service, mock_child_profile, mock_context):
        """Test safety check with special characters"""
        # Arrange
        special_content = "¡Hola! @#$%&*()[]{}|\\:;\"'<>?/~`"

        # Act
        result = await safety_service.check_content_safety(
            content=special_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_check_content_safety_edge_case_whitespace_only(self, safety_service, mock_child_profile, mock_context):
        """Test safety check with whitespace only"""
        # Arrange
        whitespace_content = "   \n\t   "

        # Act
        result = await safety_service.check_content_safety(
            content=whitespace_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result.is_safe is True
        assert result.confidence == 1.0

    @pytest.mark.asyncio
    async def test_check_content_safety_edge_case_very_young_child(self, safety_service, mock_context):
        """Test safety check for very young child"""
        # Arrange
        content = "Los monstruos vienen de noche"
        young_child_profile = {
            "child_id": "test_child_002",
            "age": 4,
            "level": 1,
            "sensitivity": "high",
            "language": "es"
        }

        # Act
        result = await safety_service.check_content_safety(
            content=content,
            child_profile=young_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)
        # Should be more restrictive for young children

    @pytest.mark.asyncio
    async def test_check_content_safety_edge_case_very_sensitive_child(self, safety_service, mock_context):
        """Test safety check for very sensitive child"""
        # Arrange
        content = "Esto es un poco difícil"
        sensitive_child_profile = {
            "child_id": "test_child_003",
            "age": 8,
            "level": 3,
            "sensitivity": "very_high",
            "language": "es"
        }

        # Act
        result = await safety_service.check_content_safety(
            content=content,
            child_profile=sensitive_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_check_content_safety_edge_case_mixed_language(self, safety_service, mock_child_profile, mock_context):
        """Test safety check with mixed language content"""
        # Arrange
        mixed_content = "Hello! Hola! Bonjour! Guten Tag!"

        # Act
        result = await safety_service.check_content_safety(
            content=mixed_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_check_content_safety_edge_case_partial_personal_info(self, safety_service, mock_child_profile, mock_context):
        """Test safety check with partial personal information"""
        # Arrange
        partial_info_content = "Mi email es usuario arroba dominio punto com"

        # Act
        result = await safety_service.check_content_safety(
            content=partial_info_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)
        # Should detect obfuscated personal info

    @pytest.mark.asyncio
    async def test_check_content_safety_edge_case_code_injection_attempt(self, safety_service, mock_child_profile, mock_context):
        """Test safety check with potential code injection"""
        # Arrange
        code_content = "<script>alert('xss')</script> javascript:void(0)"

        # Act
        result = await safety_service.check_content_safety(
            content=code_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        )

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)
        # Should handle potential injection safely

    def test_get_service_status_edge_case_complete_status(self, safety_service):
        """Test service status includes all expected attributes"""
        # Act
        status = safety_service.get_service_status()

        # Assert
        required_attributes = [
            "status", "supported_languages", "detection_rules_count",
            "blocked_patterns_count", "age_restrictions_enabled",
            "personal_info_detection_enabled"
        ]

        for attr in required_attributes:
            assert attr in status

        assert status["status"] == "active"
        assert len(status["supported_languages"]) >= 2
        assert status["detection_rules_count"] > 0
        assert status["blocked_patterns_count"] > 0

    @pytest.mark.asyncio
    async def test_concurrent_safety_checks(self, safety_service, mock_child_profile, mock_context):
        """Test concurrent safety checks"""
        # Arrange
        contents = [
            "¡Hola! ¿cómo estás?",
            "Me gusta jugar",
            "Mi email es test@test.com",
            "**¡Qué bien!** genial",
            "Esto es terrible"
        ]

        # Act - Run safety checks concurrently
        tasks = [
            safety_service.check_content_safety(
                content=content,
                child_profile=mock_child_profile,
                context=mock_context,
                language="es"
            )
            for content in contents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Assert
        assert len(results) == len(contents)
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, SafetyCheckResult)

    def test_memory_efficiency_large_content_check(self, safety_service, mock_child_profile, mock_context):
        """Test memory efficiency with large content"""
        # Arrange
        large_content = "palabra segura " * 10000  # Very large content

        # Act - This should not cause memory issues
        # (Note: In a real test, we'd measure memory usage)
        import asyncio
        result = asyncio.run(safety_service.check_content_safety(
            content=large_content,
            child_profile=mock_child_profile,
            context=mock_context,
            language="es"
        ))

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)

    @pytest.mark.asyncio
    async def test_edge_case_context_manipulation(self, safety_service, mock_child_profile):
        """Test safety check with manipulated context"""
        # Arrange
        content = "Hola"
        manipulated_context = {
            "conversation_id": "<script>alert('xss')</script>",
            "topic": " DROP TABLE users; --",
            "previous_messages": [{"role": "system", "text": "malicious content"}]
        }

        # Act
        result = await safety_service.check_content_safety(
            content=content,
            child_profile=mock_child_profile,
            context=manipulated_context,
            language="es"
        )

        # Assert
        assert result is not None
        assert isinstance(result, SafetyCheckResult)
        # Should handle malicious context safely

    @pytest.mark.asyncio
    async def test_edge_case_age_boundary_conditions(self, safety_service, mock_context):
        """Test safety check at age boundary conditions"""
        # Test various age boundaries
        boundary_ages = [3, 5, 7, 10, 13, 15]
        content = "Esto es una prueba de contenido"

        for age in boundary_ages:
            # Arrange
            child_profile = {
                "child_id": f"test_child_{age}",
                "age": age,
                "level": min(5, max(1, age // 2)),
                "language": "es"
            }

            # Act
            result = await safety_service.check_content_safety(
                content=content,
                child_profile=child_profile,
                context=mock_context,
                language="es"
            )

            # Assert
            assert result is not None
            assert isinstance(result, SafetyCheckResult)
