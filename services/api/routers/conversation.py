from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime
import logging

from ..models.schemas import (
    ConversationStart, ConversationResponse, ConversationNext,
    ConversationReply, Message, EmotionType, Language
)
from ..services.llm_service import LLMService
from ..services.memory_service import MemoryService
from ..services.emotion_service import EmotionService
from ..services.safety_service import SafetyService
from ..services.extraction_service import ExtractionService
from ..core.database import get_db
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize services
memory_service = MemoryService()
safety_service = SafetyService()
llm_service = LLMService()
emotion_service = EmotionService()
extraction_service = ExtractionService()

@router.post("/start", response_model=ConversationResponse)
async def start_conversation(
    request: ConversationStart,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """Start a new conversation"""
    try:
        conversation_id = str(uuid.uuid4())

        # Get child profile
        child_profile = await db.profiles.find_one({"child_id": request.child})
        if not child_profile:
            # Create default profile if not exists
            child_profile = {
                "child_id": request.child,
                "name": request.child,
                "age": 8,
                "preferred_topics": [request.topic],
                "avoid_topics": [],
                "blocked_topics": [],
                "sensitive_topics": [],
                "level": request.level.value,
                "sensitivity": "medium",
                "language": settings.default_language
            }
            await db.profiles.insert_one(child_profile)

        # Generate starting sentence based on topic and level
        starting_sentence = await generate_starting_sentence(
            request.topic,
            request.level,
            child_profile.get("language", settings.default_language)
        )

        # Create conversation record
        conversation = {
            "conversation_id": conversation_id,
            "child_id": request.child,
            "topic": request.topic.value,
            "level": request.level.value,
            "language": child_profile.get("language", settings.default_language),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": "active",
            "message_count": 1
        }
        await db.conversations.insert_one(conversation)

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            text=starting_sentence,
            emotion=EmotionType.NEUTRAL
        )
        await db.messages.insert_one(assistant_message.dict())

        # Schedule background extraction and embedding
        if settings.enable_background_extraction:
            background_tasks.add_task(
                extract_conversation_data,
                conversation_id,
                request.child,
                [assistant_message.dict()]
            )

        # Store assistant message in semantic memory
        if settings.enable_semantic_search:
            metadata = {
                "topic": conversation["topic"],
                "level": conversation["level"],
                "language": conversation["language"]
            }
            background_tasks.add_task(
                memory_service.store_single_message,
                conversation_id=conversation_id,
                child_id=request.child,
                message=assistant_message.dict(),
                metadata=metadata
            )

        logger.info(f"Started conversation {conversation_id} for child {request.child}")

        return ConversationResponse(
            conversation_id=conversation_id,
            starting_sentence=starting_sentence,
            end=False,
            emotion=EmotionType.NEUTRAL
        )

    except Exception as e:
        logger.error(f"Error starting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start conversation")

