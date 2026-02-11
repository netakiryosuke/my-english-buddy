from threading import Event
import time

import sounddevice as sd
import numpy as np


class Speaker:
    def __init__(self, *, sample_rate: int = 24_000):
        self.sample_rate = sample_rate

    def speak(
        self,
        audio: np.ndarray,
        stop_event: Event | None = None,
        chunk_size: int = 1024,
    ) -> None:
        # Reshape for sounddevice compatibility
        if audio.ndim == 1:
            audio = audio.reshape(-1, 1)

        with sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        ) as stream:
            time.sleep(0.1)

            for i in range(0, len(audio), chunk_size):
                if stop_event and stop_event.is_set():
                    break

                chunk = audio[i:i + chunk_size]
                stream.write(chunk)
