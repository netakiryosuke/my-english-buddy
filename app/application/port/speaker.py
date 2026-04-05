from threading import Event
from typing import Protocol

import numpy as np


class Speaker(Protocol):
    def speak(
        self,
        audio: np.ndarray,
        stop_event: Event | None = None,
    ) -> bool:
        """Play back audio.  Returns True if playback completed, False if interrupted."""
        ...
