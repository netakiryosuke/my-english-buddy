from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ChatRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str


class MemoryService:
    """In-memory, short-term conversation memory.

    This memory is ephemeral and cleared on process restart.
    """

    def __init__(self, *, max_messages: int | None = None):
        self._max_messages = max_messages
        self._messages: list[ChatMessage] = []

    def add(self, *, role: ChatRole, content: str) -> None:
        content = content.strip()
        if not content:
            return

        self._messages.append(ChatMessage(role=role, content=content))
        self._trim_if_needed()

    def add_user(self, content: str) -> None:
        self.add(role="user", content=content)

    def add_assistant(self, content: str) -> None:
        self.add(role="assistant", content=content)

    def recent(self, n: int) -> list[ChatMessage]:
        if n <= 0:
            return []
        return self._messages[-n:]

    def clear(self) -> None:
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)

    def _trim_if_needed(self) -> None:
        if self._max_messages is None:
            return
        if self._max_messages <= 0:
            self._messages.clear()
            return

        overflow = len(self._messages) - self._max_messages
        if overflow > 0:
            del self._messages[:overflow]
