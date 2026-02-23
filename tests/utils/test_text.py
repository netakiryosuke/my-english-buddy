"""Unit tests for text utilities."""
from __future__ import annotations

import pytest
import tempfile
from pathlib import Path

from app.utils.text import read_text_file


class TestReadTextFile:
    """Test cases for read_text_file function."""

    def test_read_text_file(self):
        """Test reading a text file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, world!\n")
            temp_path = f.name
        
        try:
            content = read_text_file(temp_path)
            assert content == "Hello, world!"
        finally:
            Path(temp_path).unlink()

    def test_read_text_file_strips_whitespace(self):
        """Test that read_text_file strips leading/trailing whitespace."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("  \n  Content with spaces  \n  \n")
            temp_path = f.name
        
        try:
            content = read_text_file(temp_path)
            assert content == "Content with spaces"
        finally:
            Path(temp_path).unlink()

    def test_read_text_file_multiline(self):
        """Test reading a multiline text file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Line 1\nLine 2\nLine 3")
            temp_path = f.name
        
        try:
            content = read_text_file(temp_path)
            assert content == "Line 1\nLine 2\nLine 3"
        finally:
            Path(temp_path).unlink()

    def test_read_empty_file(self):
        """Test reading an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = f.name
        
        try:
            content = read_text_file(temp_path)
            assert content == ""
        finally:
            Path(temp_path).unlink()

    def test_read_nonexistent_file_raises_error(self):
        """Test that reading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            read_text_file("/nonexistent/path/file.txt")