@router.post("/next", response_model=ConversationReply)
async def continue_conversation(
    request: ConversationNext,
    background_tasks: BackgroundTasks,
    db=Depends(get_db)
):
    """Continue an existing conversation"""
    try:
        # Verify conversation exists and get child profile
        conversation = await db.conversations.find_one({
            "conversation_id": request.conversation_id
        })
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get child profile for safety checks
        child_profile = await db.profiles.find_one({"child_id": conversation["child_id"]})
        if not child_profile:
            logger.warning(f"Child profile not found for {conversation['child_id']}, using defaults")
            child_profile = {
                "child_id": conversation["child_id"],
                "age": 8,
                "level": conversation["level"],
                "sensitivity": "medium",
                "language": conversation.get("language", "es")
            }

        # Save user message
        user_message = Message(
            conversation_id=request.conversation_id,
            role="user",
            text=request.user_sentence,
            metadata={"asr_confidence": request.asr_confidence}
        )
        await db.messages.insert_one(user_message.dict())

        # Get conversation history for context
        history = await get_conversation_history(request.conversation_id, db)

        # Get semantic context from memory
        semantic_context = []
        if settings.enable_semantic_search:
            semantic_context = await memory_service.get_conversation_context(
                child_id=conversation["child_id"],
                topic=conversation["topic"],
                query=request.user_sentence
            )

        # Generate response using LLM with enhanced context
        reply_text = await generate_enhanced_response(
            child_id=conversation["child_id"],
            topic=conversation["topic"],
            level=conversation["level"],
            user_input=request.user_sentence,
            conversation_context=semantic_context
        )

        # CRITICAL SAFETY CHECK - Validate response before delivering to child
        safety_result = await safety_service.check_content_safety(
            content=reply_text,
            child_profile=child_profile,
            context={
                "conversation_id": request.conversation_id,
                "topic": conversation["topic"],
                "level": conversation["level"],
                "history": history[-3:] if history else []  # Last 3 messages for context
            },
            language=conversation.get("language", "es")
        )

        # If response is not safe, use filtered content or generate safe alternative
        if not safety_result.is_safe:
            logger.warning(f"Safety violations detected: {[v.violation_type.value for v in safety_result.violations]}")

            # Use filtered content if available, otherwise generate safe alternative
            if safety_result.filtered_content and safety_result.confidence > 0.7:
                reply_text = safety_result.filtered_content
                logger.info("Using filtered content for safety")
            else:
                # Generate completely safe alternative response
                safe_topic = await safety_service.get_safe_alternative_topic(
                    conversation["topic"], child_profile, conversation.get("language", "es")
                )
                reply_text = await generate_safe_response(
                    safe_topic, child_profile, conversation.get("language", "es")
                )
                logger.info(f"Generated safe alternative response for topic: {safe_topic}")

        # Detect emotion in response
        emotion = await detect_response_emotion(reply_text)

        # Save assistant message
        assistant_message = Message(
            conversation_id=request.conversation_id,
            role="assistant",
            text=reply_text,
            emotion=emotion
        )
        await db.messages.insert_one(assistant_message.dict())

        # Update conversation
        await db.conversations.update_one(
            {"conversation_id": request.conversation_id},
            {
                "$set": {"updated_at": datetime.now()},
                "$inc": {"message_count": 1}
            }
        )

        # Schedule background extraction and embedding
        if settings.enable_background_extraction:
            background_tasks.add_task(
                extract_conversation_data,
                request.conversation_id,
                user_message.dict(),
                assistant_message.dict()
            )

        # Store messages in semantic memory
        if settings.enable_semantic_search:
            metadata = {
                "topic": conversation["topic"],
                "level": conversation["level"],
                "language": conversation["language"]
            }

            # Store user message
            background_tasks.add_task(
                memory_service.store_single_message,
                conversation_id=request.conversation_id,
                child_id=conversation["child_id"],
                message=user_message.dict(),
                metadata=metadata
            )

            # Store assistant message
            background_tasks.add_task(
                memory_service.store_single_message,
                conversation_id=request.conversation_id,
                child_id=conversation["child_id"],
                message=assistant_message.dict(),
                metadata=metadata
            )

        # Generate suggestions if needed
        suggestions = await generate_suggestions(conversation, reply_text)

        logger.info(f"Continued conversation {request.conversation_id}")

        return ConversationReply(
            reply=reply_text,
            end=request.end,
            emotion=emotion,
            suggestions=suggestions
        )

    except Exception as e:
        logger.error(f"Error in conversation continuation: {e}")
        raise HTTPException(status_code=500, detail="Failed to continue conversation")

@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db=Depends(get_db)
):
    """Get conversation details and history"""
    try:
        conversation = await db.conversations.find_one({
            "conversation_id": conversation_id
        })
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = await get_conversation_history(conversation_id, db)

        return {
            "conversation": conversation,
            "messages": messages
        }

    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")

@router.get("/child/{child_id}")
async def get_child_conversations(
    child_id: str,
    limit: int = 10,
    db=Depends(get_db)
):
    """Get conversations for a specific child"""
    try:
        conversations = await db.conversations.find(
            {"child_id": child_id}
        ).sort("created_at", -1).limit(limit).to_list(None)

        return {"conversations": conversations}

    except Exception as e:
        logger.error(f"Error getting child conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")

@router.get("/memory/{child_id}/context")
async def get_child_memory_context(
    child_id: str,
    topic: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 3
):
    """Get semantic memory context for a child"""
    try:
        context = await memory_service.get_conversation_context(
            child_id=child_id,
            topic=topic,
            query=query,
            limit=limit
        )

        return {
            "child_id": child_id,
            "topic": topic,
            "query": query,
            "context": context,
            "count": len(context)
        }

    except Exception as e:
        logger.error(f"Error getting memory context: {e}")
        raise HTTPException(status_code=500, detail="Failed to get memory context")

