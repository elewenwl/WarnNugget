#!/usr/bin/env python3
"""SpringBoard 偏好 key 的 A/B 差分分析器（分态闸门 + 状态栏屏蔽）。

配套 `docs/data/verify_sb_round9.sh` 这类采集脚本使用。设计要点全部来自实测踩坑记录：

1. **状态栏带整条屏蔽**（默认 y < 7.5% 画面高）
   本机状态栏（左时钟 + 右信号/WiFi/电池）会随机**整条不渲染**，造成同条件帧间
   0.99%~1.01% 的差 —— 与"写不同 override 条件"的 1.00% 无法区分。不屏蔽必然批量假阳性。

2. **分态闸门**（不能直接套全局中位数）
   帧大小常呈**双峰**（有无状态栏两档，差 ~0.10%）。全局中位数会落在两峰之间的空档，
   导致每帧都超阈、闸门全红。正确做法：先按状态栏状态分组，再在组内比中位数。

3. **三条分级闸门**
   - 息屏：size < 50% 最大帧 或 全屏均值 < 10        → FATAL 重采
   - 过渡：size 偏离**本组**中位数 > 1%               → FATAL 重采
   - 状态栏伪影：状态栏像素数与基线不同                → BENIGN，屏蔽后继续用

4. **按 manifest 时序配对**，绝不用文件名排序重建顺序。

5. **双值互比**（`K__A` vs `K__B`）：同一 key 写两个不同的值直接互比，
   不需要知道默认值 —— 两个值里至少一个偏离默认，非零差即证明 key 活着。

用法:
    python tools/sim_ab_analyze.py /tmp/sweep9
    python tools/sim_ab_analyze.py /tmp/sweep9 --thresh 0.02 --mask-frac 0.075
"""
from __future__ import annotations

import argparse
import os
import statistics
import sys

import numpy as np
from PIL import Image

FATAL_TRANSITION = 0.01  # 相对本组中位数的帧大小偏离阈值
NOISE_PX = 8             # 像素变化判据 |Δ| > 8


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def statusbar_px(a: np.ndarray) -> int:
    """状态栏带内的近白像素数 —— 用来判「状态栏是否整条渲染」。"""
    H = a.shape[0]
    return int((a[int(H * 0.02):int(H * 0.06), :].min(axis=2) > 200).sum())


def read_manifest(d: str) -> list[dict]:
    p = os.path.join(d, "manifest.tsv")
    if not os.path.exists(p):
        p = os.path.join(d, "manifest.txt")
    if not os.path.exists(p):
        # 退化：目录里所有 png，按 mtime 排序（仍不是文件名序）
        return [{"label": f[:-4], "key": "", "type": "", "value": ""}
                for f in sorted(os.listdir(d))
                if f.endswith(".png") and not f.startswith("cmp")]
    rows = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            c = line.split("\t")
            # 两代 manifest 格式：round9 = label|key|type|value
            #                    round8b = label|key|value|size
            if len(c) > 2 and c[2] in ("bool", "int", "float"):
                typ, val = c[2], (c[3] if len(c) > 3 else "")
            else:
                typ, val = "", (c[2] if len(c) > 2 else "")
            rows.append({"label": c[0],
                         "key": c[1] if len(c) > 1 else "",
                         "type": typ, "value": val})
    return rows


