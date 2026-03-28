from queue import Empty, Full, Queue
from threading import Lock
from typing import NamedTuple


class _ReplyItem(NamedTuple):
    request_id: int
    text: str


class LatestReplyQueue:
    """Thread-safe queue that retains only the most recent reply.

    Maintains a monotonically increasing request ID so that stale replies
    from superseded requests are silently discarded before enqueueing.
    """

    def __init__(self) -> None:
        self._queue: Queue[_ReplyItem] = Queue(maxsize=1)
        self._lock = Lock()
        self._request_id = 0
        self._latest_request_id = 0

    def next_request_id(self) -> int:
        """Increment and return the new latest request ID."""
        with self._lock:
            self._request_id += 1
            self._latest_request_id = self._request_id
            return self._request_id

    def is_latest(self, request_id: int) -> bool:
        with self._lock:
            return request_id == self._latest_request_id

    @property
    def latest_request_id(self) -> int:
        with self._lock:
            return self._latest_request_id

    def publish(self, request_id: int, text: str) -> None:
        """Publish a reply, discarding it if a newer request has been issued.

        Also drains any previously queued item so the consumer always sees
        the freshest reply.
        """
        with self._lock:
            if request_id != self._latest_request_id:
                return

        # Drain stale item before pushing the new one.
        try:
            while True:
                self._queue.get_nowait()
        except Empty:
            pass

        try:
            self._queue.put_nowait(_ReplyItem(request_id=request_id, text=text))
        except Full:
            pass

    def get(self) -> _ReplyItem:
        """Block until a reply item is available and return it."""
        return self._queue.get()
