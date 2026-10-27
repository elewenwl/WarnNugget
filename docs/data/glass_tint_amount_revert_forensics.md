# `GlassTintAmount` 回退取证

> 问题：`UIViewGlassTintAmount` 是全项目**证据最硬**的 key（唯一有完整响应曲线），
> 却在 2026-09-12 被 `[REVERT]` 删除。**理由决定它能不能接回来。**
>
> 结论：**仓库与 GitHub 都没有留下理由**，且代码侧**找不到任何缺陷**。
> ⇒ 既不能说它是修 bug，也不能说它是随手删的。恢复它需要维护者拍板。

---

## 1. 两个提交的核准事实

| | 引入 | 回退 |
|---|---|---|
| SHA | `7f5740b171e024322b30e459592c1a18d9d0dbda` | `cf9d2d9f0d06a6b4d7f5dcb3e2516d1e3f3f2fb2` |
| 标题 | `[QOL] Liquid Glass Options` | `[REVERT] Remove Liquid Glass Tint Amount tweak` |
| 作者 | `Wind0ws11Aero`（Jason） | `awesomenull`（协作者） |
| 时间（原时区） | 2026-09-12 **19:58:10 +0800** | 2026-09-12 **18:06:24 +0300** |
| 时间（归一 UTC） | 11:58:10Z | **15:06:24Z** |
| **正文** | 仅标题，**无正文** | **仅标题，无正文** |
| 范围 | 6 文件 **+200 / −23** | 2 文件 **−51 / +0**（纯删除） |

**间隔：3 小时 08 分 14 秒**（不是"14 小时"，此前口算把时区叠错了）。

`7f5740b` 逐文件：

```
 src/cli/cmd_tweaks.py       |   5 +-
 src/gui/ios/components.py   |  50 ++++++++---
 src/gui/ios/tweaks.py       |  31 ++++++---
 src/tweaks/registry.py      |  90 +++++++++++++++-
 src/tweaks/tweak_classes.py |  36 ++++++
 src/tweaks/tweak_names.py   |  11 +
```

## 2. 回退是一次「外科手术」，不是整批撤回

`cf9d2d9` 是 `awesomenull` **同一个晚上 5 连推**的第 5 个（全部 +0300）：

```
6ca778f  15:04  [FEAT] iOS UI: danger reset button, pre-apply summary, progress bar,
                       responsive card grid, accent gradients
3174aac  15:14  [FIX]  Home cards grid: keep all cards laid out when the page starts hidden
4ea24a9  15:34  [FIX]  Home cards: fill the full row (4 cards) whenever width allows
0e6572c  16:17  [DOCS] upfart readme.md credits section
cf9d2d9  18:06  [REVERT] Remove Liquid Glass Tint Amount tweak   ← 本项
```

→ 删的是**一次 UI 大改**的收尾动作。但删除**只摘了这一条 tweak**，同批引入的
基础设施全部留在了 HEAD 里（见 §3）——所以这不是"把整个功能下线"。

## 3. 回退后残留的三样东西（都还在 HEAD）

| 残留 | 位置 | 现状 |
|---|---|---|
| `class CompanionKeyTweak(BasicPlistTweak)` | `src/tweaks/tweak_classes.py` | **类定义还在，但已无任何实例化点** → 死代码 |
| `Kind.NUMBER` 的 GUI/CLI 支持 | `registry.py` 40 处、`gui/ios/components.py`、`cli/cmd_tweaks.py` | 完好，其它 tweak 仍在用 |
| `FileLocation.uikit` | `src/tweaks/basic_plist_locations.py:21` | 仍被 `UseFloatingTabBar`（`ipad_only`）使用 |

`CompanionKeyTweak` 的唯一消费者就是被删的这条 → **它现在是孤儿**。
全仓引用只剩两处**文字**提及：`tweak_classes.py` 自身 docstring、
`tools/sim_tweak_verify.py:766` 的说明字符串。

## 4. 逐条排除「回退是在修 bug」

