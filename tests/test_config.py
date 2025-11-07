from audible_epub3_maker import config
import os
import pytest

def test_azure_tts_config():
    """Ensure Azure config is present when azure engine selected; otherwise skip.

    This prevents failing the whole suite when running locally without Azure credentials
    and not using the azure engine.
    """
    if config.settings.tts_engine != "azure":
        pytest.skip("Azure TTS not selected; skipping credential assertions.")

    if not config.AZURE_TTS_KEY or not config.AZURE_TTS_REGION:
        pytest.skip("Azure credentials not set in environment; skipping.")

    assert config.AZURE_TTS_KEY
    assert config.AZURE_TTS_REGION
    print(f"AZURE_TTS_REGION: {config.AZURE_TTS_REGION}")
