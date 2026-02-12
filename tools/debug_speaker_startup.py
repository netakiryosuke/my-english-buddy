from __future__ import annotations

import argparse
import time
import sys
from pathlib import Path

import numpy as np

# Allow running this file directly (e.g. `python tools\\debug_speaker_startup.py`).
# When executed as a script, Python sets sys.path[0] to the script directory
# (`tools/`), so the repo root isn't importable by default.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.infrastructure.audio.speaker import Speaker


def _make_test_audio(sample_rate: int) -> np.ndarray:
    """Create audio with two short tones: one at t=0ms, one at t=350ms.

    If playback startup drops the beginning, the first tone may be missing while
    the second is still audible.
    """

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

    add_tone(0.0, 60.0, 880.0)
    add_tone(350.0, 60.0, 880.0)

    return np.clip(audio, -1.0, 1.0)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Diagnose Speaker playback startup truncation."
    )
    parser.add_argument("--sample-rate", type=int, default=24_000)
    parser.add_argument("--repeats", type=int, default=15)
    parser.add_argument("--gap-ms", type=int, default=250)
    parser.add_argument("--chunk-size", type=int, default=1024)
    args = parser.parse_args()

    speaker = Speaker(sample_rate=args.sample_rate)
    audio = _make_test_audio(args.sample_rate)

    print(
        "Playing test pattern: two tones (0ms and 350ms).\n"
        "If you sometimes hear only the second tone, the output stream startup is dropping audio."
    )

    for i in range(args.repeats):
        print(f"[{i + 1}/{args.repeats}] play")
        speaker.speak(audio, chunk_size=args.chunk_size)
        time.sleep(args.gap_ms / 1000.0)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
