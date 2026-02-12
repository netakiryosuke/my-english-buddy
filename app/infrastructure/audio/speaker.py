from __future__ import annotations

from dataclasses import dataclass
from queue import Queue
from threading import Event, Lock, Thread
from typing import Optional

import numpy as np
import sounddevice as sd


@dataclass(frozen=True)
class _PlaybackRequest:
    audio: np.ndarray
    chunk_size: int
    stop_event: Optional[Event]
    done: Event


class Speaker:
    def __init__(self, *, sample_rate: int = 24_000, prime_silence_ms: int = 200):
        self.sample_rate = sample_rate
        self.prime_silence_ms = prime_silence_ms

        self._queue: Queue[_PlaybackRequest] = Queue()
        self._stream_lock = Lock()
        self._stream: sd.OutputStream | None = None
        self._stream_device: int | None = None

        self._worker_thread: Thread | None = None
        self._shutdown_event = Event()
        self._interrupt_event = Event()

    def speak(
        self,
        audio: np.ndarray,
        stop_event: Event | None = None,
        chunk_size: int = 1024,
    ) -> None:
        audio_float = np.asarray(audio, dtype=np.float32)
        if audio_float.ndim == 1:
            audio_float = audio_float.reshape(-1, 1)

        self._ensure_worker_started()
        self._ensure_stream_ready()

        done = Event()
        self._queue.put(
            _PlaybackRequest(
                audio=audio_float,
                chunk_size=chunk_size,
                stop_event=stop_event,
                done=done,
            )
        )
        done.wait()

    def interrupt(self) -> None:
        """Immediately interrupt current playback (best-effort)."""
        self._interrupt_event.set()

    def close(self) -> None:
        """Stop background thread and close audio stream."""
        self._shutdown_event.set()
        self._interrupt_event.set()

        # Unblock worker if it's waiting for a request.
        self._queue.put(
            _PlaybackRequest(
                audio=np.zeros((0, 1), dtype=np.float32),
                chunk_size=1024,
                stop_event=None,
                done=Event(),
            )
        )

        if self._worker_thread is not None:
            self._worker_thread.join(timeout=1.0)

        with self._stream_lock:
            if self._stream is not None:
                try:
                    self._stream.close()
                finally:
                    self._stream = None
                    self._stream_device = None

    def _ensure_worker_started(self) -> None:
        if self._worker_thread is not None:
            return

        self._worker_thread = Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def _default_output_device(self) -> int | None:
        device = sd.default.device
        if isinstance(device, (list, tuple)) and len(device) >= 2:
            out_dev = device[1]
            return out_dev if isinstance(out_dev, int) and out_dev >= 0 else None
        return None

    def _ensure_stream_ready(self) -> None:
        """Ensure OutputStream is open; reopen if default device changed."""

        desired_device = self._default_output_device()

        with self._stream_lock:
            if self._stream is not None and self._stream_device == desired_device:
                return

            if self._stream is not None:
                try:
                    self._stream.close()
                finally:
                    self._stream = None
                    self._stream_device = None

            self._stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="float32",
                device=desired_device,
            )
            self._stream.start()
            self._stream_device = desired_device

            # Prime the device/mixer path with a short silence to avoid
            # startup clicks/pops on some environments.
            prime_frames = int(self.sample_rate * (self.prime_silence_ms / 1000.0))
            if prime_frames > 0:
                silence = np.zeros((prime_frames, 1), dtype=np.float32)
                try:
                    self._stream.write(silence)
                except (sd.PortAudioError, OSError, RuntimeError, ValueError):
                    # If priming fails, continue; playback may still work.
                    pass

    def _write_audio(self, audio: np.ndarray, *, chunk_size: int, stop_event: Event | None) -> None:
        for i in range(0, len(audio), chunk_size):
            if self._shutdown_event.is_set() or self._interrupt_event.is_set():
                break
            if stop_event and stop_event.is_set():
                break

            chunk = audio[i : i + chunk_size]
            try:
                self._ensure_stream_ready()
                with self._stream_lock:
                    if self._stream is None:
                        break
                    self._stream.write(chunk)
            except (sd.PortAudioError, OSError, RuntimeError, ValueError):
                # If the stream becomes invalid (device change, etc.), attempt
                # to reopen once and retry this chunk.
                try:
                    self._ensure_stream_ready()
                    with self._stream_lock:
                        assert self._stream is not None
                        self._stream.write(chunk)
                except (sd.PortAudioError, OSError, RuntimeError, ValueError):
                    break

    def _worker_loop(self) -> None:
        while not self._shutdown_event.is_set():
            req = self._queue.get()

            if self._shutdown_event.is_set():
                req.done.set()
                break

            if req.audio.size == 0:
                req.done.set()
                continue

            self._interrupt_event.clear()
            self._ensure_stream_ready()
            self._write_audio(req.audio, chunk_size=req.chunk_size, stop_event=req.stop_event)
            req.done.set()
