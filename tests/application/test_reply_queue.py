"""Unit tests for LatestReplyQueue."""

import threading
import unittest

from app.application.reply_queue import LatestReplyQueue


class TestLatestReplyQueue(unittest.TestCase):
    def setUp(self):
        self.queue = LatestReplyQueue()

    def test_next_request_id_is_monotonically_increasing(self):
        ids = [self.queue.next_request_id() for _ in range(5)]
        self.assertEqual(ids, list(range(1, 6)))

    def test_publish_and_get_returns_item(self):
        request_id = self.queue.next_request_id()
        self.queue.publish(request_id=request_id, text="hello")
        item = self.queue.get()
        self.assertEqual(item.request_id, request_id)
        self.assertEqual(item.text, "hello")

    def test_stale_publish_is_discarded(self):
        _stale_id = self.queue.next_request_id()
        latest_id = self.queue.next_request_id()

        # Publish stale first, then latest
        self.queue.publish(request_id=_stale_id, text="stale")
        self.queue.publish(request_id=latest_id, text="latest")

        item = self.queue.get()
        self.assertEqual(item.text, "latest")

    def test_only_latest_item_is_retained(self):
        """Publishing multiple times with the same latest id keeps only the last."""
        request_id = self.queue.next_request_id()
        self.queue.publish(request_id=request_id, text="first")
        # Simulate a second publish that supersedes the first atomically.
        # Advance the id so first is now stale.
        new_id = self.queue.next_request_id()
        self.queue.publish(request_id=new_id, text="second")

        item = self.queue.get()
        self.assertEqual(item.text, "second")

    def test_get_blocks_until_publish(self):
        """get() should block until a reply is published."""
        result = []

        def consumer():
            result.append(self.queue.get())

        t = threading.Thread(target=consumer)
        t.start()
        request_id = self.queue.next_request_id()
        self.queue.publish(request_id=request_id, text="unblocked")
        t.join(timeout=2)
        self.assertFalse(t.is_alive(), "get() did not unblock after publish")
        self.assertEqual(result[0].text, "unblocked")

    def test_is_latest_reflects_current_id(self):
        id1 = self.queue.next_request_id()
        self.assertTrue(self.queue.is_latest(id1))
        id2 = self.queue.next_request_id()
        self.assertFalse(self.queue.is_latest(id1))
        self.assertTrue(self.queue.is_latest(id2))


if __name__ == "__main__":
    unittest.main()
