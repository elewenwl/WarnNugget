# SpringBoard Tweak 活体验证实测记录

环境：iPhone 18 Pro Max 模拟器 `2990A9E7-C09B-4D9A-A2BD-8CAD96F98999`，iOS 27.0（24A5380i），Light 外观。
差分判据：`|Δ| > 8` 的像素占比。区域划分见文末。

---

## 轮次 1 · 手工 A/B/A（键表严格配对 + 值已落盘）

| Key | 写入值 | 读回 | 结果 |
|---|---|---|---|
| `SBHomeScreenShowsSearchAffordance` | NO | ✅ | **搜索区 0.428%**；反向恢复后与基线 **0.000%** |
| `SBShowBatteryPercentage` | YES | 1 | 0.000% |
| `SBMaxIconListCount` | 5 | 5 | 0.000% |
| `SBHomeHideLabels` | YES | 1 | 0.000% |
| `SBRecentsEnabled` | YES | 1 | Dock 区 0.000% |
| `SBAppLibraryInDockEnabled` | YES | 1 | Dock 区 0.000% |

阳性对照：`simctl ui appearance` dark↔light = **99.07%**（差分管线可信）。

## 轮次 2 · 增量式批量扫描（含内建阳性对照）

设计：每键单独 respring，与**上一帧**差分实现单键归因。

| Key | 写入值 | 增量变化 |
|---|---|---|
| `SBShowRingerState` | YES | 0.000% |
| `SBShowBatteryLevel` | NO | 0.000% |
| `SBDisableLiveIcons` | YES | 0.000% |
| `SBShouldInsertDownloadFileStackIconToFloatingDock` | YES | 0.000% |
| `SBShowRSSI` | YES | 0.000%（差分传递推得） |
| **对照 `SBHomeScreenShowsSearchAffordance`** | NO | **0.158%**（主屏中 0.264%） |
| 对照反向回落 | — | **0.158%（完全对称）** |

基线帧采集失败（77066 字节 = 空屏），故「vs 基线」列全部无效，仅增量列可用。
`final`（清理后已渲染）vs `t5` / `t1` 均为 **0.000%**。

## 轮次 3 · 排除「状态栏 override 旁路」

### 3a. 证实 override 整体替换状态栏

| 区域 | override 生效 vs 清除 |
|---|---|
| 状态栏整条 | 4.031% |
| 　左（时钟/运营商） | 4.105% |
| 　右（信号·WiFi·电池） | 5.309% |
| 状态栏以外 | **0.000%** |

### 3b. override 已清除状态下复测

| Key | 栏左（噪声） | **栏右（测试区）** | 主屏中（对照区） |
|---|---|---|---|
| `SBShowBatteryLevel` = NO | 2.849% | **0.000%** | 0.000% |
| `+SBShowRingerState` = YES | 1.464% | **0.000%** | 0.000% |
| `+对照（搜索胶囊）` | 0.534% | 0.000% | **0.264%** |
| 清理后 | 0.453% | 0.000% | **0.264%** |
| 清理校验 R0 vs R4 | 3.465% | 0.000% | 0.000% |

⇒ override 不是状态栏 key 失效的原因；清除后仍为 0.000%，同轮对照正常触发。

---

## 汇总

| | |
|---|---|
| 实测不同 key 数 | **11** |
| 证实有可见效果 | **1**（`SBHomeScreenShowsSearchAffordance`） |
| 阳性对照触发轮次 | 3 / 3，均可逆 |

## 区域划分

| 名称 | 归一化 y (H=2868) | 说明 |
|---|---|---|
| 状态栏 | 0.000–0.060 | 栏左 x<0.40（时钟，噪声源）、栏右 x>0.55（信号/WiFi/电池） |
| 图标区 | 0.060–0.330 | 主屏图标网格 |
| 主屏中 | 0.330–0.930 | 搜索胶囊（约 y 0.60–0.66）与主屏中下部 |
| Dock | 0.930–1.000 | 底部 Dock |

截图基准大小：已渲染约 **4.52 MB**；空屏约 **77 KB**（>1 MB 判为已渲染并重采）。
