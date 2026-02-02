from __future__ import annotations

import io
import numpy as np
from scipy.io.wavfile import write
from openai import OpenAI


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

        wav_buffer = io.BytesIO()
        write(wav_buffer, self.sample_rate, audio)
        wav_buffer.seek(0)

        response = self.client.audio.transcriptions.create(
            file=("speech.wav", wav_buffer),
            model=self.model,
        )

        return response.text.strip()

    def _is_silent(self, audio: np.ndarray) -> bool:
        return float(np.abs(audio).mean()) < self.silence_threshold
