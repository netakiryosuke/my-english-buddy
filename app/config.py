from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_TIMEOUT_SECONDS = 60.0


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str
    base_url: str | None = None


@dataclass(frozen=True)
class AppConfig:
    openai: OpenAIConfig

    @staticmethod
    def from_env() -> "AppConfig":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required.")

        model = os.getenv("OPENAI_MODEL")
        if not model:
            raise ValueError("OPENAI_MODEL is required.")

        base_url = os.getenv("OPENAI_BASE_URL") or None

        return AppConfig(
            openai=OpenAIConfig(
                api_key=api_key,
                model=model,
                base_url=base_url,
            )
        )
