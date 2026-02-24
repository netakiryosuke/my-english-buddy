"""Common fixtures and configuration for pytest."""

import pytest
from unittest.mock import MagicMock
import numpy as np

from app.domain.vo.chat_message import ChatMessage


@pytest.fixture
def sample_chat_message() -> ChatMessage:
    """Create a sample chat message for testing."""
    return ChatMessage(role="user", content="Hello, world!")


@pytest.fixture
def sample_audio_data() -> np.ndarray:
    """Create sample audio data for testing (1 second of silence at 16kHz)."""
    return np.zeros(16000, dtype=np.float32)


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    return MagicMock()
