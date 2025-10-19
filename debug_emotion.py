import sys
sys.path.append('services/api')
from services.emotion_service import EmotionService

emotion_service = EmotionService()
mock_conversation_history = [
    {'role': 'user', 'text': 'hola', 'timestamp': '2024-01-01T10:00:00'}, 
    {'role': 'assistant', 'text': '**¡Hola!** ¿cómo estás?', 'timestamp': '2024-01-01T10:00:02'}, 
    {'role': 'assistant', 'text': '__Qué bien__ que estás feliz', 'timestamp': '2024-01-01T10:00:03'}
]

analysis = emotion_service.analyze_conversation_emotions(mock_conversation_history)
print('Analysis keys:', list(analysis.keys()))
print('Total messages:', analysis.get('total_messages'))
print('Analysis:', analysis)
