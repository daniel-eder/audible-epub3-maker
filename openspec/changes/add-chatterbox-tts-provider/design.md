# Design: add-chatterbox-tts-provider

## Overview
Integrate a remote Chatterbox TTS HTTP API as a selectable engine. We leverage existing HTML segmentation utilities and only replace the synthesis phase.

## Sequence
EPUB chapter HTML → segmentation (existing helpers) → plain text chunks → Chatterbox POST(s) → collect WAV bytes → approximate word boundaries (placeholder heuristic) → merge & save.

## Word Boundary Strategy
Chatterbox API does not return per-word timings. To maintain pipeline expectations (alignment stage), we will fabricate naive boundaries:
- Tokenize on whitespace & punctuation
- Measure total audio length (ms)
- Distribute duration evenly across tokens sequentially
This yields deterministic pseudo-alignment enabling downstream SMIL generation though accuracy is limited.

Future improvement: integrate real alignment via external tool (e.g., WhisperX) or Chatterbox streaming metadata if available.

## Error Handling
- HTTP non-200: raise RuntimeError with status + snippet
- Empty audio / zero-length content: raise TTSEmptyAudioError / TTSEmptyContentError
- JSON encode failures: let requests raise
- Timeout defaults (10s) with single retry for transient network issues

## Configuration
Environment variables (with defaults):
- CHATTERBOX_TTS_URL (default http://localhost:4123)
- CHATTERBOX_EXAGGERATION (float, default 0.5)
- CHATTERBOX_CFG_WEIGHT (float, default 0.5)
- CHATTERBOX_TEMPERATURE (float, default 0.8)
Voice: reuse `settings.tts_voice` CLI / .env.

## Dependencies
Uses existing `requests` and `pydub`. No new third-party libraries required.

## Docker Compose
Add second example file to spin up Chatterbox alongside this app; link via service name for internal DNS.

## Security
No secrets required unless Chatterbox introduces auth in future; design allows injection of API key variable later.

## Trade-offs
- Heuristic boundaries risk misalignment; chosen for simplicity and minimal surface change.
- No streaming reduces complexity; can be added by separate spec later.

