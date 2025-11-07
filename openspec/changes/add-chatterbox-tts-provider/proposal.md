# Change Proposal: Add Chatterbox TTS Provider

## change-id
add-chatterbox-tts-provider

## Summary
Introduce a new third TTS engine integration for the project: Chatterbox TTS API (OpenAI-compatible self-hosted voice cloning & multilingual TTS). This expands offline / self-hosted options beyond Kokoro and Azure by enabling HTTP calls to a running Chatterbox container.

## Motivation
Users want:
- Self-hosted alternative with voice cloning & multilingual support (22 languages)
- OpenAI-compatible API semantics for easier integration
- Avoid cloud costs / rate limits for experimentation

## Goals
- Provide `--tts_engine chatterbox` CLI / config option
- Support basic text-to-speech using `/v1/audio/speech` JSON endpoint
- Allow passing voice name, exaggeration, temperature, cfg_weight
- Gracefully handle lack of word boundaries (fallback alignment strategy TBD)
- Supply documentation & docker-compose example that spins up both this app and Chatterbox TTS API

## Non-Goals
- Implement streaming SSE support initially
- Implement voice upload or library management inside this repo (refer users to Chatterbox UI)
- Advanced retry/backoff logic (simple one-shot request with basic error handling)

## Risks / Considerations
- Chatterbox may not provide native word boundary timestamps; force alignment may require chunk text fallback
- Large inputs rely on Chatterbox internal chunking — need max length guard if API rejects overly long text
- Need to ensure license compatibility (Chatterbox repo AGPL-3.0; we only use its public HTTP API, not embed code)

## High-Level Design
Add `chatterbox_tts.py` implementing `BaseTTS.html_to_speech`:
1. Segment HTML similarly to Kokoro/Azure (reuse segmentation logic for breaks) and produce plain text.
2. POST JSON to `${CHATTERBOX_TTS_BASE_URL}/v1/audio/speech` with fields:
   - input
   - voice (optional)
   - exaggeration, temperature, cfg_weight (optional)
3. Receive WAV (default) and save to temporary file.
4. Since no word boundaries: return empty list OR attempt heuristic token boundaries (future). For now return empty list and allow worker to degrade gracefully (skip alignment but proceed embedding audio).
5. Update `create_tts_engine` factory.
6. Add env/config fields: `CHATTERBOX_TTS_BASE_URL`, `CHATTERBOX_TTS_VOICE`, `CHATTERBOX_TTS_EXAGGERATION`, `CHATTERBOX_TTS_TEMPERATURE`, `CHATTERBOX_TTS_CFG_WEIGHT`.
7. README section & docker-compose example running both services.

## Alternatives Considered
- Implement streaming first (adds complexity; postpone)
- Use OpenAI client library; unnecessary overhead vs direct HTTP

## Validation Plan
- Unit test mocking POST to speech endpoint returning simple WAV
- CLI run with sample EPUB using chatterbox engine (manual) documented
- Ensure spec updated & environment variable doc included

## Open Questions
- Should we attempt to approximate word boundaries by splitting text & measuring durations? (OUT OF SCOPE)
- Should we add retries? (maybe minimal with one retry)

## Success Metrics
- New engine selectable via CLI `--tts_engine chatterbox`
- README documents usage & env variables
- Docker compose example launches both containers seamlessly
