from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aqt import mw

from .constants import ASSETS_DIR, DEFAULT_CONFIG, USER_FILES_DIR


@dataclass
class HeaderConfig:
    name: str
    value: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HeaderConfig":
        return cls(
            name=str(data.get("name", "")).strip(),
            value=str(data.get("value", "")),
        )

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "value": self.value}


@dataclass
class MappingConfig:
    deck_name: str
    note_type_name: str
    source_field: str
    target_field: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MappingConfig":
        return cls(
            deck_name=str(data.get("deck_name", "")).strip(),
            note_type_name=str(data.get("note_type_name", "")).strip(),
            source_field=str(data.get("source_field", "")).strip(),
            target_field=str(data.get("target_field", "")).strip(),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "deck_name": self.deck_name,
            "note_type_name": self.note_type_name,
            "source_field": self.source_field,
            "target_field": self.target_field,
        }


@dataclass
class EndpointConfig:
    host: str = "127.0.0.1"
    port: int = 9150
    path: str = "/tts"
    timeout_seconds: int = 120
    text_field_name: str = "text"
    reference_audio_field_name: str = "reference_audio"
    transcript_text_field_name: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EndpointConfig":
        defaults = DEFAULT_CONFIG["endpoint"]
        return cls(
            host=str(data.get("host", defaults["host"])).strip() or defaults["host"],
            port=int(data.get("port", defaults["port"])),
            path=str(data.get("path", defaults["path"])).strip() or defaults["path"],
            timeout_seconds=int(
                data.get("timeout_seconds", defaults["timeout_seconds"])
            ),
            text_field_name=str(
                data.get("text_field_name", defaults["text_field_name"])
            ).strip()
            or defaults["text_field_name"],
            reference_audio_field_name=str(
                data.get(
                    "reference_audio_field_name",
                    defaults["reference_audio_field_name"],
                )
            ).strip()
            or defaults["reference_audio_field_name"],
            transcript_text_field_name=str(
                data.get(
                    "transcript_text_field_name",
                    defaults["transcript_text_field_name"],
                )
            ).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "path": self.path,
            "timeout_seconds": self.timeout_seconds,
            "text_field_name": self.text_field_name,
            "reference_audio_field_name": self.reference_audio_field_name,
            "transcript_text_field_name": self.transcript_text_field_name,
        }

    def url(self) -> str:
        path = self.path if self.path.startswith("/") else f"/{self.path}"
        return f"http://{self.host}:{self.port}{path}"


@dataclass
class TranslationHeaderConfig:
    name: str
    value: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranslationHeaderConfig":
        return cls(
            name=str(data.get("name", "")).strip(),
            value=str(data.get("value", "")),
        )

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "value": self.value}


@dataclass
class TranslationMappingConfig:
    deck_name: str
    note_type_name: str
    source_field: str
    target_field: str
    source_language: str
    target_language: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranslationMappingConfig":
        return cls(
            deck_name=str(data.get("deck_name", "")).strip(),
            note_type_name=str(data.get("note_type_name", "")).strip(),
            source_field=str(data.get("source_field", "")).strip(),
            target_field=str(data.get("target_field", "")).strip(),
            source_language=str(data.get("source_language", "")).strip(),
            target_language=str(data.get("target_language", "")).strip(),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "deck_name": self.deck_name,
            "note_type_name": self.note_type_name,
            "source_field": self.source_field,
            "target_field": self.target_field,
            "source_language": self.source_language,
            "target_language": self.target_language,
        }


