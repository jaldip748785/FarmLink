import re
from flask import session

from utils.translations import TRANSLATIONS


VOICE_LANGUAGE_MAP = {
    "en": "en-IN",
    "en-in": "en-IN",
    "hi": "hi-IN",
    "hi-in": "hi-IN",
    "gu": "gu-IN",
    "gu-in": "gu-IN",
}


def get_voice_language(lang=None):
    selected_lang = (lang or session.get("lang") or "gu").lower()
    if selected_lang in VOICE_LANGUAGE_MAP:
        return VOICE_LANGUAGE_MAP[selected_lang]
    if selected_lang.startswith("gu"):
        return "gu-IN"
    if selected_lang.startswith("hi"):
        return "hi-IN"
    if selected_lang.startswith("en"):
        return "en-IN"
    return "en-IN"


def sanitize_voice_text(text):
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def get_translated_voice_text(key, fallback=None, lang=None):
    selected_lang = (lang or session.get("lang") or "gu").lower()
    translations = TRANSLATIONS.get(selected_lang, TRANSLATIONS.get("gu", {}))
    return translations.get(key, fallback or key)


def set_voice_message(session_obj, key, fallback=None, lang=None):
    message = get_translated_voice_text(key, fallback=fallback, lang=lang)
    if message:
        session_obj["voice_message"] = sanitize_voice_text(message)
    return message


def build_voice_payload(message, lang=None):
    text = sanitize_voice_text(message)
    if not text:
        return None
    return {
        "text": text,
        "lang": get_voice_language(lang),
    }
