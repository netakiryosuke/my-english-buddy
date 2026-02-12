from __future__ import annotations

from queue import Empty, Full, Queue
from threading import BoundedSemaphore, Event, Lock, Thread
from typing import NamedTuple

from app.interface.errors import ExternalServiceError

from app.infrastructure.audio.listener import Listener
from app.infrastructure.audio.speaker import Speaker
from app.application.conversation_service import ConversationService
from app.interface.speech_to_text import SpeechToText
from app.interface.text_to_speech import TextToSpeech
from app.utils.logger import Logger


class _ReplyItem(NamedTuple):
    request_id: int
    text: str


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
        self.utterance_queue: Queue = Queue(maxsize=3)
        self.stop_listening_event = Event()
        self.reply_queue: Queue[_ReplyItem] = Queue(maxsize=1)
        self.stop_speaking_event = Event()
        self.is_speaking_event = Event()
        self._state_lock = Lock()
        self._request_id = 0
        self._latest_request_id = 0
        self._inflight_semaphore = BoundedSemaphore(value=2)
        self._listener_thread: Thread | None = None

    def run(self) -> None:
        self._start_speaker_thread()
        self._start_listener_thread()

        while True:
            audio = self.utterance_queue.get()

            # Limit concurrent OpenAI calls.
            self._inflight_semaphore.acquire()
            Thread(
                target=self._process_utterance,
                args=(audio,),
                daemon=True,
            ).start()

    def _process_utterance(self, audio) -> None:
        try:
            user_text = self.stt.transcribe(audio)
            if not user_text:
                return

            # Fallback: if the user spoke while Buddy was speaking, stop playback as soon as possible.
            self.stop_speaking_event.set()

            with self._state_lock:
                is_awake = self.is_awake

            if not is_awake:
                if self._detect_wake_word(user_text):
                    with self._state_lock:
                        self.is_awake = True
                else:
                    return

            self._log(f"You: {user_text}")

            request_id = self._next_request_id()
            reply = self.conversation_service.prepare_reply(user_text)
            if not reply or not reply.strip():
                return

            self._log(f"Buddy: {reply}")
            self._publish_reply_if_latest(request_id=request_id, reply=reply)
        except ExternalServiceError as e:
            self._log(f"External service error: {e}")
        except (OSError, RuntimeError, ValueError) as e:
            self._log(f"Error processing utterance: {e}")
        finally:
            self._inflight_semaphore.release()

    def _start_listener_thread(self) -> None:
        if self._listener_thread and self._listener_thread.is_alive():
            return

        self._listener_thread = self.listener.start_utterance_listener(
            utterance_queue=self.utterance_queue,
            stop_event=self.stop_listening_event,
            on_speech_start=self._on_user_speech_start,
        )

    def _on_user_speech_start(self) -> None:
        # Called from Listener.listen() when speech starts; should be fast and non-blocking.
        if self.is_speaking_event.is_set():
            self.stop_speaking_event.set()

    def _log(self, message: str) -> None:
        if self.logger:
            self.logger.log(message)

    def _detect_wake_word(self, text: str) -> bool:
        normalized_text = text.lower()
        return any(wake_word in normalized_text for wake_word in self.WAKE_WORDS)

    def _next_request_id(self) -> int:
        with self._state_lock:
            self._request_id += 1
            self._latest_request_id = self._request_id
            return self._request_id

    def _publish_reply_if_latest(self, *, request_id: int, reply: str) -> None:
        with self._state_lock:
            if request_id != self._latest_request_id:
                return

        item = _ReplyItem(request_id=request_id, text=reply)

        try:
            while True:
                self.reply_queue.get_nowait()
        except Empty:
            pass

        try:
            self.reply_queue.put_nowait(item)
        except Full:
            pass

    def _start_speaker_thread(self) -> None:
        thread = Thread(
            target=self._speaker_loop,
            daemon=True,
        )
        thread.start()

    def _speaker_loop(self) -> None:
        while True:
            item = self.reply_queue.get()

            if not item.text:
                continue

            with self._state_lock:
                if item.request_id != self._latest_request_id:
                    continue

            try:
                self.stop_speaking_event.clear()
                self.is_speaking_event.set()

                reply_audio = self.tts.synthesize(item.text)

                with self._state_lock:
                    if item.request_id != self._latest_request_id:
                        continue

                completed = self.speaker.speak(
                    reply_audio,
                    stop_event=self.stop_speaking_event,
                )
                if not completed:
                    self._log(
                        f"Buddy (interrupted, request_id={item.request_id}): {item.text}"
                    )
                else:
                    with self._state_lock:
                        if item.request_id == self._latest_request_id:
                            self.conversation_service.commit_assistant_reply(item.text)
            except (ExternalServiceError, OSError, RuntimeError, ValueError) as e:
                self._log(f"Error in speaker loop: {e}")
                self.stop_speaking_event.set()
                continue
            finally:
                self.is_speaking_event.clear()
