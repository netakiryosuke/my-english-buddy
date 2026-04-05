import numpy as np

from app.application.errors import TextToSpeechError

_DEFAULT_VOICE = "af_heart"
_DEFAULT_LANG_CODE = "a"  # American English


class TextToSpeech:
    def __init__(
        self,
        *,
        voice: str = _DEFAULT_VOICE,
        lang_code: str = _DEFAULT_LANG_CODE,
    ) -> None:
        self._voice = voice
        try:
            from kokoro import KPipeline
        except ModuleNotFoundError as e:
            raise TextToSpeechError(
                "Local TTS provider requires 'kokoro'. "
                "Install it with: uv sync --extra local-tts"
            ) from e
        except Exception as e:
            raise TextToSpeechError(
                "Failed to import local TTS dependencies. "
                f"Original error: {e}"
            ) from e

        try:
            # KPipeline のロード時にモデルが Hugging Face からダウンロードされる（初回のみ）。
            self._pipeline = KPipeline(lang_code=lang_code)
        except Exception as e:
            raise TextToSpeechError(
                f"Failed to initialize Kokoro TTS pipeline: {e}"
            ) from e

    def synthesize(self, text: str) -> np.ndarray:
        try:
            chunks = [chunk for _, _, chunk in self._pipeline(text, voice=self._voice)]
            if not chunks:
                return np.zeros(0, dtype=np.float32)
            return np.concatenate(chunks).astype(np.float32)
        except TextToSpeechError:
            raise
        except Exception as e:
            raise TextToSpeechError(str(e)) from e
