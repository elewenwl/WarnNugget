#!/bin/zsh
# 第八轮：新增 SpringBoard key 批次 A —— 主屏 / 状态栏 / 动态岛
#
# 选键原则（沿用第 1–7 轮的教训）：
#   1) 只用「元素增删型」或「静态可见」的 key（改布局 / 改尺寸 / 加删控件）。
#      纯行为型（手势、超时、计数）在模拟器上无通路，不浪费帧。
#   2) 每个 key 单独 respring → 与**上一帧**差分 → 单键归因。
#   3) 每个 key 写后**读回**，证明值确实落盘（否则"无效"可能是写失败）。
#   4) 尺寸守卫：<1MB 判未渲染重采；跑完后按**中位数 ±0.05%** 剔除离群帧。
#   5) 非零结果必须独立复现 ≥2 次才算命中（第 5 轮 1.242% 假阳性的教训）。
#   6) 差分区域**先量后切**：用行剖面定位变化带，不抄固定归一化区间。
#
# 用法：zsh docs/data/verify_sb_round8.sh [udid] [outdir]
set +e
U=${1:-2990A9E7-C09B-4D9A-A2BD-8CAD96F98999}
PY=/Users/jason/.workbuddy/binaries/python/envs/default/bin/python
OUT=${2:-/tmp/sweep8}
mkdir -p "$OUT"

MIN_BYTES=1000000
SETTLE=60
RETRIES=4
RETRY_WAIT=25

# ---- 批次定义：key|类型|值 ----
KEYS=(
  "SBRingerMuted|bool|true"
  "SBHomeLargeIcons|bool|true"
  "SBEnableHomeScreenWallpaperDimming|bool|true"
  "SBDisableParallaxOnPageControl|bool|true"
  "SBMainDisplayDarkeningPercentage|float|0.5"
  "SBShowThermalWarning|bool|true"
  "SBShowInternalWidgets|bool|true"
  "SBHomeScreenShowsBadgesInAppLibrary|bool|true"
  "SBAlwaysRenderSystemApertureFillOnGPU|bool|true"
  "SBNeverRenderSystemApertureFillOnGPU|bool|true"
  "SBShowRegionOfInterest|bool|true"
  "SBEnableSecureDrawViolationAlerts|bool|true"
)
CONTROL_KEY=SBHomeScreenShowsSearchAffordance   # 已知有效：NO 移除主屏搜索胶囊

respring_and_shoot () {   # $1 = label
  xcrun simctl spawn "$U" launchctl kickstart -k system/com.apple.SpringBoard 2>/dev/null
  sleep $SETTLE
  local n=0
  while [ $n -le $RETRIES ]; do
    xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1
    local sz=$(stat -f%z "$OUT/$1.png" 2>/dev/null || echo 0)
    if [ "$sz" -ge $MIN_BYTES ]; then
      printf "  [%-40s] %9s bytes  ok\n" "$1" "$sz"
      return 0
    fi
    printf "  [%-40s] %9s bytes  空屏，等 %ss 重采 (%s/%s)\n" "$1" "$sz" "$RETRY_WAIT" "$n" "$RETRIES"
    sleep $RETRY_WAIT
    n=$((n+1))
  done
  printf "  [%-40s] !! 重采仍空屏，本轮采集无效\n" "$1"
  return 1
}

write_key () {   # $1=key $2=type $3=value  → 写 + 读回断言
  xcrun simctl spawn "$U" defaults write com.apple.springboard "$1" "-$2" "$3" 2>/dev/null
  local got=$(xcrun simctl spawn "$U" defaults read com.apple.springboard "$1" 2>&1 | tr -d '\n')
  local want="$3"; [ "$2" = bool ] && want=$( [ "$3" = true ] && echo 1 || echo 0 )
  case "$got" in
    *"$want"*) printf "    write %-46s = %-6s readback=%-6s ✔\n" "$1" "$3" "$got" ;;
    *)         printf "    write %-46s = %-6s readback=%-6s !! MISMATCH\n" "$1" "$3" "$got" ;;
  esac
}

del_key () { xcrun simctl spawn "$U" defaults delete com.apple.springboard "$1" 2>/dev/null; }

ALL_KEYS=()
for row in $KEYS; do ALL_KEYS+=("${row%%|*}"); done

# 有些 key 是 SpringBoard 自己已经落盘的（实测 SBRingerMuted = 0）。
# 这类**不能删**：删掉会改动基线，测出来的差异归属不到被测值上。
# 处理办法：先读原值，收尾按原值还原（而不是 delete）。
declare -A PREEXISTING
for k in $ALL_KEYS; do
  v=$(xcrun simctl spawn "$U" defaults read com.apple.springboard "$k" 2>/dev/null | tr -d '\n')
  [ -n "$v" ] && PREEXISTING[$k]="$v"
