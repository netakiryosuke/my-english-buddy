from collections.abc import Callable
from queue import Queue
from threading import BoundedSemaphore, Event, Lock, Thread
from time import monotonic

import numpy as np

from app.application.conversation_service import ConversationService
from app.application.errors import ExternalServiceError
from app.application.interruption_context import build_interruption_prompt
from app.application.port.speech_to_text import SpeechToText
from app.application.port.text_to_speech import TextToSpeech
from app.application.reply_queue import LatestReplyQueue
from app.application.sleep_watchdog import SleepWatchdog
from app.application.speaker_loop import SpeakerLoop
from app.application.wake_word_detector import WakeWordDetector
from app.infrastructure.audio.listener import Listener
from app.infrastructure.audio.speaker import Speaker
from app.utils.logger import Logger


class ConversationRunner:
    SLEEP_TIMEOUT_SECONDS = 180.0
    SLEEP_POLL_INTERVAL_SECONDS = 0.5

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
        self._wake_word_detector = WakeWordDetector()
        self.is_awake = False
        self.utterance_queue: Queue[np.ndarray] = Queue(maxsize=3)
        self.stop_listening_event = Event()
        self.reply_queue = LatestReplyQueue()
        self._speaker_loop = SpeakerLoop(
            tts=tts,
            speaker=speaker,
            reply_queue=self.reply_queue,
            on_reply_completed=self._on_reply_completed,
            logger=logger,
        )
        self._state_lock = Lock()
        self._inflight_semaphore = BoundedSemaphore(value=2)
        self._listener_thread: Thread | None = None

        self._sleep_watchdog_thread: Thread | None = None
        self._last_activity_at: float = monotonic()
        self._inflight_workers = 0

        # Optional hooks for UI/observers.
        self.on_calibration_start: Callable[[], None] | None = None
        self.on_calibration_end: Callable[[float], None] | None = None
        self.on_calibration_error: Callable[[Exception], None] | None = None

    def request_noise_recalibration(self) -> None:
        self.listener.request_recalibration()
        self._log("Noise calibration requested.")

    def run(self) -> None:
        self._start_speaker_thread()
        self._start_listener_thread()
        self._start_sleep_watchdog_thread()

        self._log("Ready. Say 'Buddy' to start.")

        while True:
            audio: np.ndarray = self.utterance_queue.get()

            # Limit concurrent OpenAI calls.
            self._inflight_semaphore.acquire()
            worker = Thread(
                target=self._process_utterance,
                args=(audio,),
                daemon=True,
            )
            try:
                worker.start()
            except RuntimeError as e:
                self._log(f"Error starting worker thread: {e}")
                self._inflight_semaphore.release()
                continue

    def _process_utterance(self, audio: np.ndarray) -> None:
        with self._state_lock:
            self._inflight_workers += 1
        try:
            # Snapshot speaking state before STT so we don't miss an interruption
            # due to STT latency.
            was_speaking, speaking_text = self._speaker_loop.snapshot_speaking_state()

            user_text = self.stt.transcribe(audio)
            if not user_text:
                return

            # If Buddy is currently speaking and STT produced non-empty text, treat it as a real
            # user interruption and stop playback (do NOT stop on mere noise detection).
            interrupted = False
            if was_speaking:
                self._speaker_loop.stop_speaking()
                interrupted = True

            with self._state_lock:
                is_awake = self.is_awake

            if not is_awake:
                if self._detect_wake_word(user_text):
                    with self._state_lock:
                        self.is_awake = True
                        self._last_activity_at = monotonic()
                else:
                    return

            self._log(f"You: {user_text}")

            ephemeral_system_prompt = build_interruption_prompt(
                was_speaking=was_speaking,
                speaking_text=speaking_text if interrupted else None,
            )

            request_id = self.reply_queue.next_request_id()
            reply = self.conversation_service.prepare_reply(
                user_text,
                ephemeral_system_prompt=ephemeral_system_prompt,
            )
            if not reply or not reply.strip():
                return

            self._log(f"Buddy: {reply}")
            self.reply_queue.publish(request_id=request_id, text=reply)
        except ExternalServiceError as e:
            self._log(f"External service error: {e}")
        except (OSError, RuntimeError, ValueError) as e:
            self._log(f"Error processing utterance: {e}")
        finally:
            with self._state_lock:
                self._inflight_workers -= 1
            self._inflight_semaphore.release()

    def _start_listener_thread(self) -> None:
        if self._listener_thread and self._listener_thread.is_alive():
            return

        self._listener_thread = self.listener.listen(
            utterance_queue=self.utterance_queue,
            stop_event=self.stop_listening_event,
            # Do not stop Buddy on raw noise detection; interruption is decided after STT.
            on_speech_start=None,
            on_calibration_start=self._on_calibration_start,
            on_calibration_end=self._on_calibration_end,
            on_calibration_error=self._on_calibration_error,
        )

    def _on_calibration_start(self) -> None:
        self._log("Calibrating noise level...")
        if self.on_calibration_start:
            self.on_calibration_start()

    def _on_calibration_end(self, threshold: float) -> None:
        self._log(f"Noise calibration complete. threshold={threshold:.6f}")
        if self.on_calibration_end:
            self.on_calibration_end(threshold)

    def _on_calibration_error(self, error: Exception) -> None:
        self._log(f"Noise calibration failed: {error}")
        if self.on_calibration_error:
            self.on_calibration_error(error)

    def _on_user_speech_start(self) -> None:
        # Reserved for future use.
        return

    def _log(self, message: str) -> None:
        if self.logger:
            self.logger.log(message)

    def _detect_wake_word(self, text: str) -> bool:
        return self._wake_word_detector.detect(text)

    def _start_speaker_thread(self) -> None:
        self._speaker_loop.start()

    def _start_sleep_watchdog_thread(self) -> None:
        if self._sleep_watchdog_thread and self._sleep_watchdog_thread.is_alive():
            return

        watchdog = SleepWatchdog(
            timeout=self.SLEEP_TIMEOUT_SECONDS,
            poll_interval=self.SLEEP_POLL_INTERVAL_SECONDS,
            should_sleep=self._should_sleep,
            on_sleep=self._try_go_to_sleep,
            logger=self.logger,
        )
        self._sleep_watchdog_thread = watchdog.start()

    def _should_sleep(self) -> bool:
        with self._state_lock:
            return self._should_sleep_unsafe(now=monotonic())

    def _try_go_to_sleep(self) -> bool:
        """Atomically transition to sleep if the condition still holds.

        Returns True when sleep was applied, False when a race was detected.
        """
        with self._state_lock:
            if not self._should_sleep_unsafe(now=monotonic()):
                return False
            self.is_awake = False
        return True

    def _should_sleep_unsafe(self, *, now: float) -> bool:
        # Assumes _state_lock is already held by the caller.
        if not self.is_awake:
            return False

        # Do not sleep while speaking or while there are inflight workers.
        if self._speaker_loop.is_speaking:
            return False
        if self._inflight_workers > 0:
            return False

        return (now - self._last_activity_at) >= self.SLEEP_TIMEOUT_SECONDS

    def _on_reply_completed(self, text: str) -> None:
        """Called by SpeakerLoop when a reply has been played back in full."""
        self.conversation_service.commit_assistant_reply(text)
        with self._state_lock:
            self._last_activity_at = monotonic()
