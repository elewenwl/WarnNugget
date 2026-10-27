# 实测有效的键值对（唯一清单）

> 判定标准：**活体 A/B/A 实测出可见渲染变化，且可复现**。
> 不算数的：静态 accessor/key 配对、真机备份已落盘、名字像 key、语义自洽的差异。
> 环境：iOS 27.0 模拟器 24A5380i（iPhone 18 Pro Max 1320×2868）；真机基线 iPad16,2 / 24A5424a。
> 生成于 2026-09-13，对应报告 `SPRINGBOARD_TWEAK_CANDIDATES.md`（§3.2e / §4 / §12 / §13）。

**结论：全项目实测下来，只有 2 个 key 的取值被证明确实改变渲染。**

**累计口径（截至 2026-09-13 轮次 9）**：SpringBoard 族活体实测 **32 个不同 key**，
只有 **1 个**产生可见效果（`SBHomeScreenShowsSearchAffordance`，命中率 **3.1%**）。
另有 Liquid Glass 的 `UIViewGlassTintAmount` 证据更硬（8 点响应曲线），但**已被上游回退、不在 registry**。

---

## A. 有可见效果 —— 2 个 key

### A1. `com.apple.UIKit` → `UIViewGlassTintAmount`（Float，0…1）

唯一一个有**完整响应曲线**的 key。8 点扫描，8 个不同帧指纹，单调。

| 写入值 | 全屏变化 | 搜索框亮度 | 帧指纹 `sha256[:12]` |
|---|---|---|---|
| **`1.0`** | **1.196%** | 45.49 → **38.26** | `93056824a955` |
| **`0.75`** | — | **38.51** | `a71a3d6c89ed` |
| **`0.65`** | — | **40.51** | `af225ca929b7` |
| **`0.60`** | — | **41.94** | `762a546d45c9` |
| **`0.55`** | — | **43.58** | `2d47d622a7de` |
| **`0.25`** | — | **46.20** | `4c58fb12f338` |
| **`0.00`** | 0.017% | **47.33** | `f41d619ba80d` |
| `0.50` | 0.000% | 45.49 | `707c142da4f3` ← **= 出厂默认**，与"完全不写"**逐字节相同** |

- **有效区间 = 全部 0…1**；观感差异集中在 **0.50–0.75**（斜率由 ≈−3/单位 跳到 −38/单位），
  两端饱和（0.0≈0.5、0.75≈1.0）。所以 `step=0.05` 是必要的，贴着三档取会砍掉整个过渡区。
- **越界安全**：`-0.5` → 逐字节等于 `0.0` 那张；`1.5` → 逐字节等于 `1.0` 那张 ⇒ 二进制里 clamp 是活的。
- **伴侣 key 非必需**：单独写本 key 就改变渲染。`UIViewGlassEverEditedInSettings` 是设置页自己会写的，不写也生效。
- **三档文案 = 相对位置**，不是三档跳变：`More Clear`(<0.5) / `Default`(=0.5) / `More Tinted`(>0.5)。

> ⚠️ **状态：曾被上游回退，当前不在 registry。**
> 定义在 `7f5740b [QOL] Liquid Glass Options`（Jason，09-12 19:58 +0800），
> `cf9d2d9 [REVERT] Remove Liquid Glass Tint Amount tweak`（awesomenull，09-12 **18:06 +0300 = 15:06Z**）删除。
> `git show cf9d2d9` = **纯删除 51 行 / +0**（`registry.py` 50 + `tweak_names.py` 1），**提交信息无正文**。
> 两提交相隔 **3h08m14s**（此前写的"14 小时"是**时区叠错**，已更正）。
> 现在 registry 里 `UIViewGlass` / `TintAmount` 出现次数均为 **0**，`FileLocation.uikit` 仅剩 `UseFloatingTabBar` 一处。
> 连带后果：`docs/Simulator_Verification.md` §6「正例」与 `tools/sim_tweak_verify.py` 用法示例所引的
> `--tweaks GlassTintAmount` 已**匹配不到任何 spec**（`specs_matching` 按 key 后缀/TweakID 匹配）。
>
> ⇒ **完整取证（8 条缺陷假设逐条排除、GitHub 侧亦无记录）见
> [`docs/data/glass_tint_amount_revert_forensics.md`](glass_tint_amount_revert_forensics.md)。
> 结论：回退无可追溯的技术理由，恢复它需要维护者拍板。**

