from __future__ import annotations


class ExternalServiceError(RuntimeError):
    """Raised when an external service call fails (provider-agnostic)."""


class ChatClientError(ExternalServiceError):
    """Raised when chat completion fails."""


class SpeechToTextError(ExternalServiceError):
    """Raised when speech-to-text transcription fails."""


class TextToSpeechError(ExternalServiceError):
    """Raised when text-to-speech synthesis fails."""
