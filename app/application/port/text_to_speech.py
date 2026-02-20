from __future__ import annotations

from typing import Protocol

import numpy as np

AudioArray = np.ndarray


class TextToSpeech(Protocol):
    def synthesize(self, text: str) -> AudioArray:
        """Synthesize speech audio (float32 PCM ndarray) from text."""
        ...
