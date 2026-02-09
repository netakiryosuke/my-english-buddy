from __future__ import annotations

from app.audio.listener import Listener
from app.audio.speech_to_text import SpeechToText
from app.audio.speaker import Speaker
from app.audio.text_to_speech import TextToSpeech
from app.application.conversation_service import ConversationService
from app.utils.logger import Logger


class ConversationRunner:
    WAKE_WORDS = ["buddy"]

    def __init__(
        self,
        listener: Listener,
        stt: SpeechToText,
        conversation_service: ConversationService,
        tts: TextToSpeech,
        speaker: Speaker,
        logger: Logger,
        ) -> None:
        self.listener = listener
        self.stt = stt
        self.conversation_service = conversation_service
        self.tts = tts
        self.speaker = speaker
        self.logger = logger
        self.is_awake = False

    def run(self) -> None:
        while True:
            audio = self.listener.listen()
            user_text = self.stt.transcribe(audio)

            if not user_text:
                continue

            if not self.is_awake:
                if self._detect_wake_word(user_text):
                    self.is_awake = True
                continue

            self._log(f"You: {user_text}")

            reply = self.conversation_service.reply(user_text)

            if not reply or not reply.strip():
                continue

            self._log(f"Buddy: {reply}")

            reply_audio = self.tts.synthesize(reply)
            self.speaker.speak(reply_audio)

    def _log(self, message: str) -> None:
        if self.logger:
            self.logger.log(message)

    def _detect_wake_word(self, text: str) -> bool:
        normalized_text = text.lower()

        return any(
            wake_word in normalized_text
            for wake_word in self.WAKE_WORDS
        )
