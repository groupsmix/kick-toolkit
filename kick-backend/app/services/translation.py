"""Translation service for multi-language chat translation."""

import logging
import re

logger = logging.getLogger(__name__)

# Supported languages
SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish"},
    {"code": "fr", "name": "French"},
    {"code": "de", "name": "German"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "it", "name": "Italian"},
    {"code": "ru", "name": "Russian"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "zh", "name": "Chinese"},
    {"code": "ar", "name": "Arabic"},
    {"code": "hi", "name": "Hindi"},
    {"code": "tr", "name": "Turkish"},
    {"code": "pl", "name": "Polish"},
    {"code": "nl", "name": "Dutch"},
    {"code": "sv", "name": "Swedish"},
    {"code": "th", "name": "Thai"},
    {"code": "vi", "name": "Vietnamese"},
    {"code": "id", "name": "Indonesian"},
    {"code": "fil", "name": "Filipino"},
]


def detect_language(text: str) -> str:
    """Simple language detection heuristic based on character ranges.

    For production, integrate with a proper language detection library
    (e.g., langdetect, lingua) or an external API (Google, DeepL).
    """
    # Check for CJK characters
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
        return "ja"
    if re.search(r"[\uac00-\ud7af]", text):
        return "ko"
    # Arabic
    if re.search(r"[\u0600-\u06ff]", text):
        return "ar"
    # Cyrillic
    if re.search(r"[\u0400-\u04ff]", text):
        return "ru"
    # Thai
    if re.search(r"[\u0e00-\u0e7f]", text):
        return "th"
    # Hindi/Devanagari
    if re.search(r"[\u0900-\u097f]", text):
        return "hi"
    # Default to English for Latin scripts
    return "en"


async def translate_text(
    text: str, target_language: str, source_language: str | None = None,
) -> dict:
    """Translate text to target language.

    Currently returns a placeholder result. To enable real translation,
    integrate with Google Translate API, DeepL API, or LibreTranslate.
    Set the appropriate API key in environment variables.
    """
    detected = source_language or detect_language(text)

    if detected == target_language:
        return {
            "original_text": text,
            "translated_text": text,
            "source_language": detected,
            "target_language": target_language,
            "was_translated": False,
        }

    # Placeholder: In production, call external translation API here
    # For now, return original text with detected language info
    return {
        "original_text": text,
        "translated_text": text,
        "source_language": detected,
        "target_language": target_language,
        "was_translated": False,
        "note": "Translation API not configured. Set TRANSLATION_API_KEY to enable.",
    }
