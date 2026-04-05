from collections.abc import Callable
from threading import Event, Lock, Thread

from app.application.errors import ExternalServiceError
from app.application.port.speaker import Speaker
from app.application.port.text_to_speech import TextToSpeech
from app.application.reply_queue import LatestReplyQueue
from app.utils.logger import Logger


class SpeakerLoop:
    """Drives TTS synthesis and audio playback in a dedicated background thread.

    Reads from a ``LatestReplyQueue``, so stale replies from superseded requests
    are automatically discarded.  Exposes speaking state for the interruption
    detection path in ``ConversationRunner``.
    """

    def __init__(
        self,
        *,
        tts: TextToSpeech,
        speaker: Speaker,
        reply_queue: LatestReplyQueue,
        on_reply_completed: Callable[[str], None],
        logger: Logger,
    ) -> None:
        self._tts = tts
        self._speaker = speaker
        self._reply_queue = reply_queue
        self._on_reply_completed = on_reply_completed
        self._logger = logger

        self._stop_event = Event()
        self._is_speaking_event = Event()
        # Guards _is_speaking_event and _currently_speaking_text together so
        # callers can snapshot both atomically.
        self._speaking_lock = Lock()
        self._currently_speaking_text: str | None = None
        self._thread: Thread | None = None

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking_event.is_set()

    def snapshot_speaking_state(self) -> tuple[bool, str | None]:
        """Return (is_speaking, currently_speaking_text) as an atomic snapshot."""
        with self._speaking_lock:
            return self._is_speaking_event.is_set(), self._currently_speaking_text

    def stop_speaking(self) -> None:
        """Request that the current playback be interrupted."""
        self._stop_event.set()

    def start(self) -> Thread:
        if self._thread is not None:
            raise RuntimeError("SpeakerLoop is already running")
        self._thread = Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self._thread

    def _loop(self) -> None:
        while True:
            item = self._reply_queue.get()

            if not item.text:
                continue

            if not self._reply_queue.is_latest(item.request_id):
                continue

            try:
                self._stop_event.clear()

                # Keep speaking state and speaking text consistent for readers
                # that snapshot both atomically via snapshot_speaking_state().
                with self._speaking_lock:
                    self._currently_speaking_text = item.text
                    self._is_speaking_event.set()

                reply_audio = self._tts.synthesize(item.text)

                if not self._reply_queue.is_latest(item.request_id):
                    continue

                completed = self._speaker.speak(
                    reply_audio,
                    stop_event=self._stop_event,
                )
                if not completed:
                    self._logger.log(
                        f"Buddy (interrupted, request_id={item.request_id}): {item.text}"
                    )
                else:
                    # If playback completed, the user heard this reply.
                    # Do not gate on latest_request_id here: it can change while
                    # speaking, which would create a "heard but not remembered"
                    # inconsistency.
                    self._on_reply_completed(item.text)
            except (ExternalServiceError, OSError, RuntimeError, ValueError) as e:
                self._logger.log(f"Error in speaker loop: {e}")
                self._stop_event.set()
                continue
            finally:
                with self._speaking_lock:
                    self._is_speaking_event.clear()
                    self._currently_speaking_text = None
