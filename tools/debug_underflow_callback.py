from __future__ import annotations

import argparse
import queue
import time

import numpy as np
import sounddevice as sd


def _make_test_audio(sample_rate: int) -> np.ndarray:
    """Two tones: one at t=0ms and one at t=350ms."""

    duration_s = 1.0
    n = int(sample_rate * duration_s)
    audio = np.zeros(n, dtype=np.float32)

    def add_tone(start_ms: float, tone_ms: float, freq_hz: float = 880.0) -> None:
        start = int(sample_rate * (start_ms / 1000.0))
        length = int(sample_rate * (tone_ms / 1000.0))
        end = min(n, start + length)
        if end <= start:
            return

        t = np.arange(end - start, dtype=np.float32) / float(sample_rate)
        window = np.hanning(end - start).astype(np.float32)
        tone = (0.35 * np.sin(2.0 * np.pi * freq_hz * t)).astype(np.float32)
        audio[start:end] += tone * window

    add_tone(0.0, 60.0)
    add_tone(350.0, 60.0)
    return np.clip(audio, -1.0, 1.0)


class StatusCounter:
    def __init__(self) -> None:
        self.any = 0
        self.output_underflow = 0
        self.output_overflow = 0
        self.input_underflow = 0
        self.input_overflow = 0
        self.priming_output = 0

    def add(self, status: sd.CallbackFlags) -> None:
        if not status:
            return
        self.any += 1
        # These attributes exist on CallbackFlags; access defensively.
        if getattr(status, "output_underflow", False):
            self.output_underflow += 1
        if getattr(status, "output_overflow", False):
            self.output_overflow += 1
        if getattr(status, "input_underflow", False):
            self.input_underflow += 1
        if getattr(status, "input_overflow", False):
            self.input_overflow += 1
        if getattr(status, "priming_output", False):
            self.priming_output += 1

    def summary(self) -> str:
        return (
            f"status_any={self.any} "
            f"out_underflow={self.output_underflow} out_overflow={self.output_overflow} "
            f"in_underflow={self.input_underflow} in_overflow={self.input_overflow} "
            f"priming_output={self.priming_output}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Playback using callback and print PortAudio status flags (underflow etc)."
    )
    parser.add_argument("--sample-rate", type=int, default=24_000)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--gap-ms", type=int, default=250)
    parser.add_argument(
        "--latency",
        default=None,
        help="PortAudio latency: low/high or float seconds (e.g. 0.2)",
    )
    parser.add_argument(
        "--blocksize",
        type=int,
        default=None,
        help="PortAudio blocksize frames (e.g. 2048).",
    )
    parser.add_argument(
        "--prime-ms",
        type=int,
        default=0,
        help="Write/prime silence for N ms before audio in the callback.",
    )
    args = parser.parse_args()

    latency: str | float | None = None
    if args.latency is not None:
        try:
            latency = float(args.latency)
        except ValueError:
            latency = args.latency

    audio = _make_test_audio(args.sample_rate).reshape(-1, 1)

    print(
        "Callback test: two tones (0ms and 350ms).\n"
        "If you see output_underflow increments, you are starving the audio device.\n"
    )
    print(f"latency={latency} blocksize={args.blocksize} prime_ms={args.prime_ms}")

    for i in range(args.repeats):
        status_counter = StatusCounter()
        done_q: queue.Queue[None] = queue.Queue(maxsize=1)

        prime_frames = int(args.sample_rate * (args.prime_ms / 1000.0))
        cursor = 0
        primed = 0

        def callback(
            outdata,
            frames,
            _,
            status,
            *,
            _status_counter=status_counter,
            _done_q=done_q,
            _prime_frames=prime_frames,
            _audio=audio,
        ):  # noqa: ANN001
            nonlocal cursor, primed
            _status_counter.add(status)

            outdata.fill(0)

            if primed < _prime_frames:
                to_prime = min(frames, _prime_frames - primed)
                # keep silence
                primed += to_prime
                return

            remaining = len(_audio) - cursor
            if remaining <= 0:
                try:
                    _done_q.put_nowait(None)
                except queue.Full:
                    pass
                raise sd.CallbackStop

            n = min(frames, remaining)
            outdata[:n] = _audio[cursor : cursor + n]
            cursor += n

        print(f"[{i + 1}/{args.repeats}] play")
        with sd.OutputStream(
            samplerate=args.sample_rate,
            channels=1,
            dtype="float32",
            latency=latency,
            blocksize=args.blocksize,
            callback=callback,
        ):
            done_q.get()

        print("  ", status_counter.summary())
        time.sleep(args.gap_ms / 1000.0)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
