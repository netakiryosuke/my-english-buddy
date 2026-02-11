from __future__ import annotations

from typing import Literal, Protocol, Sequence, TypedDict


ChatRole = Literal["system", "user", "assistant"]


class ChatMessage(TypedDict):
    role: ChatRole
    content: str


class ChatClient(Protocol):
    def complete(self, *, system: str | None, user: str) -> str:
        """Return a single assistant message for a user input."""
        ...

    def complete_messages(self, *, messages: Sequence[ChatMessage]) -> str:
        """Return a completion given chat history messages."""
        ...
