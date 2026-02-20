from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    import numpy as np

    AudioArray = np.ndarray
else:
    AudioArray = Any


class TextToSpeech(Protocol):
    def synthesize(self, text: str) -> AudioArray:
        """Synthesize speech audio (float32 PCM ndarray) from text."""
        ...
