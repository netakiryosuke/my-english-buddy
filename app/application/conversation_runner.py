from __future__ import annotations
from queue import Empty, Queue
from threading import Event, Thread

from app.infrastructure.audio.listener import Listener
from app.infrastructure.audio.speaker import Speaker
from app.application.conversation_service import ConversationService
from app.interface.speech_to_text import SpeechToText
from app.interface.text_to_speech import TextToSpeech
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
        self.reply_queue: Queue[str] = Queue(maxsize=1)
        self.stop_speaking_event = Event()

    def run(self) -> None:
        self._start_speaker_thread()

        while True:
            audio = self.listener.listen()
            user_text = self.stt.transcribe(audio)

            if not user_text:
                continue

            self.stop_speaking_event.set()

            if not self.is_awake:
                if self._detect_wake_word(user_text):
                    self.is_awake = True
                else:
                    continue

            self._log(f"You: {user_text}")

            reply = self.conversation_service.reply(user_text)

            if not reply or not reply.strip():
                continue

            self._log(f"Buddy: {reply}")

            self._publish_reply(reply)

    def _log(self, message: str) -> None:
        if self.logger:
            self.logger.log(message)

    def _detect_wake_word(self, text: str) -> bool:
        normalized_text = text.lower()

        return any(
            wake_word in normalized_text
            for wake_word in self.WAKE_WORDS
        )

    def _publish_reply(self, reply: str) -> None:
        try:
            while True:
                self.reply_queue.get_nowait()
        except Empty:
            pass

        try:
            self.reply_queue.put_nowait(reply)
        except Exception:
            pass

    def _start_speaker_thread(self) -> None:
        thread = Thread(
            target=self._speaker_loop,
            daemon=True,
        )
        thread.start()

    def _speaker_loop(self) -> None:
        while True:
            reply = self.reply_queue.get()

            if not reply:
                continue

            try:
                self.stop_speaking_event.clear()

                reply_audio = self.tts.synthesize(reply)
                self.speaker.speak(reply_audio, stop_event=self.stop_speaking_event)
            except Exception as e:
                self._log(f"Error in speaker loop: {e}")

                self.stop_speaking_event.set()
                continue
