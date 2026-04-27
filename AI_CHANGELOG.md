# AI Changelog

## 2026-04-26

- Implemented "Bulk translate sentences" pipeline: new `translate_client.py` module, translation config dataclasses, translation batch functions, new Browse menu action, tabbed config dialog with Translation tab.
- Fixed `WrappingPathLabel` parameter order mismatch that caused runtime error on config dialog open.
- Updated `docs/DESIGN_PLAN.md`, `docs/ARCHITECTURE.md`, `docs/CONFIG.md` with translation feature documentation.
- Created temporary `docs/FEATURE_PLAN.md` for session coordination.
- Verified documentation against the translation feature changes; reconciled README, architecture, config, and operations docs with the current Browse translation action, vLLM endpoint defaults, translation mappings, and config fallback behavior.
- Inconsistencies found: README and operations docs still described only TTS usage; architecture data flow still described only generated audio output; config docs stated all defaults were shipped in `config.json` even though translation defaults currently come from `constants.py` fallback values.
- Reconciled ignored internal planning docs by adding the README to the translation feature documentation references, removing a duplicated design-plan reference block, and marking completed translation implementation checklist items in the temporary feature plan.

## 2026-04-25

- Added minimal `docs/CODE_STANDARDS.md` with `Public docs: false` so documentation update workflows have the required repository standards file.
- Updated README and operations docs to remove distribution wording from the public README while keeping package build details in internal docs. :)

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