| 假设 | 验证 | 结论 |
|---|---|---|
| 域写错了？ | 原 spec 用 `FileLocation.uikit` = `/var/Managed Preferences/mobile/com.apple.UIKit.plist` | ❌ 域正确 |
| 工厂不可达？ | `tweak_loader._build_spec` 对 `spec.factory` 走 `spec.factory()`；`_glass_tint_tweak()` 无参，匹配 | ❌ 可达 |
| 工厂把值写死导致滑杆失效？ | 走查确认 GUI 是 `tweaks[tweak_id].set_value(value)` —— 改的是**注册对象**而非 spec；`value=1.0` 只当初始值 | ❌ 滑杆正常（**我此前这条假设是错的，已划掉**） |
| companion key 会残留？ | 每次 apply 都**从零构建** `{file_location: {key: value}}`（只含已启用项），文件整体重写；禁用后两个 key 一起消失 | ❌ 不残留 |
| `CompanionKeyTweak` 有缺陷？ | 读实现：仅在 `enabled` 时 merge 主 key + `companion_keys`，与 `BasicPlistTweak` 语义一致 | ❌ 无缺陷 |
| `Kind.NUMBER` 与那批 UI 改动冲突？ | 回退后 `Kind.NUMBER` 仍在用（40 处），新 UI 正常处理 | ❌ 不冲突 |
| 被 hotload 规则隐藏？ | `hotload_rules.json` 里唯一 Liquid Glass 的 `hide_feature` 规则是标注 `Example rule (inert)`，且 `"disabled": false`（=未激活）、`only_models: ["iPhone16"]` | ❌ 不生效 |
| 分区空了？ | `Section.LIQUID_GLASS` 仍有 53 条显式登记（另有 `_usol()` 批量生成） | ❌ 分区健在 |

## 5. 外部也没记录

- `gh api .../commits/cf9d2d9` → 提交正文为空，无关联 PR、无 issue 引用。
- GitHub 提交页无任何评论。
- 回退之后唯一碰过 `registry.py` 的提交是 `0fba768`（awesomenull，
  `[FIX] Protective backup: match iOS 27 physical tree names...`）——内容无关。
- Jason 事后两次提交（09-13）也没有把它加回来：
  `6b9de5f [HOTFIX] Fix settings can't be modified`（改的是 `set_ignore_frame_limit`
  NameError、`asyncio` 缺模块级 import、restore 清单密码回落）、
  `7aa70fc bump version to 9.4a`。**均与 tint 无关。**

## 6. 结论与处置

**可确证：** 回退没有任何可追溯的技术理由；所有能想到的缺陷假设都被逐条排除；
删除是外科式的，且把 `CompanionKeyTweak` 孤儿化了。

**不可确证：** `awesomenull` 当时的真实动机（提交信息、PR、issue、评论四处皆空）。
**任何"他是为了修 X 才删的"说法都是编造。**

**当前状态判定：**

| key | 实测有效性 | 能否被 Nugget 投递 | 可用性 |
|---|---|---|---|
| `com.apple.springboard/SBHomeScreenShowsSearchAffordance` | ✅ 双向复现 | ✅ `TweakID.HideHomeSearchPill` 已在 registry | **现在就能用** |
| `com.apple.UIKit/UIViewGlassTintAmount` | ✅ 唯一有完整响应曲线 | ❌ **不在 registry** | **需先恢复代码** |

**恢复它需要三处改动**（原文已从 `cf9d2d9^` 提取，逐字可还原）：

1. `src/tweaks/registry.py` — 插回 `_glass_tint_tweak()` 工厂（含 2264 字节 docstring）
   与 `_t(TweakID.GlassTintAmount, ...)` 那条 spec；
2. `src/tweaks/tweak_names.py` — 插回 `GlassTintAmount = auto()` 枚举
   （必须落在 `DisableSpecularEverywhere` 之后，保持 `auto()` 序号不漂移）；
3. 无需改 GUI/CLI —— `Kind.NUMBER` 支持从未被删。

**未决：** 是否恢复，由维护者（Jason）决定。这是**产品决策**，
而且上游协作方曾主动删除过它，不宜由工具单方面改回。