done
if [ ${#PREEXISTING} -gt 0 ]; then
  echo "=== 已存在（将按原值还原，不删除）==="
  for k in ${(k)PREEXISTING}; do printf "    %-46s = %s\n" "$k" "${PREEXISTING[$k]}"; done
fi

echo "=== 清理，取干净基线 ==="
for k in $ALL_KEYS; do
  [ -n "${PREEXISTING[$k]}" ] && continue
  del_key "$k"
done
del_key "$CONTROL_KEY"
respring_and_shoot base || exit 1

echo "=== 逐键扫描 ==="
LABELS=()
for row in $KEYS; do
  k=${row%%|*}; rest=${row#*|}; t=${rest%%|*}; v=${rest#*|}
  echo "--- $k = $v ($t) ---"
  write_key "$k" "$t" "$v"
  respring_and_shoot "t_$k" || exit 1
  LABELS+=("t_$k")
done

echo "=== 内建阳性对照（已知有效） ==="
xcrun simctl spawn "$U" defaults write com.apple.springboard "$CONTROL_KEY" -bool NO
printf "    write %-46s = NO\n" "$CONTROL_KEY"
respring_and_shoot control || exit 1

echo "=== 清理 + 复原校验 ==="
for k in $ALL_KEYS; do
  if [ -n "${PREEXISTING[$k]}" ]; then
    xcrun simctl spawn "$U" defaults write com.apple.springboard "$k" "${PREEXISTING[$k]}" 2>/dev/null
    printf "    还原 %-46s = %s\n" "$k" "${PREEXISTING[$k]}"
  else
    del_key "$k"
  fi
done
del_key "$CONTROL_KEY"
respring_and_shoot final

echo
echo "=== 第 1 关：帧大小一致性（中位数 ±0.05%，离群帧不得用于差分）==="
"$PY" - "$OUT" <<'SZEOF'
import sys, os, statistics
OUT=sys.argv[1]
frames=[f[:-4] for f in sorted(os.listdir(OUT)) if f.endswith('.png') and not f.startswith('cmp_')]
sz={f:os.path.getsize(f'{OUT}/{f}.png') for f in frames}
if sz:
    med=statistics.median(sz.values())
    bad=[(f,s) for f,s in sz.items() if abs(s-med)/med > 0.0005]
    print(f'  帧数={len(sz)}  median={int(med)}  正常带 {int(med*0.9995)}..{int(med*1.0005)}')
    for f,s in bad: print(f'  !! {f}: {s} ({(s-med)/med*100:+.3f}%)  -> 该帧无效')
    if not bad: print('  全部落在正常带内 ✔')
SZEOF

echo
echo "=== 第 2 关：增量差分 + 变化带定位（先量后切）==="
"$PY" - "$OUT" <<'PYEOF'
import sys, os
from PIL import Image
import numpy as np
OUT=sys.argv[1]
def arr(p): return np.asarray(Image.open(p).convert('RGB'),dtype=np.int16)
files=[f[:-4] for f in sorted(os.listdir(OUT)) if f.endswith('.png') and not f.startswith('cmp_')]
order=['base']+[f for f in files if f.startswith('t_')]+['control','final']
avail=[f for f in order if os.path.exists(f'{OUT}/{f}.png')]
A={f:arr(f'{OUT}/{f}.png') for f in avail}
print('=== 增量差分（vs 上一帧）→ 单键归因 ===')
for p,c in zip(avail, avail[1:]):
    d=np.abs(A[p]-A[c]).max(axis=2)
    tot=100*(d>8).mean()
    flag='   <<< 非零，待复现' if tot>0.005 else ''
    print(f'{c:<52} 全屏 {tot:7.4f}%{flag}')
    if tot>0.005:
        rows=(d>8).sum(axis=1); H=d.shape[0]
        top=np.argsort(rows)[-3:][::-1]
        for r in top:
            if rows[r]>0: print(f'      变化带 y={r/H:.3f} 该行变化像素 {rows[r]}')
if 'base' in A and 'final' in A:
    d=np.abs(A['base']-A['final']).max(axis=2)
    tot=100*(d>8).mean()
    print(f'\n清理校验：base vs final {tot:.4f}%  ' + ('=> 完全复原 ✔' if tot<0.005 else '=> !! 有残留'))
PYEOF
echo
echo "完成。输出目录：$OUT"
