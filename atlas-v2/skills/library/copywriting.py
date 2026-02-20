"""
Agentic AGI Copywriting Master Protocol

High-converting, psychologically targeted direct-response copywriting.
Deploys NLP and behavioral psychology to maximize conversion.

AUTO-TRIGGER CONDITIONS:
- User mentions: respond, reply, email, write, draft, message, copy, pitch, ad, landing
- Context contains: prospect, client, customer, audience, convert, sell, persuade
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import re
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# PART 1: ALGORITHMIC ERADICATION (THE NEGATIVE LIST)
# =============================================================================

FORBIDDEN_LEXICON = {
    # Abstract/Diluted Nouns
    "nouns": {
        "tapestry", "realm", "landscape", "testament", "multitude", "plethora",
        "arena", "cornerstone", "paradigm", "synergy", "complexities",
        "treasure trove", "overarching", "bandwidth", "efficiency",
        "transformation", "integration",
    },
    # Actionless Verbs
    "verbs": {
        "delve", "utilize", "leverage", "foster", "align", "augment",
        "underscore", "navigate", "unlock", "unleash", "orchestrate",
        "embark", "captivate", "elevate", "resonate", "facilitate",
        "maximize", "empower",
    },
    # Padding Adjectives
    "adjectives": {
        "robust", "crucial", "essential", "dynamic", "transformative",
        "seamless", "paramount", "cutting-edge", "ever-evolving", "vibrant",
        "adept", "invaluable", "vital", "comprehensive", "commendable",
        "bespoke", "tailored",
    },
    # Transitional Adverbs
    "adverbs": {
        "furthermore", "moreover", "consequently", "subsequently",
        "ultimately", "undeniably", "meticulously", "dynamically",
        "specifically", "generally speaking", "accordingly", "arguably",
        "nevertheless", "notwithstanding",
    },
}

FORBIDDEN_PHRASES = [
    "In today's fast-paced digital world",
    "In an ever-evolving landscape",
    "Welcome to the world of",
    "As we navigate the complexities of",
    "It is important to note that",
    "While X is important, Y is also crucial",
    "To put it simply",
    "Chaos into clarity",
    "The elephant in the room",
    "In conclusion",
    "At the end of the day",
    "Only time will tell",
]

# Syntactic patterns to avoid
FORBIDDEN_PATTERNS = [
    r"It's not just about .+\. It's about",  # Contrastive negation
    r"This isn't just .+\. This is",
    r"\w+\. \w+\. \w+\.",  # Forced triads (Focused. Aligned. Measurable.)
]


# =============================================================================
# PART 2: NLP BEHAVIORAL TYPOLOGIES & META-PROGRAMS
# =============================================================================

class MotivationDirection(str, Enum):
    TOWARD = "toward"      # 40% - Goals, acquisition, pleasure
    AWAY_FROM = "away"     # 40% - Avoid pain, risk, discomfort


class FrameOfReference(str, Enum):
    INTERNAL = "internal"  # 40% - Trust gut, resist external pressure
    EXTERNAL = "external"  # 40% - Need validation, social proof


class SortingFilter(str, Enum):
    SAMENESS = "sameness"           # 5-10% - Exactly identical
    SAMENESS_EXCEPTION = "same_ex"  # 55% - Similar + improvement
    DIFFERENCE_EXCEPTION = "diff_ex"  # 25% - Novel first, then ground
    DIFFERENCE = "difference"       # 5-10% - Revolution, disruption


class ChunkSize(str, Enum):
    GLOBAL = "global"      # 60% - Big picture, conceptual
    SPECIFIC = "specific"  # 15% - Granular, step-by-step


class RepSystem(str, Enum):
    VISUAL = "visual"          # "Picture, envision, clear sight"
    AUDITORY = "auditory"      # "Hear, listen, sounds right"
    KINESTHETIC = "kinesthetic"  # "Feel, touch, experience"
    DERIVED = "derived"        # Logical, data-driven


class SpiralLevel(str, Enum):
    RED = "red"        # Level 3 - Impulsive/Power
    BLUE = "blue"      # Level 4 - Conformist/Order
    ORANGE = "orange"  # Level 5 - Success/Achiever
    GREEN = "green"    # Level 6 - Community/Humanistic
    YELLOW = "yellow"  # Level 7 - Systemic Thinker


class CoreMotive(str, Enum):
    POWER = "power"            # Leadership, dominance, authority
    ACHIEVEMENT = "achievement"  # Growth, mastery, efficiency
    AFFILIATION = "affiliation"  # Community, belonging, shared values


@dataclass
class AudienceProfile:
    """Target audience psychological profile"""
    motivation: MotivationDirection = MotivationDirection.TOWARD
    reference: FrameOfReference = FrameOfReference.EXTERNAL
    sorting: SortingFilter = SortingFilter.SAMENESS_EXCEPTION
    chunk_size: ChunkSize = ChunkSize.GLOBAL
    rep_system: RepSystem = RepSystem.VISUAL
    spiral_level: SpiralLevel = SpiralLevel.ORANGE
    core_motive: CoreMotive = CoreMotive.ACHIEVEMENT


# Trigger words by meta-program
TRIGGER_WORDS = {
    MotivationDirection.TOWARD: [
        "achieve", "gain", "secure", "build", "grow", "obtain", "expand",
        "acquire", "win", "succeed", "earn", "unlock",
    ],
    MotivationDirection.AWAY_FROM: [
        "avoid", "escape", "eliminate", "steer clear", "get rid of",
        "prevent", "stop", "protect", "shield", "guard",
    ],
    FrameOfReference.INTERNAL: [
        "only you can decide", "trust your instincts", "you evaluate",
        "your choice", "you know", "decide for yourself",
    ],
    FrameOfReference.EXTERNAL: [
        "research shows", "experts agree", "proven results", "the facts show",
        "studies confirm", "industry leaders", "testimonials",
    ],
    RepSystem.VISUAL: [
        "picture", "envision", "clear", "see", "vision", "imagine",
        "bright", "colorful", "perspective", "view", "look",
    ],
    RepSystem.AUDITORY: [
        "hear", "listen", "sounds", "tell", "resonate", "harmony",
        "tune", "voice", "ring", "click",
    ],
    RepSystem.KINESTHETIC: [
        "feel", "touch", "grasp", "handle", "solid", "concrete",
        "grounded", "firm", "smooth", "grip", "weight",
    ],
}

# Spiral Dynamics language
SPIRAL_LANGUAGE = {
    SpiralLevel.RED: [
        "dominate", "crush", "immediate power", "unapologetic",
        "take what's yours", "no mercy", "strength",
    ],
    SpiralLevel.BLUE: [
        "duty", "honor", "compliance", "proven system", "right thing",
        "tradition", "order", "discipline", "loyalty",
    ],
    SpiralLevel.ORANGE: [
        "ROI", "optimize", "strategic advantage", "science-backed",
        "outsmart", "efficiency", "results", "data-driven",
    ],
    SpiralLevel.GREEN: [
        "sustainability", "harmony", "inclusive", "sharing",
        "mutual growth", "community", "empathy", "together",
    ],
    SpiralLevel.YELLOW: [
        "functional integrity", "complex adaptive", "macro-perspective",
        "systemic", "integrated", "holistic", "emergent",
    ],
}


# =============================================================================
# PART 3: FRAMEWORKS
# =============================================================================

class Framework(str, Enum):
    AIDA = "aida"  # Attention, Interest, Desire, Action
    PAS = "pas"    # Problem, Agitate, Solution
    FAB = "fab"    # Features, Advantages, Benefits
    BAB = "bab"    # Before, After, Bridge
    PPPP = "pppp"  # Picture, Promise, Prove, Push


@dataclass
class CopyBrief:
    """Brief for copywriting generation"""
    content_type: str  # email, ad, landing, post, response
    objective: str     # What we want the reader to do
    audience: AudienceProfile
    product_service: str
    key_benefits: List[str]
    pain_points: List[str]
    framework: Framework = Framework.AIDA
    tone: str = "direct"
    max_length: Optional[int] = None


# =============================================================================
# COPYWRITING ENGINE
# =============================================================================

class CopywritingEngine:
    """
    Direct-response copywriting engine.

    Uses psychological profiling to generate high-converting copy
    while avoiding AI-detectable patterns.
    """

    def __init__(self):
        self.forbidden_all = set()
        for category in FORBIDDEN_LEXICON.values():
            self.forbidden_all.update(category)

    def detect_triggers(self, text: str) -> Set[str]:
        """Detect which triggers should auto-invoke this skill"""
        text_lower = text.lower()
        triggers = set()

        trigger_phrases = [
            "respond to", "reply to", "write", "draft", "email",
            "message", "copy", "pitch", "ad", "landing page",
            "post", "content", "prospect", "client", "customer",
            "convert", "sell", "persuade", "engage", "outreach",
        ]

        for phrase in trigger_phrases:
            if phrase in text_lower:
                triggers.add(phrase)

        return triggers

    def should_auto_trigger(self, text: str, context: Dict[str, Any] = None) -> bool:
        """Check if this skill should auto-trigger based on input"""
        triggers = self.detect_triggers(text)
        return len(triggers) > 0

    def analyze_audience(self, description: str) -> AudienceProfile:
        """Analyze audience description to build profile"""
        desc_lower = description.lower()
        profile = AudienceProfile()

        # Motivation detection
        if any(w in desc_lower for w in ["risk", "afraid", "worried", "avoid"]):
            profile.motivation = MotivationDirection.AWAY_FROM
        elif any(w in desc_lower for w in ["ambitious", "goal", "achieve", "grow"]):
            profile.motivation = MotivationDirection.TOWARD

        # Reference detection
        if any(w in desc_lower for w in ["data", "proof", "evidence", "testimonial"]):
            profile.reference = FrameOfReference.EXTERNAL
        elif any(w in desc_lower for w in ["intuitive", "gut", "independent"]):
            profile.reference = FrameOfReference.INTERNAL

        # Spiral level detection
        if any(w in desc_lower for w in ["executive", "ceo", "leader", "power"]):
            profile.spiral_level = SpiralLevel.RED
        elif any(w in desc_lower for w in ["traditional", "conservative", "compliance"]):
            profile.spiral_level = SpiralLevel.BLUE
        elif any(w in desc_lower for w in ["entrepreneur", "startup", "results"]):
            profile.spiral_level = SpiralLevel.ORANGE
        elif any(w in desc_lower for w in ["community", "social", "sustainable"]):
            profile.spiral_level = SpiralLevel.GREEN

        return profile

    def scrub_forbidden(self, text: str) -> str:
        """Remove forbidden AI-signature words and phrases"""
        result = text

        # Remove forbidden phrases
        for phrase in FORBIDDEN_PHRASES:
            result = re.sub(re.escape(phrase), "", result, flags=re.IGNORECASE)

        # Remove forbidden words
        for word in self.forbidden_all:
            # Word boundary replacement
            result = re.sub(
                rf'\b{re.escape(word)}\b',
                self._get_replacement(word),
                result,
                flags=re.IGNORECASE
            )

        # Remove forbidden patterns
        for pattern in FORBIDDEN_PATTERNS:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)

        return result.strip()

    def _get_replacement(self, word: str) -> str:
        """Get natural replacement for forbidden word"""
        replacements = {
            "leverage": "use",
            "utilize": "use",
            "facilitate": "help",
            "navigate": "handle",
            "delve": "look into",
            "robust": "strong",
            "seamless": "smooth",
            "paramount": "key",
            "furthermore": "also",
            "moreover": "and",
            "consequently": "so",
        }
        return replacements.get(word.lower(), "")

    def inject_triggers(
        self,
        text: str,
        profile: AudienceProfile,
    ) -> str:
        """Inject psychological triggers based on profile"""
        # This would be handled during generation, not post-processing
        # Keeping method for API consistency
        return text

    def build_prompt(self, brief: CopyBrief) -> str:
        """Build prompt for LLM with copywriting protocol"""
        trigger_words = []

        # Add motivation triggers
        trigger_words.extend(TRIGGER_WORDS.get(brief.audience.motivation, [])[:5])

        # Add reference triggers
        trigger_words.extend(TRIGGER_WORDS.get(brief.audience.reference, [])[:3])

        # Add rep system triggers
        trigger_words.extend(TRIGGER_WORDS.get(brief.audience.rep_system, [])[:3])

        # Add spiral triggers
        spiral_words = SPIRAL_LANGUAGE.get(brief.audience.spiral_level, [])[:3]

        prompt = f"""You are a direct-response copywriter. No fluff. No AI-speak. Just words that convert.

