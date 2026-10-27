"""Idempotent compatibility adapters for the pinned mobilebackup2 protocol."""
import shutil
import sys
from pymobiledevice3.exceptions import NotEnoughDiskSpaceError
from src.utils.log_util import log_info, log_warn, log_debug

def install_verbose(disk_space_message) -> None:
    """Log free-space traffic and answer purge requests without aborting the link.

    The device decides how much it uploads (and whether it trims large app
    containers like PosterBoard) based on the free-space value the host reports
    on ``DLMessageGetFreeDiskSpace`` — the only platform-forked part of the
    whole backup path (APFS purgeable space on macOS). A purge request is not
    the device's final verdict. Match the upstream fix after pinned 10.7.1:
    reply that no space was reclaimed, then wait for success or a real error.
    https://github.com/doronz88/pymobiledevice3/issues/1879
    """
    try:
        from pymobiledevice3.services.device_link import DeviceLink
    except Exception as e:  # pragma: no cover - defensive
        log_debug(f"DeviceLink verbose hook not installed: {e}")
        return
    if getattr(DeviceLink, "_gn_verbose_installed", False):
        return
    original_receive_message = DeviceLink.receive_message

    async def get_free_disk_space(self, _message):
        statvfs = shutil.disk_usage(self.root_path).free
        important = None
        if sys.platform == "darwin":
            try:
                from pymobiledevice3.services.device_link import _darwin_important_available_capacity
                important = _darwin_important_available_capacity(self.root_path)
            except Exception as e:
                log_debug(f"darwin important-capacity lookup failed: {e}")
        freespace = max(statvfs, important) if important is not None else statvfs
        log_info(f"DeviceLink free-space query | root={self.root_path} | "
                 f"statvfs={statvfs} | purgeable_aware={important} | reported={freespace}")
        self._gn_reported_free_space = freespace
        await self.status_response(0, status_dict=freespace)

    async def purge_disk_space(self, message):
        self._gn_purge_requested = True
        amount = message[1] if len(message) > 1 else None
        log_warn(f"DeviceLink: device requested host DISK PURGE | root={self.root_path} | "
                 f"requested_bytes={amount}; no space reclaimed, waiting for device verdict")
        # The amount is a purge request, not a reliable required-backup size.
        # Never report fabricated free space or delete user files to satisfy it.
        await self.status_response(-1, "DLPurgeDiskSpace failed to purge", status_dict=0)

    async def receive_message(self):
        message = await original_receive_message(self)
        # Preserve the pinned dl_loop's handling of every other message/error.
        # MBErrorDomain/105 after a host purge request is an actual refusal.
        if (getattr(self, "_gn_purge_requested", False)
                and len(message) > 1 and message[0] == "DLMessageProcessMessage"
                and isinstance(message[1], dict) and message[1].get("ErrorCode") == 105):
            raise NotEnoughDiskSpaceError(disk_space_message(
                self.root_path, getattr(self, "_gn_reported_free_space", None)))
        return message

    DeviceLink.get_free_disk_space = get_free_disk_space
    DeviceLink.purge_disk_space = purge_disk_space
    DeviceLink.receive_message = receive_message
    DeviceLink._gn_verbose_installed = True


def install_contents():
    """Make ``DLContentsOfDirectory`` tolerant of missing directories.

    The device enumerates the prior backup's ``Snapshot`` payload directory
    during an incremental backup. The cache master keeps payloads directly
    under ``<udid>/<xx>/<fileid>`` (no ``Snapshot`` subdirectory), so the
    stock pymobiledevice3 handler crashes on ``path.iterdir()``
    (FileNotFoundError) instead of answering. Apple's own host answers with an
    empty listing for a missing directory, which is how the device learns there
    is nothing to diff against and proceeds to a safe full rebuild. Mirror that:
    any missing/inaccessible enumeration target yields an empty status dict, so
    the backup never dies on the probe.
    """
    try:
        import datetime as _datetime
        from pymobiledevice3.services.device_link import APPLE_EPOCH, DeviceLink
        from typing import cast
    except Exception as e:  # pragma: no cover - defensive
        log_debug(f"DeviceLink contents shim not installed: {e}")
        return
    if getattr(DeviceLink, "_gn_contents_installed", False):
        return

    async def contents_of_directory(self, message):
        data = {}
        path = self.root_path / cast(str, message[1])
        if path.is_dir():
            for file in path.iterdir():
                ftype = "DLFileTypeUnknown"
                if file.is_dir():
                    ftype = "DLFileTypeDirectory"
                if file.is_file():
                    ftype = "DLFileTypeRegular"
                modifications_data = _datetime.datetime.fromtimestamp(file.stat().st_mtime - APPLE_EPOCH)
                modifications_data = modifications_data.replace(tzinfo=None)
                data[file.name] = {
                    "DLFileType": ftype,
                    "DLFileSize": file.stat().st_size,
                    "DLFileModificationDate": modifications_data,
                }
        else:
            log_debug(f"DeviceLink contents-of-directory: \"{message[1]}\" absent "
                      f"under {self.root_path} — answering with an empty listing")
        await self.status_response(0, status_dict=data)

    DeviceLink.contents_of_directory = contents_of_directory
    DeviceLink._gn_contents_installed = True
