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
    ):
        self.client = client
        self.model = model
        self.sample_rate = sample_rate

    def transcribe(self, audio: np.ndarray) -> str:
        wav_buffer = io.BytesIO()
        write(wav_buffer, self.sample_rate, audio)
        wav_buffer.seek(0)

        response = self.client.audio.transcriptions.create(
            file=("speech.wav", wav_buffer),
            model=self.model,
        )

        return response.text.strip()
