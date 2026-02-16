from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    import numpy as np

    AudioArray = np.ndarray
else:
    AudioArray = Any


class SpeechToText(Protocol):
    def transcribe(self, audio: AudioArray) -> str:
        """Transcribe raw audio (float32 PCM ndarray) into text."""
        ...