@dataclass
class TranslationEndpointConfig:
    host: str = "127.0.0.1"
    port: int = 8009
    path: str = "/v1/completions"
    timeout_seconds: int = 120
    model: str = "translategemma-4b-it"
    max_tokens: int = 256

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TranslationEndpointConfig":
        defaults = DEFAULT_CONFIG["translation_endpoint"]
        return cls(
            host=str(data.get("host", defaults["host"])).strip() or defaults["host"],
            port=int(data.get("port", defaults["port"])),
            path=str(data.get("path", defaults["path"])).strip() or defaults["path"],
            timeout_seconds=int(
                data.get("timeout_seconds", defaults["timeout_seconds"])
            ),
            model=str(data.get("model", defaults["model"])).strip() or defaults["model"],
            max_tokens=int(data.get("max_tokens", defaults["max_tokens"])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "path": self.path,
            "timeout_seconds": self.timeout_seconds,
            "model": self.model,
            "max_tokens": self.max_tokens,
        }

    def url(self) -> str:
        path = self.path if self.path.startswith("/") else f"/{self.path}"
        return f"http://{self.host}:{self.port}{path}"


@dataclass
class AddonConfig:
    endpoint: EndpointConfig = field(default_factory=EndpointConfig)
    headers: list[HeaderConfig] = field(default_factory=list)
    reference_audio_path: str = ""
    transcript_path: str = ""
    overwrite_existing_tts_audio: bool = False
    mappings: list[MappingConfig] = field(default_factory=list)
    translation_endpoint: TranslationEndpointConfig = field(default_factory=TranslationEndpointConfig)
    translation_headers: list[TranslationHeaderConfig] = field(default_factory=list)
    translation_mappings: list[TranslationMappingConfig] = field(default_factory=list)
    translation_overwrite_existing: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AddonConfig":
        payload = data or {}
        return cls(
            endpoint=EndpointConfig.from_dict(
                dict(payload.get("endpoint", DEFAULT_CONFIG["endpoint"]))
            ),
            headers=[
                HeaderConfig.from_dict(item)
                for item in list(payload.get("headers", []))
                if isinstance(item, dict)
            ],
            reference_audio_path=str(payload.get("reference_audio_path", "")).strip(),
            transcript_path=str(payload.get("transcript_path", "")).strip(),
            overwrite_existing_tts_audio=bool(
                payload.get(
                    "overwrite_existing_tts_audio",
                    DEFAULT_CONFIG["overwrite_existing_tts_audio"],
                )
            ),
            mappings=[
                MappingConfig.from_dict(item)
                for item in list(payload.get("mappings", []))
                if isinstance(item, dict)
            ],
            translation_endpoint=TranslationEndpointConfig.from_dict(
                dict(payload.get("translation_endpoint", DEFAULT_CONFIG["translation_endpoint"]))
            ),
            translation_headers=[
                TranslationHeaderConfig.from_dict(item)
                for item in list(payload.get("translation_headers", []))
                if isinstance(item, dict)
            ],
            translation_mappings=[
                TranslationMappingConfig.from_dict(item)
                for item in list(payload.get("translation_mappings", []))
                if isinstance(item, dict)
            ],
            translation_overwrite_existing=bool(
                payload.get(
                    "translation_overwrite_existing",
                    DEFAULT_CONFIG["translation_overwrite_existing"],
                )
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint.to_dict(),
            "headers": [header.to_dict() for header in self.headers if header.name],
            "reference_audio_path": self.reference_audio_path,
            "transcript_path": self.transcript_path,
            "overwrite_existing_tts_audio": self.overwrite_existing_tts_audio,
            "mappings": [mapping.to_dict() for mapping in self.mappings],
            "translation_endpoint": self.translation_endpoint.to_dict(),
            "translation_headers": [header.to_dict() for header in self.translation_headers if header.name],
            "translation_mappings": [mapping.to_dict() for mapping in self.translation_mappings],
            "translation_overwrite_existing": self.translation_overwrite_existing,
        }

    def resolved_reference_audio_path(self) -> Path | None:
        return resolve_user_file(self.reference_audio_path)

    def resolved_transcript_path(self) -> Path | None:
        return resolve_user_file(self.transcript_path)


def ensure_user_dirs() -> None:
    USER_FILES_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> AddonConfig:
    ensure_user_dirs()
    return AddonConfig.from_dict(mw.addonManager.getConfig(__name__))


def save_config(config: AddonConfig) -> None:
    ensure_user_dirs()
    mw.addonManager.writeConfig(__name__, config.to_dict())


def resolve_user_file(relative_path: str) -> Path | None:
    if not relative_path:
        return None
    path = USER_FILES_DIR / relative_path
    return path.resolve()


def import_asset(source_path: str, stem_name: str) -> str:
    ensure_user_dirs()
    source = Path(source_path).expanduser().resolve()
    suffix = source.suffix.lower()
    destination = ASSETS_DIR / f"{stem_name}{suffix}"
    if source != destination.resolve():
        shutil.copyfile(source, destination)
    return destination.relative_to(USER_FILES_DIR).as_posix()
