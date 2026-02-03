from __future__ import annotations

import sounddevice as sd
import numpy as np

class Listener:
    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        channels: int = 1,
        record_seconds: float = 5.0,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.record_seconds = record_seconds

    def listen(self) -> np.ndarray:
        """Record audio from the default microphone.

        Returns:
            numpy.ndarray: shape (samples, channels)
        """

        audio = sd.rec(
            int(self.record_seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
        )
        sd.wait()

        return audio
