from __future__ import annotations

import argparse


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Text-only OpenAI chat test")
    parser.add_argument(
        "prompt",
        nargs="?",
        help="User prompt. If omitted, a built-in sample text is used.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to .env file (default: .env). Use empty to disable.",
    )
    parser.add_argument(
        "--system",
        default=None,
        help="Optional system prompt override (otherwise default is used).",
    )
    return parser.parse_args(argv)