CONTENT TYPE: {brief.content_type}
OBJECTIVE: {brief.objective}
PRODUCT/SERVICE: {brief.product_service}

KEY BENEFITS:
{chr(10).join(f'- {b}' for b in brief.key_benefits)}

PAIN POINTS TO ADDRESS:
{chr(10).join(f'- {p}' for p in brief.pain_points)}

FRAMEWORK: {brief.framework.value.upper()}
TONE: {brief.tone}
{"MAX LENGTH: " + str(brief.max_length) + " words" if brief.max_length else ""}

PSYCHOLOGICAL PROFILE:
- Motivation: {brief.audience.motivation.value} (use words like: {', '.join(trigger_words[:4])})
- Reference: {brief.audience.reference.value}
- Chunk Size: {brief.audience.chunk_size.value}
- Rep System: {brief.audience.rep_system.value} (use words like: {', '.join(TRIGGER_WORDS.get(brief.audience.rep_system, [])[:3])})
- Value Level: {brief.audience.spiral_level.value} (use: {', '.join(spiral_words)})

RULES:
1. NEVER use these words: delve, leverage, utilize, foster, navigate, unlock, unleash, robust, crucial, seamless, paramount
2. NEVER use phrases like "In today's fast-paced world" or "At the end of the day"
3. NEVER use forced triads (Word. Word. Word.)
4. NEVER use contrastive negation ("It's not just X. It's Y.")
5. Mirror the reader's language. Be direct. Cut the fluff.
6. Use embedded commands naturally
7. Future pace the success state
8. End with a clear, urgent CTA

