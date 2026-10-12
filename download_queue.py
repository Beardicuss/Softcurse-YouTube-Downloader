"""Deterministic sequential queue state independent of the Tkinter UI."""

from dataclasses import dataclass, replace
from enum import Enum
from urllib.parse import urlparse


class QueueStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class QueueItem:
    id: int
    url: str
    status: QueueStatus = QueueStatus.PENDING
    detail: str = ""


class DownloadQueue:
    def __init__(self):
        self._items = []
        self._next_id = 1

    @property
    def items(self):
        return tuple(self._items)

    def add_urls(self, urls):
        existing = {item.url for item in self._items if item.status == QueueStatus.PENDING}
        added = []
        for raw_url in urls:
            url = raw_url.strip()
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or url in existing:
                continue
            item = QueueItem(self._next_id, url)
            self._next_id += 1
            self._items.append(item)
            existing.add(url)
            added.append(item)
        return tuple(added)

    def next_pending(self):
        if any(item.status == QueueStatus.ACTIVE for item in self._items):
            return None
        for index, item in enumerate(self._items):
            if item.status == QueueStatus.PENDING:
                active = replace(item, status=QueueStatus.ACTIVE)
                self._items[index] = active
                return active
        return None

    def finish(self, item_id, status, detail=""):
        if status not in {QueueStatus.COMPLETE, QueueStatus.FAILED, QueueStatus.CANCELLED}:
            raise ValueError("Queue item can only finish with a terminal status")
        for index, item in enumerate(self._items):
            if item.id == item_id and item.status == QueueStatus.ACTIVE:
                self._items[index] = replace(item, status=status, detail=detail)
                return self._items[index]
        return None

    def remove_pending(self, item_id):
        before = len(self._items)
        self._items = [
            item for item in self._items
            if not (item.id == item_id and item.status == QueueStatus.PENDING)
        ]
        return len(self._items) != before

    def clear_terminal(self):
        self._items = [
            item for item in self._items
            if item.status in {QueueStatus.PENDING, QueueStatus.ACTIVE}
        ]

