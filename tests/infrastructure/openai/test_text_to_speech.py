"""Unit tests for OpenAI TextToSpeech."""

from unittest.mock import Mock

import numpy as np
import pytest

from app.application.errors import TextToSpeechError
from app.infrastructure.openai.text_to_speech import TextToSpeech


class TestTextToSpeech:
    """Test cases for OpenAI TextToSpeech."""

    def test_synthesize_text(self, mock_openai_client):
        """Test synthesizing speech from text."""
        # Create mock PCM data (16-bit integers)
        sample_pcm = np.array([100, -100, 200, -200], dtype=np.int16)
        pcm_bytes = sample_pcm.tobytes()
        
        # Mock the API response
        mock_response = Mock()
        mock_response.read.return_value = pcm_bytes
        mock_openai_client.audio.speech.create.return_value = mock_response
        
        tts = TextToSpeech(client=mock_openai_client)
        
        result = tts.synthesize("Hello world")
        
        # Should return float32 array normalized to [-1, 1]
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float32
        assert len(result) == 4
        
        # Check normalization
        expected = sample_pcm.astype(np.float32) / 32767.0
        np.testing.assert_array_almost_equal(result, expected)
        
        mock_openai_client.audio.speech.create.assert_called_once()

    def test_synthesize_with_custom_model(self, mock_openai_client):
        """Test synthesize with custom model."""
        mock_response = Mock()
        mock_response.read.return_value = b"\x00\x00\x00\x00"
        mock_openai_client.audio.speech.create.return_value = mock_response
        
        tts = TextToSpeech(client=mock_openai_client, model="custom-tts-model")
        
        tts.synthesize("Test")
        
        call_args = mock_openai_client.audio.speech.create.call_args
        assert call_args.kwargs["model"] == "custom-tts-model"

    def test_synthesize_with_custom_voice(self, mock_openai_client):
        """Test synthesize with custom voice."""
        mock_response = Mock()
        mock_response.read.return_value = b"\x00\x00\x00\x00"
        mock_openai_client.audio.speech.create.return_value = mock_response
        
        tts = TextToSpeech(client=mock_openai_client, voice="nova")
        
        tts.synthesize("Test")
        
        call_args = mock_openai_client.audio.speech.create.call_args
        assert call_args.kwargs["voice"] == "nova"

    def test_synthesize_requests_pcm_format(self, mock_openai_client):
        """Test that synthesize requests PCM format."""
        mock_response = Mock()
        mock_response.read.return_value = b"\x00\x00\x00\x00"
        mock_openai_client.audio.speech.create.return_value = mock_response
        
        tts = TextToSpeech(client=mock_openai_client)
        
        tts.synthesize("Test")
        
        call_args = mock_openai_client.audio.speech.create.call_args
        assert call_args.kwargs["response_format"] == "pcm"

    def test_synthesize_openai_error_raises_tts_error(self, mock_openai_client):
        """Test that OpenAI errors are wrapped in TextToSpeechError."""
        from openai import OpenAIError
        
        mock_openai_client.audio.speech.create.side_effect = OpenAIError("API Error")
        
        tts = TextToSpeech(client=mock_openai_client)
        
        with pytest.raises(TextToSpeechError, match="API Error"):
            tts.synthesize("Test")

    def test_synthesize_empty_text(self, mock_openai_client):
        """Test synthesizing empty text."""
        mock_response = Mock()
        mock_response.read.return_value = b""
        mock_openai_client.audio.speech.create.return_value = mock_response
        
        tts = TextToSpeech(client=mock_openai_client)
        
        result = tts.synthesize("")
        
        # Should return empty array
        assert isinstance(result, np.ndarray)
        assert len(result) == 0

    def test_synthesize_normalization(self, mock_openai_client):
        """Test that audio is properly normalized from int16 to float32."""
        # Test with max/min values
        sample_pcm = np.array([32767, -32768, 0], dtype=np.int16)
        pcm_bytes = sample_pcm.tobytes()
        
        mock_response = Mock()
        mock_response.read.return_value = pcm_bytes
        mock_openai_client.audio.speech.create.return_value = mock_response
        
        tts = TextToSpeech(client=mock_openai_client)
        
        result = tts.synthesize("Test")
        
        # Check that values are approximately in range [-1, 1]
        # Allow small tolerance for floating point precision
        assert (result >= -1.01).all()
        assert (result <= 1.01).all()
        
        # Max value should be close to 1.0
        assert abs(result[0] - 1.0) < 0.01
        # Min value should be close to -1.0
        assert abs(result[1] - (-1.0)) < 0.01
        # Zero should be zero
        assert abs(result[2]) < 0.01
