from __future__ import annotations

import io
import numpy as np
from scipy.io.wavfile import write
from openai import OpenAI


class SpeechToText:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "gpt-4o-mini-transcribe",
        sample_rate: int = 16_000,
    ):
        self.sample_rate = sample_rate
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Convert recorded audio to text using OpenAI STT.
        """
        # numpy → wav (in memory)
        wav_buffer = io.BytesIO()
        write(wav_buffer, self.sample_rate, audio)
        wav_buffer.seek(0)

        response = self.client.audio.transcriptions.create(
            file=("speech.wav", wav_buffer),
            model=self.model,
        )

        return response.text.strip()
