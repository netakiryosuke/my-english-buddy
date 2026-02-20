from __future__ import annotations

from typing import Protocol

import numpy as np


class TextToSpeech(Protocol):
    def synthesize(self, text: str) -> np.ndarray:
        """Synthesize speech audio (float32 PCM ndarray) from text."""
        ...
