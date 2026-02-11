from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from app.domain.vo.chat_message import ChatMessage, ChatRole


class ChatClient(ABC):
    @abstractmethod
    def complete(self, *, system: str | None, user: str) -> str:
        """Return a single assistant message for a user input."""
        return ""

    @abstractmethod
    def complete_messages(self, *, messages: Sequence[ChatMessage]) -> str:
        """Return a completion given chat history messages."""
        return ""


__all__ = ["ChatClient", "ChatMessage", "ChatRole"]