def masked_diff(A, B, mask_frac):
    d = np.abs(A - B).max(axis=2)
    H, W = d.shape
    cut = int(H * mask_frac)
    dm = d.copy()
    dm[:cut] = 0
    tot = 100.0 * (d > NOISE_PX).mean()
    tot2 = 100.0 * (dm > NOISE_PX).mean()
    peak = ""
    if (dm > NOISE_PX).sum():
        rows = (dm > NOISE_PX).sum(axis=1)
        cols = (dm > NOISE_PX).sum(axis=0)
        tr = np.argsort(rows)[-2:][::-1]
        tc = np.argsort(cols)[-2:][::-1]
        peak = ("  行 " + ", ".join(f"y={x/H:.3f}({rows[x]})" for x in tr if rows[x])
                + " 列 " + ", ".join(f"x={x/W:.3f}({cols[x]})" for x in tc if cols[x]))
    return tot, tot2, peak


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--mask-frac", type=float, default=0.075,
                    help="状态栏带占画面高度的比例（默认 0.075，整条屏蔽）")
    ap.add_argument("--thresh", type=float, default=0.02,
                    help="判定「有信号」的去状态栏差分阈值 %%（默认 0.02）")
    ap.add_argument("--baseline", default="base", help="复原油校验用的基线帧名")
    ap.add_argument("--restored", default="final", help="复原油校验用的收尾帧名")
    args = ap.parse_args()

    rows = read_manifest(args.dir)
    frames = {}
    print(f"=== 帧清单（{len(rows)} 行）===")
    print(f"{'帧':<46}{'字节':>10}{'状态栏px':>10}{'均值':>8}")
    for r in rows:
        p = os.path.join(args.dir, r["label"] + ".png")
        if not os.path.exists(p):
            print(f"{r['label']:<46}{'-- 缺失 --':>10}")
            continue
        a = load(p)
        frames[r["label"]] = a
        r["size"] = os.path.getsize(p)
        r["sb"] = statusbar_px(a)
        r["mean"] = float(a.mean())
        print(f"{r['label']:<46}{r['size']:>10}{r['sb']:>10}{r['mean']:>8.1f}")

    live = [r for r in rows if "size" in r]
    if not live:
        sys.exit("没有可用帧")

    # ---- 分态：先按状态栏状态分组，再在组内比中位数 ----
    print("\n=== 分态闸门 ===")
    present = [r for r in live if r["sb"] > 1000]
    absent = [r for r in live if r["sb"] <= 1000]
    print(f"  状态栏「有」{len(present)} 帧 / 「无」{len(absent)} 帧")
    groups = {}
    for name, g in (("有状态栏", present), ("无状态栏", absent)):
        if g:
            groups[name] = statistics.median([r["size"] for r in g])
            print(f"  {name}组中位数 {groups[name]:,.0f}")
    if len(groups) >= 2:
        vals = sorted(groups.values())
        print(f"  两组相差 {100*(vals[1]-vals[0])/vals[0]:.3f}%  "
              f"⇒ 双峰；全局中位数会落在空档，**不能**当闸门")

    print("\n=== 逐帧裁决 ===")
    bad_fatal = []
    for r in live:
        g = "有状态栏" if r["sb"] > 1000 else "无状态栏"
        med = groups.get(g, statistics.median([x["size"] for x in live]))
        dev = abs(r["size"] - med) / med
        if r["mean"] < 10 or r["size"] < 0.5 * max(x["size"] for x in live):
            v, why = "FATAL", "息屏/黑屏"
        elif dev > FATAL_TRANSITION:
            v, why = "FATAL", f"过渡帧(偏离本组中位数 {100*dev:.3f}%)"
        else:
            v, why = "OK", g + (f" · 偏离本组 {100*dev:.3f}%" if dev > 0.0005 else "")
        if v == "FATAL":
            bad_fatal.append(r["label"])
        print(f"  {r['label']:<46}{v:<7}{why}")

    # ---- 管线自校验 + 复原校验 ----
    print("\n=== 校验 ===")
    self_lbl = next((r["label"] for r in live if r["label"].endswith("2")
                     and r["label"].startswith(args.baseline)), None)
    if self_lbl and args.baseline in frames:
        _, t, pk = masked_diff(frames[args.baseline], frames[self_lbl], args.mask_frac)
        ok = "✔" if t == 0 else "✘"
        print(f"  管线确定性 {args.baseline} vs {self_lbl}: 去状态栏 {t:.4f}% {ok}")
    if args.baseline in frames and args.restored in frames:
        _, t, _ = masked_diff(frames[args.baseline], frames[args.restored], args.mask_frac)
        print(f"  复原油 {args.baseline} vs {args.restored}: 去状态栏 {t:.4f}% "
              f"{'✔ 完全复原' if t == 0 else '✘ 有残留，先查环境再解释'}")
    if bad_fatal:
        print(f"  ⚠️ 需重采的帧: {bad_fatal}")

    # ---- 时序差分 ----
    print(f"\n=== 时序差分（屏蔽 y<{int(args.mask_frac*100)}% 状态栏带）===")
    print(f"{'写入':<46}{'全屏':>9}{'去状态栏':>10}  变化带")
    hits = []
    for i in range(1, len(rows)):
        a, b = rows[i - 1]["label"], rows[i]["label"]
        if a not in frames or b not in frames:
            continue
        r = rows[i]
        lab = f"{r['key']} = {r['value']}" if r["key"] else f"({b})"
        tot, tot2, pk = masked_diff(frames[a], frames[b], args.mask_frac)
        flag = "  <<<" if tot2 > args.thresh else ""
        print(f"{lab:<46}{tot:>8.3f}%{tot2:>9.3f}%{pk}{flag}")
        if tot2 > args.thresh:
            hits.append(lab)

    # ---- 双值互比 ----
    pairs = {}
    for r in rows:
        if r["label"].endswith("__A") or r["label"].endswith("__B"):
            pairs.setdefault(r["key"], {})[r["label"][-1]] = r["label"]
    if pairs:
        print("\n=== 双值互比（同 key 两值直比；不需知道默认值）===")
        print(f"{'key':<46}{'全屏':>9}{'去状态栏':>10}  判定")
        for k, m in pairs.items():
            if "A" not in m or "B" not in m or m["A"] not in frames or m["B"] not in frames:
                continue
            tot, tot2, pk = masked_diff(frames[m["A"]], frames[m["B"]], args.mask_frac)
            verdict = "** 有差 → key 活着 **" if tot2 > args.thresh else "无差 → 惰性"
            print(f"{k:<46}{tot:>8.3f}%{tot2:>9.3f}%  {verdict}")
            if tot2 > args.thresh:
                hits.append(k)

    print("\n=== 汇总 ===")
    print("非零命中:", hits if hits else "无")
    if bad_fatal:
        print("⚠️ 有 FATAL 帧，命中判定不可信，需重采后重跑")


if __name__ == "__main__":
    main()
