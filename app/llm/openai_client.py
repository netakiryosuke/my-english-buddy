from __future__ import annotations

from dataclasses import dataclass

from openai import OpenAI

from app.config import DEFAULT_TIMEOUT_SECONDS, OpenAIConfig


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class OpenAIChatClient:
    def __init__(self, config: OpenAIConfig):
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

    def complete(self, *, system: str | None, user: str) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        response = self._client.chat.completions.create(
            model=self._config.model,
            messages=messages,
        )

        choice = response.choices[0]
        content = (choice.message.content or "").strip()
        return content
