from __future__ import annotations

from typing import Protocol

import numpy as np

AudioArray = np.ndarray


class SpeechToText(Protocol):
    def transcribe(self, audio: AudioArray) -> str:
        """Transcribe raw audio (float32 PCM ndarray) into text."""
        ...
