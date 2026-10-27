"""Autosave outcome and revision tracking, independent of Qt or storage."""
from dataclasses import dataclass


@dataclass
class AutosaveState:
    revision: int = 0
    saved_revision: int = 0
    status: str = "idle"
    error: str = ""

    @property
    def dirty(self):
        return self.revision != self.saved_revision

    def changed(self):
        self.revision += 1
        self.status = "dirty"

    def finish(self, revision, result, *, enabled=True):
        if isinstance(result, Exception) or result is not True:
            if self.saved_revision == self.revision:
                self.saved_revision = -1
            self.status = "error" if enabled else "cancelled"
            self.error = str(result) if isinstance(result, Exception) else "Preset was not committed"
            return
        self.saved_revision = revision
        self.error = ""
        self.status = "saved" if not self.dirty else "dirty"
