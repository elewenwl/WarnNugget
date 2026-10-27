#!/bin/zsh
# 轮次 4：Managed Preferences 投递通道 + 剩余主屏静态候选
#
# 目的
#  A) 全局域（.GlobalPreferences）通道是否被 SpringBoard 采纳
#     —— 这是 Nugget 的 GP/ManagedPreferences 全局通道能否对 SB* key 生效的前提
#  B) 剩余「主屏静态可见」候选的 A/B 扫描
#
# 用真实的已知有效 key 做通道探针（不用假 key）——上一轮的 f1Mshr 探针是无效实验。
set +e
U=2990A9E7-C09B-4D9A-A2BD-8CAD96F98999
PY=/Users/jason/.workbuddy/binaries/python/envs/default/bin/python
OUT=/tmp/sweep4
mkdir -p "$OUT"

MIN_BYTES=1000000
SETTLE=72
RETRIES=4
RETRY_WAIT=30

CTRL=SBHomeScreenShowsSearchAffordance

shoot () {  # $1 = label
  xcrun simctl spawn "$U" launchctl kickstart -k system/com.apple.SpringBoard 2>/dev/null
  sleep $SETTLE
  local n=0
  while [ $n -le $RETRIES ]; do
    xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1
    local sz=$(stat -f%z "$OUT/$1.png" 2>/dev/null || echo 0)
    if [ "$sz" -ge $MIN_BYTES ]; then
      printf "  [%-14s] %9s bytes  rendered\n" "$1" "$sz"; return 0
    fi
    printf "  [%-14s] %9s bytes  blank, retry in %ss (%s/%s)\n" "$1" "$sz" "$RETRY_WAIT" "$n" "$RETRIES"
    sleep $RETRY_WAIT; n=$((n+1))
  done
  printf "  [%-14s] !! still blank - frame invalid\n" "$1"; return 1
}

wa () { xcrun simctl spawn "$U" defaults write com.apple.springboard "$1" -bool "$2"
        printf "  app-domain   %-46s = %s\n" "$1" "$2"; }
da () { xcrun simctl spawn "$U" defaults delete com.apple.springboard "$1" 2>/dev/null; }
wg () { xcrun simctl spawn "$U" defaults write .GlobalPreferences "$1" -bool "$2"
        printf "  GLOBAL-domain %-45s = %s\n" "$1" "$2"
        xcrun simctl spawn "$U" defaults read .GlobalPreferences "$1"; }
dg () { xcrun simctl spawn "$U" defaults delete .GlobalPreferences "$1" 2>/dev/null; }

APPKEYS=(SBWidgetSnapshotDebugLabels SBShouldShowWidgetIntroductionPage SBHomeShouldShowLibraryEducationView)

echo "== 0. 备份两个域 =="
D="$HOME/Library/Developer/CoreSimulator/Devices/$U/data"
cp "$D/Library/Preferences/com.apple.springboard.plist" "$OUT/bak_sb.plist"
cp "$D/Library/Preferences/.GlobalPreferences.plist"   "$OUT/bak_global.plist"

echo "== 1. 清空 app 域控制键 + 全局域探针键；取干净基线 =="
da "$CTRL"; dg "$CTRL"
for k in $APPKEYS; do da "$k"; done
shoot base || exit 1

echo "== 2. 通道探针：把已知有效的控制键写进全局域（app 域保持干净）=="
wg "$CTRL" NO
shoot g_write || exit 1

echo "== 3. 撤掉全局域探针键 =="
dg "$CTRL"
shoot g_clean || exit 1

echo "== 4. app 域逐键扫描（增量归因）=="
for k in $APPKEYS; do
  wa "$k" YES
  shoot "t_$k" || exit 1
done

echo "== 5. 清理全部测试键 + 复原校验 =="
for k in $APPKEYS; do da "$k"; done
dg "$CTRL"; da "$CTRL"
shoot final

echo
"$PY" - "$OUT" "$APPKEYS" <<'PYEOF'
import sys, os
from PIL import Image
import numpy as np
OUT=sys.argv[1]; APPKEYS=sys.argv[2].split()
REG=[(0.000,0.060,'statusbar'),(0.060,0.090,'top'),
     (0.090,0.300,'widgets'),(0.300,0.560,'icons'),
     (0.560,0.700,'search-area'),(0.700,0.930,'page-dots'),
     (0.930,1.000,'dock')]
def arr(p): return np.asarray(Image.open(p).convert('RGB'),dtype=np.int16)
def st(d):
    H=d.shape[0]
    return 100*(d>8).mean(), {n:100*(d[int(H*lo):int(H*hi)]>8).mean() for lo,hi,n in REG}
order=['base','g_write','g_clean']+[f't_{k}' for k in APPKEYS]+['final']
avail=[f for f in order if os.path.exists(f'{OUT}/{f}.png')]
A={f:arr(f'{OUT}/{f}.png') for f in avail}
print('=== vs 基线 ===')
for f in avail[1:]:
    d=np.abs(A['base']-A[f]).max(axis=2); tot,reg=st(d)
    print(f'{f:<26} TOT {tot:6.3f}%  '+'  '.join(f'{k} {v:5.3f}%' for k,v in reg.items()))
print()
print('=== 增量（vs 上一帧）→ 单键归因 ===')
for p,c in zip(avail, avail[1:]):
    d=np.abs(A[p]-A[c]).max(axis=2); tot,reg=st(d)
    flag='   <<< SIGNAL' if tot>0.02 else ''
    print(f'{c:<26} TOT {tot:6.3f}%  '+'  '.join(f'{k} {v:5.3f}%' for k,v in reg.items())+flag)
print()
if 'base' in A and 'final' in A:
    tot,_=st(np.abs(A['base']-A['final']).max(axis=2))
    print(f'cleanup check: base vs final = {tot:.3f}%  '+('=> fully restored OK' if tot<0.005 else '=> !! RESIDUE'))
PYEOF
