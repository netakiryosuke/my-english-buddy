from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from app.domain.gateway.errors import SpeechToTextError

if TYPE_CHECKING:
    from faster_whisper import WhisperModel


class SpeechToText:
    def __init__(
        self,
        *,
        model: str = "distil-large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        language: str = "en",
    ) -> None:
        self.model_name = model
        self.language = language

        try:
            from faster_whisper import WhisperModel as _WhisperModel
        except ModuleNotFoundError as e:
            raise SpeechToTextError(
                "Local STT provider requires 'faster-whisper'. "
                "Install it with: uv sync --extra local-stt"
            ) from e

        try:
            self._model: WhisperModel = _WhisperModel(
                self.model_name,
                device=device,
                compute_type=compute_type,
                num_workers=2,
            )
        except Exception as e:
            raise SpeechToTextError(
                "Failed to initialize local STT model. "
                "If you want to use GPU, ensure CUDA 12 + cuDNN 9 are installed. "
                "Otherwise switch back to OpenAI STT (MY_ENGLISH_BUDDY_STT_PROVIDER=openai). "
                f"Original error: {e}"
            ) from e

    def transcribe(self, audio: np.ndarray) -> str:
        try:
            audio_1d = np.asarray(audio, dtype=np.float32).squeeze()
            if audio_1d.ndim != 1:
                raise ValueError(f"Expected 1D audio after squeeze. Got shape={audio_1d.shape!r}")

            # Listener produces float32 PCM in [-1, 1] at 16kHz.
            audio_1d = np.clip(audio_1d, -1.0, 1.0)
            audio_1d = np.ascontiguousarray(audio_1d)

            segments, _info = self._model.transcribe(
                audio_1d,
                language=self.language,
                vad_filter=False,
                condition_on_previous_text=False,
                without_timestamps=True,
                beam_size=5,
            )

            # `segments` is a generator; force evaluation.
            text = "".join(segment.text for segment in segments).strip()
            return text
        except SpeechToTextError:
            raise
        except Exception as e:
            raise SpeechToTextError(str(e)) from e
