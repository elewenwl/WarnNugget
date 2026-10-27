"""AFC client capability boundary and compact transfer inventory entries."""
from dataclasses import dataclass
from typing import TypedDict


class TransferResult(TypedDict):
    files: int
    bytes: int


class BackupTransferResult(TransferResult, total=False):
    skipped: int
    failed: list[str]


@dataclass(frozen=True, slots=True)
class MediaEntry:
    relative: str
    size: int
    mtime: str | None

    @property
    def source(self):
        return "/" + self.relative


def service_concurrency(service) -> int:
    """Use concurrent requests only on a client that demultiplexes replies.

    This compatibility check is intentionally isolated here; unknown clients
    retain a single outstanding request. It must be revisited with the pinned
    pymobiledevice3 version when its AFC protocol adapter changes.
    """
    return 4 if (hasattr(service, "_afc_pending")
                 and hasattr(service, "_afc_write_lock")) else 1
