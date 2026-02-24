"""Unit tests for argument parsing."""

from app.utils.args import parse_args


class TestParseArgs:
    """Test cases for parse_args function."""

    def test_parse_args_default_env_file(self):
        """Test parsing with default env file."""
        args = parse_args([])
        assert args.env_file == ".env"

    def test_parse_args_custom_env_file(self):
        """Test parsing with custom env file."""
        args = parse_args(["--env-file", "custom.env"])
        assert args.env_file == "custom.env"

    def test_parse_args_empty_env_file(self):
        """Test parsing with empty env file to disable loading."""
        args = parse_args(["--env-file", ""])
        assert args.env_file == ""

    def test_parse_args_env_file_with_path(self):
        """Test parsing with env file path."""
        args = parse_args(["--env-file", "/path/to/.env"])
        assert args.env_file == "/path/to/.env"
