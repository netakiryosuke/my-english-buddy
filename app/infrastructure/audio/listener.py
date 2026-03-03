from collections.abc import Callable
from contextlib import suppress
from queue import Empty, Full, Queue
from threading import Event, Lock, Thread

import numpy as np
import sounddevice as sd

try:
    import webrtcvad  # type: ignore
except (ModuleNotFoundError, ImportError, OSError):  # Optional dependency (binary extension can fail to load).
    webrtcvad = None


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
        voice_gate_enabled: bool = True,
        voice_gate_aggressiveness: int = 2,
        voice_gate_frame_ms: int = 20,
        voice_gate_min_speech_ms: int = 250,
        voice_gate_min_speech_ratio: float = 0.12,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_duration = silence_duration
        self.chunk_duration = chunk_duration
        self.calibration_duration = calibration_duration
        self.noise_threshold_multiplier = noise_threshold_multiplier

        self.voice_gate_enabled = voice_gate_enabled
        self.voice_gate_aggressiveness = voice_gate_aggressiveness
        self.voice_gate_frame_ms = voice_gate_frame_ms
        self.voice_gate_min_speech_ms = voice_gate_min_speech_ms
        self.voice_gate_min_speech_ratio = voice_gate_min_speech_ratio

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
                        if self._should_enqueue_utterance(frames=frames):
                            self._put_drop_oldest(utterance_queue, utterance)

                    frames = []
                    silent_time = 0.0
                    speech_detected = False
                    started_notified = False

        # Drain any partial utterance on stop.
        if frames and speech_detected:
            utterance = np.concatenate(frames, axis=0)
            if self._should_enqueue_utterance(frames=frames):
                self._put_drop_oldest(utterance_queue, utterance)

    def _should_enqueue_utterance(
        self,
        *,
        frames: list[np.ndarray],
    ) -> bool:
        if not self.voice_gate_enabled:
            return True
        if webrtcvad is None:
            # Optional dependency not installed; keep existing behavior.
            return True

        # Remove the trailing silence tail we intentionally captured for end-of-utterance detection.
        # This improves VAD speech ratio for short utterances.
        silence_chunks = int(self.silence_duration / self.chunk_duration)
        vad_frames = frames
        if silence_chunks > 0 and len(frames) > silence_chunks:
            vad_frames = frames[:-silence_chunks]

        if not vad_frames:
            return False

        audio = np.concatenate(vad_frames, axis=0)
        return self._is_voice_like(audio)

    def _is_voice_like(self, audio: np.ndarray) -> bool:
        # WebRTC VAD supports only 8/16/32/48kHz mono, 16-bit PCM.
        if self.sample_rate not in {8000, 16000, 32000, 48000}:
            return True

        audio_arr = np.asarray(audio, dtype=np.float32)
        if audio_arr.ndim == 2:
            # (samples, channels)
            audio_1d = audio_arr.mean(axis=1)
        else:
            audio_1d = audio_arr

        audio_1d = np.clip(audio_1d, -1.0, 1.0)
        pcm16 = (audio_1d * 32767).astype(np.int16)

        frame_ms = int(self.voice_gate_frame_ms)
        if frame_ms not in (10, 20, 30):
            frame_ms = 20

        frame_samples = int(self.sample_rate * frame_ms / 1000)
        if frame_samples <= 0:
            return True

        total_frames = len(pcm16) // frame_samples
        if total_frames <= 0:
            return False

        try:
            aggressiveness = int(self.voice_gate_aggressiveness)
        except (TypeError, ValueError):
            aggressiveness = 3
        if aggressiveness < 0:
            aggressiveness = 0
        elif aggressiveness > 3:
            aggressiveness = 3

        vad = webrtcvad.Vad(aggressiveness)

        speech_frames = 0
        for i in range(total_frames):
            start = i * frame_samples
            end = start + frame_samples
            frame_bytes = pcm16[start:end].tobytes()
            if vad.is_speech(frame_bytes, self.sample_rate):
                speech_frames += 1

        speech_ms = speech_frames * frame_ms
        speech_ratio = speech_frames / total_frames

        return (speech_ms >= int(self.voice_gate_min_speech_ms)) and (
            speech_ratio >= float(self.voice_gate_min_speech_ratio)
        )

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
