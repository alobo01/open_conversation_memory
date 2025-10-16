# EmoRobCare ASR Service

Automatic Speech Recognition (ASR) service for children with TEA2 using faster-whisper with a 3-tier precision system.

## Features

- **3-Tier Precision System**: Fast, Balanced, and Accurate transcription modes
- **GPU Acceleration**: Automatic CUDA detection and optimization
- **Multi-language Support**: Spanish and English with auto-detection
- **Voice Activity Detection**: Improved accuracy through silence filtering
- **Comprehensive Error Handling**: Graceful fallbacks and meaningful error messages
- **Performance Monitoring**: Built-in benchmarking and statistics
- **Health Checks**: Comprehensive service health monitoring

## Architecture

### Tiers

1. **Fast Tier** (`medium` model, int8 precision)
   - ~4x realtime processing
   - Lower accuracy for quick responses
   - int8 quantization for maximum speed

2. **Balanced Tier** (`large-v2` model, fp16 precision)
   - ~2x realtime processing
   - Good balance of speed and accuracy
   - Default tier for most use cases

3. **Accurate Tier** (`large-v3` model, fp16 precision)
   - ~0.5x realtime processing
   - Maximum accuracy with beam search
   - Best for critical applications

### GPU Optimization

- Automatic CUDA detection
- Dynamic memory management
- Efficient model loading and cleanup
- Fallback to CPU when GPU unavailable

## API Endpoints

### Core Endpoints

- `POST /transcribe` - Main transcription endpoint
- `GET /health` - Health check with detailed status
- `GET /stats` - Service statistics and performance metrics
- `GET /status` - Detailed service status including models
- `GET /models` - Available models and configurations

### Testing & Monitoring

- `POST /test` - Test endpoint without audio (simulated responses)
- `POST /benchmark` - Performance benchmarking across multiple iterations

## Usage Examples

### Basic Transcription

```bash
curl -X POST http://localhost:8001/transcribe \
  -F "audio=@audio.wav" \
  -F "tier=balanced" \
  -F "language=es"
```

### Health Check

```bash
curl http://localhost:8001/health
```

### Service Status

```bash
curl http://localhost:8001/status
```

### Benchmark Performance

```bash
curl -X POST http://localhost:8001/benchmark \
  -F "audio=@audio.wav" \
  -F "tier=balanced" \
  -F "iterations=5"
```

## Configuration

The service is configured via environment variables and `core/config.py`:

```python
# Model configurations
models = {
    "fast": "medium",
    "balanced": "large-v2",
    "accurate": "large-v3"
}

# Tier-specific settings
tier_configs = {
    "fast": {
        "compute_type": "int8",
        "beam_size": 1,
        "realtime_factor": 4.0,
        "base_confidence": 0.85
    },
    "balanced": {
        "compute_type": "float16",
        "beam_size": 2,
        "realtime_factor": 2.0,
        "base_confidence": 0.92
    },
    "accurate": {
        "compute_type": "float16",
        "beam_size": 5,
        "realtime_factor": 0.5,
        "base_confidence": 0.97
    }
}
```

## Response Format

### Transcription Response

```json
{
    "text": "Transcribed text here.",
    "language": "es",
    "confidence": 0.92,
    "tier": "balanced",
    "processing_time": 1.234
}
```

### Health Check Response

```json
{
    "status": "healthy",
    "timestamp": 1234567890.123,
    "uptime": 3600.0,
    "checks": {
        "models": {
            "status": "healthy",
            "loaded": 2,
            "total": 3
        },
        "gpu": {
            "status": "healthy",
            "available": true,
            "device": "cuda"
        }
    }
}
```

## Development

### Running Tests

```bash
cd services/asr
python test_asr.py
```

The test suite includes:
- Health check validation
- All tier transcription testing
- Performance benchmarking
- Error handling verification
- Service statistics monitoring

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py

# Or with uvicorn for development
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Docker Deployment

```bash
# Build the image
docker build -t emorobcare-asr .

# Run the container
docker run -p 8001:8001 --gpus all emorobcare-asr
```

## Performance Targets

- **Fast Tier**: <0.5s processing time, >85% confidence
- **Balanced Tier**: <1.0s processing time, >92% confidence
- **Accurate Tier**: <2.0s processing time, >97% confidence

Memory usage targets:
- **Fast Tier**: ~1.5GB
- **Balanced Tier**: ~3GB
- **Accurate Tier**: ~3GB

## Troubleshooting

### Common Issues

1. **GPU not detected**: Service will automatically fall back to CPU with int8 quantization
2. **Model loading fails**: Check available disk space and internet connection for first-time downloads
3. **Audio processing errors**: Ensure audio is in supported format (WAV, MP3, etc.) and under 30 seconds
4. **High memory usage**: Consider using smaller models or running with fewer loaded tiers

### Monitoring

Check service health and performance:
- `/health` for overall status
- `/stats` for detailed metrics
- `/status` for model information
- Service logs for detailed error tracking

## Dependencies

- `fastapi` - Web framework
- `faster-whisper` - Speech recognition
- `torch` - Deep learning framework
- `librosa` - Audio processing
- `soundfile` - Audio file handling
- `uvicorn` - ASGI server

## License

This service is part of the EmoRobCare project for children with Autism Spectrum Disorder Level 2.