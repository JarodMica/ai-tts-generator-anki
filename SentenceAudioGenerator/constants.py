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
}
