from __future__ import annotations

from typing import Protocol, Sequence

from app.domain.vo.chat_message import ChatMessage, ChatRole


class ChatClient(Protocol):
    def complete(self, *, system: str | None, user: str) -> str:
        """Return a single assistant message for a user input."""
        ...

    def complete_messages(self, *, messages: Sequence[ChatMessage]) -> str:
        """Return a completion given chat history messages."""
        ...
