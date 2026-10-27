# 主屏图标外观：存储真相 + 遗留 pref 证伪（轮次 5–7）

环境：iPhone 18 Pro Max 模拟器 `2990A9E7-C09B-4D9A-A2BD-8CAD96F98999`，iOS 27.0（24A5380i）。
脚本：`docs/data/verify_icon_style.sh`。帧分辨率 1320×2868，判据 `|Δ| > 8` 的像素占比。

**一句话结论：主屏图标外观不是 pref，是 PosterBoard poster 配置里的数据；
遗留的 `SBHomeIcon*` 系列 pref 在 iOS 27 上写它没有任何可复现效果。**

---

## 1. 存储真相（强证据：真机 + 模拟器实物）

真机备份里 8 个 poster 配置中有 4 个带 `PRPosterHomeScreenCustomizationConfiguration`；
模拟器 1 个。完整数据见 `docs/data/home_screen_icon_style_schema.json`。

路径形态：

```
<data>/Library/Application Support/PRBPosterExtensionDataStore/<storeVer>/Extensions/
    <PosterExtension>/configurations/<UUID>/versions/<N>/supplements/0/
      com.apple.posterkit.provider.supplementURL.homescreenConfiguration.plist
```

该 plist 是 `NSKeyedArchiver` 归档，`PRPosterHomeScreenCustomizationConfiguration` 的字段：

| 字段 | 模拟器 | 真机（4 个配置） | 值域 |
|---|---|---|---|
| `_iconUserInterfaceStyleType` | `clear` | `color`（4/4） | **`default` / `clear` / `color` / `accent`** |
| `_iconUserInterfaceStyleVariant` | `light` | `dark`(3) / `light`(1) | **`light` / `dark` / `always`** |
| `_iconTintSource` | `wallpaperSuggestion` | `wallpaperSuggestion`(3) / `none`(1) | — |
| `_iconUserInterfaceSize` | `SMALL` | `SMALL` | — |
| `_dimmed` | `true` | `true`(3) / `false`(1) | — |
| `_tintColorStyle` | `PUIDiscreteGradientVariatedCustomStyle` | 同 | hue / luminance / luminanceValue / saturation |

**三条可复用推论**

1. **图标外观是 per-poster（per-壁纸）数据**，不是全局偏好。真机 4 个配置各带一份；
   ⇒ **换壁纸 = 换图标样式**，反过来恢复流程只搬回壁纸而没搬回 supplement，
   图标样式就会回落默认。这与「壁纸添加后未生效」是同一类失效面。
2. **遗留 pref 与真实字段一一对应**（名字里都带 IconUserInterfaceStyle* / Tint）：
   `SBHomeIconUserInterfaceStyle` → `_iconUserInterfaceStyleType`；
   `SBHomeIconUserInterfaceStyleVariation` → `_iconUserInterfaceStyleVariant`；
   `…Luminance` / `…Saturation` → `_tintColorStyle` 的 luminance/saturation。
   `SBHomeIconTintColor` → `_iconTintSource`（无同名遗留 key）。
3. 缓存里 SpringBoardFoundation 字符串池把这批 key 与 `auto / dark / light / accent` 放在一起，
   而 `SBMigratedHomeScreenDefaultsTintToPosterBoard` 紧邻其后 —— 名字就写着「主屏默认值已迁移到 PosterBoard」。
   真机该 key = `True`；**模拟器上不存在**（迁移未跑）。

---

## 2. 遗留 pref 的活体测试：三轮，结论是「无效果」

`SBHomeIconUserInterfaceStyle` 依次写入不同值 + respring + 截屏差分。

| 轮次 | 写入 | 结果 |
|---|---|---|
| 5 | `dark` / `light` / `auto`（先） | 均 0.000% |
| 5 | **`accent`** | **1.242%**（小组件区 2.97% / 图标区 2.04%）← 一度以为命中 |
| 5 | `Variation=1.0` `Saturation=2.0`（float） | 0.001% |
| 5 | 清理 | base vs final 0.000% |
| 6 | `color` / `default` / `clear` | 均 0.000% |
| 6 | `accent` + `Variation=dark` | **0.000%** ← 与轮次 5 矛盾 |
| 6 | `accent` + `Saturation=2.0` `Luminance=0.5` | 0.000% |
| 7 | `accent`（单独，第一帧 A1） | **0.000%** |
| 7 | 同值再 respring（A2） | 0.239% ← 又出现 |
| 7 | `+Variation=dark`（A3） | 0.002%（回落） |
| 7 | 删 `Variation`（A4，仅 accent） | 0.000% |

⇒ **`accent` 在两次独立复现里都读 0**（轮次 6、轮次 7 的 A1/A4）。
轮次 5 与轮次 7-A2 那两个非零值是**不可复现的一次性结果**。

### 定案证据：帧大小

本轮全部 20 个主屏帧的截屏大小分布极其紧：

```
正常带   4,527,072 – 4,527,319   （18 帧，离散度 ±0.006%）
离群     4,319,125  (-4.6%)      = sweep5/v_accent.png   差分 1.242%
离群     4,523,412  (-0.085%)    = sweep7/A2.png         差分 0.239%
```

**唯一两个非零差分，正好是唯一两个帧大小离群的帧。**
⇒ 两者是瞬态渲染态（同一画面的不同绘制阶段），不是 key 的效果。

**轮次 5 的 `accent` 帧**曾经看起来很有说服力：4.6% 的体积偏小、差值集中在
小组件与图标区、图标饱和度 59.79 → 67.60（"图标被着色"的语义完全自洽），
清理后还 0.000% 可逆。**只有重复实验 + 帧大小对照才把它拆掉。**
教训：**语义自洽的差异不等于因果**，尤其当差异本身就是"另一种渲染态"时。

---

## 3. 结论

- **`SBHomeIconUserInterfaceStyle`（及 Variation / Luminance / Saturation / TintColor）
  在 iOS 27 上不可用于改主屏图标外观。** 存储已迁到 PosterBoard poster 配置。
- 想改图标样式必须走：改写上述 supplement 归档，或经
  `SBSHomeScreenService setHomeScreenIconStyleConfiguration:`
  / `PRSPosterUpdateTypeHomeScreenIconUserInterfaceStyle` 通路。
  **不要做成 registry 里的 plist tweak。**
- 报告里原先列为「优先验证」的 `SBHomeIcon*` 家族（§8 loose 桶）**到此结案：否**。

## 4. 新增护栏（已写回 skill）

`≥1MB 判空屏` 太松 —— 它放过了 4.319 MB 那帧。改为：

> **帧大小必须落在本轮帧大小中位数 ±0.05% 内**，否则判该帧无效、重采。
> 实测正常带离散度只有 **≤0.006%**，所以 ±0.05% 有约 8 倍余量。
> 阈值实测过：±0.5% / ±0.1% 抓不到 −0.084% 那个离群帧；±0.05% 起两个都抓到，
> 且对 18 个正常帧零误杀；再收紧到 ±0.01% 没有额外收益。

再叠加一条：

> **单个非零结果不算证据。** 同一值至少独立复现 2 次（respring 两次、两次截屏），
> 两次都非零才进入下一步。轮次 5 的 1.242% 与轮次 7 的 0.239% 各自孤立出现一次，
> 如果任一次被当成结论写进报告，就会上线一个不生效的 tweak。

两条护栏已进 `docs/data/verify_aba_template.sh` 与 `docs/data/verify_icon_style.sh`，
对轮次 5/6/7 的真实帧回归验证：`v_accent`(−4.595%) 与 `A2`(−0.084%) 被判无效，
其余 18 帧全部通过。
