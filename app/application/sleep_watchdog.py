from collections.abc import Callable
from threading import Event, Thread
from time import monotonic

from app.utils.logger import Logger


class SleepWatchdog:
    """Monitors conversation inactivity and transitions the system to sleep.

    The watchdog polls at a fixed interval.  When the ``should_sleep`` predicate
    returns True it immediately calls ``on_sleep``, which is expected to atomically
    perform the state transition.  ``on_sleep`` must re-validate the condition
    under a lock to avoid TOCTOU races (double-checked locking pattern).

    The timeout threshold itself is encapsulated in the ``should_sleep`` callback;
    this class only owns the poll interval.
    """

    def __init__(
        self,
        *,
        poll_interval: float,
        should_sleep: Callable[[], bool],
        on_sleep: Callable[[], bool],
        logger: Logger,
    ) -> None:
        self._poll_interval = poll_interval
        self._should_sleep = should_sleep
        self._on_sleep = on_sleep
        self._logger = logger
        self._stop_event = Event()

    def start(self) -> Thread:
        thread = Thread(target=self._loop, daemon=True)
        thread.start()
        return thread

    def stop(self) -> None:
        """Signal the watchdog loop to exit on its next poll."""
        self._stop_event.set()

    def _loop(self) -> None:
        while not self._stop_event.wait(timeout=self._poll_interval):
            if not self._should_sleep():
                continue

            # on_sleep performs the atomic state transition and returns True when
            # sleep was actually applied (False means a race was detected).
            slept = self._on_sleep()
            if slept:
                self._logger.log("Sleeping (idle timeout). Say 'Buddy' to start.")
