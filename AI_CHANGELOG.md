# AI Changelog

## 2026-04-24

- Verified documentation against the current `SentenceAudioGenerator` package, build scripts, config defaults, and AnkiWeb packaging flow.
- Reconciled documentation with current code by adding the `X.Y.Z` version requirement, generated media filename shape, case-insensitive overwrite matching, skipped-unmapped behavior, and TTS response validation notes.

## 2026-04-23

- Added user-facing documentation for the Sentence Audio Generator (AI TTS) add-on in `README.md`.
- Added `docs/ARCHITECTURE.md` covering Anki startup wiring, Browse menu registration, batch processing flow, and TTS request flow.
- Added `docs/CONFIG.md` covering endpoint settings, headers, asset paths, overwrite behavior, and deck + note type mappings.
- Added `docs/OPERATIONS.md` covering local build/install workflow, `.ankiaddon` packaging, setup steps, and Browse usage.
- Updated `docs/FEATURE_PLAN.md` so the implemented feature state includes explicit status, related code references, and related documentation references.
- Updated `README.md` and `docs/OPERATIONS.md` to reflect the current packaging-only `build.bat` workflow and AnkiWeb-based update path.
- Added `docs/DESIGN_PLAN.md` as the canonical roadmap/status document required by the author notes.
- Reduced `docs/FEATURE_PLAN.md` to a historical coordination pointer so durable planning now lives in `docs/DESIGN_PLAN.md`.
- Updated `docs/ARCHITECTURE.md` and `docs/CONFIG.md` to document the `__name__`-based addon-manager config resolution that keeps the custom config dialog working in both local and AnkiWeb-installed copies.
