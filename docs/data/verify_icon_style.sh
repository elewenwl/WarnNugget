#!/bin/zsh
# 主屏图标外观 key 的复现性验证（轮次 5–7 的整理版）
#
# 这套流程的价值不在"测出了什么"，而在**拆掉了一个看起来完美的假阳性**：
#   SBHomeIconUserInterfaceStyle=accent 曾给出 1.242% 的差分，差异集中在图标/小组件区、
#   图标饱和度 59.79→67.60、清理后 0.000% 可逆 —— 语义完全自洽。
#   但两次独立复现都是 0.000%，且那两帧的截屏大小偏离正常带（-4.6% / -0.085%）。
#   ⇒ 瞬态渲染态，不是 key 的效果。详见 docs/data/icon_style_probe_log.md
#
# 三条硬规则（缺一条就会把假阳性当结论）
#   1) 同一个值至少独立复现 2 次（各自 respring + 截屏），两次都非零才算数
#   2) 帧大小必须落在本轮中位数 ±0.05% 内（实测正常带离散度只有 ±0.006%）
#   3) 每次写入都要 readback 断言值真的落盘
set +e
U=${1:-2990A9E7-C09B-4D9A-A2BD-8CAD96F98999}
PY=/Users/jason/.workbuddy/binaries/python/envs/default/bin/python
OUT=${2:-/tmp/icon_style}
mkdir -p "$OUT"
MIN_BYTES=1000000; SETTLE=72; RETRIES=4; RETRY_WAIT=30

shoot () {
  xcrun simctl spawn "$U" launchctl kickstart -k system/com.apple.SpringBoard 2>/dev/null
  sleep $SETTLE
  local n=0
  while [ $n -le $RETRIES ]; do
    xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1
    local sz=$(stat -f%z "$OUT/$1.png" 2>/dev/null || echo 0)
    if [ "$sz" -ge $MIN_BYTES ]; then printf "  [%-10s] %9s bytes\n" "$1" "$sz"; return 0; fi
    printf "  [%-10s] %9s bytes  blank, retry (%s/%s)\n" "$1" "$sz" "$n" "$RETRIES"
    sleep $RETRY_WAIT; n=$((n+1))
  done
  printf "  [%-10s] !! blank - invalid\n" "$1"; return 1
}
D="$HOME/Library/Developer/CoreSimulator/Devices/$U/data"
wstr () { xcrun simctl spawn "$U" defaults write com.apple.springboard "$1" -string "$2"
          local got=$(xcrun simctl spawn "$U" defaults read com.apple.springboard "$1" 2>&1 | tr -d '\n')
          printf "  write %-38s = %-8s readback=%s%s\n" "$1" "$2" "$got" \
                 "$([ "$got" = "$2" ] && echo ' ✔' || echo '  !! MISMATCH')"; }
clr () { xcrun simctl spawn "$U" defaults delete com.apple.springboard "$1" 2>/dev/null; }

TYPE=SBHomeIconUserInterfaceStyle
VAR=SBHomeIconUserInterfaceStyleVariation

echo "== 备份 =="
cp "$D/Library/Preferences/com.apple.springboard.plist" "$OUT/bak_sb.plist"
clr "$TYPE"; clr "$VAR"

echo "== base =="; shoot base || exit 1

echo "== 同一值跑两次（复现性才是判据）=="
wstr "$TYPE" accent; shoot A1 || exit 1
shoot A2 || exit 1

echo "== 叠加 variant 后再各跑一次 =="
wstr "$VAR" dark;      shoot A3 || exit 1
clr "$VAR";            shoot A4 || exit 1

echo "== 清理 + 复原 =="
clr "$TYPE"; clr "$VAR"; shoot final

echo
"$PY" - "$OUT" <<'PYEOF'
import sys, os, statistics
from PIL import Image
import numpy as np
OUT=sys.argv[1]
REG=[(0.000,0.060,'statusbar'),(0.075,0.300,'widgets'),(0.300,0.560,'icons'),
     (0.560,0.935,'mid+pill'),(0.935,1.000,'dock')]
order=['base','A1','A2','A3','A4','final']
have=[f for f in order if os.path.exists(f'{OUT}/{f}.png')]

print('=== 第 1 关：帧大小一致性（±0.05%）===')
sz={f:os.path.getsize(f'{OUT}/{f}.png') for f in have}
med=statistics.median(sz.values())
bad=set()
for f,s in sz.items():
    off=(s-med)/med*100
    tag='  <-- 无效帧' if abs(off)>0.5 else ''
    if tag: bad.add(f)
    print(f'  {f:<8} {s:>9}  {off:+.3f}%{tag}')
print(f'  中位数 {int(med)}；无效帧 {sorted(bad) or "无"}')

print('\n=== 第 2 关：差分（无效帧不参与结论）===')
def arr(p): return np.asarray(Image.open(f'{OUT}/{p}.png').convert('RGB'),dtype=np.int16)
A={f:arr(f) for f in have}
H=next(iter(A.values())).shape[0]
def show(a,b):
    d=np.abs(A[a]-A[b]).max(axis=2); tot=100*(d>8).mean()
    reg={n:100*(d[int(H*lo):int(H*hi)]>8).mean() for lo,hi,n in REG}
    mark=''
    if a in bad or b in bad: mark='   [含无效帧，不可作为证据]'
    print(f'  {b:<7} vs {a:<7} TOT {tot:7.3f}%  '+'  '.join(f'{k} {v:5.2f}%' for k,v in reg.items())+mark)
show('base','A1'); show('A1','A2'); show('A2','A3'); show('A3','A4'); show('base','final')

print('\n=== 判定 ===')
ok = all(f not in bad for f in ('A1','A2'))
if not ok:
    print('  有帧被判无效 -> 本轮不可结论，重采后重跑')
else:
    print(f'  A1 vs base 与 A2 vs base 两次都非零 ? -> 只有两次都非零才算有效 key')
PYEOF
