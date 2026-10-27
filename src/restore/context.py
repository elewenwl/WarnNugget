"""Explicit configuration and connection ownership for restore phases."""
from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class RestoreOptions:
    backup_password: str = field(default="", repr=False)
    reboot: bool = False
    skip_setup: bool = True
    skip_protective_backup: bool = False
    include_keychain: bool = False
    merge_phases: bool = True
    supervised: bool = False
    organization_name: str = ""
    prompt_choice: Callable | None = None
    stage_callback: Callable | None = None


@dataclass
class RestoreSession:
    # Each phase publishes replacements even on an exception, so the caller
    # closes the current session rather than a stale pre-reconnect client.
    client: object
    backup_complete: bool = False
