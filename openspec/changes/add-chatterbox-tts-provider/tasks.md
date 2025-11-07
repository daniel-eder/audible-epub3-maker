# Tasks: add-chatterbox-tts-provider

1. Add config variables to `config.py` for chatterbox (base URL + params) (with safe defaults)
2. Implement `audible_epub3_maker/tts/chatterbox_tts.py` subclassing `BaseTTS`
3. Update `audible_epub3_maker/tts/__init__.py` factory to support `chatterbox`
4. Adjust worker logic to tolerate empty word boundaries and skip alignment gracefully
5. Add unit test `tests/test_chatterbox_tts.py` mocking HTTP POST and validating audio saved
6. Create `docker-compose.chatterbox-example.yml` with both services
7. Extend README: new engine docs + environment variable table + usage example
8. Update OpenSpec: create spec file with ADDED requirements and scenarios
9. Run pytest and ensure all tests pass
10. Review and refine spec vs implementation, finalize change directory
