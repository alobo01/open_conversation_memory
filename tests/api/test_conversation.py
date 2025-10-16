#!/usr/bin/env python3
"""
Tests for the conversation API endpoints
"""

import pytest
import httpx
from fastapi.testclient import TestClient
import sys
import os

# Add the services/api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../services/api'))

from main import app

client = TestClient(app)

class TestConversationAPI:
    """Test cases for conversation API endpoints"""

    def test_health_check(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "services" in data

    def test_start_conversation(self):
        """Test starting a new conversation"""
        payload = {
            "child": "test_child",
            "topic": "school",
            "level": 3
        }

        response = client.post("/conv/start", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "conversation_id" in data
        assert "starting_sentence" in data
        assert data["end"] is False
        assert "emotion" in data

    def test_start_conversation_invalid_data(self):
        """Test starting conversation with invalid data"""
        payload = {
            "child": "",
            "topic": "invalid_topic",
            "level": 10
        }

        response = client.post("/conv/start", json=payload)
        assert response.status_code == 422  # Validation error

    def test_continue_conversation(self):
        """Test continuing an existing conversation"""
        # First start a conversation
        start_payload = {
            "child": "test_child",
            "topic": "hobbies",
            "level": 3
        }

        start_response = client.post("/conv/start", json=start_payload)
        conversation_id = start_response.json()["conversation_id"]

        # Continue the conversation
        continue_payload = {
            "conversation_id": conversation_id,
            "user_sentence": "Me gusta jugar al fútbol",
            "end": False
        }

        response = client.post("/conv/next", json=continue_payload)
        assert response.status_code == 200

        data = response.json()
        assert "reply" in data
        assert data["end"] is False
        assert "emotion" in data

    def test_continue_nonexistent_conversation(self):
        """Test continuing a conversation that doesn't exist"""
        payload = {
            "conversation_id": "nonexistent_id",
            "user_sentence": "Hola",
            "end": False
        }

        response = client.post("/conv/next", json=payload)
        assert response.status_code == 404

    def test_get_conversation(self):
        """Test getting conversation details"""
        # First start a conversation
        start_payload = {
            "child": "test_child",
            "topic": "food",
            "level": 3
        }

        start_response = client.post("/conv/start", json=start_payload)
        conversation_id = start_response.json()["conversation_id"]

        # Get the conversation
        response = client.get(f"/conv/{conversation_id}")
        assert response.status_code == 200

        data = response.json()
        assert "conversation" in data
        assert "messages" in data
        assert len(data["messages"]) >= 1  # At least the starting message

    def test_get_child_conversations(self):
        """Test getting conversations for a specific child"""
        response = client.get("/conv/child/test_child")
        assert response.status_code == 200

        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)

    def test_different_topics(self):
        """Test conversations with different topics"""
        topics = ["school", "hobbies", "holidays", "food", "friends"]

        for topic in topics:
            payload = {
                "child": f"test_child_{topic}",
                "topic": topic,
                "level": 3
            }

            response = client.post("/conv/start", json=payload)
            assert response.status_code == 200

            data = response.json()
            assert "starting_sentence" in data
            assert len(data["starting_sentence"]) > 0

    def test_different_levels(self):
        """Test conversations with different levels"""
        for level in range(1, 6):
            payload = {
                "child": f"test_child_level_{level}",
                "topic": "school",
                "level": level
            }

            response = client.post("/conv/start", json=payload)
            assert response.status_code == 200

            data = response.json()
            assert "starting_sentence" in data

    def test_end_conversation(self):
        """Test ending a conversation"""
        # Start a conversation
        start_payload = {
            "child": "test_child_end",
            "topic": "school",
            "level": 3
        }

        start_response = client.post("/conv/start", json=start_payload)
        conversation_id = start_response.json()["conversation_id"]

        # End the conversation
        continue_payload = {
            "conversation_id": conversation_id,
            "user_sentence": "Adiós",
            "end": True
        }

        response = client.post("/conv/next", json=continue_payload)
        assert response.status_code == 200

        data = response.json()
        assert "reply" in data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])