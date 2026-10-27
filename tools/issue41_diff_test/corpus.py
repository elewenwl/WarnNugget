"""Corpus：用真实的 FileToRestore 构造生产等价的注入项。

所有 item 都是仓库里真实的 FileToRestore（src/utils/file_to_restore.py，stdlib-only），
因此 contents / contents_path 的形态与生产一致（posterboard 的绝大多数 payload 是
contents=None + contents_path=<真实文件>）。
"""
import hashlib
from pathlib import Path

CONFIG_DOMAIN = "SysSharedContainerDomain-systemgroup.com.apple.configurationprofiles"
PB_DOMAIN = "AppDomain-com.apple.PosterBoard"
HOME = "HomeDomain"

# 在 fixture 里真实存在、且剪枝后仍保留的行（payload 已在 fixture 中）
EXISTING = [
    (HOME, "Library/SpringBoard/IconState.plist"),
    (HOME, "Library/ControlCenter/ControlsIconState.plist"),
    (HOME, "Library/Preferences/com.apple.Accessibility.plist"),
    (HOME, "Library/Accounts/Accounts3.sqlite"),
]


def _fid(domain: str, rel: str) -> str:
    return hashlib.sha1(f"{domain}-{rel}".encode()).hexdigest()


def _src(dirpath: Path, name: str, data: bytes) -> str:
    dirpath.mkdir(parents=True, exist_ok=True)
    p = dirpath / name
    p.write_bytes(data)
    return str(p)


def build_items(dev: Path, scenario: str, make, *, FileToRestore,
                payload_dir: Path):
    """make(...) 是 FileToRestore 的构造器（真实类）。返回 items 列表。"""
    src = payload_dir
    items = []

    def add(domain, rel, contents=None, contents_path=None, owner=501, group=501):
        items.append(FileToRestore(contents=contents, contents_path=contents_path,
                                   restore_path="/" + rel, domain=domain,
                                   owner=owner, group=group))
        return items[-1]

    if scenario == "mixed":
        # 1) 已存在且字节完全相同 -> 新路径的 skip 分支
        d, r = EXISTING[0]
        add(d, r, contents_path=_src(src, "identical.bin", b"PRISTINE:" + _fid(d, r).encode()))
        # 2) 已存在但字节不同 -> 必须重写
        d, r = EXISTING[2]
        add(d, r, contents_path=_src(src, "changed.bin", b"CHANGED-CONTENT"))
        # 3) 已存在的深层目录 + 3MB payload
        d, r = EXISTING[3]
        add(d, r, contents_path=_src(src, "big.bin", b"X" * (3 << 20)))
        # 4) 全新目录链
        add(HOME, "Library/NuggetTweak/deep/nested/asset.bin", contents=b"new-tree")
        # 5) _SKIP_PATH_PREFIXES 下的路径（被剪枝，行必须新建）
        add(HOME, "Library/SpringBoard/statusBarOverrides/Bar.plist", contents=b"statusbar")
        # 6) 被剪掉的兄弟目录（Documents 不在任何前缀里）
        add(HOME, "Documents/tweak-note.txt", contents=b"note")
        # 7) PosterBoard 深层新目录
        add(PB_DOMAIN, "Library/PRBPosterExtensionDataStore/DCIM/100APPLE/versions/0/contents/0.ca",
            contents=b"posterball")
        # 8) fixture 里完全没有行的域 -> _build_mbfile_blob 回退
        add(CONFIG_DOMAIN, "Library/ConfigurationProfiles/lockscreen.plist", contents=b"profiles")
        # 9) 无目录成分的路径
        add(HOME, "top.txt", contents=b"top")
        # 10) str 形态 contents
        add(HOME, "Library/Preferences/str-contents.plist", contents="str-contents")
        # 11) 保留域根的域（SystemPreferencesDomain 根行被剪枝保留）
        add("SystemPreferencesDomain", "Library/Preferences/com.apple.Accessibility.plist",
            contents=b"sysprefs")
        return items

    if scenario == "reapply-identical":
        # 全部命中 skip 分支：正是「同一个 tweak 再应用一次」的真实形态
        for i, (d, r) in enumerate(EXISTING[:3]):
            add(d, r, contents_path=_src(src, f"same{i}.bin", b"PRISTINE:" + _fid(d, r).encode()))
        return items

    if scenario == "missing-contents":
        add(HOME, "Library/SpringBoard/IconState.plist")   # contents 与 contents_path 都是 None
        return items

    if scenario == "encrypted":
        return build_items(dev, "mixed", make, FileToRestore=FileToRestore,
                           payload_dir=payload_dir)

    if scenario == "wall":
        small = b"Y" * 4096
        for i in range(200):
            add(PB_DOMAIN, f"Library/PRBPosterExtensionDataStore/DCIM/{i:04d}/versions/0/contents/{i}.ca",
                contents_path=_src(src, f"w{i}.bin", small))
        return items

    if scenario == "memory":
        blob = b"Z" * (6 << 20)          # 6 MB / 文件
        for i in range(40):
            add(PB_DOMAIN, f"Library/PRBPosterExtensionDataStore/BIG/{i}/v/0/contents/{i}.ca",
                contents_path=_src(src, f"m{i}.bin", blob))
        return items

    raise SystemExit(f"unknown scenario {scenario}")
