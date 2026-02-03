from __future__ import annotations

import argparse


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audio-based OpenAI chat application")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env). Use empty to disable.",
    )
    return parser.parse_args(argv)
