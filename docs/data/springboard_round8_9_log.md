# SpringBoard key 扫描 · 第八 / 第九轮记录

> 目的：从 351 个「未测且未被 registry 占用」的 SB\* key 里，继续找**经活体实测确实生效**的键值对。
> 前序 18 个已测 key 中只有 1 个有效（`SBHomeScreenShowsSearchAffordance`）。
>
> 结论摘要：**第八轮 12 个新 key 无新增有效项**，但挖出**四条方法论缺陷**与**两处此前误判的更正**。
> 第九轮换方法（双值互比）复测，结果见 §9。

---

## 1. 候选池与筛选口径

| 项 | 数 |
| --- | --- |
| accessor/key 配对表内唯一 `SB*` key | 357 |
| 减去 registry 已占用 | − |
| 减去前序已实测 18 个 | −18 |
| **可测池** | **339** |
| 按「元素增删型」正则筛选（Hide/Show/Disable/Enable/Suppress/Always/Only/Dock/Widget/Home/Icon/Badge/…） | **121** |

从 121 里人工剔掉**前置不可达**与**机型不符**后，选出 12 个进入第八轮。

### 1.1 机型范围限制（此前未写明的坑）

测试机 = **iPhone 18 Pro Max（1320×2868）**。以下候选在 iPhone 上**天然不是空测也是伪测**，
必须预先剔除，否则整轮白烧：

```
Chamois / Stage Manager / Medusa(多任务) / Split&SlideOver Peek / Sidebar /
MenuBar / ExternalDisplay / DisableHomeButton(无 home 键)
```

---

## 2. 第八轮初版：**整轮作废**

跑完就发现两个缺陷，结论一律不可用：

1. **状态栏没冻结** —— 日志里 `base vs final` 有 0.237% 残留，而两者状态完全相同；
   变化带全在 `y=0.038`（状态栏）。是**时钟跳分钟**造成的假差分。
2. **差分顺序错了** —— 分析脚本按文件名两两差分，进的是**字母序**，不是写入时序。
   单键归因全部失效。

⇒ 重写为 `docs/data/verify_sb_round8b.sh`：开头 `status_bar override --time "9:41"`、
按 manifest 时序配对、收尾 `clear`。

---

## 3. 第八轮修正版（`/tmp/sweep8b`）

### 3.1 采集

16 帧：`base` / `base2`（管线自校验）+ 12 个待测 key + `control`（阳性对照）+ `final`（复原油）。
每帧 = `launchctl kickstart -k system/com.apple.SpringBoard` → sleep 50 → 截图。

### 3.2 分态闸门

| 组 | 帧数 | 帧大小中位数 |
| --- | --- | --- |
| 有状态栏 | 9 | 4,528,375 |
| 无状态栏 | 7 | 4,523,507 |
| **两组相差** | | **0.108%** |

⇒ **双峰**。全局中位数（4,525,906）落在两峰之间的空档，
若直接套「±0.05%」闸门，**16 帧全部超阈**。

### 3.3 管线与复原校验

```
base vs base2   去状态栏 0.0000%   ✔ 采集确定性
base vs final   去状态栏 0.0000%   ✔ 完全复原（12 个 key + control 全清理后）
```

### 3.4 时序差分结果（屏蔽 `y < 0.075·H` 状态栏带）

| 写入 | 全屏 | **去状态栏** | 判定 |
| --- | --- | --- | --- |
| `SBRingerMuted = true` | 0.269% | **0.002%**（2px） | 无效 |
| `SBHomeLargeIcons = true` | 0.002% | 0.002% | 无效 |
| `SBEnableHomeScreenWallpaperDimming = true` | 0.002% | 0.002% | 无效 |
| `SBDisableParallaxOnPageControl = true` | 0.002% | 0.002% | 无效 |
| `SBMainDisplayDarkeningPercentage = 0.5` | 0.000% | 0.000% | 无效 |
| `SBShowThermalWarning = true` | 0.000% | 0.000% | 无效 |
| `SBShowInternalWidgets = true` | 0.268% | **0.000%** | 无效 |
| `SBHomeScreenShowsBadgesInAppLibrary = true` | 0.002% | 0.002% | 无效 |
| `SBAlwaysRenderSystemApertureFillOnGPU = true` | 0.002% | 0.002% | **空测**（见 §5） |
| `SBNeverRenderSystemApertureFillOnGPU = true` | 0.268% | **0.000%** | **空测**（见 §5） |
| `SBShowRegionOfInterest = true` | 0.000% | 0.000% | 无效（前置不可达） |
| `SBEnableSecureDrawViolationAlerts = true` | 0.000% | 0.000% | 无效（前置不可达） |
| **`SBHomeScreenShowsSearchAffordance = NO`** | 0.426% | **0.158%** | ✅ **有效**（阳性对照） |
| `RESTORED` | 0.158% | **0.158%** | ✅ 可逆 |

