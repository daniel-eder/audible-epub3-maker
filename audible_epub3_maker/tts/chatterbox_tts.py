import logging, io, json, re
from pathlib import Path
from typing import List
import requests
from bs4 import BeautifulSoup
from pydub import AudioSegment

from audible_epub3_maker.tts.base_tts import BaseTTS
from audible_epub3_maker.config import (
    settings,
    CHATTERBOX_TTS_URL,
    CHATTERBOX_EXAGGERATION,
    CHATTERBOX_CFG_WEIGHT,
    CHATTERBOX_TEMPERATURE,
    in_dev,
)
from audible_epub3_maker.utils import helpers
from audible_epub3_maker.utils.constants import BEAUTIFULSOUP_PARSER
from audible_epub3_maker.utils.types import WordBoundary, TTSEmptyAudioError, TTSEmptyContentError
from audible_epub3_maker.segmenter import html_segmenter, text_segmenter

logger = logging.getLogger(__name__)

# Basic limits / defaults
_MAX_CHARS_PER_REQUEST = 5000  # Conservative guard; Chatterbox auto-chunks but we pre-split to manage boundaries
_TIMEOUT_SECONDS = 30

class ChatterboxTTS(BaseTTS):
    """Chatterbox TTS engine (self-hosted HTTP API).

    Uses the OpenAI-compatible endpoint: POST <base>/v1/audio/speech with JSON body.
    Response is raw audio bytes (WAV). Word boundaries are heuristically generated because
    the API does not (yet) provide per-word timestamps.
    """

    def __init__(self):
        super().__init__()
        pass

    @staticmethod
    def _chunk_text(text: str, max_chars: int) -> List[str]:
        if len(text) <= max_chars:
            return [text]
        # Prefer splitting on sentence boundaries.
        sentences = re.split(r'(?:[\.!?]+\s+)', text)
        chunks = []
        current = ''
        for s in sentences:
            if not s:
                continue
            if len(current) + len(s) > max_chars:
                if current.strip():
                    chunks.append(current.strip())
                current = s
            else:
                current += (' ' + s if current else s)
        if current.strip():
            chunks.append(current.strip())
        # Fallback if splitting failed (e.g. no punctuation)
        if not chunks:
            chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)]
        return chunks

    def _prepare_text(self, html_text: str) -> List[str]:
        soup = BeautifulSoup(html_text, BEAUTIFULSOUP_PARSER)
        break_map = {
            "h1": "_#BRK#",
            "h2": "_#BRK#",
            "h3": "_#BRK#",
            "h4": "_#BRK#",
            "h5": "_#BRK#",
            "h6": "_#BRK#",
            "li": "_#BRK#",
            "p": "_#BRK#",
        }
        html_segmenter.bs_append_suffix_to_tags(soup, break_map)
        body_text = soup.body.get_text() if soup.body else soup.get_text()
        body_text = text_segmenter.normalize_newlines(body_text, settings.newline_mode)
        body_text = body_text.replace('_#BRK#', '\n')  # Represent breaks with newlines
        if not body_text.strip():
            raise TTSEmptyContentError("Input HTML contains no valid text content.")
        # chunking
        chunks = self._chunk_text(body_text, settings.tts_chunk_len if settings.tts_chunk_len > 0 else _MAX_CHARS_PER_REQUEST)
        return chunks

    def _post_chunk(self, chunk_text: str) -> bytes:
        url = CHATTERBOX_TTS_URL.rstrip('/') + '/v1/audio/speech'
        payload = {
            "input": chunk_text,
        }
        # Optional voice selection
        if settings.tts_voice:
            payload["voice"] = settings.tts_voice
        # Include optional parameters (CLI overrides first)
        exaggeration = settings.chatterbox_exaggeration if settings.chatterbox_exaggeration is not None else CHATTERBOX_EXAGGERATION
        cfg_weight = settings.chatterbox_cfg_weight if settings.chatterbox_cfg_weight is not None else CHATTERBOX_CFG_WEIGHT
        temperature = settings.chatterbox_temperature if settings.chatterbox_temperature is not None else CHATTERBOX_TEMPERATURE
        payload.update({
            "exaggeration": exaggeration,
            "cfg_weight": cfg_weight,
            "temperature": temperature,
        })
        try:
            resp = requests.post(url, json=payload, timeout=_TIMEOUT_SECONDS)
        except requests.RequestException as e:
            raise RuntimeError(f"Chatterbox request failed: {e}") from e
        if resp.status_code != 200:
            snippet = resp.text[:200].replace('\n', ' ')
            raise RuntimeError(f"Chatterbox TTS error {resp.status_code}: {snippet}")
        return resp.content

    def _generate_word_boundaries(self, audio_seg: AudioSegment, text: str) -> List[WordBoundary]:
        tokens = [t for t in re.split(r"\s+", text) if t]
        if not tokens:
            return []
        total_ms = len(audio_seg)
        n = len(tokens)
        wb_list: List[WordBoundary] = []
        for i, tok in enumerate(tokens):
            start = (total_ms * i) / n
            end = (total_ms * (i + 1)) / n
            wb_list.append(WordBoundary(start_ms=start, end_ms=end, text=tok))
        return wb_list

    def html_to_speech(self, html_text: str, output_file: Path, metadata: dict | None = None) -> List[WordBoundary]:
        output_file = Path(output_file)
        metadata = metadata or {}
        metadata.update({"artist": f"Chatterbox TTS - {settings.tts_voice}", "language": f"{settings.tts_lang}"})

        text_chunks = self._prepare_text(html_text)
        if in_dev():
            output_file.with_suffix('.chunks.txt').write_text("\n\n##### chunk #####\n\n".join(text_chunks))

        chunk_results = []
        for idx, chunk in enumerate(text_chunks):
            raw_audio = self._post_chunk(chunk)
            audio_data = io.BytesIO(raw_audio)
            audio_data.seek(0)
            audio_seg = AudioSegment.from_file(audio_data, format='wav')
            if len(audio_seg) == 0:
                raise TTSEmptyAudioError("Received empty audio segment from Chatterbox API.")
            wbs = self._generate_word_boundaries(audio_seg, chunk)
            # Re-encode to WAV BytesIO for merging
            wav_buf = io.BytesIO()
            audio_seg.export(wav_buf, format='wav')
            wav_buf.seek(0)
            chunk_results.append({
                "idx": idx,
                "text": chunk,
                "audio_data": wav_buf,
                "wbs": wbs,
            })

        merged_audio, merged_wbs = self.merge_audios_and_word_boundaries(chunk_results, key="audio_data")
        if merged_audio is None or len(merged_audio) == 0:
            raise TTSEmptyAudioError("Merged audio is empty.")

        self.save_audio(merged_audio, output_file, metadata)
        if in_dev():
            helpers.save_wbs_as_json(merged_wbs, output_file.with_suffix('.wbs.txt'))

        return merged_wbs
