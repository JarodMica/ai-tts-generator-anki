from __future__ import annotations

from pathlib import Path

ADDON_DIR = Path(__file__).resolve().parent
USER_FILES_DIR = ADDON_DIR / "user_files"
ASSETS_DIR = USER_FILES_DIR / "assets"

DEFAULT_CONFIG = {
    "endpoint": {
        "host": "127.0.0.1",
        "port": 9150,
        "path": "/tts",
        "timeout_seconds": 120,
        "text_field_name": "text",
        "reference_audio_field_name": "reference_audio",
        "transcript_text_field_name": "",
    },
    "headers": [],
    "reference_audio_path": "",
    "transcript_path": "",
    "overwrite_existing_tts_audio": False,
    "mappings": [],
    "translation_endpoint": {
        "host": "127.0.0.1",
        "port": 8009,
        "path": "/v1/completions",
        "timeout_seconds": 120,
        "model": "translategemma-4b-it",
        "max_tokens": 256,
    },
    "translation_headers": [],
    "translation_mappings": [],
    "translation_overwrite_existing": False,
}

LANGUAGE_NAMES = {
    "en": "English",
    "ja": "Japanese",
    "zh": "Chinese",
    "zh-cn": "Chinese",
    "zh-hans": "Chinese",
    "zh-hant": "Chinese",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
    "hi": "Hindi",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
}