阳性对照的变化带：`y=0.828(137px) / y=0.800(136px)`，列 `x=0.475` —— 正是**搜索胶囊**所在。

**屏蔽状态栏后残差地板 = 固定 2 px**（`y≈0.452, x≈0.591` 一条细竖线，
两次渲染的 AA 差，6 次差分都出现在同一坐标）。任何 < 0.005% 的读数都在这个地板以下。

### 3.5 如果不屏蔽状态栏

3 个**惰性** key 会各自"测出" 0.27% 的漂亮信号，而且语义全都讲得通
（静音图标 / 内部组件 / Aperture 填充）——**这是本项目迄今最像真阳性的批量假阳性来源**。

---

## 4. 状态栏伪影定性（控制实验）

第八轮修正版里，`SBRingerMuted` / `SBShowInternalWidgets` / `SBNeverRender…` 三个
互不相关的 key 都给出 0.268–0.269%，且变化带**完全相同**（`y=0.038`, 262px）
⇒ 强烈提示与 key 无关。

### 4.1 反例一：固定 override 下连采（`/tmp/sbstate`，经 `launchctl kickstart` 每帧 respring）

| 对照 | 差分 | 峰值行 |
| --- | --- | --- |
| A1 vs A2（**同为 clear**） | **0.9907%** | y=0.028 |
| B1 vs B2（**同为 override**） | **1.0073%** | y=0.034 |
| A2 vs B1（不同条件） | 1.0088% | y=0.034 |

⇒ **同条件帧间差 ≈ 不同条件间的差。** 在这个状态下，截图**无法区分两个 override 条件**。

### 4.2 反例二：完全不写任何 prefs，只连拍（`/tmp/sbburst`）

| 帧 | 字节 | 全屏均值 | 状态栏近白 |
| --- | --- | --- | --- |
| b1 / b2 | 77 KB | 0.0 | 0 |
| b3 | 4,314,651 | 106.7 | 0 |
| b4 / b5 | 4,523,560 | 106.5 | 0 |
| b6 / b7 / b8 | 77 KB | 0.0 | 0 |

⇒ 又出现一整类帧：**77 KB / 均值 0.0 = 息屏**。显示会自己在开关。

### 4.3 根因（看图即明）

状态栏**整条**（左 `09:41`+静音图标、右信号/WiFi/电池）会随机**整条不渲染**：

| 帧 | 状态栏带近白像素 | 判定 |
| --- | --- | --- |
| `sweep7/A1` | 4564 | 有 |
| `sweep7/A2` | **0** | **整条消失** |
| `sweep8b/t_SBRingerMuted` | 5534 | 有 |
| `sweep8b/t_SBShowInternalWidgets` | **0** | **整条消失** |

翻转时刻（相对 base）：105s / 426s / 586s / 772s —— **间隔不规则**（321/160/186s），
与所写 key 无任何语义关系。

⇒ **硬规则：SpringBoard / 主屏类 A-B 差分，必须把 `y < 0.075·H` 整条屏蔽。**

---

## 5. 更正：2 个 key 从「无效」改判为「空测」

复核截图后发现**模拟器根本不渲染动态岛**：

```
中心带 x[560,760) y[40,140)：
  t_SBRingerMuted  min=37  均值=83.0   <60 的像素 = 0    ← 纯壁纸，没有胶囊
  base             min=37  均值=83.0   <60 的像素 = 0
  final            min=37  均值=83.0   <60 的像素 = 0
对照（状态栏左区 x[150,320) y[80,140)）：
  有状态栏帧  >200 像素 = 2075
  无状态栏帧  >200 像素 = 0
```

