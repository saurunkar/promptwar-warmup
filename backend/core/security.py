"""
Security Module — Input sanitization (prompt injection protection)
and output filtering for the Agentic Learning Assistant.
"""
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Patterns commonly used in prompt injection attacks
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(all\s+)?above",
    r"disregard\s+(all\s+)?previous",
    r"forget\s+(all\s+)?previous",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+if\s+you\s+are",
    r"pretend\s+you\s+are",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<<SYS>>",
    r"<</SYS>>",
]

# Toxic / harmful output patterns
OUTPUT_FILTER_PATTERNS = [
    r"(hack|exploit|crack)\s+(into|a|the)\s+(system|server|database)",
    r"(how\s+to\s+)?(make|build|create)\s+(a\s+)?(bomb|weapon|explosive)",
    r"(self[- ]?harm|suicid)",
]


def sanitize_input(user_input: str) -> Tuple[str, bool]:
    """
    Sanitize user input to protect against prompt injection.
    Returns (sanitized_text, is_safe).
    """
    if not user_input or not user_input.strip():
        return "", False

    # Check for injection patterns
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            logger.warning(f"Prompt injection attempt detected: pattern='{pattern}'")
            return "", False

    # Truncate excessively long inputs (> 2000 chars)
    if len(user_input) > 2000:
        logger.warning(f"Input truncated from {len(user_input)} to 2000 chars")
        user_input = user_input[:2000]

    # Strip potential HTML/script tags
    sanitized = re.sub(r"<[^>]+>", "", user_input)

    return sanitized.strip(), True


def filter_output(llm_output: str) -> str:
    """
    Filter LLM output for toxic or harmful content.
    Returns filtered output.
    """
    if not llm_output:
        return ""

    for pattern in OUTPUT_FILTER_PATTERNS:
        if re.search(pattern, llm_output, re.IGNORECASE):
            logger.warning(f"Toxic output detected and filtered: pattern='{pattern}'")
            return "I'm unable to provide that information. Let's focus on your learning goals."

    return llm_output


def validate_user_id(user_id: str) -> bool:
    """Validate user ID format to prevent injection."""
    if not user_id:
        return False
    # Allow alphanumeric, hyphens, underscores, max 128 chars
    return bool(re.match(r"^[a-zA-Z0-9_-]{1,128}$", user_id))
