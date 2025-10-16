import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from services.api.routers.background_tasks import router
from services.api.models.extraction_models import ExtractionJob, ExtractionResult
from services.api.models.schemas import Message
from datetime import datetime


class TestBackgroundTasksRouter:
    """Test suite for background tasks router"""

    @pytest.fixture
    def app(self):
        """Create FastAPI app with router"""
        app = FastAPI()
        app.include_router(router, prefix="/tasks")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def sample_messages(self):
        """Create sample messages"""
        return [
            Message(
                conversation_id="conv_123",
                role="user",
                text="Hola, me gusta jugar",
                timestamp=datetime.now()
            ).dict(),
            Message(
                conversation_id="conv_123",
                role="assistant",
                text="**¡Hola!** ¿Qué te gusta jugar?",
                timestamp=datetime.now()
            ).dict()
        ]

    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = Mock()
        db.messages.find.return_value.to_list = AsyncMock(return_value=[])
        return db

    def test_start_extraction_job_success(self, client, sample_messages):
        """Test successful extraction job start"""
        with patch('services.api.routers.background_tasks.get_db') as mock_get_db, \
             patch('services.api.routers.background_tasks.extraction_service') as mock_service:

            # Setup mocks
            mock_db = mock_get_db.return_value
            mock_db.messages.find.return_value.to_list.return_value = sample_messages

            mock_service.create_extraction_job.return_value = "job_123"

            # Make request
            response = client.post(
                "/tasks/extraction/start/conv_123/child_456"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job_123"
            assert data["conversation_id"] == "conv_123"
            assert data["status"] == "started"
            assert data["message_count"] == 2

            # Verify service was called
            mock_service.create_extraction_job.assert_called_once_with("conv_123", "child_456")

    def test_start_extraction_job_no_messages(self, client, mock_db):
        """Test extraction job start with no messages"""
        with patch('services.api.routers.background_tasks.get_db') as mock_get_db, \
             patch('services.api.routers.background_tasks.extraction_service') as mock_service:

            # Setup mock with no messages
            mock_db.messages.find.return_value.to_list.return_value = []

            # Make request
            response = client.post(
                "/tasks/extraction/start/conv_123/child_456"
            )

            assert response.status_code == 404
            assert "No messages found" in response.json()["detail"]

    def test_get_extraction_status_success(self, client):
        """Test getting extraction job status"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            # Setup mock job
            mock_job = ExtractionJob(
                job_id="job_123",
                conversation_id="conv_123",
                child_id="child_456",
                status="completed"
            )
            mock_service.get_job_status.return_value = mock_job

            # Make request
            response = client.get("/tasks/extraction/status/job_123")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job_123"
            assert data["conversation_id"] == "conv_123"
            assert data["status"] == "completed"

    def test_get_extraction_status_not_found(self, client):
        """Test getting status for non-existent job"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            mock_service.get_job_status.return_value = None

            response = client.get("/tasks/extraction/status/non_existent")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_extraction_results_success(self, client):
        """Test getting extraction results"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            # Setup mock job with results
            from services.api.models.extraction_models import ExtractedEntity, EntityType

            mock_entity = ExtractedEntity(
                text="parque",
                type=EntityType.PLACE,
                confidence=0.95,
                start_pos=10,
                end_pos=15,
                normalized_form="parque"
            )

            mock_result = ExtractionResult(
                conversation_id="conv_123",
                child_id="child_456",
                entities=[mock_entity],
                relationships=[],
                processing_time_ms=1500
            )

            mock_job = ExtractionJob(
                job_id="job_123",
                conversation_id="conv_123",
                child_id="child_456",
                status="completed",
                result=mock_result
            )
            mock_service.get_job_status.return_value = mock_job

            response = client.get("/tasks/extraction/results/job_123")

            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == "conv_123"
            assert data["child_id"] == "child_456"
            assert len(data["entities"]) == 1
            assert data["entities"][0]["text"] == "parque"
            assert data["processing_time_ms"] == 1500

    def test_get_extraction_results_job_not_completed(self, client):
        """Test getting results for job that hasn't completed"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            mock_job = ExtractionJob(
                job_id="job_123",
                conversation_id="conv_123",
                child_id="child_456",
                status="processing"
            )
            mock_service.get_job_status.return_value = mock_job

            response = client.get("/tasks/extraction/results/job_123")

            assert response.status_code == 400
            assert "not completed" in response.json()["detail"]

    def test_get_extraction_results_job_no_results(self, client):
        """Test getting results for completed job with no results"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            mock_job = ExtractionJob(
                job_id="job_123",
                conversation_id="conv_123",
                child_id="child_456",
                status="completed",
                result=None
            )
            mock_service.get_job_status.return_value = mock_job

            response = client.get("/tasks/extraction/results/job_123")

            assert response.status_code == 404
            assert "No results found" in response.json()["detail"]

    def test_list_extraction_jobs(self, client):
        """Test listing all extraction jobs"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            # Setup mock jobs
            jobs = [
                ExtractionJob(
                    job_id="job_1",
                    conversation_id="conv_1",
                    child_id="child_1",
                    status="completed"
                ),
                ExtractionJob(
                    job_id="job_2",
                    conversation_id="conv_2",
                    child_id="child_2",
                    status="processing"
                )
            ]
            mock_service.active_jobs.values.return_value = jobs

            response = client.get("/tasks/extraction/jobs")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["job_id"] == "job_1"
            assert data[1]["job_id"] == "job_2"

    def test_cleanup_extraction_job_success(self, client):
        """Test cleaning up completed job"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            # Setup mock job
            mock_job = ExtractionJob(
                job_id="job_123",
                conversation_id="conv_123",
                child_id="child_456",
                status="completed"
            )
            mock_service.get_job_status.return_value = mock_job

            # Make request
            response = client.delete("/tasks/extraction/jobs/job_123")

            assert response.status_code == 200
            data = response.json()
            assert data["job_id"] == "job_123"
            assert data["status"] == "cleaned_up"

    def test_cleanup_extraction_job_not_found(self, client):
        """Test cleaning up non-existent job"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            mock_service.get_job_status.return_value = None

            response = client.delete("/tasks/extraction/jobs/non_existent")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_cleanup_extraction_job_active(self, client):
        """Test cleaning up job that is still active"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            mock_job = ExtractionJob(
                job_id="job_123",
                conversation_id="conv_123",
                child_id="child_456",
                status="processing"
            )
            mock_service.get_job_status.return_value = mock_job

            response = client.delete("/tasks/extraction/jobs/job_123")

            assert response.status_code == 400
            assert "Cannot cleanup" in response.json()["detail"]

    def test_get_extraction_stats(self, client):
        """Test getting extraction statistics"""
        with patch('services.api.routers.background_tasks.extraction_service') as mock_service:
            # Setup mock jobs with different statuses
            from services.api.models.extraction_models import ExtractedEntity, EntityType, ValidationReport

            mock_entity = ExtractedEntity(
                text="parque",
                type=EntityType.PLACE,
                confidence=0.95,
                start_pos=10,
                end_pos=15,
                normalized_form="parque"
            )

            mock_result = ExtractionResult(
                conversation_id="conv_123",
                child_id="child_456",
                entities=[mock_entity],
                relationships=[],
                processing_time_ms=1500
            )

            validation_report = ValidationReport(
                valid=True,
                violations=[],
                shapes_checked=["ChildShape"]
            )

            jobs = [
                ExtractionJob(
                    job_id="job_1",
                    conversation_id="conv_1",
                    child_id="child_1",
                    status="completed",
                    result=mock_result,
                    validation_report=validation_report
                ),
                ExtractionJob(
                    job_id="job_2",
                    conversation_id="conv_2",
                    child_id="child_2",
                    status="failed",
                    error_message="Processing failed"
                ),
                ExtractionJob(
                    job_id="job_3",
                    conversation_id="conv_3",
                    child_id="child_3",
                    status="processing"
                )
            ]

            mock_service.active_jobs.values.return_value = jobs

            response = client.get("/tasks/extraction/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["total_jobs"] == 3
            assert data["pending_jobs"] == 0
            assert data["processing_jobs"] == 1
            assert data["completed_jobs"] == 1
            assert data["failed_jobs"] == 1
            assert data["total_entities_extracted"] == 1
            assert data["average_processing_time_ms"] == 1500.0
            assert data["average_entities_per_conversation"] == 1.0