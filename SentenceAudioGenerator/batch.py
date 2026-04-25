from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Sequence

from anki.collection import Collection, OpChanges
from anki.notes import Note
from anki.sound import strip_av_refs
from anki.utils import html_to_text_line
from aqt import mw
from aqt.browser import Browser
from aqt.operations import CollectionOp
from aqt.utils import askUser, showInfo, showWarning

from .config import AddonConfig, MappingConfig, load_config
from .config_dialog import show_config_dialog
from .tts_client import TTSClientError, TTSRequest, synthesize

SOUND_TAG_RE = re.compile(r"(?i)\[sound:(?P<fname>[^\]]+)\]")


@dataclass
class BatchCounts:
    generated: int = 0
    skipped_empty: int = 0
    skipped_existing: int = 0
    skipped_unmapped: int = 0
    failed: int = 0


@dataclass
class BatchRunResult:
    changes: OpChanges
    total: int
    counts: BatchCounts = field(default_factory=BatchCounts)
    errors: list[str] = field(default_factory=list)


def run_bulk_add_tts(browser: Browser) -> None:
    config = load_config()
    note_ids = list(browser.selected_notes())
    if not note_ids:
        showInfo("Select one or more notes in Browse before running Bulk add TTS.")
        return

    config = prompt_for_missing_setup(browser, config)
    if config is None:
        return

    reference_path = config.resolved_reference_audio_path()

    transcript_text: str | None = None
    transcript_path = config.resolved_transcript_path()
    if config.transcript_path and transcript_path:
        transcript_text = transcript_path.read_text(encoding="utf-8").strip()

    assert reference_path is not None
    reference_audio_bytes = reference_path.read_bytes()
    request_reference_name = reference_path.name

    CollectionOp(
        browser,
        lambda col: process_notes(
            col=col,
            note_ids=note_ids,
            config=config,
            reference_audio_bytes=reference_audio_bytes,
            reference_audio_name=request_reference_name,
            transcript_text=transcript_text,
        ),
    ).success(lambda result: show_batch_summary(result)).run_in_background()


def prompt_for_missing_setup(
    browser: Browser,
    config: AddonConfig,
) -> AddonConfig | None:
    if not config.mappings:
        return reconfigure_if_user_wants(
            browser,
            config,
            "No deck and note type mappings are configured yet.\n\nOpen the add-on settings now?",
            lambda updated: bool(updated.mappings),
            "No deck and note type mappings are configured yet.",
        )

    reference_path = config.resolved_reference_audio_path()
    if not reference_path or not reference_path.is_file():
        return reconfigure_if_user_wants(
            browser,
            config,
            "A reference audio file has not been configured.\n\nOpen the add-on settings now?",
            lambda updated: bool(
                updated.resolved_reference_audio_path()
                and updated.resolved_reference_audio_path().is_file()
            ),
            "A reference audio file has not been configured in the add-on settings.",
        )

    transcript_path = config.resolved_transcript_path()
    if config.transcript_path and (not transcript_path or not transcript_path.is_file()):
        return reconfigure_if_user_wants(
            browser,
            config,
            "The configured transcript file is missing.\n\nOpen the add-on settings now?",
            lambda updated: (
                not updated.transcript_path
                or bool(
                    updated.resolved_transcript_path()
                    and updated.resolved_transcript_path().is_file()
                )
            ),
            "The configured transcript file is missing. Update or clear it in the add-on settings.",
        )

    return config


def reconfigure_if_user_wants(
    browser: Browser,
    config: AddonConfig,
    prompt: str,
    is_fixed: Callable[[AddonConfig], bool],
    failure_message: str,
) -> AddonConfig | None:
    if not askUser(prompt, parent=browser):
        return None
    show_config_dialog()
    updated = load_config()
    if not is_fixed(updated):
        showWarning(failure_message)
        return None
    return updated


