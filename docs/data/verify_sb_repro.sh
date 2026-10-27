#!/bin/zsh
# 复现校验：对某个已出现非零差分的 key 做 N 轮**独立** A/B
#
# 为什么必须单独跑：第 5 轮 `SBHomeIconUserInterfaceStyle=accent` 给出 1.242%，
# 差异区域、饱和度变化、可逆性**每一个侧面都自洽**，但两次独立复现都是 0.000%。
# 定案靠帧大小（离群帧 4,319,125 / -4.6%）。
# ⇒ 规则：非零结果只有在**独立复现 ≥2 次且帧大小合规**时才可采信。
#
# 设计：不以"上一帧"为对照，而是每轮都从**无 key 状态**出发：
#   roundk_base（无 key）→ 写 key → roundk_val（有 key）
# 这样每轮都是一个完整 A/B，互不复用状态。
#
# 用法：zsh docs/data/verify_sb_repro.sh <key> <type> <value> [rounds] [udid] [outdir]
set +e
K=${1:?用法: verify_sb_repro.sh <key> <type> <value> [rounds] [udid] [outdir]}
T=${2:-bool}
V=${3:-true}
N=${4:-3}
U=${5:-2990A9E7-C09B-4D9A-A2BD-8CAD96F98999}
PY=/Users/jason/.workbuddy/binaries/python/envs/default/bin/python
OUT=${6:-/tmp/repro_$K}
mkdir -p "$OUT"
MIN_BYTES=1000000; SETTLE=60; RETRIES=4; RETRY_WAIT=25

shoot () {   # $1=label
  xcrun simctl spawn "$U" launchctl kickstart -k system/com.apple.SpringBoard 2>/dev/null
  sleep $SETTLE
  local i=0
  while [ $i -le $RETRIES ]; do
    xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1
    local sz=$(stat -f%z "$OUT/$1.png" 2>/dev/null || echo 0)
    [ "$sz" -ge $MIN_BYTES ] && { printf "  [%-16s] %9s\n" "$1" "$sz"; return 0; }
    sleep $RETRY_WAIT; i=$((i+1))
  done
  printf "  [%-16s] !! 空屏\n" "$1"; return 1
}

del () { xcrun simctl spawn "$U" defaults delete com.apple.springboard "$1" 2>/dev/null; }

# 该 key 原本就存在时，先记原值，最后还原
ORIG=$(xcrun simctl spawn "$U" defaults read com.apple.springboard "$K" 2>/dev/null | tr -d '\n')
echo "待验 $K = $V ($T)   原值=${ORIG:-<不存在>}   轮数=$N"

for r in $(seq 1 $N); do
  echo "--- 第 $r 轮 ---"
  [ -n "$ORIG" ] && xcrun simctl spawn "$U" defaults write com.apple.springboard "$K" "$ORIG" 2>/dev/null || del "$K"
  shoot "r${r}_base" || exit 1
  xcrun simctl spawn "$U" defaults write com.apple.springboard "$K" "-$T" "$V" 2>/dev/null
  got=$(xcrun simctl spawn "$U" defaults read com.apple.springboard "$K" 2>&1 | tr -d '\n')
  printf "     readback=%s\n" "$got"
  shoot "r${r}_val" || exit 1
done

# 还原
if [ -n "$ORIG" ]; then
  xcrun simctl spawn "$U" defaults write com.apple.springboard "$K" "$ORIG" 2>/dev/null
else
  del "$K"
fi
shoot restored

echo
echo "=== 帧大小一致性（中位数 ±0.05%）==="
"$PY" - "$OUT" <<'SZEOF'
import sys, os, statistics
OUT=sys.argv[1]
f=[x[:-4] for x in sorted(os.listdir(OUT)) if x.endswith('.png')]
sz={x:os.path.getsize(f'{OUT}/{x}.png') for x in f}
med=statistics.median(sz.values())
bad=[(x,s) for x,s in sz.items() if abs(s-med)/med > 0.0005]
print(f'  n={len(sz)} median={int(med)} 正常带 {int(med*0.9995)}..{int(med*1.0005)}')
for x,s in bad: print(f'  !! {x}: {s} ({(s-med)/med*100:+.3f}%) -> 无效帧')
if not bad: print('  全部合规 ✔')
SZEOF

echo
echo "=== 每轮 A/B 差分 ==="
"$PY" - "$OUT" <<'PYEOF'
import sys, os, re
from PIL import Image
import numpy as np
OUT=sys.argv[1]
def arr(p): return np.asarray(Image.open(p).convert('RGB'),dtype=np.int16)
rounds=sorted({int(m.group(1)) for x in os.listdir(OUT) if (m:=re.match(r'r(\d+)_base\.png$',x))})
vals=[]
for r in rounds:
    a,b=f'{OUT}/r{r}_base.png', f'{OUT}/r{r}_val.png'
    if not (os.path.exists(a) and os.path.exists(b)): continue
    d=np.abs(arr(a)-arr(b)).max(axis=2)
    tot=100*(d>8).mean(); vals.append(tot)
    line=f'  round {r}: 全屏 {tot:7.4f}%'
    if tot>0.005:
        H=d.shape[0]; rows=(d>8).sum(axis=1)
        top=int(np.argmax(rows))
        line+=f'   峰值行 y={top/H:.3f} ({rows[top]} px)'
    print(line)
if vals:
    nz=[v for v in vals if v>0.005]
    print(f'\n  {len(nz)}/{len(vals)} 轮非零', end='')
    if len(nz)>=2 and len(nz)==len(vals):
        print('  => 可复现，命中 ✔')
    elif nz:
        print('  => !!! 不可复现（不足 2 轮或非全轮），判噪声')
    else:
        print('  => 无效（全部 0.000%）')
PYEOF
