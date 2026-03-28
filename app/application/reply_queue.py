from collections import deque
from threading import Condition, Lock
from typing import NamedTuple


class ReplyItem(NamedTuple):
    request_id: int
    text: str


class LatestReplyQueue:
    """Thread-safe queue that retains only the most recent reply.

    Maintains a monotonically increasing request ID so that stale replies
    from superseded requests are silently discarded before enqueueing.
    Drain and enqueue happen under the same lock to prevent TOCTOU races.
    """

    def __init__(self) -> None:
        self._cond = Condition(Lock())
        self._items: deque[ReplyItem] = deque(maxlen=1)
        self._latest_request_id = 0

    def next_request_id(self) -> int:
        """Increment and return the new latest request ID."""
        with self._cond:
            self._latest_request_id += 1
            return self._latest_request_id

    def is_latest(self, request_id: int) -> bool:
        with self._cond:
            return request_id == self._latest_request_id

    @property
    def latest_request_id(self) -> int:
        with self._cond:
            return self._latest_request_id

    def publish(self, request_id: int, text: str) -> None:
        """Publish a reply, discarding it if a newer request has been issued.

        Drain and enqueue are performed atomically under the same lock to
        prevent a TOCTOU race where a valid newer item could be drained by
        a stale publisher that passed the staleness check just before the
        lock was released.
        """
        with self._cond:
            if request_id != self._latest_request_id:
                return
            self._items.clear()
            self._items.append(ReplyItem(request_id=request_id, text=text))
            self._cond.notify()

    def get(self) -> ReplyItem:
        """Block until a reply item is available and return it."""
        with self._cond:
            while not self._items:
                self._cond.wait()
            return self._items.popleft()
