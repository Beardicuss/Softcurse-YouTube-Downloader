"""Coordinates asynchronous preview requests independently of Tkinter."""


class PreviewRequestCoordinator:
    def __init__(self):
        self.current_url = ""

    def begin(self, url: str) -> bool:
        if not url or url == self.current_url:
            return False
        self.current_url = url
        return True

    def clear(self):
        self.current_url = ""

    def is_current(self, url: str) -> bool:
        return bool(url) and url == self.current_url
