import sounddevice as sd
import numpy as np
import time


class Speaker:
    def __init__(self, *, sample_rate: int = 24_000):
        self.sample_rate = sample_rate

    def speak(self, audio: np.ndarray) -> None:
        # Reshape for sounddevice compatibility
        if audio.ndim == 1:
            audio = audio.reshape(-1, 1)

        with sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32'
        ) as stream:
            time.sleep(0.1)
            stream.write(audio)
