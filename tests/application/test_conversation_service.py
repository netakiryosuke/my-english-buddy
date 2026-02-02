"""Unit tests for ConversationService."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, call

from app.application.conversation_service import ConversationService
from app.application.memory_service import MemoryService
from app.llm.openai_client import OpenAIChatClient


class TestConversationService(unittest.TestCase):
    """Test cases for ConversationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_chat_client = MagicMock(spec=OpenAIChatClient)
        self.service = ConversationService(chat_client=self.mock_chat_client)

    def test_reply_sends_system_and_user_message(self):
        """Test that reply sends system prompt and user message."""
        self.mock_chat_client.complete_messages.return_value = "Test response"
        
        response = self.service.reply("Hello")
        
        self.assertEqual(response, "Test response")
        self.mock_chat_client.complete_messages.assert_called_once()
        
        # Check the messages sent
        call_args = self.mock_chat_client.complete_messages.call_args
        messages = call_args.kwargs["messages"]
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("My English Buddy", messages[0]["content"])
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "Hello")

    def test_reply_stores_messages_in_memory(self):
        """Test that reply stores user and assistant messages in memory."""
        self.mock_chat_client.complete_messages.return_value = "Test response"
        
        self.service.reply("Hello")
        
        # Check memory contains both messages
        self.assertEqual(len(self.service.memory), 2)
        messages = self.service.memory.recent(2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Hello")
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[1].content, "Test response")

    def test_reply_sends_recent_conversation_history(self):
        """Test that reply sends recent conversation history."""
        self.mock_chat_client.complete_messages.return_value = "Response"
        
        # First exchange
        self.service.reply("First message")
        # Second exchange
        self.service.reply("Second message")
        
        # Check the second call includes history
        self.assertEqual(self.mock_chat_client.complete_messages.call_count, 2)
        
        # Get the messages from the second call
        second_call_args = self.mock_chat_client.complete_messages.call_args
        messages = second_call_args.kwargs["messages"]
        
        # Should have: system, first user, first assistant, second user
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertEqual(messages[1]["content"], "First message")
        self.assertEqual(messages[2]["role"], "assistant")
        self.assertEqual(messages[2]["content"], "Response")
        self.assertEqual(messages[3]["role"], "user")
        self.assertEqual(messages[3]["content"], "Second message")

    def test_reply_respects_memory_window(self):
        """Test that reply only sends messages within memory_window."""
        # Set a small memory window
        self.service.memory_window = 4  # Will send last 4 messages
        self.mock_chat_client.complete_messages.return_value = "Response"
        
        # Add 3 exchanges (6 messages total)
        for i in range(3):
            self.service.reply(f"Message {i}")
        
        # Check the third call
        # At the time of the third call, memory has:
        # [0] user: Message 0, [1] assistant: Response
        # [2] user: Message 1, [3] assistant: Response
        # [4] user: Message 2
        # With window=4, we get the last 4 messages: indices 1-4
        third_call_args = self.mock_chat_client.complete_messages.call_args
        messages = third_call_args.kwargs["messages"]
        
        # Should have: system + last 4 messages
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["content"], "Response")
        self.assertEqual(messages[2]["content"], "Message 1")
        self.assertEqual(messages[3]["content"], "Response")
        self.assertEqual(messages[4]["content"], "Message 2")

    def test_reply_with_many_messages_respects_window(self):
        """Test that memory window works correctly with many messages."""
        # Set memory window to 6 messages
        self.service.memory_window = 6
        self.mock_chat_client.complete_messages.return_value = "Reply"
        
        # Add 10 exchanges (20 messages total)
        for i in range(10):
            self.service.reply(f"User message {i}")
        
        # Get the last call (10th call)
        # At the time of the 10th call, memory has:
        # [0-1] exchange 0, [2-3] exchange 1, ..., [16-17] exchange 8
        # [18] user: User message 9
        # Memory has max 50 messages, so all 19 messages are kept
        # With window=6, we get the last 6 messages: indices 13-18
        # That's: [13] assistant: Reply, [14] user: User message 7,
        # [15] assistant: Reply, [16] user: User message 8,
        # [17] assistant: Reply, [18] user: User message 9
        last_call_args = self.mock_chat_client.complete_messages.call_args
        messages = last_call_args.kwargs["messages"]
        
        # Should have: system + last 6 messages
        self.assertEqual(len(messages), 7)
        self.assertEqual(messages[0]["role"], "system")
        
        # Last 6 messages should end with User message 9
        self.assertEqual(messages[1]["content"], "Reply")
        self.assertEqual(messages[2]["content"], "User message 7")
        self.assertEqual(messages[3]["content"], "Reply")
        self.assertEqual(messages[4]["content"], "User message 8")
        self.assertEqual(messages[5]["content"], "Reply")
        self.assertEqual(messages[6]["content"], "User message 9")

    def test_reply_empty_string_returns_empty(self):
        """Test that empty string returns empty response."""
        response = self.service.reply("")
        self.assertEqual(response, "")
        self.mock_chat_client.complete_messages.assert_not_called()

    def test_reply_whitespace_only_returns_empty(self):
        """Test that whitespace-only string returns empty response."""
        response = self.service.reply("   ")
        self.assertEqual(response, "")
        self.mock_chat_client.complete_messages.assert_not_called()

    def test_custom_system_prompt(self):
        """Test that custom system prompt is used."""
        self.service.system_prompt = "Custom prompt"
        self.mock_chat_client.complete_messages.return_value = "Response"
        
        self.service.reply("Hello")
        
        call_args = self.mock_chat_client.complete_messages.call_args
        messages = call_args.kwargs["messages"]
        
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], "Custom prompt")

    def test_no_system_prompt(self):
        """Test that conversation works without system prompt."""
        self.service.system_prompt = None
        self.mock_chat_client.complete_messages.return_value = "Response"
        
        self.service.reply("Hello")
        
        call_args = self.mock_chat_client.complete_messages.call_args
        messages = call_args.kwargs["messages"]
        
        # Should only have user message, no system message
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Hello")

    def test_custom_memory_service(self):
        """Test that custom memory service can be provided."""
        custom_memory = MemoryService(max_messages=5)
        service = ConversationService(
            chat_client=self.mock_chat_client,
            memory=custom_memory
        )
        
        self.assertIs(service.memory, custom_memory)


if __name__ == "__main__":
    unittest.main()
