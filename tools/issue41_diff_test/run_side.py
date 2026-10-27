"""按 1:1 复刻生产的两种调用方式跑同一份 fixture，产出可比对的 artifact。

- old = 仓库当前源码（参照实现）
- new = 补丁机械应用后的源码（/tmp/gn_audit/patched）
两边都是**源码原文**，通过 importlib 按路径加载（绕开 src/restore/__init__.py 的设备栈）。
"""
import argparse
import hashlib
import importlib.util
import json
import os
import plistlib
import resource
import shutil
import sqlite3
import sys
import time
import types
from pathlib import Path

AUDIT_DIR = os.environ.get("GN_AUDIT_DIR", "/tmp/gn_audit")
OLD_SRC = os.environ.get("GN_OLD_INJECT", "/Users/jason/GoldenNugget/src/restore/inject.py")
NEW_SRC = os.environ.get("GN_PATCHED_INJECT", f"{AUDIT_DIR}/patched/src/restore/inject.py")
FILE_TO_RESTORE = "/Users/jason/GoldenNugget/src/utils/file_to_restore.py"

sys.path.insert(0, AUDIT_DIR)
import corpus  # noqa: E402  (corpus 自己 import FileToRestore)


def stub_device_stack():
    """pymobiledevice3 只被用来拿一个加密标记 —— 打桩，保证可离线跑。"""
    enc = os.environ.get("GN_STUB_ENCRYPTED") == "1"
    p = types.ModuleType("pymobiledevice3")
    services = types.ModuleType("pymobiledevice3.services")
    mb2 = types.ModuleType("pymobiledevice3.services.mobilebackup2")

    class Mobilebackup2Service:
        @staticmethod
        def _is_encrypted_backup(device_dir):
            return enc

    mb2.Mobilebackup2Service = Mobilebackup2Service
    services.mobilebackup2 = mb2
    p.services = services
    sys.modules["pymobiledevice3"] = p
    sys.modules["pymobiledevice3.services"] = services
    sys.modules["pymobiledevice3.services.mobilebackup2"] = mb2


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def typed(value, depth=0):
    """带类型标签的规范化表示 —— int/real/bool/bytes/uid 不会被中转格式压平。"""
    if depth > 6:
        return "..."
    if isinstance(value, bool):
        return f"bool:{'true' if value else 'false'}"
    if isinstance(value, int):
        return f"int:{value}"
    if isinstance(value, float):
        return f"real:{value!r}"
    if isinstance(value, str):
        return f"str:{value}"
    if isinstance(value, (bytes, bytearray)):
        return "bytes:" + bytes(value).hex()
    if isinstance(value, plistlib.UID):
        return f"uid:{value.data}"
    if isinstance(value, dict):
        return "{" + ",".join(f"{k}={typed(v, depth + 1)}" for k, v in sorted(value.items())) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(typed(v, depth + 1) for v in value) + "]"
    return f"{type(value).__name__}:{value!r}"


def dump_state(dev: Path):
    conn = sqlite3.connect(str(dev / "Manifest.db"))
    rows = []
    for fid, domain, rel, flags, blob in conn.execute(
            "SELECT fileID, domain, relativePath, flags, file FROM Files"):
        if blob is None:
            body = None
        else:
            try:
                body = typed(plistlib.loads(blob))
            except Exception as e:                                    # noqa: BLE001
                body = f"UNPARSEABLE:{type(e).__name__}"
        rows.append([fid, domain, rel, flags, body])
    rows.sort()
    conn.close()

    payloads = {}
    for p in sorted(dev.rglob("*")):
        if p.is_file() and p.name != "Manifest.db":
            payloads[str(p.relative_to(dev))] = (
                hashlib.sha1(p.read_bytes()).hexdigest(), p.stat().st_size)
    return rows, payloads


def run(impl: str, fixture: Path, scenario: str, workdir: Path):
    stub_device_stack()
    mod = load_module(OLD_SRC if impl == "old" else NEW_SRC, f"inject_{impl}")
    ftr_mod = load_module(FILE_TO_RESTORE, "file_to_restore")

    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True)
    shutil.copytree(fixture / "device", workdir / "device", symlinks=True)
    dev = workdir / "device"

    items = corpus.build_items(dev, scenario, None,
                               FileToRestore=ftr_mod.FileToRestore,
                               payload_dir=workdir / "_src")
    injected = failed = skipped = 0
    errors = []

    t0 = time.perf_counter()
    try:
        if impl == "old":
            for f in items:
                rel = f.restore_path.lstrip("/")
                data = f.contents
                if data is None and f.contents_path:
                    with open(f.contents_path, "rb") as fh:
                        data = fh.read()
                if isinstance(data, str):
                    data = data.encode("utf-8")
                ok = mod.inject_file_into_backup(
                    str(workdir), "device", f.domain, rel, data,
                    mode=ftr_mod._FileMode.S_IFREG | 0o644,
                    owner=f.owner, group=f.group, manifest_password="")
                injected += 1 if ok else 0
                failed += 0 if ok else 1
        else:
            prepared = []
            for f in items:
                rel = f.restore_path.lstrip("/")
                data = f.contents
                if data is None and f.contents_path:
                    with open(f.contents_path, "rb") as fh:
                        data = fh.read()
                if isinstance(data, str):
                    data = data.encode("utf-8")
                prepared.append((f.domain, rel, data,
                                 ftr_mod._FileMode.S_IFREG | 0o644, f.owner, f.group))
            if prepared:
                injected, failed, skipped = mod.inject_files_into_backup(
                    str(workdir), "device", prepared, manifest_password="")
    except Exception as e:                                            # noqa: BLE001
        errors.append(f"{type(e).__name__}: {e}")
    wall = time.perf_counter() - t0

    rows, payloads = dump_state(dev)
    return {
        "impl": impl,
        "scenario": scenario,
        "items": len(items),
        "counters": {"injected": injected, "failed": failed, "skipped": skipped},
        "wall_s": round(wall, 3),
        "peak_rss_kb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "errors": errors,
        "rows": rows,
        "payloads": payloads,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", required=True, choices=["old", "new"])
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    art = run(a.impl, Path(a.fixture), a.scenario,
              Path(AUDIT_DIR) / "work" / f"{a.scenario}_{a.impl}")
    Path(a.out).write_text(json.dumps(art))
    print(f"{a.impl}/{a.scenario}: counters={art['counters']} wall={art['wall_s']}s "
          f"peakRSS={art['peak_rss_kb'] / 1048576:.1f}MB errors={art['errors']}")


if __name__ == "__main__":
    main()
