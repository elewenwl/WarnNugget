"""Cooperative cancellation for bounded local background work."""
from contextvars import ContextVar
from threading import Event

_token = ContextVar("local_job_cancellation", default=None)


class JobCancelled(Exception):
    pass


class CancellationToken:
    def __init__(self):
        self._cancelled = Event()

    def cancel(self):
        self._cancelled.set()

    def check(self):
        if self._cancelled.is_set():
            raise JobCancelled("Local background operation cancelled")


def check_cancelled():
    token = _token.get()
    if token is not None:
        token.check()


def run_cancellable(callback, token):
    state = _token.set(token)
    try:
        token.check()
        return callback()
    finally:
        _token.reset(state)
