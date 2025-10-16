# LLM Integration with vLLM

This document describes the vLLM integration implemented for the EmoRobCare project.

## Overview

The LLM service has been upgraded from template-based responses to actual AI generation using vLLM with the Qwen2-7B-Instruct model. This provides natural, contextually appropriate conversations for children with TEA2 (Autism Spectrum Disorder Level 2).

## Key Features

### vLLM Integration
- **Model**: Qwen2-7B-Instruct (configurable)
- **Inference Engine**: vLLM for efficient local processing
- **Response Time**: Target < 2 seconds per generation
- **Memory Optimization**: Conservative GPU memory usage (60%)

### Child-Appropriate Responses
- **Token Limits**: 150 tokens max for child-friendly length
- **Temperature**: 0.7 for creative but safe responses
- **Emotional Markup**: Support for `**positive**` and `__calm__` expressions
- **Content Validation**: Built-in safety checks and appropriate tone filtering

### Performance Features
- **Concurrent Protection**: Thread-safe generation with locks
- **Performance Metrics**: Response time tracking and performance grading
- **Health Monitoring**: Real-time model health checks
- **Graceful Fallbacks**: Template responses when model unavailable

## Configuration

### Environment Variables
```bash
OFFLINE_MODE=true                    # Use local vLLM model
LLM_MODEL=Qwen/Qwen2-7B-Instruct    # Model to use
LLM_TEMPERATURE=0.7                 # Generation temperature
LLM_MAX_TOKENS=150                  # Max tokens per response
```

### Requirements
Updated `requirements.txt` includes:
- `vllm==0.6.1` - Main inference engine
- `torch==2.1.1` - PyTorch backend
- `transformers==4.36.0` - Model support

## Usage

### Initialize Service
```python
from services.llm_service import LLMService

llm_service = LLMService()
```

### Generate Response
```python
response = await llm_service.generate_response(
    prompt="Me gusta jugar en el parque",
    child_profile={"age": 8, "level": 3, "language": "es"},
    context={"topic": "juegos", "level": 3}
)
```

### Check Model Status
```python
status = await llm_service.get_model_status()
print(f"Model ready: {status['ready']}")
print(f"Avg response time: {status['avg_response_time']}s")
```

### Health Check
```python
health = await llm_service.health_check()
print(f"Health status: {health['status']}")
```

## Performance Targets

| Metric | Target | Current Implementation |
|--------|--------|------------------------|
| Response Time | < 2s | Tracked and graded |
| Memory Usage | < 8GB | Conservative GPU usage (60%) |
| Throughput | 1+ req/s | Optimized batch processing |
| Availability | > 99% | Health monitoring + fallbacks |

## Safety Features

### Response Validation
- Content length checks (max 500 characters)
- Repetition detection (< 50% unique words threshold)
- Emotional markup validation
- Positive tone enforcement

### Error Handling
- Graceful degradation to template responses
- Comprehensive error logging
- Model health monitoring
- Automatic fallback on failures

## Testing

Run the test script to verify integration:

```bash
cd services/api
python ../../../test_llm_integration.py
```

## Troubleshooting

### Common Issues

1. **vLLM Import Error**
   ```
   pip install vllm==0.6.1
   ```

2. **Model Loading Failure**
   - Check GPU memory availability
   - Verify model name in configuration
   - Review logs for specific error details

3. **Slow Response Times**
   - Check GPU utilization
   - Consider reducing `max_tokens`
   - Monitor system resources

4. **Memory Issues**
   - Reduce `gpu_memory_utilization` in config
   - Use smaller model if needed
   - Ensure sufficient system RAM

## File Changes

### Modified Files
- `services/api/services/llm_service.py` - Main implementation
- `services/api/requirements.txt` - Added vLLM dependency
- `services/api/core/config.py` - Updated default token limit

### New Files
- `test_llm_integration.py` - Test script for verification
- `LLM_INTEGRATION_README.md` - This documentation

## Next Steps

1. **Model Fine-tuning**: Consider fine-tuning on child-appropriate conversations
2. **Caching**: Implement response caching for common prompts
3. **Multi-language**: Expand support beyond Spanish/English
4. **Analytics**: Add detailed usage analytics and reporting