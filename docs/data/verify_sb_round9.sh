#!/bin/zsh
# 第九轮：SpringBoard key 扫描 —— 「同 key 双值互比」法
#
# 为什么换方法（第八轮的教训）：
#   第八轮对 12 个 key 一律写 `true`，但**不知道默认值**。
#   若某 key 默认已是 true，则「写入 true」= 什么都没变 ⇒ 0.000% 是**假阴性**，
#   它只证明「写一个已经成立的值没变化」，不证明 key 惰性。
#   新方法：同一个 key 先后写两个不同的值，直接互比。
#   两个值里至少有一个偏离默认（除非默认是第三种状态）⇒ 差值非零即可判 key 有效。
#   这样**不需要知道默认值**，也绕开了"默认不可测"的死结。
#
# 同时落实第八轮挖出的状态栏伪影对策：
#   本机状态栏整条（左时钟+右信号/WiFi/电池）会随机**整条消失**，
#   造成帧间 0.99%~1.01% 的差 —— 与"写不同 override 条件"的 1.00% 无法区分。
#   ⇒ 分析阶段必须把 y < 0.075*H 整条屏蔽（本脚本只采帧，屏蔽在分析脚本里做）。
#
# 范围限制（写死在注释里，避免下次重复踩）：
#   本设备 = iPhone 18 Pro Max (1320x2868) ⇒ 以下候选**天然空测**，本轮不选：
#     Chamois / Stage Manager / Medusa(多任务) / Split&SlideOver Peek / Sidebar /
#     MenuBar / ExternalDisplay / DisableHomeButton(无 home 键)
set +e
U=${1:-2990A9E7-C09B-4D9A-A2BD-8CAD96F98999}
OUT=${2:-/tmp/sweep9}
PY=/Users/jason/.workbuddy/binaries/python/envs/default/bin/python
mkdir -p "$OUT"; rm -f "$OUT"/*.png "$OUT"/manifest.txt "$OUT"/run.log
SETTLE=50; MIN_BYTES=1500000

echo "=== 固定状态栏 override（消除时钟跳分钟）==="
xcrun simctl status_bar "$U" override --time "9:41" --dataNetwork wifi --wifiMode active \
  --wifiBars 3 --cellularMode active --cellularBars 4 --batteryState charged --batteryLevel 100

shoot () {   # $1 = label
  xcrun simctl spawn "$U" launchctl kickstart -k system/com.apple.SpringBoard 2>/dev/null
  sleep $SETTLE
  xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1
  local sz=$(stat -f%z "$OUT/$1.png" 2>/dev/null || echo 0)
  for i in 1 2; do
    [ "$sz" -ge $MIN_BYTES ] && break
    sleep 20
    xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1
    sz=$(stat -f%z "$OUT/$1.png" 2>/dev/null || echo 0)
  done
  printf "  [%-30s] %9s\n" "$1" "$sz"
  printf '%s\t%s\n' "$1" "$sz" >> "$OUT/sizes.tsv"
}

# ---- 参数：TYPE  key  VALUE_A  VALUE_B  [COMPANION=VAL] ----
# TYPE: bool -> -bool ; int -> -int ; float -> -float
scan () {    # $1=TYPE $2=key $3=A $4=B $5=companion(可空) $6=compval
  local T=$1 K=$2 A=$3 B=$4 CK=$5 CV=$6
  wkey () { xcrun simctl spawn "$U" defaults write com.apple.springboard "$K" "-$T" "$1"; \
            [ -n "$CK" ] && xcrun simctl spawn "$U" defaults write com.apple.springboard "$CK" "-$T" "$CV"; }
  # 先清 companion 到非阻塞态（否则 onboarding 类 key 会被"已展示过"标志挡掉）
  wkey "$A"; sleep 1
  shoot "${K}__A"; printf '%s\t%s\t%s\t%s\n' "${K}__A" "$K" "$T" "$A" >> "$OUT/manifest.tsv"
  wkey "$B"; sleep 1
  shoot "${K}__B"; printf '%s\t%s\t%s\t%s\n' "${K}__B" "$K" "$T" "$B" >> "$OUT/manifest.tsv"
  xcrun simctl spawn "$U" defaults delete com.apple.springboard "$K" 2>/dev/null
  [ -n "$CK" ] && xcrun simctl spawn "$U" defaults delete com.apple.springboard "$CK" 2>/dev/null
}

echo "=== 干净基线 ×2（管线确定性自校验）==="
for k in SBShowInternalApps SBWallpaperZoomScaleHomeScreen SBWallpaperParallaxFactorHomeScreen \
         SBHomeScreenScreenTypeOverride SBDisableIdleSleep SBShouldShowPageHidingOnBoardingAlert \
         SBShouldShowAppLibraryOnBoardingAlert SBHomeScreenPageHidingUIHasEverBeenShown \
         SBHomeScreenShowsSearchAffordance; do
  xcrun simctl spawn "$U" defaults delete com.apple.springboard "$k" 2>/dev/null
done
shoot base  ; printf 'base\t\t\t\n'  >> "$OUT/manifest.tsv"
shoot base2 ; printf 'base2\t\t\t\n' >> "$OUT/manifest.tsv"

echo "=== 1. SBShowInternalApps ==="
scan bool SBShowInternalApps true false
echo "=== 2. SBWallpaperZoomScaleHomeScreen ==="
scan float SBWallpaperZoomScaleHomeScreen 2.0 0.5
echo "=== 3. SBWallpaperParallaxFactorHomeScreen ==="
scan float SBWallpaperParallaxFactorHomeScreen 0.0 1.0
echo "=== 4. SBHomeScreenScreenTypeOverride ==="
scan int SBHomeScreenScreenTypeOverride 0 2
echo "=== 5. SBDisableIdleSleep ==="
scan bool SBDisableIdleSleep true false
echo "=== 6. SBShouldShowPageHidingOnBoardingAlert（companion 压到 false）==="
scan bool SBShouldShowPageHidingOnBoardingAlert true false SBHomeScreenPageHidingUIHasEverBeenShown false
echo "=== 7. SBShouldShowAppLibraryOnBoardingAlert ==="
scan bool SBShouldShowAppLibraryOnBoardingAlert true false

echo "=== 阳性对照：SBHomeScreenShowsSearchAffordance（已知有效）==="
scan bool SBHomeScreenShowsSearchAffordance false true

echo "=== 清理 + 复原校验 ==="
for k in SBShowInternalApps SBWallpaperZoomScaleHomeScreen SBWallpaperParallaxFactorHomeScreen \
         SBHomeScreenScreenTypeOverride SBDisableIdleSleep SBShouldShowPageHidingOnBoardingAlert \
         SBShouldShowAppLibraryOnBoardingAlert SBHomeScreenPageHidingUIHasEverBeenShown \
         SBHomeScreenShowsSearchAffordance; do
  xcrun simctl spawn "$U" defaults delete com.apple.springboard "$k" 2>/dev/null
done
shoot final ; printf 'final\t\t\t\n' >> "$OUT/manifest.tsv"

echo "=== 解冻状态栏 ==="
xcrun simctl status_bar "$U" clear

echo
echo "=== 分析（同 key 双值互比；状态栏带 y<0.075*H 整条屏蔽）==="
"$PY" - "$OUT" <<'PYEOF'
import sys, os
from PIL import Image
import numpy as np
OUT=sys.argv[1]
H,W=2868,1320; SB_END=int(H*0.075)
cache={}
def arr(n):
    if n not in cache: cache[n]=np.asarray(Image.open(f'{OUT}/{n}.png').convert('RGB'),dtype=np.int16)
    return cache[n]
def sbstate(a): return int((a[int(H*0.02):int(H*0.06),:].min(axis=2)>200).sum())
def mean(a): return float(a.mean())

man=[l.split('\t') for l in open(f'{OUT}/manifest.tsv',encoding='utf-8').read().strip().split('\n') if l.strip()]
print(f"{'帧':<46}{'字节':>10}{'状态栏':>7}{'均值':>8}")
for r in man:
    n=r[0]
    if not os.path.exists(f'{OUT}/{n}.png'): continue
    a=arr(n); print(f"{n:<46}{os.path.getsize(f'{OUT}/{n}.png'):>10}{sbstate(a):>7}{mean(a):>8.1f}")
print()

def diff(a,b,label):
    A,B=arr(a),arr(b)
    d=np.abs(A-B).max(axis=2)
    tot=100*(d>8).mean()
    dm=d.copy(); dm[:SB_END]=0
    tot2=100*(dm>8).mean()
    ex=""
    if (dm>8).sum():
        rows=(dm>8).sum(axis=1); cols=(dm>8).sum(axis=0)
        tr=np.argsort(rows)[-2:][::-1]; tc=np.argsort(cols)[-2:][::-1]
        ex="  行 "+", ".join(f"y={x/H:.3f}({rows[x]})" for x in tr if rows[x])+" 列 "+", ".join(f"x={x/W:.3f}({cols[x]})" for x in tc if cols[x])
    print(f"{label:<46}{tot:>8.3f}%{tot2:>9.3f}%{ex}")
    return tot2

print("=== 管线自校验（同值应 0）===")
d_self=diff('base','base2','base vs base2')
print()
print("=== 同 key 双值互比（屏蔽状态栏后）===")
keys=[]
for r in man:
    if r[1] and r[1] not in keys: keys.append(r[1])
res={}
for k in keys:
    a,b=f"{k}__A",f"{k}__B"
    if not (os.path.exists(f'{OUT}/{a}.png') and os.path.exists(f'{OUT}/{b}.png')): continue
    d=diff(a,b,f"{k}  A-vs-B")
    res[k]=d
print()
print("=== 复原校验 ===")
diff('base','final','base vs final')
print()
hits=[k for k,v in res.items() if v>0.02]
print("双值有差（key 活着）:", hits if hits else "无")
print("阳性对照 SBHomeScreenShowsSearchAffordance:", res.get('SBHomeScreenShowsSearchAffordance'))
PYEOF
echo; echo "完成 → $OUT"