def process_notes(
    *,
    col: Collection,
    note_ids: Sequence[int],
    config: AddonConfig,
    reference_audio_bytes: bytes,
    reference_audio_name: str,
    transcript_text: str | None,
) -> BatchRunResult:
    counts = BatchCounts()
    errors: list[str] = []
    updated_notes: list[Note] = []
    total = len(note_ids)

    publish_progress(total, 0, counts)
    for index, note_id in enumerate(note_ids, start=1):
        note = col.get_note(note_id)
        mapping = find_mapping_for_note(col, note, config.mappings)
        if not mapping:
            counts.skipped_unmapped += 1
            publish_progress(total, index, counts, note.id, "No mapping for note.")
            continue

        if mapping.source_field not in note:
            counts.failed += 1
            errors.append(
                f"Note {note.id}: source field '{mapping.source_field}' does not exist."
            )
            publish_progress(total, index, counts, note.id, "Missing source field.")
            continue
        if mapping.target_field not in note:
            counts.failed += 1
            errors.append(
                f"Note {note.id}: target field '{mapping.target_field}' does not exist."
            )
            publish_progress(total, index, counts, note.id, "Missing target field.")
            continue

        cleaned_text = normalize_tts_text(note[mapping.source_field])
        if not cleaned_text:
            counts.skipped_empty += 1
            publish_progress(total, index, counts, note.id, "Skipped empty source.")
            continue
        overwrite_existing = can_overwrite_existing_tts_audio(
            note[mapping.target_field], config
        )
        if note[mapping.target_field].strip() and not overwrite_existing:
            counts.skipped_existing += 1
            publish_progress(
                total,
                index,
                counts,
                note.id,
                "Skipped existing target audio.",
            )
            continue

        try:
            wav_bytes = synthesize(
                config,
                TTSRequest(
                    text=cleaned_text,
                    reference_audio_name=reference_audio_name,
                    reference_audio_bytes=reference_audio_bytes,
                    transcript_text=transcript_text,
                ),
            )
            media_name = col.media.write_data(
                build_media_filename(note.id, cleaned_text),
                wav_bytes,
            )
            note[mapping.target_field] = f"[sound:{media_name}]"
            updated_notes.append(note)
            counts.generated += 1
            publish_progress(
                total,
                index,
                counts,
                note.id,
                "Overwrote existing TTS audio."
                if overwrite_existing
                else "Generated audio.",
            )
        except TTSClientError as exc:
            counts.failed += 1
            errors.append(f"Note {note.id}: {exc}")
            publish_progress(total, index, counts, note.id, "TTS request failed.")
        except Exception as exc:
            counts.failed += 1
            errors.append(f"Note {note.id}: {exc}")
            publish_progress(total, index, counts, note.id, "Unexpected failure.")

    changes = col.update_notes(updated_notes) if updated_notes else OpChanges()
    publish_progress(total, total, counts, summary="Finished.")
    return BatchRunResult(changes=changes, total=total, counts=counts, errors=errors)


def find_mapping_for_note(
    col: Collection,
    note: Note,
    mappings: Sequence[MappingConfig],
) -> MappingConfig | None:
    note_type = note.note_type()
    if not note_type:
        return None
    note_type_name = str(note_type["name"])
    note_deck_names: set[str] = set()
    for card in note.cards():
        deck = col.decks.get_legacy(card.current_deck_id())
        if deck:
            note_deck_names.add(str(deck["name"]))
    for mapping in mappings:
        if (
            mapping.note_type_name == note_type_name
            and mapping.deck_name in note_deck_names
        ):
            return mapping
    return None


def normalize_tts_text(value: str) -> str:
    text = strip_av_refs(value)
    text = html_to_text_line(text)
    return " ".join(text.split()).strip()


def can_overwrite_existing_tts_audio(value: str, config: AddonConfig) -> bool:
    if not config.overwrite_existing_tts_audio:
        return False
    trimmed = value.strip()
    if not trimmed:
        return False
    matches = list(SOUND_TAG_RE.finditer(trimmed))
    if not matches:
        return False
    remainder = SOUND_TAG_RE.sub("", trimmed).strip()
    if remainder:
        return False
    return all("tts" in match.group("fname").lower() for match in matches)


def build_media_filename(note_id: int, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]
    return f"tts-{note_id}-{digest}.wav"


def publish_progress(
    total: int,
    current: int,
    counts: BatchCounts,
    note_id: int | None = None,
    detail: str | None = None,
    summary: str | None = None,
) -> None:
    label_parts = [
        f"Bulk add TTS {current}/{total}",
        f"generated={counts.generated}",
        f"skip-empty={counts.skipped_empty}",
        f"skip-existing={counts.skipped_existing}",
        f"skip-unmapped={counts.skipped_unmapped}",
        f"failed={counts.failed}",
    ]
    if summary:
        label_parts.append(summary)
    elif note_id is not None and detail:
        label_parts.append(f"note={note_id}")
        label_parts.append(detail)
    label = " | ".join(label_parts)
    mw.taskman.run_on_main(
        lambda: mw.progress.update(
            label=label,
            value=current,
            max=max(total, 1),
        )
    )


def show_batch_summary(result: BatchRunResult) -> None:
    lines = [
        "Bulk add TTS finished.",
        f"Processed: {result.total}",
        f"Generated: {result.counts.generated}",
        f"Skipped (empty source): {result.counts.skipped_empty}",
        f"Skipped (existing target): {result.counts.skipped_existing}",
        f"Skipped (no mapping): {result.counts.skipped_unmapped}",
        f"Failed: {result.counts.failed}",
    ]
    if result.errors:
        lines.append("")
        lines.append("Failures:")
        lines.extend(result.errors[:25])
        if len(result.errors) > 25:
            lines.append(f"...and {len(result.errors) - 25} more.")
    showInfo("\n".join(lines))
