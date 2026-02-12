from __future__ import annotations

import numpy as np
from openai import OpenAI, OpenAIError

from app.interface.errors import TextToSpeechError


class TextToSpeech:
    def __init__(
        self,
        *,
        client: OpenAI,
        model: str = "gpt-4o-mini-tts",
        voice: str = "alloy",
    ):
        self.client = client
        self.model = model
        self.voice = voice

    def synthesize(self, text: str) -> np.ndarray:
        try:
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format="pcm",
            )
            pcm_bytes = response.read()
        except OpenAIError as e:
            raise TextToSpeechError(str(e)) from e

        audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
        audio_float = audio_int16.astype(np.float32) / 32767.0

        return audio_float
