from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread

import numpy as np
import sounddevice as sd


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

        self._recalibration_requested = Event()
        self._threshold_lock = Lock()
        self._last_threshold: float | None = None

    def request_recalibration(self) -> None:
        """Request noise recalibration.

        This method is thread-safe and can be called from UI threads.
        The recalibration itself will be performed from the listening loop
        using the same InputStream when the listener is idle (not in speech).
        """
        self._recalibration_requested.set()

    def get_last_threshold(self) -> float | None:
        with self._threshold_lock:
            return self._last_threshold

    def _calibrate_noise_level(self, stream) -> float:
        noise_samples = []
        calibration_chunks = int(self.calibration_duration / self.chunk_duration)

        for _ in range(calibration_chunks):
            chunk, _ = stream.read(int(self.sample_rate * self.chunk_duration))
            volume = float(np.abs(chunk).mean())
            noise_samples.append(volume)

        if not noise_samples:
            raise RuntimeError(
                "Failed to calibrate noise level: no audio samples were collected."
            )

        noise_level = np.mean(noise_samples)
        return noise_level * self.noise_threshold_multiplier

    def _calibrate(
        self,
        stream,
        *,
        on_calibration_start: Callable[[], None] | None = None,
        on_calibration_end: Callable[[float], None] | None = None,
    ) -> float:
        if on_calibration_start:
            with suppress(Exception):
                on_calibration_start()

        threshold = self._calibrate_noise_level(stream)
        with self._threshold_lock:
            self._last_threshold = float(threshold)

        if on_calibration_end:
            with suppress(Exception):
                on_calibration_end(float(threshold))

        return float(threshold)

    def listen(
        self,
        *,
        utterance_queue: Queue[np.ndarray],
        stop_event: Event,
        on_speech_start: Callable[[], None] | None = None,
        on_calibration_start: Callable[[], None] | None = None,
        on_calibration_end: Callable[[float], None] | None = None,
        on_calibration_error: Callable[[Exception], None] | None = None,
    ) -> Thread:
        """Listen continuously and publish utterances to a queue.

        This spawns a daemon thread and returns it.
        """
        thread = Thread(
            target=self._utterance_listen_loop,
            kwargs={
                "utterance_queue": utterance_queue,
                "stop_event": stop_event,
                "on_speech_start": on_speech_start,
                "on_calibration_start": on_calibration_start,
                "on_calibration_end": on_calibration_end,
                "on_calibration_error": on_calibration_error,
            },
            daemon=True,
        )
        thread.start()
        return thread

    def _utterance_listen_loop(
        self,
        *,
        utterance_queue: Queue[np.ndarray],
        stop_event: Event,
        on_speech_start: Callable[[], None] | None = None,
        on_calibration_start: Callable[[], None] | None = None,
        on_calibration_end: Callable[[float], None] | None = None,
        on_calibration_error: Callable[[Exception], None] | None = None,
    ) -> None:
        frames: list[np.ndarray] = []
        silent_time = 0.0
        speech_detected = False
        started_notified = False

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
        ) as stream:
            try:
                threshold = self._calibrate(
                    stream,
                    on_calibration_start=on_calibration_start,
                    on_calibration_end=on_calibration_end,
                )
            except Exception as e:
                if on_calibration_error:
                    with suppress(Exception):
                        on_calibration_error(e)
                stop_event.set()
                return

            while not stop_event.is_set():
                # Perform (re)calibration only when idle to avoid disrupting an utterance.
                if self._recalibration_requested.is_set() and (not speech_detected):
                    self._recalibration_requested.clear()
                    try:
                        threshold = self._calibrate(
                            stream,
                            on_calibration_start=on_calibration_start,
                            on_calibration_end=on_calibration_end,
                        )
                    except Exception as e:  # Keep listening even if recalibration fails.
                        if on_calibration_error:
                            with suppress(Exception):
                                on_calibration_error(e)

                chunk, _ = stream.read(int(self.sample_rate * self.chunk_duration))
                volume = float(np.abs(chunk).mean())

                if volume >= threshold:
                    silent_time = 0.0
                    if not speech_detected:
                        speech_detected = True
                        if (not started_notified) and on_speech_start:
                            started_notified = True
                            with suppress(Exception):
                                on_speech_start()
                    frames.append(chunk)
                elif speech_detected:
                    silent_time += self.chunk_duration
                    frames.append(chunk)

                if speech_detected and silent_time >= self.silence_duration:
                    if frames:
                        utterance = np.concatenate(frames, axis=0)
                        self._put_drop_oldest(utterance_queue, utterance)

                    frames = []
                    silent_time = 0.0
                    speech_detected = False
                    started_notified = False

        # Drain any partial utterance on stop.
        if frames and speech_detected:
            utterance = np.concatenate(frames, axis=0)
            self._put_drop_oldest(utterance_queue, utterance)

    @staticmethod
    def _put_drop_oldest(queue: Queue[np.ndarray], item: np.ndarray) -> None:
        while True:
            try:
                queue.put_nowait(item)
                return
            except Full:
                try:
                    queue.get_nowait()
                except Empty:
                    return
