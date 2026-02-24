"""Unit tests for OpenAI ChatClient."""

from unittest.mock import Mock

import pytest

from app.application.errors import ChatClientError
from app.domain.vo.chat_message import ChatMessage
from app.infrastructure.openai.chat_client import OpenAIChatClient


class TestOpenAIChatClient:
    """Test cases for OpenAIChatClient."""

    def test_complete_with_system_and_user(self, mock_openai_client):
        """Test complete method with system and user messages."""
        # Setup mock response
        mock_choice = Mock()
        mock_choice.message.content = "Test response"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIChatClient(client=mock_openai_client, model="gpt-4")
        
        response = client.complete(system="System prompt", user="Hello")
        
        assert response == "Test response"
        mock_openai_client.chat.completions.create.assert_called_once()
        
        # Check the messages sent
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_complete_without_system(self, mock_openai_client):
        """Test complete method without system message."""
        mock_choice = Mock()
        mock_choice.message.content = "Response"
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIChatClient(client=mock_openai_client, model="gpt-4")
        
        response = client.complete(system=None, user="Hello")
        
        assert response == "Response"
        
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_complete_messages(self, mock_openai_client):
        """Test complete_messages method."""
        mock_choice = Mock()
        mock_choice.message.content = "  Response text  "
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIChatClient(client=mock_openai_client, model="gpt-4")
        
        messages = [
            ChatMessage(role="system", content="System"),
            ChatMessage(role="user", content="Hello"),
        ]
        
        response = client.complete_messages(messages=messages)
        
        # Should strip whitespace
        assert response == "Response text"
        
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "gpt-4"

    def test_complete_messages_empty_response(self, mock_openai_client):
        """Test complete_messages with empty response content."""
        mock_choice = Mock()
        mock_choice.message.content = None
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIChatClient(client=mock_openai_client, model="gpt-4")
        
        messages = [ChatMessage(role="user", content="Hello")]
        response = client.complete_messages(messages=messages)
        
        assert response == ""

    def test_complete_messages_no_choices_raises_error(self, mock_openai_client):
        """Test that no choices in response raises RuntimeError."""
        mock_response = Mock()
        mock_response.choices = []
        mock_openai_client.chat.completions.create.return_value = mock_response
        
        client = OpenAIChatClient(client=mock_openai_client, model="gpt-4")
        
        messages = [ChatMessage(role="user", content="Hello")]
        
        with pytest.raises(RuntimeError, match="no choices"):
            client.complete_messages(messages=messages)

    def test_complete_messages_openai_error_raises_chat_client_error(self, mock_openai_client):
        """Test that OpenAI API errors are wrapped in ChatClientError."""
        from openai import OpenAIError
        
        mock_openai_client.chat.completions.create.side_effect = OpenAIError("API Error")
        
        client = OpenAIChatClient(client=mock_openai_client, model="gpt-4")
        
        messages = [ChatMessage(role="user", content="Hello")]
        
        with pytest.raises(ChatClientError, match="API Error"):
            client.complete_messages(messages=messages)
