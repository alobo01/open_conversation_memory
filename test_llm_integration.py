#!/usr/bin/env python3
"""
Test script for LLM service vLLM integration
"""

import asyncio
import sys
import os

# Add the services/api directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services', 'api'))

from services.llm_service import LLMService
from core.config import settings


async def test_llm_service():
    """Test the LLM service with vLLM integration"""
    print("🧪 Testing LLM Service vLLM Integration")
    print("=" * 50)

    # Initialize service
    print(f"📋 Initializing LLM service...")
    print(f"   - Model: {settings.llm_model}")
    print(f"   - Offline mode: {settings.offline_mode}")
    print(f"   - Max tokens: {settings.llm_max_tokens}")
    print(f"   - Temperature: {settings.llm_temperature}")

    try:
        llm_service = LLMService()
        print(f"✅ Service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return

    # Check model status
    print("\n📊 Model Status:")
    try:
        status = await llm_service.get_model_status()
        for key, value in status.items():
            if key == "performance_metrics":
                print(f"   {key}:")
                for subkey, subvalue in value.items():
                    print(f"     - {subkey}: {subvalue}")
            else:
                print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Failed to get model status: {e}")

    # Test health check
    print("\n🏥 Health Check:")
    try:
        health = await llm_service.health_check()
        for key, value in health.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")

    # Test response generation (if model is ready)
    if llm_service.model_ready:
        print("\n💬 Testing Response Generation:")
        test_prompts = [
            "Hola, me llamo Juan y tengo 8 años.",
            "Me gusta jugar con mis amigos en el parque.",
            "Hoy aprendí matemáticas en la escuela."
        ]

        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n   Test {i}: {prompt}")
            try:
                response = await llm_service.generate_response(
                    prompt=prompt,
                    child_profile={"age": 8, "level": 3, "language": "es"},
                    context={"topic": "general", "level": 3}
                )
                print(f"   🤖 Response: {response}")
            except Exception as e:
                print(f"   ❌ Generation failed: {e}")
    else:
        print("\n⚠️ Model not ready, skipping generation tests")

    print("\n🏁 Test completed!")


if __name__ == "__main__":
    asyncio.run(test_llm_service())