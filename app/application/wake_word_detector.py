from typing import ClassVar


class WakeWordDetector:
    """Detects wake words in transcribed user speech."""

    WAKE_WORDS: ClassVar[tuple[str, ...]] = ("buddy",)

    def detect(self, text: str) -> bool:
        normalized = text.lower()
        return any(word in normalized for word in self.WAKE_WORDS)
