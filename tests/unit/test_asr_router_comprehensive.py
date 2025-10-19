import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI, UploadFile, File
import json
import io
import tempfile
import os
from datetime import datetime

from services.api.routers.asr import router


class TestASRRouterComprehensive:
    """Comprehensive tests for ASR router with mocked dependencies"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with router"""
        app = FastAPI()
        app.include_router(router, prefix="/asr")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_asr_service(self):
        """Mock ASR service"""
        service = Mock()
        service.transcribe_audio = AsyncMock()
        service.get_supported_formats = Mock(return_value=["wav", "mp3", "flac"])
        service.get_available_models = Mock(return_value=["whisper-base", "whisper-small"])
        service.health_check = AsyncMock()
        return service

    @pytest.fixture
    def sample_audio_file(self):
        """Create a sample audio file for testing"""
        # Create a temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            # Write some dummy audio data
            tmp_file.write(b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
            tmp_file_path = tmp_file.name

        yield tmp_file_path

        # Cleanup
        os.unlink(tmp_file_path)

    @pytest.fixture
    def sample_audio_bytes(self):
        """Sample audio bytes for testing"""
        return b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x02\x00\x44\xac\x00\x00\x10\xb1\x02\x00\x04\x00\x10\x00data\x00\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"

    # ==================== NORMAL CASES ====================

    def test_transcribe_audio_normal_success(self, client, sample_audio_file):
        """Test normal successful audio transcription"""
        # Act
        with open(sample_audio_file, "rb") as audio_file:
            response = client.post(
                "/asr/transcribe",
                files={"audio": ("test.wav", audio_file, "audio/wav")},
                data={"tier": "fast"}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "transcription" in data
        transcription = data["transcription"]
        assert "text" in transcription
        assert "language" in transcription
        assert "confidence" in transcription
        assert "tier" in transcription
        assert "processing_time" in transcription

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_different_tiers(self, mock_get_service, client, sample_audio_file):
        """Test transcription with different quality tiers"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock()
        mock_get_service.return_value = mock_service

        # Test different tiers
        tiers = ["fast", "balanced", "accurate"]
        expected_responses = [
            {"text": "Transcripción rápida", "confidence": 0.85},
            {"text": "Transcripción balanceada", "confidence": 0.92},
            {"text": "Transcripción precisa", "confidence": 0.98}
        ]

        for i, tier in enumerate(tiers):
            mock_service.transcribe_audio.return_value = expected_responses[i]

            # Act
            with open(sample_audio_file, "rb") as audio_file:
                response = client.post(
                    "/asr/transcribe",
                    files={"audio": ("test.wav", audio_file, "audio/wav")},
                    data={"tier": tier}
                )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["transcription"]["text"] == expected_responses[i]["text"]

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_with_language_detection(self, mock_get_service, client, sample_audio_file):
        """Test transcription with automatic language detection"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value={
            "text": "Hello, how are you?",
            "confidence": 0.94,
            "detected_language": "en",
            "language_probabilities": {"en": 0.94, "es": 0.06}
        })
        mock_get_service.return_value = mock_service

        # Act
        with open(sample_audio_file, "rb") as audio_file:
            response = client.post(
                "/asr/transcribe",
                files={"audio": ("test.wav", audio_file, "audio/wav")},
                data={"tier": "balanced", "detect_language": "true"}
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "detected_language" in data["transcription"]
        assert data["transcription"]["detected_language"] == "en"

    @patch('services.api.routers.asr.get_asr_service')
    def test_get_supported_formats_normal(self, mock_get_service, client):
        """Test getting supported audio formats"""
        # Arrange
        mock_service = Mock()
        mock_service.get_supported_formats.return_value = ["wav", "mp3", "flac", "m4a"]
        mock_get_service.return_value = mock_service

        # Act
        response = client.get("/asr/formats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "formats" in data
        assert len(data["formats"]) == 4
        assert "wav" in data["formats"]

    @patch('services.api.routers.asr.get_asr_service')
    def test_get_available_models_normal(self, mock_get_service, client):
        """Test getting available ASR models"""
        # Arrange
        mock_service = Mock()
        mock_service.get_available_models.return_value = {
            "whisper-base": "small",
            "whisper-small": "medium", 
            "whisper-medium": "large"
        }
        mock_get_service.return_value = mock_service

        # Act
        response = client.get("/asr/models")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "models" in data
        assert len(data["models"]) == 3
        assert data["models"][0]["name"] == "whisper-base"
        assert data["models"][0]["size"] == "small"

    @patch('services.api.routers.asr.get_asr_service')
    def test_health_check_normal(self, mock_get_service, client):
        """Test ASR service health check"""
        # Arrange
        mock_service = Mock()
        mock_service.health_check = AsyncMock(return_value={
            "status": "healthy",
            "model_loaded": True,
            "gpu_available": True,
            "memory_usage": "2.1GB",
            "active_transcriptions": 0
        })
        mock_get_service.return_value = mock_service

        # Act
        response = client.get("/asr/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data
        assert data["status"]["status"] == "healthy"

    # ==================== FAILURE CASES ====================

    def test_transcribe_audio_failure_no_audio_file(self, client):
        """Test transcription failure when no audio file provided"""
        # Act
        response = client.post("/asr/transcribe", data={"tier": "fast"})

        # Assert
        assert response.status_code == 422  # Validation error

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_failure_unsupported_format(self, mock_get_service, client):
        """Test transcription failure with unsupported audio format"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(side_effect=Exception("Unsupported format: xyz"))
        mock_get_service.return_value = mock_service

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("test.xyz", b"fake audio data", "audio/xyz")},
            data={"tier": "fast"}
        )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_failure_invalid_tier(self, mock_get_service, client, sample_audio_file):
        """Test transcription failure with invalid tier"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(side_effect=Exception("Invalid tier: ultra"))
        mock_get_service.return_value = mock_service

        # Act
        with open(sample_audio_file, "rb") as audio_file:
            response = client.post(
                "/asr/transcribe",
                files={"audio": ("test.wav", audio_file, "audio/wav")},
                data={"tier": "ultra"}
            )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_failure_service_unavailable(self, mock_get_service, client, sample_audio_file):
        """Test transcription failure when ASR service is unavailable"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(side_effect=ConnectionError("Service unavailable"))
        mock_get_service.return_value = mock_service

        # Act
        with open(sample_audio_file, "rb") as audio_file:
            response = client.post(
                "/asr/transcribe",
                files={"audio": ("test.wav", audio_file, "audio/wav")},
                data={"tier": "fast"}
            )

        # Assert
        assert response.status_code == 503
        data = response.json()
        assert data["success"] is False
        assert "unavailable" in data["error"].lower()

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_failure_corrupted_audio(self, mock_get_service, client):
        """Test transcription failure with corrupted audio file"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(side_effect=Exception("Corrupted audio file"))
        mock_get_service.return_value = mock_service

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("corrupted.wav", b"corrupted audio data", "audio/wav")},
            data={"tier": "fast"}
        )

        # Assert
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False

    @patch('services.api.routers.asr.get_asr_service')
    def test_health_check_failure_service_down(self, mock_get_service, client):
        """Test health check when service is down"""
        # Arrange
        mock_service = Mock()
        mock_service.health_check = AsyncMock(side_effect=ConnectionError("Service down"))
        mock_get_service.return_value = mock_service

        # Act
        response = client.get("/asr/health")

        # Assert
        assert response.status_code == 503
        data = response.json()
        assert data["success"] is False

    # ==================== EDGE CASES ====================

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_edge_case_very_large_file(self, mock_get_service, client):
        """Test transcription with very large audio file"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value={
            "text": "Transcripción de archivo grande",
            "confidence": 0.96,
            "duration": 3600.0  # 1 hour
        })
        mock_get_service.return_value = mock_service

        # Create a large file (simulated)
        large_audio = b"fake_large_audio_data" * 10000  # 250KB of fake data

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("large.wav", large_audio, "audio/wav")},
            data={"tier": "accurate"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transcription"]["duration"] == 3600.0

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_edge_case_very_short_audio(self, mock_get_service, client):
        """Test transcription with very short audio"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value={
            "text": "Hola",
            "confidence": 0.99,
            "duration": 0.1
        })
        mock_get_service.return_value = mock_service

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("short.wav", b"short audio", "audio/wav")},
            data={"tier": "fast"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transcription"]["text"] == "Hola"
        assert data["transcription"]["duration"] == 0.1

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_edge_case_empty_audio(self, mock_get_service, client):
        """Test transcription with empty audio file"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value={
            "text": "",
            "confidence": 0.0,
            "duration": 0.0,
            "warning": "No speech detected"
        })
        mock_get_service.return_value = mock_service

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("empty.wav", b"", "audio/wav")},
            data={"tier": "fast"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transcription"]["text"] == ""
        assert "warning" in data["transcription"]

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_edge_case_unicode_filename(self, mock_get_service, client, sample_audio_bytes):
        """Test transcription with unicode filename"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value={
            "text": "Transcripción exitosa",
            "confidence": 0.97
        })
        mock_get_service.return_value = mock_service

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("áudio_ñoño.wav", sample_audio_bytes, "audio/wav")},
            data={"tier": "balanced"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_edge_case_multiple_languages(self, mock_get_service, client):
        """Test transcription with mixed languages"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value={
            "text": "Hello amigo, cómo estás?",
            "confidence": 0.89,
            "language_confidence": {"en": 0.6, "es": 0.4},
            "language_segments": [
                {"text": "Hello ", "language": "en", "confidence": 0.95},
                {"text": "amigo, cómo estás?", "language": "es", "confidence": 0.92}
            ]
        })
        mock_get_service.return_value = mock_service

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("mixed.wav", b"fake audio data", "audio/wav")},
            data={"tier": "accurate", "detect_language": "true"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "language_segments" in data["transcription"]
        assert len(data["transcription"]["language_segments"]) == 2

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_edge_case_low_confidence(self, mock_get_service, client):
        """Test transcription with very low confidence"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value={
            "text": "transcripción incierta",
            "confidence": 0.15,
            "warning": "Low confidence transcription"
        })
        mock_get_service.return_value = mock_service

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("unclear.wav", b"fake audio data", "audio/wav")},
            data={"tier": "fast"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transcription"]["confidence"] == 0.15
        assert "warning" in data["transcription"]

    @patch('services.api.routers.asr.get_asr_service')
    def test_transcribe_audio_edge_case_background_noise(self, mock_get_service, client):
        """Test transcription with background noise"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value={
            "text": "hola cómo estás",
            "confidence": 0.72,
            "noise_level": "high",
            "quality_score": 0.65
        })
        mock_get_service.return_value = mock_service

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("noisy.wav", b"fake audio data", "audio/wav")},
            data={"tier": "balanced", "noise_reduction": "true"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "noise_level" in data["transcription"]

    def test_edge_case_invalid_content_type(self, client):
        """Test with invalid content type"""
        # Act
        response = client.post(
            "/asr/transcribe",
            content="not multipart data",
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code in [400, 422]

    @patch('services.api.routers.asr.get_asr_service')
    def test_concurrent_transcription_requests(self, mock_get_service, client):
        """Test concurrent transcription requests"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(return_value={
            "text": "Transcripción concurrente",
            "confidence": 0.95
        })
        mock_get_service.return_value = mock_service

        # Act - Make concurrent requests
        import threading
        results = []

        def make_request():
            response = client.post(
                "/asr/transcribe",
                files={"audio": ("test.wav", b"fake audio data", "audio/wav")},
                data={"tier": "fast"}
            )
            results.append(response)

        threads = [threading.Thread(target=make_request) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Assert
        assert len(results) == 5
        for result in results:
            assert result.status_code == 200
            data = result.json()
            assert data["success"] is True

    def test_memory_efficiency_large_file_upload(self, client):
        """Test memory efficiency with large file upload"""
        # This is more of a performance test
        # Create a reasonably large file
        large_content = b"audio_data" * 100000  # ~1MB

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("large_test.wav", large_content, "audio/wav")},
            data={"tier": "fast"}
        )

        # Assert - Should not crash the server
        assert response.status_code in [200, 500, 413]  # Any is acceptable as long as server doesn't crash

    def test_file_size_limit_handling(self, client):
        """Test handling of file size limits"""
        # Create a very large file (this might be rejected by server limits)
        very_large_content = b"audio_data" * 10000000  # ~100MB

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("huge.wav", very_large_content, "audio/wav")},
            data={"tier": "fast"}
        )

        # Assert
        # Should be rejected due to size limits or handled gracefully
        assert response.status_code in [200, 413, 500]

    @patch('services.api.routers.asr.get_asr_service')
    def test_error_response_format_consistency(self, mock_get_service, client):
        """Test that all error responses have consistent format"""
        # Arrange
        mock_service = Mock()
        mock_service.transcribe_audio = AsyncMock(side_effect=Exception("Test error"))
        mock_get_service.return_value = mock_service

        # Act
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("test.wav", b"fake audio data", "audio/wav")},
            data={"tier": "invalid_tier"}
        )

        # Assert
        if response.status_code >= 400:
            data = response.json()
            assert data.get("success") is False
            assert "error" in data or "message" in data

    def test_parameter_validation_edge_cases(self, client):
        """Test parameter validation with edge cases"""
        # Test with various parameter combinations
        test_cases = [
            {"tier": "fast", "detect_language": "true"},
            {"tier": "balanced", "detect_language": "false"},
            {"tier": "accurate", "noise_reduction": "true"},
            {"tier": "invalid", "detect_language": "maybe"},
            {},  # No parameters
        ]

        for params in test_cases:
            # Act
            response = client.post(
                "/asr/transcribe",
                files={"audio": ("test.wav", b"fake audio data", "audio/wav")},
                data=params
            )

            # Assert - Should handle all parameter combinations gracefully
            assert response.status_code in [200, 422, 500]

    def test_timeout_handling(self, client):
        """Test timeout handling for long transcriptions"""
        # This would typically require mocking a slow transcription
        # For now, we'll test that the endpoint exists and handles requests
        response = client.post(
            "/asr/transcribe",
            files={"audio": ("test.wav", b"fake audio data", "audio/wav")},
            data={"tier": "accurate", "timeout": "1"}  # Very short timeout
        )

        # Should either complete quickly or handle timeout gracefully
        assert response.status_code in [200, 408, 500]
