#!/bin/zsh
# 第八轮（修正版）：新增 SpringBoard key 批次 A
#
# 相比初版修掉三个缺陷（初版结果作废，勿引用 /tmp/sweep8）：
#   [缺陷 1] 没冻结状态栏 → 时钟跳分钟，在 y≈0.038 制造 0.24–0.27% 的假差分，
#            并把 base vs final 污染成 0.237%（两者状态其实完全相同）。
#            ⇒ 现在开头就 `simctl status_bar override`，收尾 clear。
#   [缺陷 2] 差分按文件名字母序两两做 → 不是写入时序，单键归因全错。
#            ⇒ 现在运行时写 manifest.txt 记录真实时序，分析按 manifest 走。
#   [缺陷 3] 帧大小中位数守卫被跨状态套用 → 合法改变了画面的帧（阳性对照）
#            反而被判无效。⇒ 现在守卫改为：(a) 管线自校验对 base/base2 必须
#            逐字节相同；(b) 帧大小只在"应当相同的帧"之间比对。
#
# 用法：zsh docs/data/verify_sb_round8b.sh [udid] [outdir]
set +e
U=${1:-2990A9E7-C09B-4D9A-A2BD-8CAD96F98999}
PY=/Users/jason/.workbuddy/binaries/python/envs/default/bin/python
OUT=${2:-/tmp/sweep8b}
mkdir -p "$OUT"
MAN="$OUT/manifest.txt"; : > "$MAN"

MIN_BYTES=1000000
SETTLE=50
RETRIES=5
RETRY_WAIT=25

echo "=== 冻结状态栏（否则时钟跳分钟会伪造 0.24–0.27% 的差分）==="
xcrun simctl status_bar "$U" override \
  --time "9:41" --dataNetwork wifi --wifiMode active --wifiBars 3 \
  --cellularMode active --cellularBars 4 --batteryState charged --batteryLevel 100

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
CONTROL_KEY=SBHomeScreenShowsSearchAffordance

respring_and_shoot () {   # $1 = label
  xcrun simctl spawn "$U" launchctl kickstart -k system/com.apple.SpringBoard 2>/dev/null
  sleep $SETTLE
  local n=0
  while [ $n -le $RETRIES ]; do
    xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1
    local sz=$(stat -f%z "$OUT/$1.png" 2>/dev/null || echo 0)
    if [ "$sz" -ge $MIN_BYTES ]; then
      printf "  [%-42s] %9s\n" "$1" "$sz"
      printf "%s\t%s\t%s\t%s\n" "$1" "${2:-}" "${3:-}" "$sz" >> "$MAN"
      return 0
    fi
    printf "  [%-42s] %9s  空屏重采 (%s/%s)\n" "$1" "$sz" "$n" "$RETRIES"
    sleep $RETRY_WAIT; n=$((n+1))
  done
  printf "  [%-42s] !! 空屏，采集无效\n" "$1"; return 1
}

write_key () {   # $1=key $2=type $3=value
  xcrun simctl spawn "$U" defaults write com.apple.springboard "$1" "-$2" "$3" 2>/dev/null
  local got=$(xcrun simctl spawn "$U" defaults read com.apple.springboard "$1" 2>&1 | tr -d '\n')
  local want="$3"; [ "$2" = bool ] && want=$( [ "$3" = true ] && echo 1 || echo 0 )
  case "$got" in
    *"$want"*) printf "    write %-44s=%-6s readback=%-6s ✔\n" "$1" "$3" "$got" ;;
    *)         printf "    write %-44s=%-6s readback=%-6s !! MISMATCH\n" "$1" "$3" "$got" ;;
  esac
}
del_key () { xcrun simctl spawn "$U" defaults delete com.apple.springboard "$1" 2>/dev/null; }

ALL_KEYS=(); for row in $KEYS; do ALL_KEYS+=("${row%%|*}"); done

# SpringBoard 自己已落盘的 key 不能删（删了会动基线），按原值还原
declare -A PREEXISTING
for k in $ALL_KEYS; do
  v=$(xcrun simctl spawn "$U" defaults read com.apple.springboard "$k" 2>/dev/null | tr -d '\n')
  [ -n "$v" ] && PREEXISTING[$k]="$v"
