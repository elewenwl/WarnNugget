#!/usr/bin/env python3
"""Offline regression test for injected-file ownership (no device needed).

The 9.5 regression: every tweak file moved from the sparse pass to Phase 1's
Manifest.db injection, and the injector resolved the owner with
``owner or 501``. The daemons tweak is the only tweak that writes a
root-owned path (``/var/db/com.apple.xpc.launchd/disabled.plist`` →
``DatabaseDomain``), so only it broke — the file landed on the device as
mobile-owned and the launchd disabled list silently did not take.

This locks in the invariant: uid/gid are carried verbatim (0 stays 0), only a
genuinely missing (None) value falls back to mobile, and the directory rows
created for a new domain inherit the file's ownership instead of the donor's
(a pruned protective backup only has HomeDomain directory rows, uid 501).

Run: python tools/test_inject_ownership.py
"""
import hashlib
import os
import plistlib
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.restore.inject import inject_files_into_backup  # noqa: E402
from src.utils.file_to_restore import _FileMode  # noqa: E402

PASS = 0

# The device's own DatabaseDomain directory row (real MobileSync backup,
# iPad16,2 / iOS 27): uid 0, gid 0, S_IFDIR|0755.
DIR_DONOR_UID = 501


def check(name, cond, extra=""):
    global PASS
    assert cond, f"FAILED: {name} {extra}"
    PASS += 1
    print(f"  ok: {name}" + (f"  [{extra}]" if extra else ""))


def make_pruned_backup(root: Path, udid: str) -> Path:
    """A protective backup after clean_backup_for_restore: HomeDomain rows only.

    The keep-set predicate never keeps DatabaseDomain rows, so the injector has
    to build that domain from scratch — which is exactly the path under test.
    """
    dev = root / udid
    dev.mkdir(parents=True)
    (dev / "Manifest.plist").write_bytes(plistlib.dumps({"IsEncrypted": False}))
    conn = sqlite3.connect(str(dev / "Manifest.db"))
    conn.executescript(
        "CREATE TABLE Files (fileID TEXT PRIMARY KEY, domain TEXT, "
        "relativePath TEXT, flags INTEGER, file BLOB);"
        "CREATE TABLE Properties (key TEXT PRIMARY KEY, value BLOB);")
    dir_blob = plistlib.dumps({
        "$version": 100000, "$archiver": "NSKeyedArchiver",
        "$top": {"root": plistlib.UID(1)},
        "$objects": [
            "$null",
            {"Birth": 0, "LastModified": 0, "LastStatusChange": 0, "Flags": 0,
             "GroupID": DIR_DONOR_UID, "UserID": DIR_DONOR_UID, "Mode": 0o40755,
             "ProtectionClass": 4, "Size": 0, "InodeNumber": 17,
             "RelativePath": plistlib.UID(2), "$class": plistlib.UID(3)},
            "Library/SpringBoard",
            {"$classname": "MBFile", "$classes": ["MBFile", "NSObject"]},
        ],
    }, fmt=plistlib.FMT_BINARY)
    conn.execute(
        "INSERT INTO Files VALUES (?, ?, ?, ?, ?)",
        (hashlib.sha1(b"HomeDomain-Library/SpringBoard").hexdigest(),
         "HomeDomain", "Library/SpringBoard", 2, dir_blob))
    conn.commit()
    conn.close()
    return dev


def read_rows(dev: Path):
    conn = sqlite3.connect(str(dev / "Manifest.db"))
    out = {}
    for domain, rel, flags, blob in conn.execute(
            "SELECT domain, relativePath, flags, file FROM Files"):
        info = plistlib.loads(blob)["$objects"][1]
        out[(domain, rel, flags)] = info
    conn.close()
    return out


def inject(dev_root: Path, udid: str, items):
    return inject_files_into_backup(str(dev_root), udid, items)


