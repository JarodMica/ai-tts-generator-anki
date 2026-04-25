# Sentence Audio Generator (AI TTS) Config

This add-on uses a custom configuration dialog from Anki's add-on manager.

Stored settings include:

- local TTS endpoint host, port, and path
- multipart field names for text, reference audio, and optional transcript text
- optional custom HTTP headers
- the global reference audio file stored under `user_files/`
- the optional transcript file stored under `user_files/`
- whether existing target audio can be replaced when it already looks like generated TTS
- deck and note type field mappings for source text and target audio
