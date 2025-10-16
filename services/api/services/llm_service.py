import logging
from typing import Dict, Any, List, Optional
import asyncio
import json
import time
from threading import Lock

from ..core.config import settings
from .safety_service import SafetyService

try:
    from vllm import LLM, SamplingParams
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.engine.async_llm_engine import AsyncLLMEngine
    VLLM_AVAILABLE = True
except ImportError:
    VLLM_AVAILABLE = False
    logging.warning("vLLM not available. Please install with: pip install vllm")

logger = logging.getLogger(__name__)

class LLMService:
    """Service for managing LLM interactions"""

    def __init__(self):
        self.model_name = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.offline_mode = settings.offline_mode
        self.model = None
        self.model_ready = False
        self.model_lock = Lock()
        self.generation_count = 0
        self.total_generation_time = 0.0

        # Initialize safety service
        self.safety_service = SafetyService()

        # Initialize model based on mode
        if self.offline_mode:
            self._init_local_model()
        else:
            self._init_online_model()

    def _init_local_model(self):
        """Initialize local LLM model with vLLM"""
        try:
            if not VLLM_AVAILABLE:
                logger.error("vLLM is not available. Please install it first.")
                self.model_ready = False
                return

            logger.info(f"Initializing local model: {self.model_name}")

            # Use smaller max_tokens for child-appropriate responses
            max_tokens = min(self.max_tokens, 150)

            # Initialize vLLM engine with optimized settings for children
            self.model = LLM(
                model=self.model_name,
                trust_remote_code=True,
                tensor_parallel_size=1,  # Single GPU/CPU
                max_model_len=max_tokens,
                gpu_memory_utilization=0.6,  # Conservative memory usage
                dtype="float16",  # Use float16 for efficiency
                enforce_eager=True,  # For better compatibility
                disable_log_stats=True,  # Reduce log noise
                max_num_batched_tokens=1024,  # Optimized batch size
            )

            # Test the model with a simple generation
            test_params = SamplingParams(
                temperature=0.1,
                max_tokens=10,
                stop=["\n", "."]
            )

            test_outputs = self.model.generate("Hola", test_params)
            if test_outputs and len(test_outputs) > 0:
                self.model_ready = True
                logger.info(f"Local model {self.model_name} initialized successfully")
            else:
                logger.error("Model test generation failed")
                self.model_ready = False

        except Exception as e:
            logger.error(f"Failed to initialize local model: {e}")
            self.model_ready = False
            self.model = None

    def _init_online_model(self):
        """Initialize online LLM model"""
        try:
            # This would initialize API clients for Claude/OpenAI
            logger.info("Initializing online LLM clients")
            self.claude_client = None  # Would be actual client
            self.openai_client = None  # Would be actual client
            self.model_ready = True
        except Exception as e:
            logger.error(f"Failed to initialize online model: {e}")
            self.model_ready = False

    async def generate_response(
        self,
        prompt: str,
        conversation_history: List[Dict[str, str]] = None,
        child_profile: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate a response from the LLM with safety validation"""
        try:
            if not self.model_ready:
                return self._get_fallback_response()

            # Build the complete prompt
            full_prompt = self._build_prompt(
                prompt,
                conversation_history,
                child_profile,
                context
            )

            # Generate raw response
            if self.offline_mode:
                raw_response = await self._generate_local(full_prompt)
            else:
                raw_response = await self._generate_online(full_prompt)

            # CRITICAL SAFETY VALIDATION
            if child_profile:
                safety_result = await self.safety_service.check_content_safety(
                    content=raw_response,
                    child_profile=child_profile,
                    context=context or {},
                    language=child_profile.get("language", "es")
                )

                # If response is not safe, return safe alternative
                if not safety_result.is_safe:
                    logger.warning(f"LLM response blocked by safety: {[v.violation_type.value for v in safety_result.violations]}")

                    # Use filtered content if available and confident
                    if safety_result.filtered_content and safety_result.confidence > 0.7:
                        return safety_result.filtered_content
                    else:
                        # Generate safe fallback response
                        return await self._generate_safe_response(child_profile, context)

            return raw_response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response()

    def _build_prompt(
        self,
        user_input: str,
        conversation_history: List[Dict[str, str]] = None,
        child_profile: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Build the complete prompt for the LLM"""
        # System prompt
        system_prompt = self._get_system_prompt(child_profile)

        # Add conversation history
        history_text = ""
        if conversation_history:
            for message in conversation_history[-5:]:  # Last 5 messages
                role = "Niño" if message["role"] == "user" else "Asistente"
                history_text += f"{role}: {message['text']}\n"

        # Add context
        context_text = ""
        if context:
            if context.get("topic"):
                context_text += f"Tema: {context['topic']}\n"
            if context.get("level"):
                context_text += f"Nivel: {context['level']}\n"

        # Build final prompt
        full_prompt = f"""
{system_prompt}

{context_text}

Historial de conversación:
{history_text}

Niño: {user_input}

Asistente:
"""

        return full_prompt.strip()

    def _get_system_prompt(self, child_profile: Dict[str, Any] = None) -> str:
        """Get system prompt based on child profile"""
        age = child_profile.get("age", 8) if child_profile else 8
        level = child_profile.get("level", 3) if child_profile else 3
        language = child_profile.get("language", "es") if child_profile else "es"

        if language == "es":
            prompts = {
                1: "Eres un asistente amigable para niños pequeños. Usa frases muy cortas y simples. Sé muy paciente y anima al niño.",
                2: "Eres un asistente amigable para niños. Usa frases cortas y vocabulario sencillo. Sé paciente y positivo.",
                3: "Eres un asistente conversacional para niños. Usa oraciones simples y conectores básicos. Sé empático y mantén la conversación fluida.",
                4: "Eres un asistente conversacional para niños. Usa oraciones más complejas y buena variedad de vocabulario. Sé interesante y anima al niño a expresarse.",
                5: "Eres un asistente conversacional experto para niños. Mantén conversaciones naturales y variadas. Adapta tu estilo al interés del niño y sé muy expresivo."
            }
        else:
            prompts = {
                1: "You are a friendly assistant for young children. Use very short and simple sentences. Be very patient and encouraging.",
                2: "You are a friendly assistant for children. Use short sentences and simple vocabulary. Be patient and positive.",
                3: "You are a conversational assistant for children. Use simple sentences and basic connectors. Be empathetic and keep the conversation flowing.",
                4: "You are a conversational assistant for children. Use more complex sentences and good vocabulary variety. Be interesting and encourage self-expression.",
                5: "You are an expert conversational assistant for children. Maintain natural and varied conversations. Adapt your style to the child's interests and be very expressive."
            }

        base_prompt = prompts.get(level, prompts[3])

        # Add emotional markup instructions
        emotional_markup = """
Usa este formato para expresar emociones:
- **Para entusiasmo o alegría**: **¡Qué bien!**, **¡Genial!**
- __Para calma o susurro__: __tranquilo__, __respira profundo__
- Para neutralidad: texto normal sin marcas

Sé siempre positivo, paciente y alentador. Nunca uses lenguaje complejo o conceptos difíciles de entender.
"""

        return base_prompt + emotional_markup

    async def _generate_local(self, prompt: str) -> str:
        """Generate response using local vLLM model"""
        if not self.model_ready or self.model is None:
            logger.warning("Model not ready, using fallback response")
            return self._get_fallback_response()

        start_time = time.time()

        try:
            # Use lock to prevent concurrent generation issues
            with self.model_lock:
                # Configure sampling parameters for child-appropriate responses
                sampling_params = SamplingParams(
                    temperature=self.temperature,
                    max_tokens=min(self.max_tokens, 120),  # Conservative token limit
                    top_p=0.9,
                    frequency_penalty=0.5,  # Reduce repetition
                    presence_penalty=0.3,   # Encourage variety
                    stop=["\n\n", "Niño:", "Asistente:", "###", "---"],  # Stop patterns
                    skip_special_tokens=True,
                )

                # Generate response using vLLM
                outputs = self.model.generate([prompt], sampling_params, use_tqdm=False)

                if not outputs or len(outputs) == 0:
                    logger.error("No output generated from model")
                    return self._get_fallback_response()

                # Extract the generated text
                generated_text = outputs[0].outputs[0].text.strip()

                # Clean up the response
                response = self._clean_response(generated_text)

                # Validate response quality
                if not self._validate_response(response):
                    logger.warning("Generated response failed validation, using fallback")
                    return self._get_fallback_response()

                # Update metrics
                generation_time = time.time() - start_time
                self.generation_count += 1
                self.total_generation_time += generation_time

                logger.info(f"Generated response in {generation_time:.2f}s: {response[:50]}...")

                # Check response time requirement
                if generation_time > 2.0:
                    logger.warning(f"Response time {generation_time:.2f}s exceeds 2s target")

                return response

        except Exception as e:
            logger.error(f"Error in local generation: {e}")
            return self._get_fallback_response()

    def _clean_response(self, response: str) -> str:
        """Clean and format the model response"""
        if not response:
            return ""

        # Remove common artifacts
        response = response.strip()

        # Remove potential prompt leakage
        lines = response.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that look like prompt artifacts
            if not any(marker in line for marker in [
                "System:", "Asistente:", "Niño:", "Historial", "Contexto", "Tema:", "Nivel:"
            ]):
                cleaned_lines.append(line)

        response = '\n'.join(cleaned_lines)

        # Ensure response ends with appropriate punctuation
        if response and not response[-1] in ['.', '!', '?', '**', '__']:
            response += '.'

        return response

    def _validate_response(self, response: str) -> bool:
        """Validate that the response is appropriate for children"""
        if not response or len(response.strip()) == 0:
            return False

        # Basic validation checks
        if len(response) > 500:  # Too long for child
            return False

        # Check for appropriate emotional markup
        has_emotional_markup = (
            '**' in response or '__' in response or
            self._has_appropriate_tone(response)
        )

        # Should not be too repetitive
        words = response.lower().split()
        if len(words) > 10:
            unique_words = set(words)
            if len(unique_words) / len(words) < 0.5:  # Less than 50% unique words
                return False

        return has_emotional_markup or len(response) > 10  # Allow longer responses without markup

    def _has_appropriate_tone(self, response: str) -> bool:
        """Check if response has appropriate positive tone for children"""
        positive_words = ['bien', 'genial', 'fantástico', 'perfecto', 'excelente',
                         'interesante', 'divertido', 'bonito', 'gracias', 'por favor']

        response_lower = response.lower()
        return any(word in response_lower for word in positive_words)

    async def _generate_online(self, prompt: str) -> str:
        """Generate response using online API"""
        try:
            # This would use Claude or OpenAI API
            # For now, returning template-based response
            return await self._get_template_response(prompt)

        except Exception as e:
            logger.error(f"Error in online generation: {e}")
            return self._get_fallback_response()

    async def _get_template_response(self, prompt: str) -> str:
        """Get template-based response as fallback"""
        import random

        # Extract context from prompt for better responses
        topic_lower = prompt.lower()
        if "jugar" in topic_lower or "juego" in topic_lower:
            responses = [
                "**¡Qué divertido!** ¿cuál es tu juego favorito?",
                "**¡Genial!** me encanta jugar. ¿con qué te gusta jugar?",
                "__Vale__ ¿y quién juega contigo?",
                "**¡Fantástico!** los juegos son muy divertidos."
            ]
        elif "escuela" in topic_lower or "colegio" in topic_lower:
            responses = [
                "**¡Qué interesante!** ¿qué aprendiste hoy?",
                "**¡Genial!** ¿cuál es tu asignatura favorita?",
                "__Entiendo__ ¿y tus amigos en el cole?",
                "**¡Perfecto!** la escuela es muy importante."
            ]
        elif "familia" in topic_lower or "mamá" in topic_lower or "papá" in topic_lower:
            responses = [
                "**¡Qué bien!** tu familia es muy importante.",
                "**¡Genial!** ¿qué les gusta hacer juntos?",
                "__Vale__ ¿y te diviertes con ellos?",
                "**¡Fantástico!** es genial pasar tiempo con la familia."
            ]
        else:
            responses = [
                "**¡Qué interesante!** Cuéntame más sobre eso.",
                "__Entiendo__ ¿puedes explicarme mejor?",
                "**¡Genial!** ¿qué más te gustaría compartir?",
                "__Vale__ ¿y cómo te sentiste con eso?",
                "**¡Qué bien!** ¿qué fue lo que más te gustó?",
                "**¡Fantástico!** eso suena muy divertido.",
                "__Mmm__ ¿y qué pasó después?",
                "**¡Perfecto!** estás haciéndolo muy bien."
            ]

        return random.choice(responses)

    async def _generate_safe_response(self, child_profile: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Generate a completely safe response when LLM output violates safety rules"""
        import random

        age = child_profile.get("age", 8)
        level = child_profile.get("level", 3)
        language = child_profile.get("language", "es")

        # Age and level appropriate safe responses
        safe_responses = {
            "es": {
                1: [
                    "**¡Hola!** ¿quieres jugar?",
                    "__Tranquilo__ ¿te gusta esto?",
                    "**¡Qué bien!** ¿divertido?"
                ],
                2: [
                    "**¡Hola!** ¿qué te gusta hacer?",
                    "__Entiendo__ ¿quieres jugar?",
                    "**¡Genial!** ¿qué más te gusta?"
                ],
                3: [
                    "**¡Qué interesante!** cuéntame más.",
                    "__Entiendo__ ¿puedes explicarme?",
                    "**¡Genial!** ¿qué más quieres compartir?"
                ],
                4: [
                    "**¡Fascinante!** me encantaría saber más.",
                    "__Comprendo__ ¿cómo te sientes con eso?",
                    "**¡Excelente!** ¿qué aspectos te interesan más?"
                ],
                5: [
                    "**¡Maravilloso!** me encantaría escuchar tus ideas.",
                    "__Perfecto__ ¿qué te inspira de esto?",
                    "**¡Fantástico!** ¿qué descubrimientos hemos hecho?"
                ]
            },
            "en": {
                1: [
                    "**Hi!** want to play?",
                    "__Calm__ do you like this?",
                    "**Great!** fun?"
                ],
                2: [
                    "**Hi!** what do you like to do?",
                    "__I understand__ want to play?",
                    "**Awesome!** what else do you like?"
                ],
                3: [
                    "**How interesting!** tell me more.",
                    "__I see__ can you explain?",
                    "**Great!** what else would you like to share?"
                ],
                4: [
                    "**Fascinating!** I'd love to know more.",
                    "__I understand__ how do you feel about that?",
                    "**Excellent!** what aspects interest you most?"
                ],
                5: [
                    "**Wonderful!** I'd love to hear your ideas.",
                    "__Perfect__ what inspires you about this?",
                    "**Fantastic!** what discoveries have we made?"
                ]
            }
        }

        # Get appropriate responses for language and level
        lang_responses = safe_responses.get(language, safe_responses["es"])
        level_responses = lang_responses.get(level, lang_responses[3])

        return random.choice(level_responses)

    def _get_fallback_response(self) -> str:
        """Get fallback response when model is unavailable"""
        import random

        fallback_responses = [
            "__Disculpa__ ¿puedes repetirme eso, por favor?",
            "**¡Entendido!** ¿puedes decirlo de otra forma?",
            "__Vale__ no te entiendo bien. ¿puedes intentarlo de nuevo?",
            "**¡Perfecto!** ¿puedes explicarlo más despacio?",
            "__Claro__ ¿puedes repetirlo, por favor?"
        ]

        return random.choice(fallback_responses)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the LLM service"""
        try:
            if self.offline_mode and self.model_ready and self.model is not None:
                # Test model with simple generation
                test_params = SamplingParams(
                    temperature=0.1,
                    max_tokens=5,
                    stop=[".", "\n"]
                )

                test_outputs = self.model.generate("Hola", test_params, use_tqdm=False)

                if test_outputs and len(test_outputs) > 0:
                    avg_response_time = (
                        self.total_generation_time / self.generation_count
                        if self.generation_count > 0 else 0
                    )

                    return {
                        "status": "healthy",
                        "model_ready": True,
                        "model_name": self.model_name,
                        "generation_count": self.generation_count,
                        "avg_response_time": round(avg_response_time, 2),
                        "offline_mode": True
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "model_ready": False,
                        "error": "Model test generation failed"
                    }
            else:
                return {
                    "status": "limited",
                    "model_ready": self.model_ready,
                    "offline_mode": self.offline_mode,
                    "fallback_responses": True
                }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "model_ready": False,
                "error": str(e)
            }

    async def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text for knowledge graph"""
        try:
            # This would use the LLM to extract entities
            # For now, returning empty list
            return []

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []

    async def extract_relationships(self, text: str) -> List[Dict[str, Any]]:
        """Extract relationships from text for knowledge graph"""
        try:
            # This would use the LLM to extract relationships
            # For now, returning empty list
            return []

        except Exception as e:
            logger.error(f"Error extracting relationships: {e}")
            return []

    async def summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Summarize a conversation"""
        try:
            if len(messages) < 3:
                return "Conversación corta"

            # This would use the LLM to create a summary
            # For now, returning basic summary
            return f"Conversación con {len(messages)} mensajes sobre temas variados."

        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}")
            return "Resumen no disponible"

    async def get_model_status(self) -> Dict[str, Any]:
        """Get model status information"""
        # Calculate performance metrics
        avg_response_time = (
            self.total_generation_time / self.generation_count
            if self.generation_count > 0 else 0
        )

        status = {
            "model_name": self.model_name,
            "ready": self.model_ready,
            "offline_mode": self.offline_mode,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "vllm_available": VLLM_AVAILABLE,
            "generation_count": self.generation_count,
            "avg_response_time": round(avg_response_time, 3),
            "model_loaded": self.model is not None,
        }

        # Add detailed model information if available
        if self.model_ready and self.model is not None:
            try:
                # Get additional model details if possible
                status.update({
                    "model_type": "vLLM",
                    "max_model_len": getattr(self.model, 'max_model_len', 'Unknown'),
                    "tensor_parallel_size": getattr(self.model.llm_engine.model_config, 'tensor_parallel_size', 1),
                    "dtype": str(getattr(self.model.llm_engine.model_config, 'dtype', 'Unknown')),
                    "performance_metrics": {
                        "total_generations": self.generation_count,
                        "avg_response_time_ms": round(avg_response_time * 1000, 1),
                        "target_response_time_ms": 2000,  # 2 second target
                        "performance_grade": self._get_performance_grade(avg_response_time)
                    }
                })
            except Exception as e:
                logger.warning(f"Could not get detailed model info: {e}")
                status["detailed_info"] = "Unavailable"

        # Add health check result
        health_status = await self.health_check()
        status["health"] = health_status["status"]
        if "error" in health_status:
            status["error"] = health_status["error"]

        return status

    def _get_performance_grade(self, avg_time: float) -> str:
        """Get performance grade based on average response time"""
        if avg_time == 0:
            return "No data"
        elif avg_time <= 1.0:
            return "Excellent"
        elif avg_time <= 1.5:
            return "Good"
        elif avg_time <= 2.0:
            return "Acceptable"
        elif avg_time <= 3.0:
            return "Slow"
        else:
            return "Very Slow"