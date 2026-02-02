from __future__ import annotations

from dataclasses import dataclass, field

from app.application.memory_service import MemoryService
from app.llm.openai_client import OpenAIChatClient


@dataclass
class ConversationService:
    chat_client: OpenAIChatClient
    memory: MemoryService = field(default_factory=lambda: MemoryService(max_messages=50))
    memory_window: int = 20
    system_prompt: str | None = (
        # TODO: Make this configurable per user (UI / local storage).
        "You are My English Buddy. Answer in clear, friendly English. "
        "If the user writes Japanese, you may include short Japanese hints."
    )

    def reply(self, user_text: str) -> str:
        user_text = user_text.strip()
        if not user_text:
            return ""

        self.memory.add_user(user_text)

        messages: list[dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        for m in self.memory.recent(self.memory_window):
            messages.append({"role": m.role, "content": m.content})

        reply = self.chat_client.complete_messages(messages=messages)
        self.memory.add_assistant(reply)
        return reply
