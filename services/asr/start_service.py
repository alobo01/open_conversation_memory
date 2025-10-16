#!/usr/bin/env python3
"""
Startup script for the EmoRobCare ASR Service
Provides additional validation and setup before starting the service
"""

import asyncio
import logging
import sys
import os
import torch
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import settings
from services.transcription_service import TranscriptionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def validate_environment():
    """Validate the environment before starting the service"""
    logger.info("🔍 Validating ASR service environment...")

    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("❌ Python 3.8 or higher is required")
        return False

    logger.info(f"✅ Python version: {sys.version}")

    # Check CUDA availability
    cuda_available = torch.cuda.is_available()
    if cuda_available:
        device_count = torch.cuda.device_count()
        logger.info(f"✅ CUDA available with {device_count} device(s)")
        for i in range(device_count):
            props = torch.cuda.get_device_properties(i)
            memory_gb = props.total_memory / 1024**3
            logger.info(f"   GPU {i}: {props.name} ({memory_gb:.1f}GB)")
    else:
        logger.warning("⚠️  CUDA not available, will use CPU (slower performance)")

    # Check disk space for models
    try:
        current_dir = Path(__file__).parent
        stat = os.statvfs(current_dir)
        free_space_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
        if free_space_gb < 5:
            logger.warning(f"⚠️  Low disk space: {free_space_gb:.1f}GB available")
        else:
            logger.info(f"✅ Disk space: {free_space_gb:.1f}GB available")
    except Exception as e:
        logger.warning(f"⚠️  Could not check disk space: {e}")

    # Validate configuration
    logger.info("✅ Configuration:")
    logger.info(f"   Default language: {settings.default_language}")
    logger.info(f"   Supported languages: {settings.supported_languages}")
    logger.info(f"   Model configurations: {settings.models}")
    logger.info(f"   VAD enabled: {settings.enable_vad}")
    logger.info(f"   Max audio length: {settings.max_audio_length}s")

    return True

async def test_model_loading():
    """Test loading one model to verify setup"""
    logger.info("🧪 Testing model loading...")

    try:
        # Create a temporary transcription service to test model loading
        service = TranscriptionService()

        # Wait a moment for initial model loading
        await asyncio.sleep(3)

        # Check if at least one model loaded successfully
        model_status = await service.get_model_status()
        loaded_models = sum(1 for model in model_status["models"].values() if model["loaded"])

        if loaded_models > 0:
            logger.info(f"✅ Successfully loaded {loaded_models} model(s)")
            for tier, model_info in model_status["models"].items():
                if model_info["loaded"]:
                    logger.info(f"   {tier}: {model_info['model_name']} ({model_info['compute_type']})")
        else:
            logger.warning("⚠️  No models loaded successfully")

        # Cleanup
        await service.cleanup()
        return loaded_models > 0

    except Exception as e:
        logger.error(f"❌ Model loading test failed: {e}")
        return False

async def run_startup_checks():
    """Run all startup checks"""
    logger.info("🚀 Starting EmoRobCare ASR Service...")
    logger.info("=" * 50)

    # Validate environment
    if not await validate_environment():
        logger.error("❌ Environment validation failed")
        return False

    # Test model loading
    if not await test_model_loading():
        logger.error("❌ Model loading test failed")
        return False

    logger.info("=" * 50)
    logger.info("✅ All startup checks passed!")
    logger.info("🎉 ASR Service is ready to start")
    return True

def start_service():
    """Start the ASR service"""
    import uvicorn

    logger.info("🌐 Starting FastAPI server...")
    logger.info("   Service will be available at: http://localhost:8001")
    logger.info("   API docs at: http://localhost:8001/docs")
    logger.info("   Health check at: http://localhost:8001/health")

    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8001,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("🛑 Service stopped by user")
    except Exception as e:
        logger.error(f"💥 Service failed to start: {e}")
        sys.exit(1)

async def main():
    """Main startup function"""
    try:
        # Run startup checks
        if await run_startup_checks():
            # Start the service
            start_service()
        else:
            logger.error("❌ Startup failed, service not started")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("🛑 Startup interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Startup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--skip-checks":
        logger.info("⏭️  Skipping startup checks")
        start_service()
    else:
        asyncio.run(main())