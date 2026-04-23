"""Unit tests for Conversation aggregate root."""

from app.domain.entity.conversation import Conversation


class TestConversation:
    def setup_method(self):
        self.conv = Conversation(max_turns=5)

    # --- add_turn ---

    def test_add_turn(self):
        self.conv.add_turn("Hello", "Hi there!")
        assert self.conv.turn_count == 1
        turns = self.conv.recent_context(1)
        assert turns[0].user_utterance == "Hello"
        assert turns[0].assistant_reply == "Hi there!"

    def test_add_turn_strips_whitespace(self):
        self.conv.add_turn("  Hello  ", "  Hi  ")
        turns = self.conv.recent_context(1)
        assert turns[0].user_utterance == "Hello"
        assert turns[0].assistant_reply == "Hi"

    def test_add_turn_ignores_empty_user(self):
        self.conv.add_turn("", "Hi")
        assert self.conv.turn_count == 0

    def test_add_turn_ignores_empty_assistant(self):
        self.conv.add_turn("Hello", "")
        assert self.conv.turn_count == 0

    # --- start_turn / complete_turn / cancel_turn ---

    def test_start_and_complete_turn(self):
        self.conv.start_turn("Hello")
        assert self.conv.has_pending_turn
        assert self.conv.turn_count == 0

        self.conv.complete_turn("Hi!")
        assert not self.conv.has_pending_turn
        assert self.conv.turn_count == 1
        assert self.conv.recent_context(1)[0].user_utterance == "Hello"
        assert self.conv.recent_context(1)[0].assistant_reply == "Hi!"

    def test_cancel_turn(self):
        self.conv.start_turn("Hello")
        utterance = self.conv.cancel_turn()
        assert utterance == "Hello"
        assert not self.conv.has_pending_turn
        assert self.conv.turn_count == 0

    def test_cancel_turn_when_no_pending(self):
        assert self.conv.cancel_turn() is None

    def test_complete_turn_without_start_is_noop(self):
        self.conv.complete_turn("Hi!")
        assert self.conv.turn_count == 0

    def test_complete_turn_with_empty_reply_is_noop(self):
        self.conv.start_turn("Hello")
        self.conv.complete_turn("")
        assert self.conv.has_pending_turn
        assert self.conv.turn_count == 0

    def test_start_turn_ignores_empty(self):
        self.conv.start_turn("")
        assert not self.conv.has_pending_turn

    # --- recent_context ---

    def test_recent_context(self):
        for i in range(3):
            self.conv.add_turn(f"User {i}", f"Bot {i}")
        turns = self.conv.recent_context(2)
        assert len(turns) == 2
        assert turns[0].user_utterance == "User 1"
        assert turns[1].user_utterance == "User 2"

    def test_recent_context_more_than_available(self):
        self.conv.add_turn("Hello", "Hi")
        turns = self.conv.recent_context(10)
        assert len(turns) == 1

    def test_recent_context_zero_or_negative(self):
        self.conv.add_turn("Hello", "Hi")
        assert self.conv.recent_context(0) == []
        assert self.conv.recent_context(-1) == []

    # --- build_messages ---

    def test_build_messages_with_completed_turns(self):
        self.conv.add_turn("Hello", "Hi")
        self.conv.add_turn("How?", "Good")
        messages = self.conv.build_messages(2)
        assert len(messages) == 4
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert messages[1].role == "assistant"
        assert messages[3].role == "assistant"

    def test_build_messages_includes_pending(self):
        self.conv.add_turn("Hello", "Hi")
        self.conv.start_turn("Next question")
        messages = self.conv.build_messages(5)
        assert len(messages) == 3
        assert messages[2].role == "user"
        assert messages[2].content == "Next question"

    # --- max_turns limit ---

    def test_max_turns_trims_oldest(self):
        for i in range(10):
            self.conv.add_turn(f"User {i}", f"Bot {i}")
        assert self.conv.turn_count == 5
        turns = self.conv.recent_context(5)
        assert turns[0].user_utterance == "User 5"
        assert turns[-1].user_utterance == "User 9"

    def test_no_max_turns_limit(self):
        conv = Conversation(max_turns=None)
        for i in range(100):
            conv.add_turn(f"User {i}", f"Bot {i}")
        assert conv.turn_count == 100

    # --- clear ---

    def test_clear(self):
        self.conv.add_turn("Hello", "Hi")
        self.conv.start_turn("Pending")
        self.conv.clear()
        assert self.conv.turn_count == 0
        assert not self.conv.has_pending_turn
        assert self.conv.build_messages(10) == []
