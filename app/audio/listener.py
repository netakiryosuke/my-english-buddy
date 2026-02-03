from __future__ import annotations

import sounddevice as sd
import numpy as np

class Listener:
    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        channels: int = 1,
        silence_duration: float = 1.5,
        chunk_duration: float = 0.1,
        calibration_duration: float = 1.0,
        noise_threshold_multiplier: float = 3.0,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_duration = silence_duration
        self.chunk_duration = chunk_duration
        self.calibration_duration = calibration_duration
        self.noise_threshold_multiplier = noise_threshold_multiplier

    def _calibrate_noise_level(self, stream) -> float:
        """Measure ambient noise level and return threshold"""
        noise_samples = []
        calibration_chunks = int(self.calibration_duration / self.chunk_duration)

        for _ in range(calibration_chunks):
            chunk, _ = stream.read(int(self.sample_rate * self.chunk_duration))
            volume = float(np.abs(chunk).mean())
            noise_samples.append(volume)

        noise_level = np.mean(noise_samples)
        return noise_level * self.noise_threshold_multiplier

    def listen(self) -> np.ndarray:
        frames: list[np.ndarray] = []
        silent_time = 0.0
        speech_detected = False

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
        ) as stream:
            threshold = self._calibrate_noise_level(stream)

            while True:
                chunk, _ = stream.read(
                    int(self.sample_rate * self.chunk_duration)
                )

                frames.append(chunk)
                volume = float(np.abs(chunk).mean())

                if volume >= threshold:
                    silent_time = 0.0
                    speech_detected = True
                else:
                    silent_time += self.chunk_duration

                if speech_detected and silent_time >= self.silence_duration:
                    break

        return np.concatenate(frames, axis=0)
