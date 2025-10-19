import sys
sys.path.append('services/api')
from services.api.services.llm_service import LLMService
import random

# Test the fallback response directly
service = LLMService.__new__(LLMService)
response = service._get_fallback_response()
print('Fallback response:', repr(response))
print('Length:', len(response))
print('Contains expected phrases:')
for phrase in ['disculpa', 'entiendo', 'vale', 'perfecto']:
    print(f'  {phrase}: {phrase in response}')

# Test template response
import asyncio
async def test_template():
    template_response = await service._get_template_response("Me gusta jugar")
    print('Template response:', repr(template_response))
    print('Contains playing words:')
    for word in ['jugar', 'juego', 'divertido']:
        print(f'  {word}: {word in template_response.lower()}')

asyncio.run(test_template())
