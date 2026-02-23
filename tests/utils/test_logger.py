"""Unit tests for Logger."""
from __future__ import annotations

import tempfile
from pathlib import Path

from app.utils.logger import Logger


class TestLogger:
    """Test cases for Logger."""

    def test_log_message(self):
        """Test logging a message."""
        logger = Logger()
        logger.log("Test message")
        
        assert len(logger._lines) == 1
        assert logger._lines[0] == "Test message"

    def test_log_multiple_messages(self):
        """Test logging multiple messages."""
        logger = Logger()
        logger.log("Message 1")
        logger.log("Message 2")
        logger.log("Message 3")
        
        assert len(logger._lines) == 3
        assert logger._lines[0] == "Message 1"
        assert logger._lines[1] == "Message 2"
        assert logger._lines[2] == "Message 3"

    def test_log_empty_message_ignored(self):
        """Test that empty messages are ignored."""
        logger = Logger()
        logger.log("")
        
        assert len(logger._lines) == 0

    def test_on_emit_callback(self):
        """Test that on_emit callback is called when logging."""
        emitted = []
        
        def callback(message: str) -> None:
            emitted.append(message)
        
        logger = Logger(on_emit=callback)
        logger.log("Test message")
        
        assert emitted == ["Test message"]

    def test_on_emit_replays_buffered_logs(self):
        """Test that setting on_emit replays previously buffered logs."""
        logger = Logger()
        logger.log("Message 1")
        logger.log("Message 2")
        
        emitted = []
        
        def callback(message: str) -> None:
            emitted.append(message)
        
        logger.on_emit = callback
        
        # Should replay the buffered messages
        assert emitted == ["Message 1", "Message 2"]

    def test_on_emit_called_for_new_messages(self):
        """Test that on_emit is called for new messages after being set."""
        emitted = []
        
        def callback(message: str) -> None:
            emitted.append(message)
        
        logger = Logger()
        logger.on_emit = callback
        
        logger.log("New message")
        
        assert "New message" in emitted

    def test_save_creates_log_file(self):
        """Test that save creates a log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)
            logger = Logger(log_dir=log_dir)
            
            logger.log("Message 1")
            logger.log("Message 2")
            
            logger.save()
            
            # Check that a file was created
            log_files = list(log_dir.glob("*.txt"))
            assert len(log_files) == 1
            
            # Check file content
            content = log_files[0].read_text(encoding="utf-8")
            assert "Message 1" in content
            assert "Message 2" in content

    def test_save_creates_directory_if_not_exists(self):
        """Test that save creates the log directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"
            logger = Logger(log_dir=log_dir)
            
            logger.log("Test message")
            logger.save()
            
            assert log_dir.exists()
            assert log_dir.is_dir()

    def test_on_emit_none_does_not_crash(self):
        """Test that logging works when on_emit is None."""
        logger = Logger()
        logger.log("Message 1")
        logger.on_emit = None
        logger.log("Message 2")
        
        assert len(logger._lines) == 2
