from __future__ import annotations

from typing import Sequence, TypeAlias

from openai import OpenAI, OpenAIError

from app.domain.vo.chat_message import ChatMessage
from app.application.errors import ChatClientError

try:
    from openai.types.chat import ChatCompletionMessageParam as _ChatCompletionMessageParam

    ChatCompletionMessageParam: TypeAlias = _ChatCompletionMessageParam
except (ImportError, ModuleNotFoundError):
    ChatCompletionMessageParam: TypeAlias = dict[str, str]


class OpenAIChatClient:
    def __init__(self, client: OpenAI, model: str):
        self._client = client
        self._model = model

    def complete(self, *, system: str | None, user: str) -> str:
        messages: list[ChatMessage] = []
        if system:
            messages.append(ChatMessage(role="system", content=system))
        messages.append(ChatMessage(role="user", content=user))
        return self.complete_messages(messages=messages)

    def complete_messages(self, *, messages: Sequence[ChatMessage]) -> str:
        openai_messages: list[ChatCompletionMessageParam] = [
            {"role": message.role, "content": message.content} for message in messages
        ]
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
            )
        except OpenAIError as e:
            raise ChatClientError(str(e)) from e

        choices = response.choices
        if not choices:
            raise RuntimeError(
                "OpenAI API returned no choices for chat completion response."
            )

        choice = choices[0]
        content = (choice.message.content or "").strip()
        return content
