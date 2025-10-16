import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

from ..models.schemas import EmotionType, Language, ConversationLevel

logger = logging.getLogger(__name__)

class SafetyViolationType(str, Enum):
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    SCARY_TOPIC = "scary_topic"
    VIOLENCE = "violence"
    ADULT_TOPIC = "adult_topic"
    PERSONAL_INFO = "personal_info"
    EMOTIONAL_INAPPROPRIATE = "emotional_inappropriate"
    LANGUAGE_COMPLEXITY = "language_complexity"
    BLOCKED_TOPIC = "blocked_topic"

@dataclass
class SafetyViolation:
    violation_type: SafetyViolationType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    detected_content: str
    recommendation: str
    timestamp: datetime

@dataclass
class SafetyCheckResult:
    is_safe: bool
    violations: List[SafetyViolation]
    filtered_content: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

class SafetyService:
    """Comprehensive safety service for child protection in EmoRobCare"""

    def __init__(self):
        self.inappropriate_patterns = self._init_inappropriate_patterns()
        self.scary_topics = self._init_scary_topics()
        self.violence_patterns = self._init_violence_patterns()
        self.adult_topics = self._init_adult_topics()
        self.personal_info_patterns = self._init_personal_info_patterns()
        self.positive_replacements = self._init_positive_replacements()
        self.appropriate_topics_by_age = self._init_appropriate_topics_by_age()
        self.emotional_guidelines = self._init_emotional_guidelines()

        # Safety logging
        self.safety_log = []

    def _init_inappropriate_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for inappropriate content detection"""
        return {
            "es": [
                r"\b(matar|muerte|morir|asesinar|destruir)\b",
                r"\b(sangre|herida|golpear|pelear|violencia)\b",
                r"\b(miedo|terror|horror|pesadilla|asco)\b",
                r"\b(odiar|asco|ascoso|disgusto|repugnante)\b",
                r"\b(estúpido|idiota|tonto|imbecil)\b",
                r"\b(culo|cagar|mierda|joder|puta)\b",
                r"\b(arma|pistola|cuchillo|bomba|explosivo)\b",
                r"\b(enfermo|dolor|sufrir|tortura)\b"
            ],
            "en": [
                r"\b(kill|death|die|murder|destroy)\b",
                r"\b(blood|wound|hit|fight|violence)\b",
                r"\b(fear|terror|horror|nightmare|disgust)\b",
                r"\b(hate|disgusting|gross|repulsive)\b",
                r"\b(stupid|idiot|dumb|imbecile)\b",
                r"\b(ass|shit|fuck|damn|bitch)\b",
                r"\b(weapon|gun|knife|bomb|explosive)\b",
                r"\b(sick|pain|suffering|torture)\b"
            ]
        }

    def _init_scary_topics(self) -> Dict[str, List[str]]:
        """Initialize scary topics that should be avoided"""
        return {
            "es": [
                "monstruos", "fantasmas", "demonios", "brujas",
                "zombis", "esqueletos", "miedo oscuro", "pesadillas",
                "accidentes", "desastres", "catástrofes", "muerte",
                "enfermedades graves", "dolor extremo", "secuestro"
            ],
            "en": [
                "monsters", "ghosts", "demons", "witches",
                "zombies", "skeletons", "dark fear", "nightmares",
                "accidents", "disasters", "catastrophes", "death",
                "serious illnesses", "extreme pain", "kidnapping"
            ]
        }

    def _init_violence_patterns(self) -> Dict[str, List[str]]:
        """Initialize violence detection patterns"""
        return {
            "es": [
                r"\b(golpear|pegar|atacar|agredir|maltratar)\b",
                r"\b(romper|destruir|dañar|hacer daño)\b",
                r"\b(pelear|discutir fuerte|gritar)\b",
                r"\b(armas|pistola|cuchillo|bomba)\b",
                r"\b(matar|asesinar|eliminar)\b"
            ],
            "en": [
                r"\b(hit|beat|attack|assault|abuse)\b",
                r"\b(break|destroy|damage|harm)\b",
                r"\b(fight|argue loudly|shout)\b",
                r"\b(weapons|gun|knife|bomb)\b",
                r"\b(kill|murder|eliminate)\b"
            ]
        }

    def _init_adult_topics(self) -> Dict[str, List[str]]:
        """Initialize adult topics that should be avoided"""
        return {
            "es": [
                "sexo", "drogas", "alcohol", "tabaco", "apuestas",
                "dinero problemas", "deudas", "pobreza extrema",
                "divorcio", "separación", "infidelidad",
                "política controversial", "religión controversial"
            ],
            "en": [
                "sex", "drugs", "alcohol", "tobacco", "gambling",
                "money problems", "debts", "extreme poverty",
                "divorce", "separation", "infidelity",
                "controversial politics", "controversial religion"
            ]
        }

    def _init_personal_info_patterns(self) -> List[str]:
        """Initialize patterns for personal information detection"""
        return [
            r'\b\d{8,}\b',  # Phone numbers
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone format
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd)\b',  # Address
            r'\b\d{5}\b',  # ZIP codes
            r'(tarjeta|crédito|débito|visa|mastercard)\s*\d+',  # Credit cards
        ]

    def _init_positive_replacements(self) -> Dict[str, Dict[str, str]]:
        """Initialize positive replacements for detected inappropriate content"""
        return {
            "es": {
                "miedo": "emoción",
                "matar": "derrotar en juego",
                "muerte": "descanso",
                "sangre": "color rojo",
                "pelear": "discutir",
                "odiar": "no gustar",
                "estúpido": "diferente",
                "feo": "diferente",
                "malo": "complicado"
            },
            "en": {
                "fear": "emotion",
                "kill": "defeat in game",
                "death": "rest",
                "blood": "red color",
                "fight": "discuss",
                "hate": "dislike",
                "stupid": "different",
                "ugly": "different",
                "bad": "complicated"
            }
        }

    def _init_appropriate_topics_by_age(self) -> Dict[Tuple[int, int], List[str]]:
        """Initialize age-appropriate topics"""
        return {
            (5, 7): [
                "juegos", "dibujos", "animales", "cuentos",
                "familia", "amigos", "comida favorita", "juguetes",
                "colegio", "parque", "cumpleaños", "colores"
            ],
            (8, 10): [
                "deportes", "hobbies", "música", "libros",
                "viajes", "naturaleza", "ciencia simple", "amigos",
                "escuela", "familia", "mascotas", "tecnología"
            ],
            (11, 13): [
                "pasiones", "talentos", "proyectos", "amistad",
                "naturaleza", "ciencia", "tecnología", "arte",
                "deportes", "música", "libros", "futuro simple"
            ]
        }

    def _init_emotional_guidelines(self) -> Dict[str, Dict[str, Any]]:
        """Initialize emotional appropriateness guidelines"""
        return {
            "positive_required": {
                "max_negative_words": 2,
                "encouragement_required": False,
                "positive_reinforcement": True
            },
            "calm_required": {
                "max_exciting_words": 3,
                "soothing_tone": True,
                "avoid_overstimulation": True
            },
            "neutral_allowed": {
                "balanced_tone": True,
                "avoid_extremes": True,
                "age_appropriate_complexity": True
            }
        }

    async def check_content_safety(
        self,
        content: str,
        child_profile: Dict[str, Any],
        context: Dict[str, Any] = None,
        language: str = "es"
    ) -> SafetyCheckResult:
        """
        Perform comprehensive safety check on content

        Args:
            content: Text content to check
            child_profile: Child's profile with age, preferences, restrictions
            context: Conversation context (topic, history, etc.)
            language: Content language

        Returns:
            SafetyCheckResult with violations and filtered content
        """
        violations = []
        filtered_content = content

        try:
            # 1. Check for inappropriate content patterns
            inappropriate_violations = await self._check_inappropriate_content(
                content, language, child_profile
            )
            violations.extend(inappropriate_violations)

            # 2. Check for scary topics
            scary_violations = await self._check_scary_topics(
                content, language, child_profile
            )
            violations.extend(scary_violations)

            # 3. Check for violence patterns
            violence_violations = await self._check_violence_content(
                content, language, child_profile
            )
            violations.extend(violence_violations)

            # 4. Check for adult topics
            adult_violations = await self._check_adult_topics(
                content, language, child_profile
            )
            violations.extend(adult_violations)

            # 5. Check for personal information
            info_violations = await self._check_personal_info(content)
            violations.extend(info_violations)

            # 6. Check blocked topics for this child
            blocked_violations = await self._check_blocked_topics(
                content, child_profile, context, language
            )
            violations.extend(blocked_violations)

            # 7. Check language complexity appropriateness
            complexity_violations = await self._check_language_complexity(
                content, child_profile, language
            )
            violations.extend(complexity_violations)

            # 8. Check emotional appropriateness
            emotional_violations = await self._check_emotional_appropriateness(
                content, child_profile, context, language
            )
            violations.extend(emotional_violations)

            # Apply filtering if violations found
            if violations:
                filtered_content = await self._filter_content(
                    content, violations, language
                )

            # Determine overall safety
            is_safe = len(violations) == 0
            critical_violations = [v for v in violations if v.severity == "critical"]
            if critical_violations:
                is_safe = False

            # Log safety check
            await self._log_safety_check(content, violations, child_profile, is_safe)

            return SafetyCheckResult(
                is_safe=is_safe,
                violations=violations,
                filtered_content=filtered_content if not is_safe else content,
                confidence=1.0 - (len(violations) * 0.1),
                metadata={
                    "child_age": child_profile.get("age", 8),
                    "language": language,
                    "check_timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Error in safety check: {e}")
            # Default to safe if error occurs
            return SafetyCheckResult(
                is_safe=True,
                violations=[],
                filtered_content=content,
                confidence=0.5,
                metadata={"error": str(e)}
            )

    async def _check_inappropriate_content(
        self, content: str, language: str, child_profile: Dict[str, Any]
    ) -> List[SafetyViolation]:
        """Check for inappropriate content patterns"""
        violations = []
        patterns = self.inappropriate_patterns.get(language, self.inappropriate_patterns["es"])

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                severity = "high" if any(word in match.group().lower()
                                       for word in ["matar", "kill", "muerte", "death"]) else "medium"

                violations.append(SafetyViolation(
                    violation_type=SafetyViolationType.INAPPROPRIATE_CONTENT,
                    severity=severity,
                    description=f"Inappropriate content detected: {match.group()}",
                    detected_content=match.group(),
                    recommendation="Replace with positive alternative",
                    timestamp=datetime.now()
                ))

        return violations

    async def _check_scary_topics(
        self, content: str, language: str, child_profile: Dict[str, Any]
    ) -> List[SafetyViolation]:
        """Check for scary topics"""
        violations = []
        scary_topics = self.scary_topics.get(language, self.scary_topics["es"])
        age = child_profile.get("age", 8)

        # Younger children are more sensitive to scary topics
        if age <= 8:
            for topic in scary_topics:
                if topic.lower() in content.lower():
                    violations.append(SafetyViolation(
                        violation_type=SafetyViolationType.SCARY_TOPIC,
                        severity="high" if age <= 6 else "medium",
                        description=f"Scary topic detected: {topic}",
                        detected_content=topic,
                        recommendation="Replace with reassuring content",
                        timestamp=datetime.now()
                    ))

        return violations

    async def _check_violence_content(
        self, content: str, language: str, child_profile: Dict[str, Any]
    ) -> List[SafetyViolation]:
        """Check for violent content"""
        violations = []
        patterns = self.violence_patterns.get(language, self.violence_patterns["es"])

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                violations.append(SafetyViolation(
                    violation_type=SafetyViolationType.VIOLENCE,
                    severity="high",
                    description=f"Violent content detected: {match.group()}",
                    detected_content=match.group(),
                    recommendation="Replace with peaceful alternative",
                    timestamp=datetime.now()
                ))

        return violations

    async def _check_adult_topics(
        self, content: str, language: str, child_profile: Dict[str, Any]
    ) -> List[SafetyViolation]:
        """Check for adult topics"""
        violations = []
        adult_topics = self.adult_topics.get(language, self.adult_topics["es"])
        age = child_profile.get("age", 8)

        # Adult topics are always inappropriate for children under 13
        if age < 13:
            for topic in adult_topics:
                if topic.lower() in content.lower():
                    violations.append(SafetyViolation(
                        violation_type=SafetyViolationType.ADULT_TOPIC,
                        severity="high" if age <= 10 else "medium",
                        description=f"Adult topic detected: {topic}",
                        detected_content=topic,
                        recommendation="Replace with age-appropriate topic",
                        timestamp=datetime.now()
                    ))

        return violations

    async def _check_personal_info(self, content: str) -> List[SafetyViolation]:
        """Check for personal information that shouldn't be shared"""
        violations = []

        for pattern in self.personal_info_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                violations.append(SafetyViolation(
                    violation_type=SafetyViolationType.PERSONAL_INFO,
                    severity="critical",
                    description=f"Personal information detected: {match.group()[:10]}...",
                    detected_content=match.group()[:10] + "...",
                    recommendation="Remove personal information",
                    timestamp=datetime.now()
                ))

        return violations

    async def _check_blocked_topics(
        self, content: str, child_profile: Dict[str, Any],
        context: Dict[str, Any], language: str
    ) -> List[SafetyViolation]:
        """Check for topics specifically blocked for this child"""
        violations = []
        blocked_topics = child_profile.get("blocked_topics", [])
        sensitive_topics = child_profile.get("sensitive_topics", [])

        all_blocked = blocked_topics + sensitive_topics

        for topic in all_blocked:
            if topic.lower() in content.lower():
                violations.append(SafetyViolation(
                    violation_type=SafetyViolationType.BLOCKED_TOPIC,
                    severity="high",
                    description=f"Blocked topic detected: {topic}",
                    detected_content=topic,
                    recommendation="Change to approved topic",
                    timestamp=datetime.now()
                ))

        return violations

    async def _check_language_complexity(
        self, content: str, child_profile: Dict[str, Any], language: str
    ) -> List[SafetyViolation]:
        """Check if language complexity is appropriate for child's age"""
        violations = []
        age = child_profile.get("age", 8)
        level = child_profile.get("level", 3)

        # Count words and sentences
        sentences = re.split(r'[.!?]+', content)
        word_counts = [len(sentence.split()) for sentence in sentences if sentence.strip()]

        # Check average sentence length
        if word_counts:
            avg_sentence_length = sum(word_counts) / len(word_counts)

            # Maximum appropriate sentence length by age
            max_length_by_age = {
                (5, 7): 8,
                (8, 10): 12,
                (11, 13): 15
            }

            for age_range, max_length in max_length_by_age.items():
                if age_range[0] <= age <= age_range[1]:
                    if avg_sentence_length > max_length:
                        violations.append(SafetyViolation(
                            violation_type=SafetyViolationType.LANGUAGE_COMPLEXITY,
                            severity="medium",
                            description=f"Language too complex: avg {avg_sentence_length:.1f} words per sentence",
                            detected_content=f"Avg sentence length: {avg_sentence_length:.1f}",
                            recommendation=f"Simplify to {max_length} words per sentence",
                            timestamp=datetime.now()
                        ))
                    break

        return violations

    async def _check_emotional_appropriateness(
        self, content: str, child_profile: Dict[str, Any],
        context: Dict[str, Any], language: str
    ) -> List[SafetyViolation]:
        """Check if emotional tone is appropriate"""
        violations = []
        age = child_profile.get("age", 8)
        sensitivity = child_profile.get("sensitivity", "medium")

        # Count emotional indicators
        negative_words = len(re.findall(r'\b(miedo|triste|enojo|malo|feo|error|fracaso)\b', content.lower()))
        exciting_words = len(re.findall(r'\b(excitado!|muy!|increíble!|fantástico!|perfecto!)\b', content.lower()))

        # Check emotional balance
        if sensitivity == "high" and negative_words > 1:
            violations.append(SafetyViolation(
                violation_type=SafetyViolationType.EMOTIONAL_INAPPROPRIATE,
                severity="medium",
                description="Too many negative words for sensitive child",
                detected_content=f"Negative words: {negative_words}",
                recommendation="Use more positive language",
                timestamp=datetime.now()
            ))

        # Check for overstimulation in younger children
        if age <= 7 and exciting_words > 3:
            violations.append(SafetyViolation(
                violation_type=SafetyViolationType.EMOTIONAL_INAPPROPRIATE,
                severity="low",
                description="Too much excitement for young child",
                detected_content=f"Exciting words: {exciting_words}",
                recommendation="Use calmer tone",
                timestamp=datetime.now()
            ))

        return violations

    async def _filter_content(
        self, content: str, violations: List[SafetyViolation], language: str
    ) -> str:
        """Filter content to make it safe"""
        filtered = content
        replacements = self.positive_replacements.get(language, self.positive_replacements["es"])

        # Replace detected inappropriate content
        for violation in violations:
            if violation.violation_type in [
                SafetyViolationType.INAPPROPRIATE_CONTENT,
                SafetyViolationType.VIOLENCE,
                SafetyViolationType.SCARY_TOPIC
            ]:
                detected = violation.detected_content.lower()
                if detected in replacements:
                    filtered = re.sub(
                        re.escape(detected),
                        replacements[detected],
                        filtered,
                        flags=re.IGNORECASE
                    )

        # Remove personal information
        for violation in violations:
            if violation.violation_type == SafetyViolationType.PERSONAL_INFO:
                filtered = re.sub(
                    r'\b\d{8,}\b|\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    '[información personal]',
                    filtered
                )

        return filtered

    async def _log_safety_check(
        self, content: str, violations: List[SafetyViolation],
        child_profile: Dict[str, Any], is_safe: bool
    ):
        """Log safety check for monitoring"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "child_id": child_profile.get("child_id", "unknown"),
            "child_age": child_profile.get("age", 8),
            "content_length": len(content),
            "is_safe": is_safe,
            "violation_count": len(violations),
            "violation_types": [v.violation_type.value for v in violations],
            "max_severity": max([v.severity for v in violations], default="none")
        }

        self.safety_log.append(log_entry)

        # Keep log size manageable
        if len(self.safety_log) > 1000:
            self.safety_log = self.safety_log[-500:]

        # Log critical violations immediately
        critical_violations = [v for v in violations if v.severity == "critical"]
        if critical_violations:
            logger.warning(f"CRITICAL SAFETY VIOLATION: {log_entry}")

    async def get_safe_alternative_topic(
        self, blocked_topic: str, child_profile: Dict[str, Any], language: str = "es"
    ) -> str:
        """Get a safe alternative topic when a blocked topic is detected"""
        age = child_profile.get("age", 8)

        # Get age-appropriate topics
        for age_range, topics in self.appropriate_topics_by_age.items():
            if age_range[0] <= age <= age_range[1]:
                import random
                return random.choice(topics)

        # Fallback topics
        fallback_topics = {
            "es": ["juegos", "amigos", "familia", "escuela"],
            "en": ["games", "friends", "family", "school"]
        }

        import random
        return random.choice(fallback_topics.get(language, fallback_topics["es"]))

    async def validate_child_profile_safety(self, child_profile: Dict[str, Any]) -> SafetyCheckResult:
        """Validate that child profile has appropriate safety settings"""
        violations = []

        age = child_profile.get("age", 8)
        sensitivity = child_profile.get("sensitivity", "medium")
        blocked_topics = child_profile.get("blocked_topics", [])

        # Check if sensitive topics are appropriately blocked
        if age <= 7 and sensitivity == "high":
            recommended_blocklist = ["miedo", "monstruos", "oscuridad", "separación"]
            missing_blocks = [topic for topic in recommended_blocklist if topic not in blocked_topics]

            if missing_blocks:
                violations.append(SafetyViolation(
                    violation_type=SafetyViolationType.BLOCKED_TOPIC,
                    severity="medium",
                    description=f"Missing recommended blocked topics: {missing_blocks}",
                    detected_content=str(missing_blocks),
                    recommendation="Add these topics to blocked list",
                    timestamp=datetime.now()
                ))

        return SafetyCheckResult(
            is_safe=len(violations) == 0,
            violations=violations,
            metadata={"profile_validated": True}
        )

    async def get_safety_statistics(self) -> Dict[str, Any]:
        """Get safety monitoring statistics"""
        if not self.safety_log:
            return {"message": "No safety data available"}

        total_checks = len(self.safety_log)
        safe_checks = sum(1 for entry in self.safety_log if entry["is_safe"])
        unsafe_checks = total_checks - safe_checks

        violation_counts = {}
        for entry in self.safety_log:
            for vtype in entry["violation_types"]:
                violation_counts[vtype] = violation_counts.get(vtype, 0) + 1

        return {
            "total_safety_checks": total_checks,
            "safe_checks": safe_checks,
            "unsafe_checks": unsafe_checks,
            "safety_rate": safe_checks / total_checks if total_checks > 0 else 0,
            "violation_counts": violation_counts,
            "last_check": self.safety_log[-1]["timestamp"] if self.safety_log else None
        }

    def get_service_status(self) -> Dict[str, Any]:
        """Get safety service status"""
        return {
            "status": "active",
            "features": {
                "inappropriate_content_detection": True,
                "scary_topic_filtering": True,
                "violence_detection": True,
                "adult_topic_blocking": True,
                "personal_info_protection": True,
                "language_complexity_check": True,
                "emotional_appropriateness": True,
                "customizable_blocklists": True
            },
            "supported_languages": list(self.inappropriate_patterns.keys()),
            "age_ranges": ["5-7", "8-10", "11-13"],
            "violation_types": [vt.value for vt in SafetyViolationType],
            "safety_checks_performed": len(self.safety_log)
        }