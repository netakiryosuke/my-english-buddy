class WakeWordDetector:
    """Detects wake words in transcribed user speech."""

    WAKE_WORDS: list[str] = ["buddy"]

    def detect(self, text: str) -> bool:
        normalized = text.lower()
        return any(word in normalized for word in self.WAKE_WORDS)
