"""Unit tests for application configuration."""

import os
import tempfile
from pathlib import Path
import pytest

from app.config import AppConfig, OpenAIConfig, SpeechToTextConfig


class TestOpenAIConfig:
    """Test cases for OpenAIConfig."""

    def test_create_config(self):
        """Test creating OpenAI config."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.base_url is None

    def test_create_config_with_base_url(self):
        """Test creating OpenAI config with custom base URL."""
        config = OpenAIConfig(
            api_key="test-key",
            model="gpt-4",
            base_url="https://custom.api.com"
        )
        assert config.base_url == "https://custom.api.com"


class TestSpeechToTextConfig:
    """Test cases for SpeechToTextConfig."""

    def test_default_config(self):
        """Test default STT config."""
        config = SpeechToTextConfig()
        assert config.provider == "openai"
        assert config.local_model == "distil-large-v3"

    def test_custom_config(self):
        """Test custom STT config."""
        config = SpeechToTextConfig(provider="local", local_model="large-v3")
        assert config.provider == "local"
        assert config.local_model == "large-v3"


class TestAppConfig:
    """Test cases for AppConfig."""

    def test_create_config(self):
        """Test creating app config."""
        openai_config = OpenAIConfig(api_key="test-key", model="gpt-4")
        config = AppConfig(openai=openai_config)
        
        assert config.openai == openai_config
        assert config.stt.provider == "openai"
        assert config.system_prompt is None
        assert config.system_prompt_file == "prompt.txt"

    def test_from_env_minimal(self):
        """Test creating config from environment variables (minimal)."""
        os.environ["OPENAI_API_KEY"] = "env-test-key"
        os.environ["OPENAI_MODEL"] = "gpt-3.5-turbo"
        
        try:
            config = AppConfig.from_env()
            
            assert config.openai.api_key == "env-test-key"
            assert config.openai.model == "gpt-3.5-turbo"
            assert config.openai.base_url is None
            assert config.stt.provider == "openai"
        finally:
            del os.environ["OPENAI_API_KEY"]
            del os.environ["OPENAI_MODEL"]

    def test_from_env_with_base_url(self):
        """Test creating config from environment with base URL."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["OPENAI_MODEL"] = "gpt-4"
        os.environ["OPENAI_BASE_URL"] = "https://custom.api.com"
        
        try:
            config = AppConfig.from_env()
            assert config.openai.base_url == "https://custom.api.com"
        finally:
            del os.environ["OPENAI_API_KEY"]
            del os.environ["OPENAI_MODEL"]
            del os.environ["OPENAI_BASE_URL"]

    def test_from_env_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        # Ensure key is not set
        if "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]
        
        os.environ["OPENAI_MODEL"] = "gpt-4"
        
        try:
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                AppConfig.from_env()
        finally:
            del os.environ["OPENAI_MODEL"]

    def test_from_env_missing_model_raises_error(self):
        """Test that missing model raises ValueError."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        
        # Ensure model is not set
        if "OPENAI_MODEL" in os.environ:
            del os.environ["OPENAI_MODEL"]
        
        try:
            with pytest.raises(ValueError, match="OPENAI_MODEL"):
                AppConfig.from_env()
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_from_env_with_local_stt(self):
        """Test creating config with local STT provider."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["OPENAI_MODEL"] = "gpt-4"
        os.environ["MY_ENGLISH_BUDDY_STT_PROVIDER"] = "local"
        os.environ["MY_ENGLISH_BUDDY_LOCAL_STT_MODEL"] = "large-v3"
        
        try:
            config = AppConfig.from_env()
            assert config.stt.provider == "local"
            assert config.stt.local_model == "large-v3"
        finally:
            del os.environ["OPENAI_API_KEY"]
            del os.environ["OPENAI_MODEL"]
            del os.environ["MY_ENGLISH_BUDDY_STT_PROVIDER"]
            del os.environ["MY_ENGLISH_BUDDY_LOCAL_STT_MODEL"]

    def test_from_env_invalid_stt_provider_raises_error(self):
        """Test that invalid STT provider raises ValueError."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["OPENAI_MODEL"] = "gpt-4"
        os.environ["MY_ENGLISH_BUDDY_STT_PROVIDER"] = "invalid"
        
        try:
            with pytest.raises(ValueError, match="STT_PROVIDER"):
                AppConfig.from_env()
        finally:
            del os.environ["OPENAI_API_KEY"]
            del os.environ["OPENAI_MODEL"]
            del os.environ["MY_ENGLISH_BUDDY_STT_PROVIDER"]

    def test_from_env_with_system_prompt(self):
        """Test creating config with system prompt from env."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        os.environ["OPENAI_MODEL"] = "gpt-4"
        os.environ["MY_ENGLISH_BUDDY_SYSTEM_PROMPT"] = "Custom system prompt"
        
        try:
            config = AppConfig.from_env()
            assert config.system_prompt == "Custom system prompt"
        finally:
            del os.environ["OPENAI_API_KEY"]
            del os.environ["OPENAI_MODEL"]
            del os.environ["MY_ENGLISH_BUDDY_SYSTEM_PROMPT"]

    def test_resolve_system_prompt_from_env(self):
        """Test resolving system prompt from environment variable."""
        openai_config = OpenAIConfig(api_key="test-key", model="gpt-4")
        config = AppConfig(
            openai=openai_config,
            system_prompt="Direct prompt"
        )
        
        result = config.resolve_system_prompt()
        assert result == "Direct prompt"

    def test_resolve_system_prompt_from_file(self):
        """Test resolving system prompt from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("File system prompt")
            temp_path = f.name
        
        try:
            openai_config = OpenAIConfig(api_key="test-key", model="gpt-4")
            config = AppConfig(
                openai=openai_config,
                system_prompt_file=temp_path
            )
            
            result = config.resolve_system_prompt()
            assert result == "File system prompt"
        finally:
            Path(temp_path).unlink()

    def test_resolve_system_prompt_file_not_found_returns_none(self):
        """Test that missing system prompt file returns None."""
        openai_config = OpenAIConfig(api_key="test-key", model="gpt-4")
        config = AppConfig(
            openai=openai_config,
            system_prompt_file="/nonexistent/file.txt"
        )
        
        result = config.resolve_system_prompt()
        assert result is None

    def test_resolve_system_prompt_empty_file_returns_none(self):
        """Test that empty system prompt file returns None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("   \n  \n  ")
            temp_path = f.name
        
        try:
            openai_config = OpenAIConfig(api_key="test-key", model="gpt-4")
            config = AppConfig(
                openai=openai_config,
                system_prompt_file=temp_path
            )
            
            result = config.resolve_system_prompt()
            assert result is None
        finally:
            Path(temp_path).unlink()

    def test_resolve_system_prompt_priority(self):
        """Test that env prompt has priority over file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("File prompt")
            temp_path = f.name
        
        try:
            openai_config = OpenAIConfig(api_key="test-key", model="gpt-4")
            config = AppConfig(
                openai=openai_config,
                system_prompt="Env prompt",
                system_prompt_file=temp_path
            )
            
            result = config.resolve_system_prompt()
            assert result == "Env prompt"
        finally:
            Path(temp_path).unlink()
