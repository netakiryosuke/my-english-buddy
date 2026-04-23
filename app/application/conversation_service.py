from dataclasses import dataclass, field
from threading import Lock

from app.application.port.chat_client import ChatClient
from app.domain.entity.conversation import Conversation
from app.domain.vo.chat_message import ChatMessage, ChatRole

_DEFAULT_MAX_TURNS: int = 25
_DEFAULT_CONTEXT_TURNS: int = 10


@dataclass
class ConversationService:
    chat_client: ChatClient
    conversation: Conversation = field(
        default_factory=lambda: Conversation(max_turns=_DEFAULT_MAX_TURNS)
    )
    context_turns: int = _DEFAULT_CONTEXT_TURNS
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
        user_text = user_text.strip()
        if not user_text:
            return ""

        with self._lock:
            self.conversation.start_turn(user_text)

            messages: list[ChatMessage] = []
            if self.system_prompt:
                messages.append(ChatMessage(role=ChatRole.SYSTEM, content=self.system_prompt))
            if ephemeral_system_prompt:
                messages.append(
                    ChatMessage(role=ChatRole.SYSTEM, content=ephemeral_system_prompt.strip())
                )
            messages.extend(self.conversation.build_messages(self.context_turns))

        reply = self.chat_client.complete_messages(messages=messages)
        if not reply.strip():
            with self._lock:
                if self.conversation.has_pending_turn:
                    self.conversation.cancel_turn()
        return reply

    def commit_assistant_reply(self, reply: str) -> None:
        """Commit an assistant reply to conversation (after it was spoken completely)."""
        reply = reply.strip()
        if not reply:
            return

        with self._lock:
            self.conversation.complete_turn(reply)