@router.get("/memory/{child_id}/search")
async def search_child_memory(
    child_id: str,
    query: str,
    topic: Optional[str] = None,
    limit: int = 5
):
    """Search child's semantic memory"""
    try:
        results = await memory_service.search_similar_conversations(
            query=query,
            child_id=child_id,
            topic=topic,
            limit=limit
        )

        return {
            "child_id": child_id,
            "query": query,
            "topic": topic,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        raise HTTPException(status_code=500, detail="Failed to search memory")

@router.get("/memory/{child_id}/summary")
async def get_memory_summary(
    child_id: str,
    topic: Optional[str] = None
):
    """Get semantic memory summary for a child"""
    try:
        summary = await memory_service.get_semantic_memory_summary(
            child_id=child_id,
            topic=topic
        )

        return {
            "child_id": child_id,
            "topic": topic,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Error getting memory summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get memory summary")

@router.delete("/memory/{conversation_id}")
async def delete_conversation_memory(conversation_id: str):
    """Delete conversation from semantic memory"""
    try:
        success = await memory_service.delete_conversation_memory(conversation_id)

        if success:
            return {"message": f"Conversation {conversation_id} deleted from memory"}
        else:
            raise HTTPException(status_code=404, detail="Conversation not found in memory")

    except Exception as e:
        logger.error(f"Error deleting conversation memory: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete conversation memory")

@router.get("/memory/status")
async def get_memory_status():
    """Get memory service status"""
    try:
        status = await memory_service.get_memory_status()
        return status

    except Exception as e:
        logger.error(f"Error getting memory status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get memory status")

# Helper functions
async def generate_starting_sentence(topic: str, level: int, language: str) -> str:
    """Generate a starting sentence based on topic and level"""
    templates = {
        "es": {
            "school": [
                "__Hola__ ¿te apetece hablar de la escuela?",
                "__Hola__ ¿qué tal tu día en el cole?",
                "__Hola__ ¿quieres contarme algo de tus clases?"
            ],
            "hobbies": [
                "**¡Hola!** ¿qué te gusta hacer en tu tiempo libre?",
                "__Hola__ ¿qué juegos te divierten más?",
                "**¡Hola!** ¿de qué te gustaría hablar hoy?"
            ],
            "holidays": [
                "__Hola__ ¿te gustan las vacaciones?",
                "**¡Hola!** ¿adónde te gustaría ir de viaje?",
                "__Hola__ ¿qué te divierte más en los días libres?"
            ],
            "food": [
                "__Hola__ ¿qué te gusta comer?",
                "**¡Hola!** ¿cuál es tu comida favorita?",
                "__Hola__ ¿te gusta cocinar o ayudar en la cocina?"
            ],
            "friends": [
                "__Hola__ ¿tienes amigos en el cole?",
                "**¡Hola!** ¿qué te gusta hacer con tus amigos?",
                "__Hola__ ¿quieres hablarme de tus amigos?"
            ]
        },
        "en": {
            "school": [
                "__Hello__ would you like to talk about school?",
                "__Hello__ how was your day at school?",
                "__Hello__ want to tell me about your classes?"
            ],
            "hobbies": [
                "**Hi!** what do you like to do in your free time?",
                "__Hello__ what games do you enjoy the most?",
                "**Hi!** what would you like to talk about today?"
            ]
        }
    }

    # Get template based on language and topic
    templates_by_lang = templates.get(language, templates["es"])
    topic_templates = templates_by_lang.get(topic, templates_by_lang["hobbies"])

    # Select template based on level (simpler for lower levels)
    if level <= 2:
        return topic_templates[0]
    elif level <= 4:
        return topic_templates[1]
    else:
        return topic_templates[2]

async def generate_response(conversation: dict, history: list, user_input: str, semantic_context: list = None) -> str:
    """Generate response using LLM service with semantic context"""
    try:
        # Format semantic context for LLM prompt
        context_text = ""
        if semantic_context:
            context_examples = [ctx.get("text", "") for ctx in semantic_context[:2]]
            if context_examples:
                context_text = "\nContexto relevante: " + " | ".join(context_examples)

        # Build enhanced prompt with context
        enhanced_prompt = f"""
        Conversación sobre {conversation.get('topic', 'tema general')} con nivel {conversation.get('level', 3)}.

        Historial reciente: {format_conversation_history(history[-3:])}
        {context_text}

        Usuario dice: "{user_input}"

        Responde de forma natural y apropiada para un niño con TEA2, nivel {conversation.get('level', 3)}.
        Usa marcadores emocionales (**positivo**, __calm__) cuando sea apropiado.
        """

        # Try to use LLM service if available
        try:
            response = await llm_service.generate_response(
                prompt=enhanced_prompt,
                conversation_id=conversation.get("conversation_id"),
                child_id=conversation.get("child_id"),
                level=conversation.get("level", 3)
            )
            if response:
                return response
        except Exception as e:
            logger.warning(f"LLM service not available: {e}")

        # Fallback to template-based responses with context awareness
        return generate_contextual_response(user_input, semantic_context, conversation.get("level", 3))

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "**¡Hola!** ¿quieres hablar de algo?"  # Safe fallback

def format_conversation_history(history: list) -> str:
    """Format conversation history for LLM prompt"""
    if not history:
        return "Sin historial previo."

    formatted = []
    for msg in history:
        role = "Usuario" if msg.get("role") == "user" else "Asistente"
        text = msg.get("text", "")[:50]  # Limit length
        formatted.append(f"{role}: {text}")

    return " | ".join(formatted)

def generate_contextual_response(user_input: str, semantic_context: list, level: int) -> str:
    """Generate contextual response based on semantic memory"""
    import random

    # Level-appropriate response templates
    if level <= 2:
        responses = [
            "**¡Hola!** ¿te gusta eso?",
            "__Entiendo__ ¿quieres hablar más?",
            "**¡Qué bien!** cuéntame más.",
            "__Vale__ ¿y qué más?",
            "**¡Genial!** ¿es divertido?"
        ]
    elif level <= 4:
        responses = [
            "**¡Qué interesante!** Cuéntame más sobre eso.",
            "__Entiendo__ ¿puedes explicarme mejor?",
            "**¡Genial!** ¿qué más te gustaría compartir?",
            "__Vale__ ¿y cómo te sentiste con eso?",
            "**¡Qué bien!** ¿qué fue lo que más te gustó?"
        ]
    else:
        responses = [
            "**¡Fascinante!** Me encantaría escuchar más detalles sobre tu experiencia.",
            "__Comprendo__ ¿cómo te hizo sentir esa situación?",
            "**¡Excelente!** ¿qué aspectos encuentras más interesantes?",
            "__Entiendo__ ¿hay algo más que te gustaría compartir al respecto?",
            "**¡Maravilloso!** ¿qué aprendiste de esa experiencia?"
        ]

    # Add contextual awareness if available
    if semantic_context:
        contextual_responses = [
            f"**¡Ah!** Recuerdo que hablamos de algo similar antes.",
            f"__Interesante__ ¿esto te recuerda a otras experiencias?",
            f"**¡Genial!** Me gusta que compartas esto conmigo.",
            f"__Vale__ ¿cómo se compara con otras veces?",
        ]
        responses.extend(contextual_responses)

    return random.choice(responses)

async def detect_response_emotion(text: str) -> EmotionType:
    """Detect emotion in response text"""
    if "**" in text:
        return EmotionType.POSITIVE
    elif "__" in text:
        return EmotionType.CALM
    else:
        return EmotionType.NEUTRAL

async def generate_suggestions(conversation: dict, reply: str) -> Optional[List[str]]:
    """Generate conversation suggestions"""
    level = conversation.get("level", 3)

    if level <= 2:
        return [
            "Sí / No",
            "Me gusta / No me gusta",
            "Quiero hablar de otra cosa"
        ]
    elif level <= 4:
        return [
            "Cuéntame más",
            "¿Y qué pasó después?",
            "Me gustaría hablar de otra cosa"
        ]
    else:
        return None

async def get_conversation_history(conversation_id: str, db) -> List[dict]:
    """Get conversation history"""
    messages = await db.messages.find(
        {"conversation_id": conversation_id}
    ).sort("timestamp", 1).to_list(None)

    return messages

async def generate_safe_response(topic: str, child_profile: dict, language: str = "es") -> str:
    """Generate a completely safe response when safety violations are detected"""
    import random

    age = child_profile.get("age", 8)
    level = child_profile.get("level", 3)

    # Age-appropriate safe responses
    safe_responses = {
        "es": {
            (5, 7): [
                "**¡Hola!** ¿quieres hablar de juegos divertidos?",
                "__Tranquilo__ ¿te gusta jugar con tus amigos?",
                "**¡Qué bien!** ¿qué te hace feliz hoy?",
                "__Vale__ ¿quieres dibujar algo bonito?",
                "**¡Genial!** me encanta hablar contigo."
            ],
            (8, 10): [
                "**¡Hola!** ¿qué actividades te gustan más?",
                "__Interesante__ ¿qué has aprendido hoy?",
                "**¡Fantástico!** ¿cuéntame de tus hobbies?",
                "__Claro__ ¿quieres hablar de la escuela?",
                "**¡Perfecto!** ¿qué te divierte mucho?"
            ],
            (11, 13): [
                "**¡Hola!** ¿qué proyectos interesantes tienes?",
                "__Comprendo__ ¿qué te apasiona hacer?",
                "**¡Excelente!** ¿qué has descubierto nuevo?",
                "__Entiendo__ ¿quieres compartir tus ideas?",
                "**¡Maravilloso!** ¿qué metas tienes?"
            ]
        },
        "en": {
            (5, 7): [
                "**Hi!** do you want to talk about fun games?",
                "__Calm__ do you like playing with your friends?",
                "**Great!** what makes you happy today?",
                "__Okay__ do you want to draw something nice?",
                "**Awesome!** I love talking with you."
            ],
            (8, 10): [
                "**Hi!** what activities do you like most?",
                "__Interesting__ what did you learn today?",
                "**Fantastic!** tell me about your hobbies?",
                "__Sure__ do you want to talk about school?",
                "**Perfect!** what do you find really fun?"
            ],
            (11, 13): [
                "**Hi!** what interesting projects do you have?",
                "__I understand__ what are you passionate about?",
                "**Excellent!** what new things have you discovered?",
                "__Got it__ do you want to share your ideas?",
                "**Wonderful!** what goals do you have?"
            ]
        }
    }

    # Get appropriate responses for age and language
    lang_responses = safe_responses.get(language, safe_responses["es"])

    for age_range, responses in lang_responses.items():
        if age_range[0] <= age <= age_range[1]:
            return random.choice(responses)

    # Fallback response
    fallback = {
        "es": "**¡Hola!** ¿quieres hablar de algo divertido?",
        "en": "**Hi!** do you want to talk about something fun?"
    }

    return fallback.get(language, fallback["es"])

async def extract_conversation_data(conversation_id: str, child_id: str, messages: List[Dict[str, Any]]):
    """Background task to extract data for knowledge graph"""
    try:
        logger.info(f"Extracting data for conversation {conversation_id}")

        # Convert messages to Message objects
        message_objects = []
        for msg in messages:
            message_obj = Message(**msg)
            message_objects.append(message_obj)

        # Process extraction using the extraction service
        job_id = extraction_service.create_extraction_job(conversation_id, child_id)

        # Process the extraction job
        await extraction_service.process_extraction_job(
            job_id=job_id,
            conversation_id=conversation_id,
            child_id=child_id,
            conversation_messages=message_objects
        )

        logger.info(f"Completed extraction job {job_id} for conversation {conversation_id}")

    except Exception as e:
        logger.error(f"Error in background extraction for conversation {conversation_id}: {e}")

async def generate_enhanced_response(
    child_id: str,
    topic: str,
    level: int,
    user_input: str,
    conversation_context: Optional[List[Dict[str, Any]]] = None
) -> str:
    """Generate enhanced LLM response using retrieved context"""
    try:
        # Build context-enhanced prompt
        context_text = ""
        if conversation_context:
            context_text = "\n\nContexto relevante de conversaciones anteriores:\n"
            for ctx in conversation_context[:3]:  # Limit to top 3 context items
                context_text += f"- {ctx.get('clean_text', ctx.get('text', ''))}\n"

        # Build main prompt
        prompt = f"""
{context_text}

Conversación actual:
Tema: {topic}
Nivel: {level}
Niño dice: "{user_input}"

Responde de forma natural y apropiada para un niño de nivel {level}.
Usa lenguaje simple y amigable. Sé empático y positivo.
"""

        # Generate response using LLM service
        response = await llm_service.generate_response(prompt)

        return response

    except Exception as e:
        logger.error(f"Error generating enhanced response: {e}")
        # Fallback to basic response generation
        return await generate_starting_sentence(topic, level, "es")