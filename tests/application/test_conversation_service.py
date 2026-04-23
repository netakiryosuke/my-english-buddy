"""Unit tests for ConversationService."""

import unittest
from unittest.mock import MagicMock

from app.application.conversation_service import ConversationService
from app.application.port.chat_client import ChatClient
from app.domain.entity.conversation import Conversation


class TestConversationService(unittest.TestCase):
    """Test cases for ConversationService."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_chat_client = MagicMock(spec=ChatClient)
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
        self.assertEqual(messages[0].role, "system")
        self.assertIn("My English Buddy", messages[0].content)
        self.assertEqual(messages[1].role, "user")
        self.assertEqual(messages[1].content, "Hello")

    def test_reply_stores_messages_in_conversation(self):
        """Test that reply stores user and assistant messages in conversation."""
        self.mock_chat_client.complete_messages.return_value = "Test response"
        
        self.service.reply("Hello")
        
        # Check conversation contains one completed turn
        self.assertEqual(self.service.conversation.turn_count, 1)
        turns = self.service.conversation.recent_context(1)
        self.assertEqual(turns[0].user_utterance, "Hello")
        self.assertEqual(turns[0].assistant_reply, "Test response")

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
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[1].role, "user")
        self.assertEqual(messages[1].content, "First message")
        self.assertEqual(messages[2].role, "assistant")
        self.assertEqual(messages[2].content, "Response")
        self.assertEqual(messages[3].role, "user")
        self.assertEqual(messages[3].content, "Second message")

    def test_reply_respects_context_turns(self):
        """Test that reply only sends messages within context_turns."""
        # Set a small context window
        self.service.context_turns = 2  # Will send last 2 turns
        self.mock_chat_client.complete_messages.return_value = "Response"
        
        # Add 3 exchanges (3 turns total)
        for i in range(3):
            self.service.reply(f"Message {i}")
        
        # Check the third call
        # At the time of the third call, conversation has:
        # Turn 0: (Message 0, Response), Turn 1: (Message 1, Response)
        # Pending: Message 2
        # With context_turns=2, we get turns 0 and 1 + pending user
        third_call_args = self.mock_chat_client.complete_messages.call_args
        messages = third_call_args.kwargs["messages"]
        
        # Should have: system + 2 turns (4 messages) + pending user (1 message)
        self.assertEqual(len(messages), 6)
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[1].content, "Message 0")
        self.assertEqual(messages[2].content, "Response")
        self.assertEqual(messages[3].content, "Message 1")
        self.assertEqual(messages[4].content, "Response")
        self.assertEqual(messages[5].content, "Message 2")

    def test_reply_with_many_messages_respects_context(self):
        """Test that context window works correctly with many messages."""
        # Set context window to 3 turns
        self.service.context_turns = 3
        self.mock_chat_client.complete_messages.return_value = "Reply"
        
        # Add 10 exchanges (10 turns total)
        for i in range(10):
            self.service.reply(f"User message {i}")
        
        last_call_args = self.mock_chat_client.complete_messages.call_args
        messages = last_call_args.kwargs["messages"]
        
        # At the 10th call: 9 completed turns exist, pending "User message 9"
        # context_turns=3 → last 3 completed turns (6,7,8) + pending
        # Should have: system + 3 turns (6 messages) + pending user (1)
        self.assertEqual(len(messages), 8)
        self.assertEqual(messages[0].role, "system")
        
        self.assertEqual(messages[1].content, "User message 6")
        self.assertEqual(messages[2].content, "Reply")
        self.assertEqual(messages[3].content, "User message 7")
        self.assertEqual(messages[4].content, "Reply")
        self.assertEqual(messages[5].content, "User message 8")
        self.assertEqual(messages[6].content, "Reply")
        self.assertEqual(messages[7].content, "User message 9")

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
        
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[0].content, "Custom prompt")

    def test_no_system_prompt(self):
        """Test that conversation works without system prompt."""
        self.service.system_prompt = None
        self.mock_chat_client.complete_messages.return_value = "Response"
        
        self.service.reply("Hello")
        
        call_args = self.mock_chat_client.complete_messages.call_args
        messages = call_args.kwargs["messages"]
        
        # Should only have user message, no system message
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Hello")

    def test_custom_conversation(self):
        """Test that custom conversation can be provided."""
        custom_conv = Conversation(max_turns=5)
        service = ConversationService(
            chat_client=self.mock_chat_client,
            conversation=custom_conv
        )
        
        self.assertIs(service.conversation, custom_conv)


if __name__ == "__main__":
    unittest.main()
