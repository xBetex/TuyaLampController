from collections import deque
from typing import Callable, List, Tuple
import time

# Record tuple: (timestamp_str, direction, color_hex, message)
Record = Tuple[str, str, str, str]


class ColorHistory:
    def __init__(self, maxlen: int = 10):
        self._buf: deque[Record] = deque(maxlen=maxlen)
        self._subs: List[Callable[[List[Record]], None]] = []

    def set_maxlen(self, maxlen: int):
        # Rebuild deque with new maxlen preserving most recent
        items = list(self._buf)[-maxlen:]
        self._buf = deque(items, maxlen=maxlen)
        self._notify()

    def add(self, direction: str, color: str, message: str):
        ts = time.strftime("%H:%M:%S")
        color_norm = (color or "").strip().lower()
        rec: Record = (ts, direction, color_norm, message)
        self._buf.append(rec)
        self._notify()

    def get_entries(self) -> List[Record]:
        return list(self._buf)

    def subscribe(self, callback: Callable[[List[Record]], None]):
        if callback not in self._subs:
            self._subs.append(callback)
            try:
                callback(self.get_entries())
            except Exception:
                pass

    def unsubscribe(self, callback: Callable[[List[Record]], None]):
        try:
            self._subs.remove(callback)
        except ValueError:
            pass

    def _notify(self):
        entries = self.get_entries()
        for cb in list(self._subs):
            try:
                cb(entries)
            except Exception:
                # Keep others alive even if one subscriber errors
                pass


# Global singleton
HIST = ColorHistory(maxlen=10)
