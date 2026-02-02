"""Unit tests for MemoryService."""
from __future__ import annotations

import unittest

from app.application.memory_service import MemoryService


class TestMemoryService(unittest.TestCase):
    """Test cases for MemoryService."""

    def setUp(self):
        """Set up test fixtures."""
        self.memory = MemoryService(max_messages=10)

    def test_add_user_message(self):
        """Test adding a user message."""
        self.memory.add_user("Hello")
        self.assertEqual(len(self.memory), 1)
        messages = self.memory.recent(1)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Hello")

    def test_add_assistant_message(self):
        """Test adding an assistant message."""
        self.memory.add_assistant("Hi there!")
        self.assertEqual(len(self.memory), 1)
        messages = self.memory.recent(1)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].role, "assistant")
        self.assertEqual(messages[0].content, "Hi there!")

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        self.memory.add_user("Hello")
        self.memory.add_assistant("Hi!")
        self.memory.add_user("How are you?")
        self.memory.add_assistant("I'm good, thanks!")
        
        self.assertEqual(len(self.memory), 4)
        messages = self.memory.recent(4)
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0].content, "Hello")
        self.assertEqual(messages[1].content, "Hi!")
        self.assertEqual(messages[2].content, "How are you?")
        self.assertEqual(messages[3].content, "I'm good, thanks!")

    def test_recent_messages(self):
        """Test retrieving recent messages."""
        for i in range(5):
            self.memory.add_user(f"Message {i}")
        
        recent = self.memory.recent(3)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[0].content, "Message 2")
        self.assertEqual(recent[1].content, "Message 3")
        self.assertEqual(recent[2].content, "Message 4")

    def test_recent_more_than_available(self):
        """Test requesting more recent messages than available."""
        self.memory.add_user("Only one")
        recent = self.memory.recent(10)
        self.assertEqual(len(recent), 1)

    def test_recent_zero_or_negative(self):
        """Test requesting zero or negative recent messages."""
        self.memory.add_user("Test")
        self.assertEqual(len(self.memory.recent(0)), 0)
        self.assertEqual(len(self.memory.recent(-5)), 0)

    def test_max_messages_limit(self):
        """Test that memory respects max_messages limit."""
        for i in range(15):
            self.memory.add_user(f"Message {i}")
        
        self.assertEqual(len(self.memory), 10)
        messages = self.memory.recent(10)
        # Should have messages 5-14 (the last 10)
        self.assertEqual(messages[0].content, "Message 5")
        self.assertEqual(messages[-1].content, "Message 14")

    def test_clear(self):
        """Test clearing all messages."""
        self.memory.add_user("Hello")
        self.memory.add_assistant("Hi")
        self.assertEqual(len(self.memory), 2)
        
        self.memory.clear()
        self.assertEqual(len(self.memory), 0)
        self.assertEqual(len(self.memory.recent(10)), 0)

    def test_empty_content_ignored(self):
        """Test that empty content is ignored."""
        self.memory.add_user("")
        self.memory.add_user("   ")
        self.assertEqual(len(self.memory), 0)

    def test_content_stripped(self):
        """Test that content is stripped of whitespace."""
        self.memory.add_user("  Hello  ")
        messages = self.memory.recent(1)
        self.assertEqual(messages[0].content, "Hello")

    def test_no_max_messages_limit(self):
        """Test memory without max_messages limit."""
        memory = MemoryService(max_messages=None)
        for i in range(100):
            memory.add_user(f"Message {i}")
        self.assertEqual(len(memory), 100)


if __name__ == "__main__":
    unittest.main()
