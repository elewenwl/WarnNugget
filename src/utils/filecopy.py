"""Independent filesystem clones where supported, with a portable copy fallback."""
import os
import shutil
import sys


def clone_or_copy(source, destination):
    """Unlike hardlinks, modifying the destination never changes the source."""
    cloned = False
    if sys.platform == "darwin":
        import ctypes
        library = ctypes.CDLL(None, use_errno=True)
        clone = getattr(library, "clonefile", None)
        if clone is not None:
            clone.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int)
            clone.restype = ctypes.c_int
            cloned = clone(os.fsencode(source), os.fsencode(destination), 0) == 0
    elif sys.platform.startswith("linux"):
        import fcntl
        created = False
        try:
            with open(source, "rb") as incoming, open(destination, "xb") as outgoing:
                created = True
                fcntl.ioctl(outgoing.fileno(), 0x40049409, incoming.fileno())  # FICLONE
                cloned = True
        except OSError:
            if created:
                os.unlink(destination)
    if cloned:
        shutil.copystat(source, destination)
    else:
        shutil.copy2(source, destination)
