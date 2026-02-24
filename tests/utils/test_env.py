"""Unit tests for environment loading."""

import os
import tempfile
from pathlib import Path

from app.utils.env import load_dotenv


class TestLoadDotenv:
    """Test cases for load_dotenv function."""

    def test_load_dotenv_with_file(self):
        """Test loading environment variables from a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_VAR=test_value\n")
            temp_path = f.name
        
        try:
            # Clear any existing value
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]
            
            load_dotenv(temp_path)
            
            # Check that variable was loaded
            assert os.environ.get("TEST_VAR") == "test_value"
        finally:
            # Cleanup
            Path(temp_path).unlink()
            if "TEST_VAR" in os.environ:
                del os.environ["TEST_VAR"]

    def test_load_dotenv_with_none(self):
        """Test that load_dotenv with None does nothing."""
        # Should not raise an error
        load_dotenv(None)

    def test_load_dotenv_with_empty_string(self):
        """Test that load_dotenv with empty string does nothing."""
        # Should not raise an error
        load_dotenv("")

    def test_load_dotenv_does_not_override_existing(self):
        """Test that load_dotenv doesn't override existing env vars."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
            f.write("TEST_VAR2=from_file\n")
            temp_path = f.name
        
        try:
            # Set an existing value
            os.environ["TEST_VAR2"] = "existing_value"
            
            load_dotenv(temp_path)
            
            # Should keep the existing value (override=False)
            assert os.environ.get("TEST_VAR2") == "existing_value"
        finally:
            # Cleanup
            Path(temp_path).unlink()
            if "TEST_VAR2" in os.environ:
                del os.environ["TEST_VAR2"]
