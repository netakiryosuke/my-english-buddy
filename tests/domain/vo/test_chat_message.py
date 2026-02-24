"""Unit tests for ChatMessage value object."""

import pytest

from app.domain.vo.chat_message import ChatMessage


class TestChatMessage:
    """Test cases for ChatMessage value object."""

    def test_create_user_message(self):
        """Test creating a user message."""
        message = ChatMessage(role="user", content="Hello")
        assert message.role == "user"
        assert message.content == "Hello"

    def test_create_assistant_message(self):
        """Test creating an assistant message."""
        message = ChatMessage(role="assistant", content="Hi there!")
        assert message.role == "assistant"
        assert message.content == "Hi there!"

    def test_create_system_message(self):
        """Test creating a system message."""
        message = ChatMessage(role="system", content="System prompt")
        assert message.role == "system"
        assert message.content == "System prompt"

    def test_message_is_immutable(self):
        """Test that ChatMessage is immutable (frozen dataclass)."""
        message = ChatMessage(role="user", content="Test")
        with pytest.raises(AttributeError):
            message.role = "assistant"  # type: ignore
        with pytest.raises(AttributeError):
            message.content = "New content"  # type: ignore

    def test_message_equality(self):
        """Test equality comparison of ChatMessage."""
        msg1 = ChatMessage(role="user", content="Hello")
        msg2 = ChatMessage(role="user", content="Hello")
        msg3 = ChatMessage(role="assistant", content="Hello")
        
        assert msg1 == msg2
        assert msg1 != msg3

    def test_message_with_empty_content(self):
        """Test creating message with empty content."""
        message = ChatMessage(role="user", content="")
        assert message.content == ""

    def test_message_with_multiline_content(self):
        """Test creating message with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        message = ChatMessage(role="user", content=content)
        assert message.content == content
