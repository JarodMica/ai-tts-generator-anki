# Sentence Audio Generator (AI TTS)

Sentence Audio Generator (AI TTS) is an Anki add-on that generates audio for selected notes in the Browse window by sending sentence text to a configurable local HTTP TTS service and writing the returned WAV audio into a target field as an Anki `[sound:...]` tag.

## What It Does

- Adds `Bulk add TTS` to the Browse window `Edit` menu.
- Processes only the notes currently selected in Browse.
- Uses deck + note type mappings to choose the source text field and target audio field.
- Sends requests to a configurable local TTS endpoint.
- Stores a global reference audio file and optional transcript file under the add-on's `user_files/` folder.
- Skips notes with empty source text.
- Skips notes with existing target audio unless overwrite is enabled for existing TTS-tagged audio.

## Requirements

- Anki `25.09.2` or a compatible recent Anki 25 build.
- Windows-focused local workflow.
- A running local TTS server that accepts multipart form uploads and returns `audio/wav` bytes.

## Build

Use the repo-local build script to package the add-on:

```bat
build.bat
```

`build.bat`:

- reads `app_version.txt`
- optionally updates the version when prompted
- requires the version to use `X.Y.Z` semantic form
- rebuilds `dist\SentenceAudioGenerator.ankiaddon`
- rebuilds `dist\SentenceAudioGenerator-<version>.ankiaddon`

Use this generated package when installing or updating the add-on:

```text
dist\SentenceAudioGenerator.ankiaddon
```

## Install And Setup In Anki

1. Open `Tools -> Add-ons`.
2. Install or update the add-on from AnkiWeb.
3. Select the add-on and click `Config`.
4. Set the endpoint values.
5. Import the global reference audio file.
6. Optionally import a transcript text file.
7. Add at least one deck + note type mapping.
8. Save the settings dialog.

The add-on registers a custom config dialog through Anki's add-on manager, so the `Config` button should open the Qt settings dialog instead of the raw JSON editor.

After configuration, open Browse, select a small set of notes, and run `Edit -> Bulk add TTS`.

## Default Irodori Endpoint Settings

These defaults match the current local Irodori profile used in development:

- Host: `127.0.0.1`
- Port: `9150`
- Path: `/tts`
- Text form field: `text`
- Reference audio form field: `reference_audio`
- Transcript text form field: blank by default

## Generated Media

Generated files are written into Anki media with names shaped like:

```text
tts-<note_id>-<sha1_prefix>.wav
```

The `tts` prefix is also used by the overwrite option to distinguish generated TTS audio from other audio in the target field.