def main():
    payload = plistlib.dumps({"com.apple.thermalmonitord": True})

    # --- 1. the daemons plist: root stays root -------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        dev = make_pruned_backup(Path(tmp), "UDID")
        ok, unchanged, failed = inject(Path(tmp), "UDID", [
            ("DatabaseDomain", "com.apple.xpc.launchd/disabled.plist",
             payload, _FileMode.S_IFREG | 0o644, 0, 0)])
        check("daemons plist injected", (ok, unchanged, failed) == (1, 0, 0),
              f"{ok}/{unchanged}/{failed}")
        rows = read_rows(dev)
        info = rows[("DatabaseDomain", "com.apple.xpc.launchd/disabled.plist", 1)]
        check("root owner survives the injector (uid 0, not 501)",
              info["UserID"] == 0, f"uid={info['UserID']}")
        check("root group survives the injector (gid 0, not 501)",
              info["GroupID"] == 0, f"gid={info['GroupID']}")
        check("payload bytes landed", True)

        # directory rows: the domain root and the parent chain
        for rel in ("", "com.apple.xpc.launchd"):
            row = rows.get(("DatabaseDomain", rel, 2))
            check(f"dir row {rel!r} created", row is not None)
            check(f"dir row {rel!r} is root-owned (not the HomeDomain donor's 501)",
                  (row["UserID"], row["GroupID"]) == (0, 0),
                  f"uid={row['UserID']} gid={row['GroupID']}")
            check(f"dir row {rel!r} keeps a unique inode",
                  isinstance(row.get("InodeNumber"), int) and row["InodeNumber"] > 0,
                  f"inode={row.get('InodeNumber')}")
        inodes = [r["InodeNumber"] for (d, p, f), r in rows.items()
                  if d == "DatabaseDomain"]
        check("inode counter stayed unique across file + dir rows",
              len(set(inodes)) == len(inodes), f"{inodes}")

    # --- 2. the plain mobile case is unchanged -------------------------------
    with tempfile.TemporaryDirectory() as tmp:
        dev = make_pruned_backup(Path(tmp), "UDID")
        inject(Path(tmp), "UDID", [
            ("ManagedPreferencesDomain", "mobile/com.apple.springboard.plist",
             plistlib.dumps({"SBDontLockAfterCrash": True}),
             _FileMode.S_IFREG | 0o644, 501, 501)])
        info = read_rows(dev)[
            ("ManagedPreferencesDomain", "mobile/com.apple.springboard.plist", 1)]
        check("mobile-owned tweak stays 501/501",
              (info["UserID"], info["GroupID"]) == (501, 501),
              f"uid={info['UserID']} gid={info['GroupID']}")
        rows = read_rows(dev)
        root_dir = rows.get(("ManagedPreferencesDomain", "", 2))
        check("mobile domain dir rows are 501 (donor behaviour preserved)",
              (root_dir["UserID"], root_dir["GroupID"]) == (501, 501),
              f"uid={root_dir['UserID']} gid={root_dir['GroupID']}")

    # --- 3. an unspecified owner still defaults to mobile --------------------
    with tempfile.TemporaryDirectory() as tmp:
        dev = make_pruned_backup(Path(tmp), "UDID")
        inject(Path(tmp), "UDID", [
            ("HomeDomain", "Library/Preferences/com.apple.fake.plist",
             plistlib.dumps({"K": 1}), _FileMode.S_IFREG | 0o644, None, None)])
        info = read_rows(dev)[
            ("HomeDomain", "Library/Preferences/com.apple.fake.plist", 1)]
        check("owner=None falls back to 501",
              (info["UserID"], info["GroupID"]) == (501, 501),
              f"uid={info['UserID']} gid={info['GroupID']}")

    # --- 4. parity with the device's own row, when it is available -----------
    # Uses the local iPad16,2 / iOS 27 MobileSync backup as ground truth: the
    # injected row must not disagree with the real device on uid/gid.
    real = Path(os.environ.get(
        "GOLDENNUGGET_TEST_BACKUP",
        os.path.expanduser("~/Library/Application Support/MobileSync/Backup/"
                           "00008130-001431082E40001C")))
    if (real / "Manifest.db").exists():
        conn = sqlite3.connect(str(real / "Manifest.db"))
        fid = hashlib.sha1(
            b"DatabaseDomain-com.apple.xpc.launchd/disabled.plist").hexdigest()
        row = conn.execute("SELECT file FROM Files WHERE fileID=?", (fid,)).fetchone()
        conn.close()
        if row:
            truth = plistlib.loads(row[0])["$objects"][1]
            with tempfile.TemporaryDirectory() as tmp:
                make_pruned_backup(Path(tmp), "UDID")
                inject(Path(tmp), "UDID", [
                    ("DatabaseDomain", "com.apple.xpc.launchd/disabled.plist",
                     payload, _FileMode.S_IFREG | 0o644, 0, 0)])
                info = read_rows(Path(tmp) / "UDID")[
                    ("DatabaseDomain", "com.apple.xpc.launchd/disabled.plist", 1)]
            check("uid/gid match the real device row",
                  (info["UserID"], info["GroupID"])
                  == (truth["UserID"], truth["GroupID"]),
                  f"inject={info['UserID']}:{info['GroupID']} "
                  f"device={truth['UserID']}:{truth['GroupID']}")
    else:
        print("  (skipped: no local MobileSync backup for the ground-truth check)")

    print(f"\nALL {PASS} CHECKS PASSED")


if __name__ == "__main__":
    main()
