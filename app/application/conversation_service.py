from __future__ import annotations

from dataclasses import dataclass

from app.llm.openai_client import OpenAIChatClient


@dataclass
class ConversationService:
    chat_client: OpenAIChatClient
    system_prompt: str | None = (
        # TODO: Make this configurable per user (UI / local storage).
        "You are My English Buddy. Answer in clear, friendly English. "
        "If the user writes Japanese, you may include short Japanese hints."
    )

    def reply(self, user_text: str) -> str:
        user_text = user_text.strip()
        if not user_text:
            return ""
        return self.chat_client.complete(system=self.system_prompt, user=user_text)