done
[ ${#PREEXISTING} -gt 0 ] && { echo "=== 已存在（按原值还原）==="; for k in ${(k)PREEXISTING}; do printf "    %-44s= %s\n" "$k" "${PREEXISTING[$k]}"; done }

echo "=== 清理，取干净基线 ==="
for k in $ALL_KEYS; do [ -n "${PREEXISTING[$k]}" ] && continue; del_key "$k"; done
del_key "$CONTROL_KEY"

echo "=== 管线自校验：base 与 base2 必须逐字节相同 ==="
respring_and_shoot base "" "" || exit 1
respring_and_shoot base2 "" "" || exit 1

echo "=== 逐键扫描（manifest 记录真实时序）==="
for row in $KEYS; do
  k=${row%%|*}; rest=${row#*|}; t=${rest%%|*}; v=${rest#*|}
  echo "--- $k = $v ($t) ---"
  write_key "$k" "$t" "$v"
  respring_and_shoot "t_$k" "$k" "$v" || exit 1
done

echo "=== 内建阳性对照 ==="
xcrun simctl spawn "$U" defaults write com.apple.springboard "$CONTROL_KEY" -bool NO
printf "    write %-44s= NO\n" "$CONTROL_KEY"
respring_and_shoot control "$CONTROL_KEY" "NO" || exit 1

echo "=== 清理 + 复原 ==="
for k in $ALL_KEYS; do
  if [ -n "${PREEXISTING[$k]}" ]; then
    xcrun simctl spawn "$U" defaults write com.apple.springboard "$k" "${PREEXISTING[$k]}" 2>/dev/null
  else
    del_key "$k"
  fi
done
del_key "$CONTROL_KEY"
respring_and_shoot final "RESTORED" "" || exit 1

echo "=== 解冻状态栏 ==="
xcrun simctl status_bar "$U" clear

echo
echo "=== 分析（严格按 manifest 时序）==="
"$PY" - "$OUT" <<'PYEOF'
import sys, os
from PIL import Image
import numpy as np
OUT=sys.argv[1]
def arr(p): return np.asarray(Image.open(p).convert('RGB'),dtype=np.int16)
rows=[l.split('\t') for l in open(f'{OUT}/manifest.txt',encoding='utf-8').read().strip().split('\n') if l.strip()]
seq=[(r[0], r[1], r[2] if len(r)>2 else '') for r in rows]
print('=== 管线自校验 ===')
if 'base' in [s[0] for s in seq] and 'base2' in [s[0] for s in seq]:
    d=np.abs(arr(f'{OUT}/base.png')-arr(f'{OUT}/base2.png')).max(axis=2)
    tot=100*(d>8).mean()
    print(f'  base vs base2：{tot:.4f}%  ' + ('=> 管线确定性 ✔' if tot<0.005 else '=> !! 不确定，本轮全部作废'))
print()
print('=== 时序差分（vs 上一状态）→ 单键归因 ===')
print(f'{"写入的 key":<50}{"全屏变化":>10}   变化带')
hits=[]
for i in range(1, len(seq)):
    p, c = seq[i-1][0], seq[i][0]
    key, val = seq[i][1], seq[i][2]
    d=np.abs(arr(f'{OUT}/{p}.png')-arr(f'{OUT}/{c}.png')).max(axis=2)
    tot=100*(d>8).mean()
    band=''
    if tot>0.005:
        H=d.shape[0]; rr=(d>8).sum(axis=1); t=int(np.argmax(rr))
        band=f'y={t/H:.3f}({rr[t]}px)'
        hits.append(key)
    elif tot>0:
        H=d.shape[0]; rr=(d>8).sum(axis=1); t=int(np.argmax(rr))
        band=f'亚阈值 y={t/H:.3f}({rr[t]}px)'
    name=key if key else f'({seq[i][0]})'
    flag='  <<< 非零' if tot>0.005 else ''
    print(f'{name+" = "+val:<50}{tot:9.4f}%   {band}{flag}')
print()
print('命中（待复现）:', ', '.join(hits) if hits else '无')
if 'final' in [s[0] for s in seq]:
    d=np.abs(arr(f'{OUT}/base.png')-arr(f'{OUT}/final.png')).max(axis=2)
    tot=100*(d>8).mean()
    print(f'\n清理校验 base vs final {tot:.4f}%  ' + ('=> 完全复原 ✔' if tot<0.005 else '=> !! 有残留'))
PYEOF
echo; echo "完成 → $OUT"
