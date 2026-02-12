from __future__ import annotations

import argparse
import platform
import sys

import sounddevice as sd


def _fmt_device(idx: int, dev: dict) -> str:
    name = dev.get("name", "?")
    hostapi = dev.get("hostapi", "?")
    sr = dev.get("default_samplerate", "?")
    out_ch = dev.get("max_output_channels", 0)
    in_ch = dev.get("max_input_channels", 0)
    return f"#{idx} hostapi={hostapi} sr={sr} in={in_ch} out={out_ch} name={name}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Print sounddevice/PortAudio diagnostics")
    parser.add_argument("--list", action="store_true", help="List all devices")
    args = parser.parse_args()

    print(f"python: {sys.version.splitlines()[0]}")
    print(f"platform: {platform.platform()}")
    print(f"sounddevice: {getattr(sd, '__version__', '?')}")

    try:
        pa_ver = sd.get_portaudio_version()
        pa_txt = sd.get_portaudio_version_text()
        print(f"portaudio: {pa_ver} ({pa_txt})")
    except Exception as e:
        print(f"portaudio: ? ({e})")

    print(f"default.device: {sd.default.device}")
    print(f"default.latency: {sd.default.latency}")

    devices = sd.query_devices()

    out_default = sd.default.device[1] if isinstance(sd.default.device, (list, tuple)) else None
    in_default = sd.default.device[0] if isinstance(sd.default.device, (list, tuple)) else None

    if in_default is not None and in_default >= 0:
        try:
            print("default input:", _fmt_device(in_default, devices[in_default]))
        except Exception:
            pass

    if out_default is not None and out_default >= 0:
        try:
            print("default output:", _fmt_device(out_default, devices[out_default]))
        except Exception:
            pass

    if args.list:
        print("\n-- devices --")
        for i, dev in enumerate(devices):
            print(_fmt_device(i, dev))

        print("\n-- hostapis --")
        for i, api in enumerate(sd.query_hostapis()):
            name = api.get("name", "?")
            default_in = api.get("default_input_device", "?")
            default_out = api.get("default_output_device", "?")
            print(f"#{i} name={name} default_in={default_in} default_out={default_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
