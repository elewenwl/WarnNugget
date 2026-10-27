"""Cooperative pause at AFC file boundaries; never suspend a restore thread."""
import asyncio
from contextvars import ContextVar
from threading import Event

current_pause_control = ContextVar("restore_pause_control", default=None)


class RestorePauseControl:
    def __init__(self, on_resume=None):
        self.requested = Event()
        self.state = "unavailable"
        self.on_resume = on_resume

    def request_pause(self):
        if self.state != "available":
            return
        self.requested.set()
        self.state = "pending"

    def resume(self):
        self.requested.clear()

    async def wait_for_resume(self):
        self.state = "paused"
        while self.requested.is_set():
            await asyncio.sleep(0.15)
        self.state = "resuming"
        if self.on_resume:
            self.on_resume()

    def finish_media(self):
        self.requested.clear()
        self.state = "unavailable"

    def finish(self):
        self.finish_media()
