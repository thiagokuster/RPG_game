from queue import Queue
from threading import Lock


class EventBus:
    def __init__(self):
        self._subs = {}
        self._lock = Lock()

    def subscribe(self, room_code):
        queue = Queue()
        with self._lock:
            self._subs.setdefault(room_code, []).append(queue)
        return queue

    def unsubscribe(self, room_code, queue):
        with self._lock:
            subscribers = self._subs.get(room_code, [])
            if queue in subscribers:
                subscribers.remove(queue)
            if not subscribers:
                self._subs.pop(room_code, None)

    def publish(self, room_code, payload):
        with self._lock:
            subscribers = list(self._subs.get(room_code, []))
        for queue in subscribers:
            queue.put(payload)
