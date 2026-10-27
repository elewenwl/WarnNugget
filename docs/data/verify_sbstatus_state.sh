#!/bin/zsh
# 定性：状态栏右侧整簇图标（信号/WiFi/电池）为何会整簇出现/消失
#
# 观察到（第八轮修正版 /tmp/sweep8b）：
#   base/base2            白像素 0      （无图标）
#   SBRingerMuted..ShowThermalWarning  2320（有图标，且外形 = override 的 4格/3格/充电）
#   ShowInternalWidgets.. 白像素 0
#   ...
# 且闪烁点与所写 key 无语义关系 ⇒ 判为环境行为，必须与 key 效果分离。
#
# 本脚本控制"override 状态 × respring 次数"两个变量，各采两帧看是否稳定。
set +e
U=${1:-2990A9E7-C09B-4D9A-A2BD-8CAD96F98999}
PY=/Users/jason/.workbuddy/binaries/python/envs/default/bin/python
OUT=${2:-/tmp/sbstate}
mkdir -p "$OUT"
MIN_BYTES=1000000; SETTLE=50

shoot () {
  xcrun simctl spawn "$U" launchctl kickstart -k system/com.apple.SpringBoard 2>/dev/null
  sleep $SETTLE
  xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1
  local sz=$(stat -f%z "$OUT/$1.png" 2>/dev/null || echo 0)
  [ "$sz" -ge $MIN_BYTES ] || { sleep 25; xcrun simctl io "$U" screenshot "$OUT/$1.png" >/dev/null 2>&1; }
  printf "  [%-22s] %9s\n" "$1" "$(stat -f%z "$OUT/$1.png")"
}

echo "=== 条件 A：clear（真实状态栏），连采两帧 ==="
xcrun simctl status_bar "$U" clear
shoot A1; shoot A2

echo "=== 条件 B：override（9:41 / 4格 / WiFi3 / 充电100%），连采三帧 ==="
xcrun simctl status_bar "$U" override --time "9:41" --dataNetwork wifi --wifiMode active \
  --wifiBars 3 --cellularMode active --cellularBars 4 --batteryState charged --batteryLevel 100
shoot B1; shoot B2; shoot B3

echo "=== 条件 C：再 clear，采一帧（确认可逆）==="
xcrun simctl status_bar "$U" clear
shoot C1

echo
"$PY" - "$OUT" <<'PYEOF'
import sys, os
from PIL import Image
import numpy as np
OUT=sys.argv[1]
H=2868; y0,y1=int(H*0.025),int(H*0.055)
print(f"{'帧':<10}{'字节':>10}{'状态栏右白像素':>16}{'全屏近白像素':>14}")
arrs={}
for n in ['A1','A2','B1','B2','B3','C1']:
    p=f'{OUT}/{n}.png'
    if not os.path.exists(p): continue
    a=np.asarray(Image.open(p).convert('RGB'),dtype=np.int16)
    arrs[n]=a
    right=a[y0:y1, int(1320*0.60):]
    w=(right.min(axis=2)>200).sum()
    wall=(a.min(axis=2)>200).sum()
    print(f"{n:<10}{os.path.getsize(p):>10}{w:>16}{wall:>14}")
print()
def cmp(a,b):
    if a in arrs and b in arrs:
        d=np.abs(arrs[a]-arrs[b]).max(axis=2)
        tot=100*(d>8).mean()
        Hh=d.shape[0]; rr=(d>8).sum(axis=1); t=int(np.argmax(rr)) if rr.max()>0 else 0
        print(f"  {a} vs {b}: {tot:7.4f}%   峰值行 y={t/Hh:.3f}({rr[t]}px)")
print('=== 同条件内一致性 ==='); cmp('A1','A2'); cmp('B1','B2'); cmp('B2','B3')
print('=== 条件间 ==='); cmp('A2','B1'); cmp('B3','C1')
PYEOF
echo; echo "完成 → $OUT"
