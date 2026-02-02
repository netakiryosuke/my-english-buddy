from __future__ import annotations

from typing import TypeAlias

from openai import OpenAI

from app.config import DEFAULT_TIMEOUT_SECONDS, OpenAIConfig


try:
    from openai.types.chat import ChatCompletionMessageParam as _ChatCompletionMessageParam

    ChatCompletionMessageParam: TypeAlias = _ChatCompletionMessageParam
except Exception:  # pragma: no cover
    # Keep runtime working even if OpenAI SDK's type exports move.
    ChatCompletionMessageParam: TypeAlias = dict[str, str]


class OpenAIChatClient:
    def __init__(self, config: OpenAIConfig):
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )

    def complete(self, *, system: str | None, user: str) -> str:
        messages: list[ChatCompletionMessageParam] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        response = self._client.chat.completions.create(
            model=self._config.model,
            messages=messages,
        )

        choices = response.choices
        if not choices:
            raise RuntimeError(
                "OpenAI API returned no choices for chat completion response."
            )

        choice = choices[0]
        content = (choice.message.content or "").strip()
        return content