Write the {brief.content_type} now. No preamble. Just the copy."""

        return prompt

    def generate_system_prompt(self) -> str:
        """Generate system prompt for copywriting mode"""
        return """You are a direct-response copywriter trained in NLP and behavioral psychology.

Your copy converts because you:
1. Match the reader's psychological profile
2. Use sensory language that triggers emotional responses
3. Avoid AI-detectable patterns and corporate speak
4. Write like a human who gives a damn
5. Cut the fluff, get to the point
6. Challenge assumptions, don't just validate

FORBIDDEN (automatic fail):
- Corporate buzzwords: leverage, utilize, navigate, seamless, robust
- AI transitions: Furthermore, Moreover, Consequently
- Weak openings: "In today's fast-paced world"
- Weak endings: "At the end of the day", "In conclusion"
- Forced structures: "It's not just X. It's Y."

When triggered, immediately analyze the target audience and deploy matching psychological triggers.
"""


# Singleton instance
_engine: Optional[CopywritingEngine] = None


def get_copywriting_engine() -> CopywritingEngine:
    """Get copywriting engine instance"""
    global _engine
    if _engine is None:
        _engine = CopywritingEngine()
    return _engine


# Auto-trigger function for skill system
def should_trigger(text: str, context: Dict[str, Any] = None) -> bool:
    """Check if copywriting skill should auto-trigger"""
    return get_copywriting_engine().should_auto_trigger(text, context)


def get_system_prompt() -> str:
    """Get system prompt for copywriting mode"""
    return get_copywriting_engine().generate_system_prompt()