⇒ `SBAlwaysRenderSystemApertureFillOnGPU`、`SBNeverRenderSystemApertureFillOnGPU`
的 0.000% **不证明 key 惰性**，只证明**采集通路里没有这个元素**。
同族另两个（`SBSuppressDynamicIslandCompletely`、`SBAlwaysShowSystemApertureInSnapshots`）
据此**预先剔除**，不再测。

**新判据（已写入 skill）**：测之前先量目标元素的**存在性指纹**；
两帧指纹都为 0 ⇒ 该 key 本轮**不可判**，不许写"无效"。

---

## 6. 更正：`accent` 假阳性的机制判错了

前序结论把 `accent` 的 1.242% 归为"瞬态渲染态"。**结论对（不是 key 效果），机制错。**
逐帧量状态栏后真相是**两个不同的伪影**：

| 离群帧 | 真机制 | 指纹 |
| --- | --- | --- |
| `sweep7/A2`（4,523,412，−0.084%） | **状态栏整条消失** | 状态栏近白 = **0**（同批其余 4564） |
| `sweep5/v_accent`（4,319,125，−4.595%） | **过渡帧（主页淡入中）** | 状态栏**在**（4563）；色度差有、**亮度差 0**（\|Δ\|>8 的亮度像素 = 0） |

两者**各有各的处置**：状态栏类 → 整条屏蔽；过渡帧 → 帧大小闸门。

---

## 7. 第二条方法论缺陷：「写入值 = 默认值」会伪造完美阴性

第八轮对 12 个 key **一律写 `true`**，事先**不知道默认值**。
若某 key 默认已是 `true`，读到的 0.000% 只等于"把已成立的值又写了一遍"。

| 类别 | 个数 | 明细 |
| --- | --- | --- |
| 前置条件不可达 | 4 | `SBShowThermalWarning`（需设备发热）、`SBShowRegionOfInterest`（需交互）、`SBEnableSecureDrawViolationAlerts`（需触发违例）、`SBHomeScreenShowsBadgesInAppLibrary`（需 badge 数据） |
| 元素不存在于采集通路 | 2 | 两个 SystemAperture key（§5） |
| 写入值极可能≈默认 | 1 | `SBAlwaysRenderSystemApertureFillOnGPU` |
| **真正干净的阴性** | **7** | `SBRingerMuted`、`SBHomeLargeIcons`、`SBEnableHomeScreenWallpaperDimming`、`SBDisableParallaxOnPageControl`、`SBShowInternalWidgets`、`SBNeverRenderSystemApertureFillOnGPU`、`SBMainDisplayDarkeningPercentage` |

⇒ **不能说"12 个全阴性"**，只能说「**7 个干净阴性 + 5 个不可判**」。

**解法：同 key 双值互比。** 见 §8。

---

## 8. 第九轮：同 key 双值互比（`/tmp/sweep9`）

### 8.1 方法

对每个 key 先后写两个**不同的**值（`A` / `B`），直接比 `t_K__A` vs `t_K__B`：

- **不需要知道默认值** —— 两个值里至少一个偏离默认，非零差即证明 key 活着。
- **结论自包含** —— 不依赖"干净基线"是否真的干净。
- 代价：每 key 两次采集；要求状态栏带已屏蔽。

另加两个前置：
1. **元素存在性指纹**先量（§5），指纹为 0 的候选**直接不选**。
2. **阳性对照**放进同一批（`SBHomeScreenShowsSearchAffordance` 的 false/true），
   证明这条管线在本批次确实看得见差异。

### 8.2 本批候选（7 个 + 1 对照）

| # | key | 类型 | A / B | 选它的理由 |
| --- | --- | --- | --- | --- |
| 1 | `SBShowInternalApps` | bool | true / false | 内部 App 出现在主屏 = 大块元素增删 |
| 2 | `SBWallpaperZoomScaleHomeScreen` | float | 2.0 / 0.5 | 壁纸缩放 = 大面积可见 |
| 3 | `SBWallpaperParallaxFactorHomeScreen` | float | 0.0 / 1.0 | 壁纸视差因子 |
| 4 | `SBHomeScreenScreenTypeOverride` | int | 0 / 2 | 主屏布局类型覆盖 |
| 5 | `SBDisableIdleSleep` | bool | true / false | 直接关系到观察到的息屏伪影 |
| 6 | `SBShouldShowPageHidingOnBoardingAlert` | bool | true / false | 引导弹窗 = 高可见（companion 同时压 false） |
| 7 | `SBShouldShowAppLibraryOnBoardingAlert` | bool | true / false | 同上 |
| — | `SBHomeScreenShowsSearchAffordance` | bool | false / true | **阳性对照** |

