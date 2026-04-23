"""Unit tests for Turn value object."""

import pytest

from app.domain.vo.turn import Turn


class TestTurn:
    def test_create_turn(self):
        turn = Turn(user_utterance="Hello", assistant_reply="Hi there!")
        assert turn.user_utterance == "Hello"
        assert turn.assistant_reply == "Hi there!"

    def test_turn_is_immutable(self):
        turn = Turn(user_utterance="Hello", assistant_reply="Hi")
        with pytest.raises(AttributeError):
            turn.user_utterance = "Changed"  # type: ignore

    def test_turn_equality(self):
        t1 = Turn(user_utterance="Hello", assistant_reply="Hi")
        t2 = Turn(user_utterance="Hello", assistant_reply="Hi")
        t3 = Turn(user_utterance="Hello", assistant_reply="Hey")
        assert t1 == t2
        assert t1 != t3

    def test_to_messages(self):
        turn = Turn(user_utterance="Hello", assistant_reply="Hi")
        messages = turn.to_messages()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hi"
