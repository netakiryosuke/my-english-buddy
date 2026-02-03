from __future__ import annotations

import sounddevice as sd
import numpy as np

class Listener:
    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        channels: int = 1,
        min_volume: float = 1e-3,
        silence_duration: float = 0.8,
        chunk_duration: float = 0.1,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.min_volume = min_volume
        self.silence_duration = silence_duration
        self.chunk_duration = chunk_duration

    def listen(self) -> np.ndarray:
        frames: list[np.ndarray] = []

        silent_time = 0.0

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
        ) as stream:
            while True:
                chunk, _ = stream.read(
                    int(self.sample_rate * self.chunk_duration)
                )

                frames.append(chunk)

                volume = float(np.abs(chunk).mean())

                if volume < self.min_volume:
                    silent_time += self.chunk_duration
                else:
                    silent_time = 0.0

                if silent_time >= self.silence_duration:
                    break

        return np.concatenate(frames, axis=0)
