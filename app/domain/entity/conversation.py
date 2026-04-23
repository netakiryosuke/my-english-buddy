from app.domain.vo.chat_message import ChatMessage, ChatRole
from app.domain.vo.turn import Turn


class Conversation:

    def __init__(self, *, max_turns: int | None = None):
        self._max_turns = max_turns
        self._turns: list[Turn] = []
        self._pending_user_utterance: str | None = None

    def add_turn(self, user_utterance: str, assistant_reply: str) -> None:
        user_utterance = user_utterance.strip()
        assistant_reply = assistant_reply.strip()
        if not user_utterance or not assistant_reply:
            return

        self._turns.append(Turn(user_utterance=user_utterance, assistant_reply=assistant_reply))
        self._trim_if_needed()

    def start_turn(self, user_utterance: str) -> None:
        user_utterance = user_utterance.strip()
        if not user_utterance:
            return
        self._pending_user_utterance = user_utterance

    def complete_turn(self, assistant_reply: str) -> None:
        assistant_reply = assistant_reply.strip()
        if self._pending_user_utterance is None or not assistant_reply:
            return
        self._turns.append(
            Turn(
                user_utterance=self._pending_user_utterance,
                assistant_reply=assistant_reply,
            )
        )
        self._pending_user_utterance = None
        self._trim_if_needed()

    def cancel_turn(self) -> str | None:
        utterance = self._pending_user_utterance
        self._pending_user_utterance = None
        return utterance

    @property
    def has_pending_turn(self) -> bool:
        return self._pending_user_utterance is not None

    def recent_context(self, n: int) -> list[Turn]:
        if n <= 0:
            return []
        return self._turns[-n:]

    def build_messages(self, n: int) -> list[ChatMessage]:
        messages: list[ChatMessage] = []
        for turn in self.recent_context(n):
            messages.extend(turn.to_messages())
        if self._pending_user_utterance is not None:
            messages.append(
                ChatMessage(role=ChatRole.USER, content=self._pending_user_utterance)
            )
        return messages

    def clear(self) -> None:
        self._turns.clear()
        self._pending_user_utterance = None

    @property
    def turn_count(self) -> int:
        return len(self._turns)

    def _trim_if_needed(self) -> None:
        if self._max_turns is None:
            return
        if self._max_turns <= 0:
            self._turns.clear()
            return
        overflow = len(self._turns) - self._max_turns
        if overflow > 0:
            del self._turns[:overflow]
