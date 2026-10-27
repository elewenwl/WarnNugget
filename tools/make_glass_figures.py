#!/usr/bin/env python3
"""Regenerate the Liquid Glass figures embedded in docs/.

Two figures:

* ``docs/img/glass_tint_values.png`` -- 2x2 crop of the Settings search field
  under four states (no key / 0.5 / 1.0 / 0.0). Source frames come from
  ``tools/sim_tweak_verify.py`` (``/tmp/T0.png`` is the untouched baseline);
  pass ``--frames DIR`` if they live somewhere else.
* ``docs/img/glass_tint_curve.png`` -- the measured response curve. The
  numbers are the *measured* luminances, transcribed from the 8-point sweep;
  they are deliberately hard-coded rather than recomputed, because the point
  of the figure is to be the frozen record of one specific experiment.

Why this script exists at all: the first two attempts were produced ad hoc with
inline Python and both came out with every CJK glyph rendered as tofu (PIL's
default bitmap font has no CJK coverage, and it fails *silently* -- no warning,
no exception, just boxes). Keeping the figure generation in the repo means the
font is pinned and the mistake cannot recur.

Run with the managed interpreter::

    /Users/jason/.workbuddy/binaries/python/envs/default/bin/python \
        tools/make_glass_figures.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "docs" / "img"

# Hiragino Sans GB ships with macOS and has full CJK coverage. index=0 is W3
# (regular), index=2 is W6 (bold) inside the .ttc collection.
FONT_PATH = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FONT_REGULAR = 0
FONT_BOLD = 2

BG = (20, 20, 22)
FG = (236, 236, 238)
MUTED = (150, 150, 158)
GRID = (58, 58, 64)
ACCENT = (255, 159, 92)
ACCENT_DIM = (255, 159, 92, 26)
SEP = (90, 90, 98)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        FONT_PATH, size, index=FONT_BOLD if bold else FONT_REGULAR
    )


# --------------------------------------------------------------------------
# Figure 1: four-state crop of the Settings search field
# --------------------------------------------------------------------------

# The search field sits at y 2605..2735 in the 1320x2868 simulator capture; the
# crop pads it a little so the surrounding card edge is visible.
CROP_BOX = (0, 2560, 1320, 2820)

# ...but the *measurement* band is the field's inner strip only (y 2640..2696).
# Keep the two separate: measuring over the display crop pulls in the darker
# card edge and shifts every number by ~13, which silently invalidates the
# luminances quoted in the captions. (The guard below caught exactly that on
# the first run of this script.)
BAND_BOX = (0, 2640, 1320, 2696)

# Tolerance on the caption luminances. This is a *staleness* guard, not a
# precision check: the smallest real gap in this figure is 45.49 vs 47.33, and
# a wrong frame is off by 6-13. Meanwhile the exact mean depends on the pixel
# stride (the original sweep sampled every 8th pixel; this samples every 3rd),
# which drifts the number by up to ~0.25. So 0.5 rejects every real mistake and
# tolerates the sampling difference.
LUMA_TOLERANCE = 0.5

PANELS = [
    ("T0.png", "不写任何 key", "基准", "45.49", None),
    ("SW_amt_0.5.png", "UIViewGlassTintAmount = 0.5", "默认", "45.49", "与基准逐字节相同"),
    ("SW_amt_1.0.png", "UIViewGlassTintAmount = 1.0", "更深", "38.26", "明显变暗且不透明"),
    ("SW_amt_0.0.png", "UIViewGlassTintAmount = 0.0", "更透", "47.33", "有差异但很轻微"),
]


def mean_luma(im: Image.Image) -> float:
    g = im.convert("L")
    w, h = g.size
    px = g.load()
    vals = [px[x, y] for y in range(0, h, 3) for x in range(0, w, 3)]
    return sum(vals) / len(vals)


def figure_values(frames: Path, out: Path) -> None:
    scale = 0.92
    panels = []
    for name, title, tag, expected, note in PANELS:
        src = frames / name
        if not src.exists():
            raise SystemExit(f"缺少源帧：{src}")
        full = Image.open(src).convert("RGB")
        measured = mean_luma(full.crop(BAND_BOX))
        # The caption quotes the measured number; assert it still matches so a
        # stale frame can never silently produce a figure with wrong labels.
        if abs(measured - float(expected)) > LUMA_TOLERANCE:
            raise SystemExit(
                f"源帧与实验记录不符：{name} 期望亮度 {expected}，实测 {measured:.3f}\n"
                f"  -> 帧目录 {frames} 里的不是当次实验的截图，别拿它生成图。"
            )
        # The caption quotes the recorded figure, not this re-measurement --
        # otherwise the last digit could disagree with the tables in
        # docs/LiquidGlass_Keys.md. The measurement is only the staleness guard.
        panels.append((full.crop(CROP_BOX), title, tag, note, float(expected)))

    tw = int(panels[0][0].width * scale)
    th = int(panels[0][0].height * scale)
    gap = 14
    header = 46
    canvas = Image.new(
        "RGB", (tw * 2 + gap * 3, (th + header) * 2 + gap * 3), BG
    )
    d = ImageDraw.Draw(canvas)
    f_title = font(21, bold=True)
    f_meta = font(17)

    for i, (im, title, tag, note, measured) in enumerate(panels):
        col, row = i % 2, i // 2
        x = gap + col * (tw + gap)
        y = gap + row * (th + header + gap)
        d.text((x + 2, y + 10), title, font=f_title, fill=FG)
        meta = f"{tag} · 亮度 {measured:.2f}"
        if note:
            meta += f" · {note}"
        d.text((x + 2, y + 34), meta, font=f_meta, fill=MUTED)
        canvas.paste(im.resize((tw, th), Image.LANCZOS), (x, y + header))

    canvas.save(out)
    print(f"saved {out} {canvas.size}")


# --------------------------------------------------------------------------
# Figure 2: the measured response curve
# --------------------------------------------------------------------------

# (amount, sha256[:12], mean luminance of the search field)
CURVE = [
    (0.00, "f41d619ba80d", 47.33),
    (0.25, "4c58fb12f338", 46.20),
    (0.50, "707c142da4f3", 45.49),
    (0.55, "2d47d622a7de", 43.58),
    (0.60, "762a546d45c9", 41.94),
    (0.65, "af225ca929b7", 40.51),
    (0.75, "a71a3d6c89ed", 38.51),
    (1.00, "93056824a955", 38.26),
]


def figure_curve(out: Path) -> None:
    W, H = 1400, 780
    L, R, T, B = 96, 70, 116, 128  # margins
    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)

    y_lo, y_hi = 37.4, 48.2

    def px(amount: float) -> float:
        return L + amount * (W - L - R)

    def py(lum: float) -> float:
        return T + (y_hi - lum) / (y_hi - y_lo) * (H - T - B)

    # --- title
    d.text((L - 44, 30), "UIViewGlassTintAmount —— 实测响应曲线", font=font(27, bold=True), fill=FG)
    d.text(
        (L - 44, 68),
        "iOS 27 · iPhone 18 Pro Max 模拟器 · 设置 App 置前台 · 外观钉死深色 · 对照窗口=搜索框",
        font=font(17),
        fill=MUTED,
    )

    # --- effective band 0.50 - 0.75
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([px(0.50), T, px(0.75), H - B], fill=ACCENT_DIM)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(canvas)

    # --- grid + y axis
    for lum in (38, 40, 42, 44, 46, 48):
        y = py(lum)
        d.line([(L, y), (W - R, y)], fill=GRID, width=1)
        d.text((L - 44, y - 9), f"{lum}", font=font(16), fill=MUTED)
    d.text((L + 40, T - 30), "搜索框平均亮度", font=font(16), fill=MUTED)

    # --- x axis
    d.line([(L, H - B), (W - R, H - B)], fill=SEP, width=2)
    for amount in (0.00, 0.25, 0.50, 0.75, 1.00):
        x = px(amount)
        d.line([(x, H - B), (x, H - B + 7)], fill=SEP, width=2)
        lbl = f"{amount:.2f}"
        tw = d.textlength(lbl, font=font(16))
        d.text((x - tw / 2, H - B + 14), lbl, font=font(16), fill=MUTED)
    d.text((L, H - B + 46), "UIViewGlassTintAmount", font=font(16), fill=MUTED)

    # --- the 0.5 neutral marker
    x05 = px(0.50)
    for y in range(T, H - B, 12):
        d.line([(x05, y), (x05, y + 6)], fill=(120, 120, 128), width=1)

    # --- curve
    pts = [(px(a), py(v)) for a, _, v in CURVE]
    d.line(pts, fill=ACCENT, width=3, joint="curve")
    for i, ((a, fp, v), (x, y)) in enumerate(zip(CURVE, pts)):
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=ACCENT, outline=BG, width=2)
        # alternate label side so the crowd around 0.55-0.75 stays readable
        up = i in (0, 1, 2, 4, 6)
        off = -34 if up else 12
        txt = f"{v:.2f}"
        tw = d.textlength(txt, font=font(16, bold=True))
        d.text((x - tw / 2, y + off), txt, font=font(16, bold=True), fill=FG)

    # --- endpoint annotations (kept clear of the subtitle band and of the
    #     point-value labels, which sit *above* their points)
    d.text((L + 16, py(47.33) + 16), "0.00 = More Clear", font=font(17, bold=True), fill=(150, 214, 170))
    t_end = "1.00 = More Tinted"
    tw = d.textlength(t_end, font=font(17, bold=True))
    d.text((W - R - tw - 6, py(38.26) - 40), t_end, font=font(17, bold=True), fill=ACCENT)

    # --- neutral label under the marker
    n_lbl = "0.50 = Default"
    tw = d.textlength(n_lbl, font=font(16))
    d.text((x05 - tw / 2, H - B + 46), n_lbl, font=font(16), fill=(170, 190, 220))

    # --- band label
    d.text((px(0.50) + 10, T + 12), "有效区间 0.50 – 0.75", font=font(17, bold=True), fill=ACCENT)

    # --- slope summary
    # NB: ASCII "-" only -- U+2212 MINUS SIGN is tofu in Hiragino Sans GB,
    # same as "=>" above. PIL fails silently on missing glyphs.
    d.text(
        (L - 44, H - 62),
        "斜率：0.0-0.5 约 -3/单位（几乎不动）  →  0.5-0.55 骤增至 -38/单位  →  0.75 以上回到 -1/单位（两端饱和）",
        font=font(17),
        fill=FG,
    )
    d.text(
        (L - 44, H - 36),
        # NB: no "⇒" here -- Hiragino Sans GB has no glyph for it and PIL
        # renders tofu without complaining.
        "8 个取值 → 8 个不同 PNG 指纹，曲线平滑单调，不存在阈值跳变 → 设置页是连续滑杆，不是三档开关。",
        font=font(17),
        fill=MUTED,
    )

    canvas.save(out)
    print(f"saved {out} {canvas.size}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", default="/tmp", help="sim_tweak_verify.py 留下的源帧目录")
    ap.add_argument("--only", choices=["values", "curve"], help="只生成其中一张")
    args = ap.parse_args()

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    if args.only != "curve":
        figure_values(Path(args.frames), IMG_DIR / "glass_tint_values.png")
    if args.only != "values":
        figure_curve(IMG_DIR / "glass_tint_curve.png")


if __name__ == "__main__":
    main()
