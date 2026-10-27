# Managed Preferences 投递通道验证记录（轮次 4）

环境：iPhone 18 Pro Max 模拟器 `2990A9E7-C09B-4D9A-A2BD-8CAD96F98999`，iOS 27.0（24A5380i），Light 外观。
脚本：`docs/data/verify_managed_channel.sh`（每帧 respring + ≥1MB 尺寸守卫 + 重采）。
差分判据：`|Δ| > 8` 的像素占比。帧分辨率 1320×2868。

---

## 0. 前置：真机 Managed Preferences 的实际形态

来源：MobileSync 备份 `00008130-001431082E40001C`（iPad16,2 / iOS 27.0 / 24A5424a），
`ManagedPreferencesDomain`。完整内容见 `docs/data/device_managed_prefs.json`。

| 文件 | 体积 | key 数 | 内容 |
|---|---|---|---|
| `mobile/com.apple.springboard.plist` | 269 B | **1** | `SBExtendedDisplayOverrideSupportForAirPlayAndDontFileRadars = True` |
| `mobile/.GlobalPreferences.plist` | 682 B | 15 | 8 个 Nugget 投递的 key（`SBIconVisibility` / `SBSearchDisabledDomains` / `SBDisableClockIconSecondsHand` / `UIStatusBarShowBuildVersion` / `SolariumForceEnhancedSpeculars` / `AccessoryDeveloperEnabled`）+ 7 个 Apple 自写（content-rating、`INNext*`、AutoCorrection/SpellCheck） |
| `mobile/com.apple.sharingd.plist` | 239 B | 1 | `OverrideTimeLimitEveryoneMode = True` |
| `mobile/com.apple.webcontentfilter.plist` | 502 B | 8 | 内容过滤默认值 |

**两个可复用结论**

1. Managed Preferences 是**稀疏覆盖文件**，不是完整副本。SpringBoard 自己的状态在
   `/var/mobile/Library/Preferences/com.apple.springboard.plist`（真机 50 个 key），
   写 Managed 不会污染它。⇒ 这就是 Nugget 敢把 tweak 全写 Managed 的原因。
2. registry 共 133 条 tweak，落地文件**只有 2 条不在 Managed Preferences**
   （`footnote` / `nanoregistry`）；其余全部经 Managed 投递（见
   `docs/data/registry_plist_channels.txt`）。

---

## 1. 通道探针：全局域（`.GlobalPreferences`）能否穿透到 SpringBoard

**动机**：registry 有 109 条 tweak 走 `FileLocation.globalPreferences`（Managed
`.GlobalPreferences.plist`，全局域），其中包含 13 个 `SB*` key。要被这套通道认可，
前提是 **SpringBoard 的偏好读取会回落到全局域**。这一点此前从未验证过。

**设计**：用**已知有效**的 key 做探针（上一轮用假 key `f1Mshr` 探路是无效实验）。

```
app 域  com.apple.springboard  : 清空 SBHomeScreenShowsSearchAffordance
全局域  .GlobalPreferences     : 无该 key
→ 基线帧 base（胶囊应在）
→ 只往全局域写 SBHomeScreenShowsSearchAffordance = NO，app 域保持干净
→ respring → 帧 g_write
→ 删除全局域该 key → respring → 帧 g_clean
```

**结果**

| 对照 | 全屏 | **胶囊带 y[0.78,0.84] x[0.30,0.70]** | 状态栏 | 图标区 | 主屏中 | Dock |
|---|---|---|---|---|---|---|
| `base` vs `g_write` | 0.929% | **6.616%** | 12.84%（时钟噪声） | 0.000% | 0.43% | 0.000% |
| `g_write` vs `g_clean` | 0.929% | **6.616%** | 12.84% | 0.000% | 0.43% | 0.000% |
| `base` vs `g_clean` | **0.000%** | **0.000%** | 0.000% | 0.000% | 0.000% | 0.000% |

视觉确认（`/tmp/sweep4/g_write.png`）：**`g_write` 帧主屏搜索胶囊（"🔍 搜索"）消失，页点出现**；
`g_clean` 帧恢复到与基线相同的画面。

**复原精度（别写成"逐像素一致"）**：`base` vs `g_clean` 全帧 max|Δ| = **5**，
>8 判据下 0.000%，仅 0.0072% 像素 >2；**胶囊区（y[0.78,0.84] x[0.30,0.70]）max|Δ| = 0**。
即重渲染抖动仅存在于阈值以下，胶囊区完全没有残留。
⇒ **SpringBoard 对这条 key 的读取会回落到全局域。** 全局域通道对 SpringBoard 有效。

**边界（必须写清）**：本实验写的是**全局域的用户域文件**
`data/Library/Preferences/.GlobalPreferences.plist`（用 `defaults write .GlobalPreferences`），
**不是** `data/Library/Managed Preferences/mobile/.GlobalPreferences.plist`。
即：证明的是「全局域本身被 SpringBoard 读取」，不是「模拟器 Managed 目录可用」——
后者按已知结论是惰性的，模拟器上无法验证。真机侧「Managed 全局域投递真实生效」由
§0 的真机文件形态 + 现网已上线的 109 条 GP 条目共同支撑。

---

## 2. 新候选扫描（app 域，增量归因）

| Key | 写入值 | 读回 | 全屏增量 | 判定 |
|---|---|---|---|---|
| `SBWidgetSnapshotDebugLabels` | YES | ✅ | 0.000% | ❌ 无效 |
| `SBShouldShowWidgetIntroductionPage` | YES | ✅ | 0.000% | ❌ 无效 |
| `SBHomeShouldShowLibraryEducationView` | YES | ✅ | 0.000% | ❌ 无效 |

三个都是「往主屏新增元素」型（小组件调试标签 / 小组件引导弹窗 / 资源库引导页），
与前两轮的规律一致：**新增元素型在模拟器上全部惰性**。

清理校验：`base` vs `final` = **0.000%**（逐像素一致）。

---

## 3. 累计战果

| | |
|---|---|
| 实测不同 key 数 | **14** |
| 证实有可见效果 | **1**（`SBHomeScreenShowsSearchAffordance`） |
| 新增结论（与像素无关但决定性） | 全局域通道对 SpringBoard 有效（§1） |

---

## 4. 踩坑：区域定义必须按设备实测

本轮首次分析把「胶囊带」定义为 y[0.56,0.70]（沿用旧报告的假设），
读到 **0.000%**，差点据此写出「全局域不生效」的错误结论。

实测该设备（iPhone 18 Pro Max / 1320×2868）搜索胶囊位于 **y ≈ 0.80**
（x 0.30–0.70），页点位于 y ≈ 0.79。旧报告 §3 的区域划分只给了
「主屏中 0.330–0.930」这一宽档，恰好覆盖它，所以旧数据没错；
但本轮把它细分成多档时切在了胶囊上方，才暴露出这个问题。

**规则**：差分区域一律先用「变化像素的行剖面」定位，再用固定区域；
不要从文档抄归一化区间。
