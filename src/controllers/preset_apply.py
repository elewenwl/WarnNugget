"""Prepare a complete preset before publishing any tweak state."""
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class PresetApplyResult:
    applied: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def success(self):
        return not self.errors


def apply_preset_transaction(entries: dict, store, prepare: Callable) -> PresetApplyResult:
    candidates, skipped = {}, []
    for name, data in entries.items():
        try:
            prepared = prepare(name, data)
            if prepared is None:
                skipped.append(name)
            else:
                key, candidate = prepared
                candidates[key] = candidate
        except Exception as exc:
            return PresetApplyResult(skipped=tuple(skipped),
                                     errors=(f"{name}: {type(exc).__name__}: {exc}",))
    if hasattr(store, "commit"):
        store.commit(candidates)
    else:
        # Compatibility for callers providing an ordinary dict in tools.
        for key, candidate in candidates.items():
            store[key].__dict__.update(candidate.__dict__)
    return PresetApplyResult(tuple(key.name for key in candidates), tuple(skipped))
