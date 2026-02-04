import sounddevice as sd
import numpy as np


class Speaker:
    def __init__(self, *, sample_rate: int = 16_000):
        self.sample_rate = sample_rate

    def speak(self, audio: np.ndarray) -> None:
        sd.play(audio, self.sample_rate)
        sd.wait()
