from dataclasses import dataclass

from app.domain.vo.chat_message import ChatMessage, ChatRole


@dataclass(frozen=True)
class Turn:

    user_utterance: str
    assistant_reply: str

    def to_messages(self) -> list[ChatMessage]:
        return [
            ChatMessage(role=ChatRole.USER, content=self.user_utterance),
            ChatMessage(role=ChatRole.ASSISTANT, content=self.assistant_reply),
        ]
