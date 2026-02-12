from __future__ import annotations

import argparse
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


def play_sd_play(audio: np.ndarray, sample_rate: int) -> None:
    sd.play(audio, samplerate=sample_rate)
    sd.wait()


def play_stream_write(
    audio: np.ndarray,
    sample_rate: int,
    chunk_size: int,
    latency: str | float | None,
    blocksize: int | None,
) -> None:
    if audio.ndim == 1:
        audio = audio.reshape(-1, 1)

    with sd.OutputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        latency=latency,
        blocksize=blocksize,
    ) as stream:
        # Intentionally do NOT sleep here; this reproduces the typical startup behavior.
        for i in range(0, len(audio), chunk_size):
            stream.write(audio[i : i + chunk_size])


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare sd.play vs OutputStream.write startup")
    parser.add_argument("--sample-rate", type=int, default=24_000)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--gap-ms", type=int, default=250)
    parser.add_argument("--chunk-size", type=int, default=1024)
    parser.add_argument(
        "--latency",
        default=None,
        help="PortAudio latency: low/high or a float seconds (e.g. 0.2)",
    )
    parser.add_argument(
        "--blocksize",
        type=int,
        default=None,
        help="PortAudio blocksize frames (e.g. 2048).",
    )
    parser.add_argument(
        "--mode",
        choices=["play", "stream"],
        default="stream",
        help="Playback mode to test.",
    )
    args = parser.parse_args()

    latency: str | float | None = None
    if args.latency is not None:
        try:
            latency = float(args.latency)
        except ValueError:
            latency = args.latency

    audio = _make_test_audio(args.sample_rate)

    print(
        "Test pattern: two tones (0ms and 350ms).\n"
        "- If only the 2nd tone is audible sometimes, startup drops audio.\n"
        "- Compare 'play' (buffered) vs 'stream' (write loop).\n"
    )
    print(f"mode={args.mode} chunk_size={args.chunk_size} latency={latency} blocksize={args.blocksize}")

    for i in range(args.repeats):
        print(f"[{i + 1}/{args.repeats}] {args.mode}")
        if args.mode == "play":
            play_sd_play(audio, args.sample_rate)
        else:
            play_stream_write(audio, args.sample_rate, args.chunk_size, latency, args.blocksize)
        time.sleep(args.gap_ms / 1000.0)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
