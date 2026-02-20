from __future__ import annotations

from typing import Protocol

import numpy as np


class SpeechToText(Protocol):
    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe raw audio (float32 PCM ndarray) into text."""
        ...
