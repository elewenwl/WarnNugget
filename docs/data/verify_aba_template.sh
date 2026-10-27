#!/bin/zsh
# A/B/A 验证模板（SpringBoard 偏好 key，iOS 模拟器）
#
# 核心设计
#  1) 尺寸守卫 + 重采：respring 后截屏 < 1MB 视为"未渲染"（空屏），
#     必须重采而不是当作结果 —— 否则会读出完美的 0.000% 假阴性。
#     实测坑：等 70s 仍偶发拿到 77KB 空屏（正常帧 4.5MB）。
#  2) 增量差分：每轮与"上一帧"比 → 单键归因；与基线比 → 累计效应。
#  3) 内建阳性对照：末尾写一个已知有效的 key，必须出现预期变化，
#     否则说明管线或采集坏了，本轮全部结论作废。
#  4) 清理校验：收尾删除所有测试 key 后，应与基线逐像素一致。
#  5) 帧大小一致性：≥1MB 只能拦全空屏，拦不住「画到一半」的帧。
#     实测同一画面的帧大小离散度只有 ±0.006%，所以**任何偏离中位数 >0.05% 的帧判无效**。
#     踩过的坑：一个 4.319MB（-4.6%）的半渲染帧给出 1.242% 的"有效"差分，
#     语义还完全自洽，两次复现却是 0.000% —— 详见 docs/data/icon_style_probe_log.md。
#
# 用法：把 UDID / 键清单按需改掉即可。
set +e
U=${1:-2990A9E7-C09B-4D9A-A2BD-8CAD96F98999}
PY=/Users/jason/.workbuddy/binaries/python/envs/default/bin/python
OUT=${2:-/tmp/sweep}
mkdir -p "$OUT"

MIN_BYTES=1000000          # <1MB 视为未渲染
SETTLE=70                  # 首次等待秒数
RETRIES=4                  # 未渲染时的重试次数
RETRY_WAIT=30

settle_and_shoot () {      # $1 = label
  xcrun simctl spawn "$U" launchctl kickstart -k system/com.apple.SpringBoard 2>/dev/null
  sleep $SETTLE
  local n=0
  while [ $n -le $RETRIES ]; do
    xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1
    local sz=$(stat -f%z "$OUT/$1.png" 2>/dev/null || echo 0)
    if [ "$sz" -ge $MIN_BYTES ]; then
      printf "  [%-12s] %9s bytes  已渲染\n" "$1" "$sz"
      return 0
    fi
    printf "  [%-12s] %9s bytes  空屏，等待 %ss 后重采 (%s/%s)\n" "$1" "$sz" "$RETRY_WAIT" "$n" "$RETRIES"
    sleep $RETRY_WAIT
    n=$((n+1))
  done
  printf "  [%-12s] !! 多次重采仍为空屏 —— 本轮采集无效\n" "$1"
  return 1
}

w   () { xcrun simctl spawn "$U" defaults write com.apple.springboard "$1" -bool "$2"
         printf "  write %-54s = %s\n" "$1" "$2"; }
del () { xcrun simctl spawn "$U" defaults delete com.apple.springboard "$1" 2>/dev/null; }

TEST_KEYS=(SBShowRSSI SBShowRingerState SBDisableLiveIcons)
CONTROL_KEY=SBHomeScreenShowsSearchAffordance   # 已知有效（移除主屏搜索胶囊）

echo "--- 清理，取干净基线 ---"
for k in $TEST_KEYS $CONTROL_KEY; do del "$k"; done
settle_and_shoot base || exit 1

echo "--- 逐键扫描（增量归因依赖前一帧有效，故每帧都要守卫）---"
for k in $TEST_KEYS; do
  w "$k" YES
  settle_and_shoot "t_$k" || exit 1
done

echo "--- 内建阳性对照 ---"
w "$CONTROL_KEY" NO
settle_and_shoot control || exit 1

echo "--- 清理 + 校验复原 ---"
for k in $TEST_KEYS $CONTROL_KEY; do del "$k"; done
settle_and_shoot final

echo "--- 帧大小一致性（偏离中位数 >0.05% 的帧判无效，不要用于差分）---"
"$PY" - "$OUT" <<'SZEOF'
import sys, os, statistics
OUT=sys.argv[1]
frames=[f[:-4] for f in sorted(os.listdir(OUT)) if f.endswith('.png') and not f.startswith('cmp_')]
sz={f:os.path.getsize(f'{OUT}/{f}.png') for f in frames}
if sz:
    med=statistics.median(sz.values())
    bad=[(f,s) for f,s in sz.items() if abs(s-med)/med > 0.005]
    print(f'  median={int(med)}   正常带 ±0.05% = {int(med*0.9995)}..{int(med*1.0005)}')
    for f,s in bad: print(f'  !! {f}: {s} ({(s-med)/med*100:+.3f}%)  -> 该帧无效')
    if not bad: print('  全部落在正常带内 ✔')
SZEOF

echo
"$PY" - "$OUT" <<'PYEOF'
import sys, os
from PIL import Image
import numpy as np
OUT=sys.argv[1]
REG=[(0.000,0.060,'状态栏'),(0.060,0.330,'图标区'),(0.330,0.930,'主屏中'),(0.930,1.000,'Dock')]
def arr(p): return np.asarray(Image.open(p).convert('RGB'),dtype=np.int16)
def st(d):
    H=d.shape[0]
    return 100*(d>8).mean(), {n:100*(d[int(H*lo):int(H*hi)]>8).mean() for lo,hi,n in REG}
files=['base']+[f't_{k}' for k in ('SBShowRSSI','SBShowRingerState','SBDisableLiveIcons')]+['control','final']
avail=[f for f in files if os.path.exists(f'{OUT}/{f}.png')]
A={f:arr(f'{OUT}/{f}.png') for f in avail}
print('=== 增量差分（vs 上一帧）→ 单键归因 ===')
for p,c in zip(avail, avail[1:]):
    d=np.abs(A[p]-A[c]).max(axis=2); tot,reg=st(d)
    print(f'{c:<34} 全屏 {tot:6.3f}%  '+'  '.join(f'{k} {v:5.3f}%' for k,v in reg.items())
          + ('   <<< 有效!' if tot>0.02 else ''))
if 'base' in A and 'final' in A:
    tot,_=st(np.abs(A['base']-A['final']).max(axis=2))
    print(f'\n清理校验：基线 vs 清理后 {tot:.3f}%  ' + ('=> 完全复原 ✔' if tot<0.005 else '=> !! 有残留'))
PYEOF