### 8.3 结果

**本轮采集中止**（见 §8.4），只采到前 2 个 key 的完整 A/B 对 —— 但这两个是**自包含**的
（双值互比不需要基线），所以结论仍然成立：

| key | A vs B | 全屏 | **去状态栏** | 判定 |
| --- | --- | --- | --- | --- |
| `SBShowInternalApps` | true vs false | 0.000% | **0.000%** | 惰性（**干净阴性**） |
| `SBWallpaperZoomScaleHomeScreen` | 2.0 vs 0.5 | 0.239% | **0.002%**（2px 地板） | 惰性（**干净阴性**） |
| `SBWallpaperParallaxFactorHomeScreen` | 0.0 vs 1.0 | — | — | 只采到 A，未完成 |

管线自校验：`base vs base2` 去状态栏 **0.0000%** ✔（且两帧状态栏均在位）。

注意 `SBWallpaperZoomScaleHomeScreen = 0.5` 那一行：全屏 0.239%，看着像信号，
**去状态栏后掉到 0.002%** —— 又是状态栏消失。这是护栏第 1 条在本轮**再次救回一个假阳性**。

未完成：第 3–7 个 key + 阳性对照。

### 8.4 采集中止的原因（**未查明，记为已知问题**）

`/tmp/sweep9` 逐帧时间戳显示严重且不规律的停顿：

```
base                                  0s
base2                                63s      ← 正常（~60s/帧）
SBShowInternalApps__A              1110s      ← 空档 1047s（17.5 min）
SBShowInternalApps__B              1172s
SBWallpaperZoomScaleHomeScreen__A  2171s      ← 空档 999s（16.7 min）
SBWallpaperZoomScaleHomeScreen__B  3140s      ← 空档 969s（16.2 min）
SBWallpaperParallaxFactor__A       3194s
```

逐项排除：

| 嫌疑 | 实测 | 结论 |
| --- | --- | --- |
| `simctl io screenshot` 慢 | 连测 3 次：1.6s / 0.6s / 0.6s，且**三帧逐字节相同** | ✘ 不是它 |
| `launchctl kickstart` 挂起 | 连测 2 次均 **0.6s** 返回 | ✘ 不是它 |
| settle 时间 | 脚本写死 `sleep 50` | ✘ 不解释 |

⇒ 停顿发生在 `sleep 50`、重采循环、或 `xcrun simctl spawn … defaults` 三者之一，
**未能定位**。第九轮跑满需 17 帧，按此速率不可接受，故中止。

**下次要注意**：采集脚本必须**给每一步加超时看门狗**并把每步耗时写进日志
（本次只有截图耗时进了 `sizes.tsv`，无法区分是哪一步卡住）。
在定位之前，长批次扫描不可靠。

---

## 9. 累计战果（截至第九轮）

| 项 | 数 |
| --- | --- |
| 活体实测的不同 key | **32** |
| 其中**确证有可见效果** | **1**（`SBHomeScreenShowsSearchAffordance`，命中率 3.1%） |
| 干净阴性 | **26**（轮次 1–7 的 17 个 + 轮次 8 的 7 个 + 轮次 9 的 2 个） |
| 不可判（空测 / 前置不可达 / 写入值≈默认） | **5** |

SpringBoard 族无新增可用项。唯一另一个有硬证据的键值对是
`com.apple.UIKit / UIViewGlassTintAmount`（8 点响应曲线），但它**已被上游回退、不在 registry**。

---

## 10. 新增的四条硬护栏

1. **状态栏带整条屏蔽**（`y < 0.075·H`）—— 不屏蔽必然批量假阳性（§4）。
2. **分态闸门** —— 帧大小双峰时不能套全局中位数；先按状态栏有无分组，再在组内比（§3.2）。
3. **写入值必须偏离默认**；对 bool key 用**双值互比**（§7 / §8）。
4. **先证明目标元素存在于采集通路**，再测它的 key（§5）。

配套落地：
- 采集模板：`docs/data/verify_sb_round9.sh`
- 分析器：`tools/sim_ab_analyze.py`（分态闸门 + 状态栏屏蔽 + 双值互比，一次跑完）
