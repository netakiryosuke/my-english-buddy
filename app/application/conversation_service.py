from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.entity.conversation_memory import ConversationMemory
from app.domain.vo.chat_message import ChatMessage
from app.interface.chat_client import ChatClient


@dataclass
class ConversationService:
    chat_client: ChatClient
    memory_service: ConversationMemory = field(
        default_factory=lambda: ConversationMemory(max_messages=50)
    )
    memory_window: int = 20
    system_prompt: str | None = (
        "You are My English Buddy. Answer in clear, friendly English. "
        "If the user writes Japanese, you may include short Japanese hints."
    )

    def reply(self, user_text: str) -> str:
        user_text = user_text.strip()
        if not user_text:
            return ""

        self.memory_service.add_user(user_text)

        messages: list[ChatMessage] = []
        if self.system_prompt:
            messages.append(ChatMessage(role="system", content=self.system_prompt))
        for recent_message in self.memory_service.recent(self.memory_window):
            messages.append(recent_message)

        reply = str(self.chat_client.complete_messages(messages=messages))
        self.memory_service.add_assistant(reply)
        return reply
