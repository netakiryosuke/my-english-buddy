from __future__ import annotations

from typing import TypeAlias

from openai import OpenAI

try:
    from openai.types.chat import ChatCompletionMessageParam as _ChatCompletionMessageParam

    ChatCompletionMessageParam: TypeAlias = _ChatCompletionMessageParam
except Exception:
    ChatCompletionMessageParam: TypeAlias = dict[str, str]


class OpenAIChatClient:
    def __init__(self, client: OpenAI, model: str):
        self._client = client
        self._model = model

    def complete(self, *, system: str | None, user: str) -> str:
        messages: list[ChatCompletionMessageParam] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        return self.complete_messages(messages=messages)

    def complete_messages(self, *, messages: list[ChatCompletionMessageParam]) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
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
