from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str = "gpt-4o-mini"
    base_url: str | None = None
    timeout_seconds: float = 60.0


@dataclass(frozen=True)
class AppConfig:
    openai: OpenAIConfig

    @staticmethod
    def from_env() -> "AppConfig":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required. Set it in your environment before running."
            )

        model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
        base_url = os.getenv("OPENAI_BASE_URL") or None

        timeout_raw = os.getenv("OPENAI_TIMEOUT_SECONDS")
        timeout_seconds = 60.0
        if timeout_raw:
            try:
                timeout_seconds = float(timeout_raw)
            except ValueError as exc:
                raise ValueError(
                    "OPENAI_TIMEOUT_SECONDS must be a number (seconds)."
                ) from exc

        return AppConfig(
            openai=OpenAIConfig(
                api_key=api_key,
                model=model,
                base_url=base_url,
                timeout_seconds=timeout_seconds,
            )
        )