### A2. `com.apple.springboard` → `SBHomeScreenShowsSearchAffordance`（Bool）

| 写入值 | 效果 |
|---|---|
| **`false`** | 主屏底部 Dock 上方**搜索胶囊消失**（全屏 0.158% / 主屏中 0.264% / 搜索区 0.428%）|
| `true` | 恢复胶囊；与基线差分 **0.000%**，逐字可逆 |

- 唯一经**正向/反向双向复现**的 SB* key，在 4 个不同轮次里都触发。
- 已落地：`TweakID.HideHomeSearchPill` / `Section.SPRINGBOARD` / `FileLocation.springboard`（Managed）。
- `min_version="26.0"`，风险低（纯 UI，可逆）。

---

## B. 实测无效 —— 不要写（全部 0.000%）

| 组 | 数量 | 备注 |
|---|---|---|
| SB\* key · 轮次 1–7（报告 §3.2e） | **17** | 含状态栏族、`SBHomeIcon*` 全家族、widget/教育页类 |
| SB\* key · 轮次 8（单值法） | **7** 干净阴性 | `SBRingerMuted`、`SBHomeLargeIcons`、`SBEnableHomeScreenWallpaperDimming`、`SBDisableParallaxOnPageControl`、`SBShowInternalWidgets`、`SBNeverRenderSystemApertureFillOnGPU`、`SBMainDisplayDarkeningPercentage`。去状态栏差分 0.000–0.002%（2px 地板） |
| SB\* key · 轮次 9（**双值互比法**） | **2** 干净阴性 | `SBShowInternalApps`（true vs false，0.000%）、`SBWallpaperZoomScaleHomeScreen`（2.0 vs 0.5，0.002%） |
| `UIViewGlassLegibilitySetting` | 3 值 | `0` / `1` / `2`，且**叠加 `EverEditedInSettings` 闸门后仍 0.000%** |
| Tier 1 八个 SpringBoard 玻璃/主屏开关 | 8 | **两个候选域都试过**（`NSGlobalDomain` 与 `com.apple.springboard`），均 0.000% |
| GP 系列（`SolariumIncreasedDiffusion` / `GlassVisualDebug` / `SolariumForceFallback` 等） | 若干 | 含**已在线**的 `SolariumForceFallback` 同样 0.000% |

`SBHomeIcon*` 的"无效"有额外成因：存储已迁到 PosterBoard poster 配置
（`SBMigratedHomeScreenDefaultsTintToPosterBoard`，真机 True），写遗留 pref 本就不该生效。

### B1. 不可判（**别写成"无效"**）

| 类别 | key | 为什么不可判 |
|---|---|---|
| 元素不在采集通路 | `SBAlwaysRenderSystemApertureFillOnGPU`<br>`SBNeverRenderSystemApertureFillOnGPU` | 模拟器截图里**没有动态岛** —— 中心带 `x[560,760) y[40,140)` 三个帧全是 `min=37`、`<60` 像素 = 0（纯壁纸）。同族 `SBSuppressDynamicIslandCompletely` / `SBAlwaysShowSystemApertureInSnapshots` 据此预先剔除 |
| 前置不可达（静态无路径） | `SBShowThermalWarning`、`SBShowRegionOfInterest`、`SBEnableSecureDrawViolationAlerts`、`SBHomeScreenShowsBadgesInAppLibrary` | 分别需设备发热 / 触控交互 / 触发绘制违例 / App 库内有 badge 数据 |

---

## C. 未证实 —— 不等于无效

| key | 域 | 为什么不能判死 |
|---|---|---|
| `NewScrollEdgeEffectTag` | `com.apple.Preferences` | 真假值两帧**逐字节相同**（`08cb7a61b86e`）。它切的是滚动边缘**打标通路**，静态 A/B 看不见差异；要验得滚动后比 pocket 行为。键本身已由 lldb 活体调用确认（`UserDefaultKeyedFeature` 的 `key.getter` 返回该名） |

另有整类**模拟器验不了**（非无效，是通路不存在）：AOD / Capture Button / 传感器族 / 状态栏族（真机）。

---

