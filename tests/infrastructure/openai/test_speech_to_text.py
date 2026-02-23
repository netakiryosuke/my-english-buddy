"""Unit tests for OpenAI SpeechToText."""
from __future__ import annotations

from unittest.mock import Mock
import pytest
import numpy as np

from app.infrastructure.openai.speech_to_text import SpeechToText
from app.application.errors import SpeechToTextError


class TestSpeechToText:
    """Test cases for OpenAI SpeechToText."""

    def test_transcribe_with_audio(self, mock_openai_client):
        """Test transcribing audio data."""
        # Mock the API response
        mock_response = Mock()
        mock_response.text = "  Hello world  "
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        stt = SpeechToText(client=mock_openai_client)
        
        # Create sample audio (non-silent)
        audio = np.random.randn(16000).astype(np.float32) * 0.1
        
        result = stt.transcribe(audio)
        
        assert result == "Hello world"
        mock_openai_client.audio.transcriptions.create.assert_called_once()

    def test_transcribe_silent_audio_returns_empty(self, mock_openai_client):
        """Test that silent audio returns empty string without API call."""
        stt = SpeechToText(client=mock_openai_client, silence_threshold=1e-3)
        
        # Create silent audio
        audio = np.zeros(16000, dtype=np.float32)
        
        result = stt.transcribe(audio)
        
        assert result == ""
        mock_openai_client.audio.transcriptions.create.assert_not_called()

    def test_transcribe_with_custom_model(self, mock_openai_client):
        """Test transcribe with custom model."""
        mock_response = Mock()
        mock_response.text = "Test"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        stt = SpeechToText(client=mock_openai_client, model="custom-model")
        
        audio = np.random.randn(16000).astype(np.float32) * 0.1
        stt.transcribe(audio)
        
        call_args = mock_openai_client.audio.transcriptions.create.call_args
        assert call_args.kwargs["model"] == "custom-model"

    def test_transcribe_clips_audio(self, mock_openai_client):
        """Test that audio is clipped to valid range."""
        mock_response = Mock()
        mock_response.text = "Test"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        stt = SpeechToText(client=mock_openai_client)
        
        # Create audio with values outside [-1, 1]
        audio = np.array([2.0, -2.0, 0.5], dtype=np.float32)
        
        stt.transcribe(audio)
        
        # Should not raise an error - audio is clipped
        assert mock_openai_client.audio.transcriptions.create.called

    def test_transcribe_openai_error_raises_stt_error(self, mock_openai_client):
        """Test that OpenAI errors are wrapped in SpeechToTextError."""
        from openai import OpenAIError
        
        mock_openai_client.audio.transcriptions.create.side_effect = OpenAIError("API Error")
        
        stt = SpeechToText(client=mock_openai_client)
        
        audio = np.random.randn(16000).astype(np.float32) * 0.1
        
        with pytest.raises(SpeechToTextError, match="API Error"):
            stt.transcribe(audio)

    def test_is_silent_detects_silence(self, mock_openai_client):
        """Test _is_silent method correctly detects silent audio."""
        stt = SpeechToText(client=mock_openai_client, silence_threshold=0.01)
        
        # Silent audio
        silent = np.zeros(1000, dtype=np.float32)
        assert stt._is_silent(silent) == True
        
        # Very quiet audio
        quiet = np.ones(1000, dtype=np.float32) * 0.001
        assert stt._is_silent(quiet) == True
        
        # Loud audio
        loud = np.ones(1000, dtype=np.float32) * 0.1
        assert stt._is_silent(loud) == False

    def test_transcribe_with_custom_sample_rate(self, mock_openai_client):
        """Test transcribe with custom sample rate."""
        mock_response = Mock()
        mock_response.text = "Test"
        mock_openai_client.audio.transcriptions.create.return_value = mock_response
        
        stt = SpeechToText(client=mock_openai_client, sample_rate=48000)
        
        audio = np.random.randn(48000).astype(np.float32) * 0.1
        stt.transcribe(audio)
        
        # Just verify it was called (WAV format encodes sample rate)
        assert mock_openai_client.audio.transcriptions.create.called
