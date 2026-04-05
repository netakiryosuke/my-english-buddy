import numpy as np

from app.application.errors import TextToSpeechError
from app.utils.logger import Logger

_DEFAULT_VOICE = "af_heart"
_DEFAULT_LANG_CODE = "a"  # American English


class TextToSpeech:
    def __init__(
        self,
        *,
        voice: str = _DEFAULT_VOICE,
        lang_code: str = _DEFAULT_LANG_CODE,
        logger: Logger | None = None,
    ) -> None:
        self._voice = voice
        self._lang_code = lang_code
        self._logger = logger

        self._log(
            f"[TTS] Initializing local TTS (Kokoro): voice={voice}, lang_code={lang_code}"
        )

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

        self._log("[TTS] Local TTS initialized.")

    def _log(self, message: str) -> None:
        if self._logger:
            self._logger.log(message)

    def synthesize(self, text: str) -> np.ndarray:
        try:
            chunks = [chunk for _, _, chunk in self._pipeline(text, voice=self._voice)]
            if not chunks:
                return np.zeros(0, dtype=np.float32)
            # Kokoro は float32 を返すが、将来のライブラリ変更に備えて明示的に変換する。
            return np.concatenate(chunks).astype(np.float32)
        except TextToSpeechError:
            raise
        except Exception as e:
            raise TextToSpeechError(str(e)) from e