## D. 五条会伪造"有效 / 无效"的坑（验新 key 前必读）

### D1. 状态栏会**整条**随机消失 —— 必须整条屏蔽（最大的坑）

冻结时钟**不够**。override 全程固定不动、只反复 respring + 截屏，同条件的帧间差仍然有
**0.99–1.01%**，与"写不同 override 条件"的 **1.00%** 无法区分。根因：状态栏整条
（左时钟+右信号/WiFi/电池）会随机不渲染（状态栏带近白像素 4564 → **0**）。

⇒ **任何 SpringBoard/主屏类差分，必须把 `y < 0.075·H` 整条屏蔽。** 不屏蔽的后果：
3 个**惰性** key 各自"测出" 0.27% 的漂亮信号，且语义全都讲得通（静音图标/内部组件/Aperture 填充）。

### D2. 帧大小闸门必须**先分态再判**

帧大小常呈**双峰**（有无状态栏两档，实测相差 0.079–0.108%）。全局中位数会落在两峰之间的空档，
`±0.05%` 会**每帧都超阈**。正确三条分级闸门：

| 闸门 | 判据 | 处置 |
|---|---|---|
| 息屏 | 帧 < 50% 最大帧 或 全屏均值 < 10 | FATAL 重采（实测 77 KB 帧） |
| 过渡帧 | 帧大小偏离**本组**中位数 > 1% | FATAL 重采 |
| 状态栏伪影 | 状态栏像素数与基线不同 | BENIGN，**屏蔽后继续用**（不复采） |

### D3. 两个历史假阳性帧的机制**不同**（此前判错）

| 帧 | 机制 | 指纹 |
|---|---|---|
| `sweep7/A2`（4,523,412，−0.084%） | **状态栏整条消失** | 状态栏近白 = **0**（同批其余 4564） |
| `sweep5/v_accent`（4,319,125，−4.595%） | **过渡帧（主页淡入中）** | 状态栏**在**；色度差有、**亮度差 0**（`\|Δ\|>8` 的亮度像素 = 0） |

`SBHomeIconUserInterfaceStyle=accent` 的 1.242% 就在这两帧上 —— 它差异集中在图标区、
图标饱和度 59.79→67.60、"被 accent 着色"语义完全自洽、清理后可逆，
但两次独立复现全 0.000%。**语义自洽 ≠ 因果。**

**屏蔽状态栏后的残差地板 = 固定 2 px**（`y≈0.452, x≈0.591` 一条细竖线，两次渲染的 AA 差）。
任何 < 0.005% 的读数都在地板以下。

### D4.「写入值 = 默认值」会伪造**完美阴性**

轮次 8 对 12 个 key 一律写 `true`，但不知道默认值。若某 key 默认已是 `true`，
读到的 0.000% 只等于"把已成立的值又写了一遍"。

⇒ **解法：同 key 双值互比**（`A=true` / `B=false`，直接比 `t_K__A` vs `t_K__B`）。
两个值里至少一个偏离默认 ⇒ **不需要知道默认值**，非零差即证明 key 活着；结论自包含。

### D5. 测之前先证明「目标元素在截图里存在」

比"key 是否生效"更前置：这个 key 控制的东西，截图里到底有没有？没有 ⇒ 无论 key 多有效都是 0.000%，
而你会把它误记成"key 惰性"（本项目已发生 2 次）。做法：先量目标元素的**存在性指纹**
（近白/近黑像素数、所在行带）；两帧都为 0 ⇒ 本轮**不可判**。

---

## E. 复现工具

| 文件 | 用途 |
|---|---|
| `tools/sim_ab_analyze.py` | 分析器：分态闸门 + 状态栏屏蔽 + 双值互比，一次跑完。`python tools/sim_ab_analyze.py <采集目录>` |
| `docs/data/verify_sb_round9.sh` | 采集模板：同 key 双值互比 + 元素存在性预筛 + 阳性对照 |
| `docs/data/verify_aba_template.sh` | 通用 A/B/A 模板 |
| `docs/data/springboard_round8_9_log.md` | 轮次 8/9 完整记录（含四条缺陷的发现过程） |
| `docs/data/glass_tint_amount_revert_forensics.md` | A1 那条 key 被回退的取证（时间线核准、8 条假设逐条排除、残留死代码清点） |

