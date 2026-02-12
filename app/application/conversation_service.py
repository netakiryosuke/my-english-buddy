from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import cast

from app.domain.entity.conversation_memory import ConversationMemory
from app.domain.vo.chat_message import ChatMessage
from app.interface.chat_client import ChatClient


@dataclass
class ConversationService:
    chat_client: ChatClient
    conversation_memory: ConversationMemory = field(
        default_factory=lambda: ConversationMemory(max_messages=50)
    )
    memory_window: int = 20
    system_prompt: str | None = (
        "You are My English Buddy. Answer in clear, friendly English. "
        "If the user writes Japanese, you may include short Japanese hints."
    )

    _lock: Lock = field(default_factory=Lock, init=False, repr=False, compare=False)

    def reply(self, user_text: str) -> str:
        reply = self.prepare_reply(user_text)
        if reply:
            self.commit_assistant_reply(reply)
        return reply

    def prepare_reply(
        self,
        user_text: str,
        *,
        ephemeral_system_prompt: str | None = None,
    ) -> str:
        """Generate an assistant reply but do not store it in memory yet.

        This enables two-phase commit: only commit the assistant reply after it was
        fully spoken to the user.
        """
        user_text = user_text.strip()
        if not user_text:
            return ""

        with self._lock:
            self.conversation_memory.add_user(user_text)

            messages: list[ChatMessage] = []
            if self.system_prompt:
                messages.append(ChatMessage(role="system", content=self.system_prompt))
            if ephemeral_system_prompt:
                messages.append(
                    ChatMessage(role="system", content=ephemeral_system_prompt.strip())
                )
            messages.extend(self.conversation_memory.recent(self.memory_window))

        reply = cast(str, self.chat_client.complete_messages(messages=messages))
        return reply

    def commit_assistant_reply(self, reply: str) -> None:
        """Commit an assistant reply to memory (after it was spoken completely)."""
        reply = reply.strip()
        if not reply:
            return

        with self._lock:
            self.conversation_memory.add_assistant(reply)
