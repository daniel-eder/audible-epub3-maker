# Project Context

## Purpose
Convert EPUB3 ebooks into structured, high‑quality audio output using multiple Text‑to‑Speech (TTS) engines. The system ingests `.epub` files, segments their textual/HTML content into narratable units (chapters, sections, paragraphs), then synthesizes audio via Azure Cognitive Services Speech and Kokoro TTS, producing concatenated audio assets suitable for listening (e.g., audiobook tracks). A lightweight web GUI (Gradio) and a programmatic API/CLI facilitate batch processing and experimentation.

### Core Goals
- Accurate extraction of readable text from diverse EPUB sources (including multilingual content like Chinese).
- Flexible segmentation (HTML- and text-based) to create natural listening breaks.
- Pluggable TTS backends with unified interface (`base_tts.py`).
- Efficient audio assembly with normalization and metadata handling.
- Clear logging, reproducible configuration, and test coverage of critical transformations.

### Non-Goals (Current)
- Full audiobook distribution platform (DRM, catalog management).
- Advanced NLP editing (summarization, rewriting) beyond minor normalization.
- Real-time streaming synthesis; current focus is batch generation.

## Tech Stack
- Language: Python (targeting 3.11+; compatibility notes for 3.13 via `audioop-lts`).
- Audio Processing: `pydub`, `soundfile`, `audioop-lts`.
- TTS Providers: `azure-cognitiveservices-speech`, `kokoro` (>=0.9.4).
- Text / HTML Parsing: `beautifulsoup4`, `lxml`.
- Fuzzy Matching / Utilities: `rapidfuzz`, `psutil`.
- Interface: `gradio` (web GUI), `main.py` / `app.py` for CLI/entry-point orchestration.
- Testing: `pytest`, `pytest-html`.
- Configuration: `.env` via `python-dotenv`, plus `config.py` typed accessors.
- Containerization: `Dockerfile`, optional `docker-compose.example.yml`.

## Project Conventions

### Code Style
- PEP 8 with pragmatic line length (≈ 100–120 chars where readability benefits).
- Snake_case for functions, variables; PascalCase for classes; CONSTANT_CASE for constants (see `constants.py`).
- Prefer explicit imports from local modules (`from audible_epub3_maker.epub import epub_book`) rather than wildcard.
- Logging through centralized `logging_setup.py` (avoid bare `print`). Use appropriate level: debug for internals, info for high-level progress, warning/error for recoverable/fatal issues.
- Type hints for public functions, especially in boundary modules (`epub_book.py`, segmenters, TTS interfaces). Gradual typing acceptable—add hints when modifying code.

### Architecture Patterns
- Layered modular design:
	- Ingestion & Parsing: `epub/` (load EPUB, extract spine, sanitize HTML → text).
	- Segmentation: `segmenter/` (HTML vs plain text strategies) producing normalized text chunks.
	- Synthesis: `tts/` (strategy pattern). `base_tts.py` defines contract; concrete providers implement `synthesize(text, voice, options)`.
	- Orchestration: `app.py` / `worker.py` coordinate pipeline (parse → segment → synthesize → assemble).
	- Utilities: `utils/` (helpers, constants, types, logging).
- Dependency Direction: Upper layers call down (orchestration depends on segmenter & tts; tts does not import segmentation). Avoid cycles.
- Configuration Injection: Pass config objects rather than reading env globally deep inside modules.
- Extensibility: New TTS provider requires only subclass of base and registration in a factory.

### Testing Strategy
- Pytest unit tests in `tests/` focusing on: config loading (`test_config.py`), EPUB parsing/book model (`test_epub.py`), text segmentation (`test_text.py`).
- Add snapshot/fixture EPUBs under `input/` for deterministic parsing tests.
- Future additions: audio synthesis dry-run tests (mocking provider calls), performance regression checks for large EPUBs.
- HTML coverage report via `pytest-html` optional. Aim: >80% coverage on transformation logic, tolerant of lower coverage in provider integration wrappers.

### Git Workflow
- Branching: Feature branches off default branch (assumed `main`); current example `feature/chatterbox`.
- Commits: Prefer Conventional Commits (`feat: add kokoro prosody tuning`, `fix: handle missing spine item`), or at minimum imperative present tense.
- PRs: Require brief description + testing notes. Rebase preferred over merge commits to keep linear history.
- Tags: Semantic versioning for release boundaries (planned; not yet enforced).

## Domain Context
- EPUB Structure: Container → Package OPF (manifest + spine). Segmentation uses spine order and chapter boundaries; HTML cleaning strips scripts/styles, normalizes whitespace, preserves emphasis minimally.
- Multilingual Handling: Must gracefully process CJK text without word-boundary segmentation errors; segmentation functions avoid naive space-based splits.
- TTS Specifics: Voice selection and rate/pitch options differ per provider; abstraction normalizes a minimal common subset (voice id, speaking rate, style). Azure may impose quotas; Kokoro local models may require GPU/CPU performance tuning.
- Audio Assembly: Chunks concatenated; optional silence padding between segments; normalization to consistent loudness (
	target around -16 LUFS conceptually—implementation may rely on pydub simple dBFS adjustments).

## Important Constraints
- Performance: Large EPUBs (e.g., >1MB text) must not exhaust memory; stream processing and incremental audio writing desirable.
- Rate Limits: Azure Speech quotas—must batch and optionally retry with exponential backoff.
- Licensing: Ensure synthesized content respects source text rights (user-provided content assumed permissible).
- Unicode Robustness: Avoid assumptions of ASCII; maintain correct encoding when reading/writing.
- Determinism: Segmenter should produce stable results given same input & config so audio can be regenerated consistently.

## External Dependencies
- Azure Cognitive Services Speech API (network calls, API key in environment variables).
- Kokoro TTS local package (may download models or expect them locally; version pinned >=0.9.4).
- Optional system-level audio codecs via underlying libraries (e.g., ffmpeg for `pydub` operations—document requirement for runtime environment).
- Gradio for ad-hoc local UI (not a production web stack; treat as developer convenience).

### Environment / Config Keys (Indicative)
- `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` for Azure.
- Voice selection and output directory settings in `.env` mapped by `config.py` (expand spec as implemented).

## Future Enhancements (Informational)
- Streaming synthesis pipeline.
- Caching layer for repeated paragraph synthesis.
- Additional TTS providers (e.g., Amazon Polly, ElevenLabs) via same interface.
- Rich metadata embedding (chapters, timestamps) into output formats.

## How To Add A New TTS Provider (Mini Contract)
1. Create subclass of `BaseTTS` in `tts/` implementing `synthesize(text, voice, options) -> AudioSegment`.
2. Register in a provider factory or mapping.
3. Add provider-specific config keys to `config.py`.
4. Write unit test with mocked responses.
5. Update this document under Tech Stack / External Dependencies.

## Edge Cases To Consider
- Empty chapters or chapters containing only images.
- Malformed EPUB (missing spine references) → graceful error & log.
- Very long paragraphs → chunk before provider limits.
- Mixed languages requiring fallback voice selection.
- Network hiccups during Azure calls (retry + jitter).

---
This spec should be updated alongside notable architectural changes or when introducing new providers or segmentation strategies.
