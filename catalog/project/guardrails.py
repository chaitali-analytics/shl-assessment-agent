import re
from typing import List

PROMPT_INJECTION_PATTERNS = [
    "ignore previous",
    "ignore all instructions",
    "ignore system prompt",
    "system prompt",
    "developer message",
    "reveal prompt",
    "show prompt",
    "print prompt",
    "act as",
    "jailbreak",
    "bypass",
    "forget previous",
    "override instructions",
    "prompt injection",
]

OFF_TOPIC_KEYWORDS = [
    "law",
    "lawsuit",
    "visa",
    "salary",
    "payroll",
    "weather",
    "doctor",
    "politics",
    "recipes",
    "recipe",
    "investment",
    "tax",
    "immigration",
    "privacy",
]

RELEVANT_MARKERS = [
    "assessment",
    "assessments",
    "test",
    "tests",
    "catalog",
    "shl",
    "product",
    "products",

    "opq",
    "gsa",
    "verify",
    "personality",
    "cognitive",
    "simulation",

    "hire",
    "hiring",
    "developer",
    "engineer",
    "analyst",
    "sales",
    "safety",
    "healthcare",
    "contact",
    "graduate",
    "leadership",
]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def is_prompt_injection(text: str) -> bool:
    text = normalize_text(text)
    return any(pattern in text for pattern in PROMPT_INJECTION_PATTERNS)


def is_off_topic(text: str) -> bool:
    text = normalize_text(text)
    if any(keyword in text for keyword in OFF_TOPIC_KEYWORDS):
        return True
    if not any(marker in text for marker in RELEVANT_MARKERS):
        return True
    return False


def should_clarify(text: str) -> bool:
    normalized = normalize_text(text)
    if is_prompt_injection(normalized) or is_off_topic(normalized):
        return False
    return not any(marker in normalized for marker in ["assessment", "test", "shl", "catalog"])
