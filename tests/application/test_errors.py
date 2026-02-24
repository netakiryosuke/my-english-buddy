"""Unit tests for application error classes."""

import pytest

from app.application.errors import (
    ExternalServiceError,
    ChatClientError,
    SpeechToTextError,
    TextToSpeechError,
)


class TestExternalServiceError:
    """Test cases for ExternalServiceError."""

    def test_create_error(self):
        """Test creating an ExternalServiceError."""
        error = ExternalServiceError("Service failed")
        assert str(error) == "Service failed"
        assert isinstance(error, RuntimeError)

    def test_raise_error(self):
        """Test raising an ExternalServiceError."""
        with pytest.raises(ExternalServiceError) as exc_info:
            raise ExternalServiceError("Test error")
        assert "Test error" in str(exc_info.value)


class TestChatClientError:
    """Test cases for ChatClientError."""

    def test_create_error(self):
        """Test creating a ChatClientError."""
        error = ChatClientError("Chat failed")
        assert str(error) == "Chat failed"
        assert isinstance(error, ExternalServiceError)
        assert isinstance(error, RuntimeError)

    def test_raise_error(self):
        """Test raising a ChatClientError."""
        with pytest.raises(ChatClientError) as exc_info:
            raise ChatClientError("Chat error")
        assert "Chat error" in str(exc_info.value)


class TestSpeechToTextError:
    """Test cases for SpeechToTextError."""

    def test_create_error(self):
        """Test creating a SpeechToTextError."""
        error = SpeechToTextError("STT failed")
        assert str(error) == "STT failed"
        assert isinstance(error, ExternalServiceError)
        assert isinstance(error, RuntimeError)

    def test_raise_error(self):
        """Test raising a SpeechToTextError."""
        with pytest.raises(SpeechToTextError) as exc_info:
            raise SpeechToTextError("STT error")
        assert "STT error" in str(exc_info.value)


class TestTextToSpeechError:
    """Test cases for TextToSpeechError."""

    def test_create_error(self):
        """Test creating a TextToSpeechError."""
        error = TextToSpeechError("TTS failed")
        assert str(error) == "TTS failed"
        assert isinstance(error, ExternalServiceError)
        assert isinstance(error, RuntimeError)

    def test_raise_error(self):
        """Test raising a TextToSpeechError."""
        with pytest.raises(TextToSpeechError) as exc_info:
            raise TextToSpeechError("TTS error")
        assert "TTS error" in str(exc_info.value)
