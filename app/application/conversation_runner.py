from __future__ import annotations

from app.audio.listener import Listener
from app.audio.speech_to_text import SpeechToText
from app.audio.speaker import Speaker
from app.audio.text_to_speech import TextToSpeech
from app.application.conversation_service import ConversationService


class ConversationRunner:
    def __init__(
        self,
        listener: Listener,
        stt: SpeechToText,
        conversation_service: ConversationService,
        tts: TextToSpeech,
        speaker: Speaker,
    ) -> None:
        self.listener = listener
        self.stt = stt
        self.conversation_service = conversation_service
        self.tts = tts
        self.speaker = speaker

    def run(self) -> None:
        while True:
            audio = self.listener.listen()
            user_text = self.stt.transcribe(audio)

            if not user_text:
                return

            reply = self.conversation_service.reply(user_text)

            if not reply or not reply.strip():
                return

            print(reply)

            reply_audio = self.tts.synthesize(reply)
            self.speaker.speak(reply_audio)
