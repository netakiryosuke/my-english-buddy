from collections.abc import Callable
from queue import Queue
from threading import Event, Thread
from typing import Protocol

import numpy as np


class Listener(Protocol):
    def listen(
        self,
        *,
        utterance_queue: Queue[np.ndarray],
        stop_event: Event,
        on_speech_start: Callable[[], None] | None,
        on_calibration_start: Callable[[], None] | None,
        on_calibration_end: Callable[[float], None] | None,
        on_calibration_error: Callable[[Exception], None] | None,
    ) -> Thread:
        """Listen continuously and publish utterances to a queue."""
        ...

    def request_recalibration(self) -> None:
        """Request noise recalibration."""
        ...
