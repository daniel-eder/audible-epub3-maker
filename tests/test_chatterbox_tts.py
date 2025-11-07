import io, wave, struct, math
from pathlib import Path
from unittest.mock import patch, Mock

from audible_epub3_maker.tts.chatterbox_tts import ChatterboxTTS

TEST_HTML = """<html><body><h1>Title</h1><p>Hello world. This is a test.</p></body></html>"""


def _make_wav_bytes(duration_ms: int = 500, freq: int = 440) -> bytes:
    sample_rate = 16000
    n_samples = int(sample_rate * (duration_ms / 1000.0))
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            val = int(32767.0 * math.sin(2 * math.pi * freq * (i / sample_rate)))
            wf.writeframes(struct.pack('<h', val))
    return buf.getvalue()


def test_chatterbox_html_to_speech(tmp_path: Path):
    out_file = tmp_path / "out.wav"
    wav_bytes = _make_wav_bytes()

    mock_resp = Mock()
    mock_resp.status_code = 200
    mock_resp.content = wav_bytes

    with patch("requests.post", return_value=mock_resp) as post_mock:
        tts = ChatterboxTTS()
        wbs = tts.html_to_speech(TEST_HTML, out_file)

    assert out_file.exists(), "Output audio file should be created"
    assert len(wbs) > 0, "Heuristic word boundaries should be generated"
    # Ensure we called API the expected number of times (single chunk for short input)
    post_mock.assert_called_once()
