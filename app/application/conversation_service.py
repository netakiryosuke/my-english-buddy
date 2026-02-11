from __future__ import annotations

from dataclasses import dataclass, field

from app.application.memory_service import MemoryService
from app.interface.chat_client import ChatClient, ChatMessage


@dataclass
class ConversationService:
    chat_client: ChatClient
    memory_service: MemoryService = field(default_factory=lambda: MemoryService(max_messages=50))
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
            messages.append({"role": "system", "content": self.system_prompt})
        for recent_message in self.memory_service.recent(self.memory_window):
            messages.append({"role": recent_message.role, "content": recent_message.content})

        reply = self.chat_client.complete_messages(messages=messages)
        self.memory_service.add_assistant(reply)
        return reply
