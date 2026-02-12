from __future__ import annotations

import io

import numpy as np
from openai import OpenAI, OpenAIError
from scipy.io.wavfile import write

from app.interface.errors import SpeechToTextError


class SpeechToText:
    def __init__(
        self,
        *,
        client: OpenAI,
        model: str = "gpt-4o-mini-transcribe",
        sample_rate: int = 16_000,
        silence_threshold: float = 1e-3,
    ):
        self.client = client
        self.model = model
        self.sample_rate = sample_rate
        self.silence_threshold = silence_threshold

    def transcribe(self, audio: np.ndarray) -> str:
        if self._is_silent(audio):
            return ""

        audio = np.clip(audio, -1.0, 1.0)
        audio_int16 = (audio * 32767).astype(np.int16)

        wav_buffer = io.BytesIO()
        write(wav_buffer, self.sample_rate, audio_int16)
        wav_buffer.seek(0)

        try:
            response = self.client.audio.transcriptions.create(
                file=("speech.wav", wav_buffer),
                model=self.model,
            )
            return response.text.strip()
        except OpenAIError as e:
            raise SpeechToTextError(str(e)) from e

    def _is_silent(self, audio: np.ndarray) -> bool:
        audio_float = np.asarray(audio, dtype=np.float32)
        rms = np.sqrt(np.mean(audio_float**2))
        return rms < self.silence_threshold
