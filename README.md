# SRW Animation Skip Patches · 超级机器人大战 动画跳过补丁

Battle animation skip patches for the **Super Robot Wars** series (スーパーロボット大戦).
**For games in the series that don't let you skip battle animations — we add it.** Every patch is applied in your browser: drop in a ROM, get a patched ROM back. Nothing to install.

为**超级机器人大战**系列作品添加**战斗动画跳过**功能：原作跳不了动画的，用 ROM 补丁给它加上。补丁页在浏览器里拖入 ROM 即可完成，无需安装任何工具。

## Patch Catalog / 补丁目录

| Game / 游戏 | Version / 版本 | Patch page / 补丁页 |
|---|---|---|
| Super Robot Wars A (GBA) · 超级机器人大战A | V5 (2026-10-13) | **<https://srw.cc.cd/srwa>** |
| Super Robot Wars R (GBA) · 超级机器人大战R | V1 (2026-10-07) | **<https://srw.cc.cd/srwr>** |
| Super Robot Wars Compact 1 (WonderSwan) · 超级机器人大战COMPACT 1 | V1 (2026-10-22) | **<https://srw.cc.cd/compact1>** |
| Super Robot Wars Compact 2 (WonderSwan) · 超级机器人大战COMPACT 2 | V1 (2026-10-22) | **<https://srw.cc.cd/compact2>** |

*This catalog keeps growing — more titles will be added.*
*收录持续扩充中，更多作品陆续添加。*

---

## How to use / 使用方法

1. Open the patch page of your game / 打开对应游戏的补丁页
2. Drop your ROM (GBA or WonderSwan) onto the page (or click to choose a file) / 把 ROM（GBA / WonderSwan）拖入页面（或点击选择文件）
3. The ROM is identified automatically by CRC32 — ROMs with older patches already applied are recognized and upgraded too / 页面按 CRC32 自动识别 ROM；已打过旧版补丁的 ROM 同样能识别并引导升级
4. Click **Apply patch**, then download the patched ROM / 点「应用补丁」，下载打好补丁的 ROM

Everything runs locally in your browser — no ROM is ever uploaded. Please provide your own ROM file; this site does not distribute ROMs. Patch pages are available in Chinese and Japanese.

全部在浏览器本地完成，不上传任何文件；请自备 ROM，本站不提供 ROM 下载。补丁页界面支持中文 / 日本語。

---

## Super Robot Wars A (GBA) · 超级机器人大战A — V5

**Patch page / 补丁页**: <https://srw.cc.cd/srwa> · **Reverse-engineering notes / 逆向笔记**: [srwa/README.md](srwa/README.md)

### Features / 功能

**English**

- New 6th entry `ANIMATION ON/OFF` in the system menu, toggled instantly with A (default ON = fully original game)
- OFF: all normal-attack and counterattack animations are skipped, settling through the game's native flow — damage, EXP and kills are never lost
- Hold **B** during a battle animation to skip it immediately
- Hold **START+A** the moment you confirm an attack → one-off quick battle (direct settlement + map damage popups, toggle unchanged)
- Hold **SELECT+A** the moment you confirm an attack → force this animation to play even in OFF mode (one-off)
- mGBA default keys: A = keyboard X, B = Z, START = Enter, SELECT = Backspace → START+A = Enter+X, SELECT+A = Backspace+X

**中文**

- 系统菜单新增第 6 项 `动画 ＯＮ/ＯＦＦ`，按 A 即时切换（开机默认 ＯＮ = 完全原版）
- ＯＦＦ：普攻/反击动画全部跳过，走原生结算——伤害/经验/击坠完全不损失
- 动画播放中按住 **B** → 立即跳过当前动画
- 确认攻击瞬间按住 **START+A** → 本场临时速战：直接结算 + 地图伤害弹字（单次，不改开关）
- 确认攻击瞬间按住 **SELECT+A** → ＯＦＦ 模式下强制播放该场动画（单次）
- mGBA 默认键位：A=键盘 X、B=Z、START=回车、SELECT=退格

> V4 and earlier used R+A (quick) / L+A (play once); they were moved to START/SELECT in V5 because L/R operate support attacks on the confirm screen.
> V4 及以前为 R+A（速战）/L+A（动画），因确认界面 L/R 需要操作援护，V5 改为 START/SELECT。

### Supported ROMs / 支持的 ROM（CRC32: original → patched / 原版 → 打补丁后）

| ROM | Original | Patched (V5) |
|---|---|---|
| Japanese original · 原版日文 | 2F6E9788 | 8FDFD94A |
| WGF v1.1 Chinese translation · WGF v1.1 汉化版 | 7C9BF014 | D6A4A290 |
| Red_Comet_x mod · Red_Comet_x 修改版 | 448A5691 | 9678C9C3 |
| Leleu Chinese translation · Leleu 汉化版 | D3F293FD | 03238CED |
| Pirated Chinese translation · 盗版汉化版 | 1B2370D5 | BB923E17 |

20 embedded patch packages: 5 direct-to-V5, 5 V4→V5 upgrades, 10 legacy chains to V4. ROMs patched with any V1–V4 build are recognized and upgraded.
内置 20 个补丁包：5 直打 V5 + 5 个 V4→V5 升级 + 10 个旧版 V4 链；V1–V4 旧补丁 ROM 均可识别升级。

### Version history / 版本史

| Version | Date | Changes / 更新内容 |
|---|---|---|
| V1 | 2026-10-09 | Menu animation toggle + full skip when OFF + B-button skip / 菜单动画开关 + ＯＦＦ全跳过 + 动画中按B跳过 |
| V2 | 2026-10-10 | Fixed "move → select weapon → cancel → infinite movement" in OFF mode / 修复ＯＦＦ模式「选武器→取消→无限移动」 |
| V3 | 2026-10-10 | Removed two gates proven redundant by testing; patch finalized as 4 code caves / 移除实测冗余的两处门控，补丁精简定版 |
| V4 | 2026-10-10 | Confirm-moment combos R+A / L+A; 5 ROM variants supported / 确认瞬间组合键 R+A速战/L+A动画；适配 5 版 ROM |
| V5 | 2026-10-13 | Combos moved to START+A / SELECT+A (freeing L/R for support); fixed Awakening extra-action loss in OFF mode / 组合键换位 START+A/SELECT+A；修复ＯＦＦ模式觉醒失效 |

Full reverse-engineering notes (memory maps, patch listings, dead ends) / 完整逆向解析笔记（地址表、补丁清单、失败记录）: [srwa/README.md](srwa/README.md)

---

## Super Robot Wars R (GBA) · 超级机器人大战R — V1

**Patch page / 补丁页**: <https://srw.cc.cd/srwr> · **Reverse-engineering notes / 逆向笔记**: [srwr/README.md](srwr/README.md)

### Features / 功能

**English**

- Hold **B** during a battle animation and it ends instantly into settlement via the game's own finish path — damage numbers, EXP and kills all normal
- The native animation ON/OFF setting is untouched: turn animations off natively, or keep them on and just hold B — use both together
- Implementation: one 0x58-byte code cave + a per-frame key-read hook that replays the official "animation finished" callback's mode switch, timing identical to the original

**中文**

- 战斗动画播放中按住 **B** → 动画立即收尾进入结算（走游戏官方结束路径，伤害数字/经验/击坠全部正常）
- 游戏原生「动画 ON/OFF」设置不受影响：关动画用原生设置，想看动画又嫌太长时按 B——两者配合
- 实现：一处 0x58 字节代码洞 + 每帧读键钩子，在动画播放中途复刻官方「动画完成回调」的模式切换，时序与官方一致

### Supported ROMs / 支持的 ROM（CRC32: original → patched / 原版 → 打补丁后）

| ROM | Original | Patched (V1) |
|---|---|---|
| Xingzu Chinese translation · 星组汉化版 | 68676832 | AA577351 |
| Rumble version · 震动版 | AE06084A | 6561C84C |
| Japanese original · 官方日文原版 | DF7F91BC | 3D3B30BA |

All three ROMs share byte-identical engine code (differences are only in fonts/tail data), so a single patch covers all of them.
三版 ROM 引擎代码逐字节一致（差异只在字库/尾部数据），同一份补丁通吃。

Full reverse-engineering notes / 完整逆向解析笔记: [srwr/README.md](srwr/README.md)

---

## Super Robot Wars Compact 1 (WonderSwan) · 超级机器人大战COMPACT 1 — V1

**Patch page / 补丁页**: <https://srw.cc.cd/compact1> · **Patch notes / 补丁说明**: [compact1/README.md](compact1/README.md)

The original *Compact*: Japanese Rev 2, the Chinese fan translation 0.91, and the WonderSwan Color re-release — three versions (2 MB `.ws` / 4 MB `.wsc`).
初代《COMPACT》：日版 Rev 2、简体汉化 0.91 与 WonderSwan Color 版，共 3 个版本（2MB `.ws` / 4MB `.wsc`）。

### Features / 功能

**English**

- New 6th entry in the system menu: native `ON/OFF` in the Japanese versions (the WSC one shows オン/オフ), and `动画ON/动画OFF` in the Chinese translation
- ON: battle animations play normally; hold **B** during an animation to end it right away into settlement
- OFF: battle animations are skipped entirely — settlement runs through the game's native flow straight back to the map
- Press **A** on the 6th entry to toggle; press **B** to close the menu without toggling
- Toggle state is kept in RAM; no ON/OFF glyphs leak into other menus

**中文**

- 系统菜单新增第 6 项：两个日版为原生 `ON/OFF`（WSC 版显示 オン/オフ），汉化版为 `动画ON/动画OFF`
- ON：战斗动画正常播放；动画中按住 **B** 立即结束动画进入结算
- OFF：完全不进入战斗动画，按原版结算流程直接回地图
- 菜单第 6 项按 **A** 切换，按 **B** 只关闭菜单不切换
- 开关状态保存在 RAM；其他菜单不会残留 ON/OFF 字形

> Chinese-translation code table courtesy of **断空零** ([bilibili](https://space.bilibili.com/3747501796494245)). / 感谢 **断空零** 提供码表。

### Supported ROMs / 支持的 ROM（CRC32: original → patched / 原版 → 打补丁后）

| ROM | Original | Patched (V1) |
|---|---|---|
| Japanese Rev 2 (2MB WS) · 日版 Rev2 | 7021D54F | D025E529 |
| Chinese 0.91 (2MB WS) · 汉化版 0.91 | 80CD2F14 | 4BCE3EA0 |
| WonderSwan Color Japanese (4MB) · WSC 日版 | 16E0D929 | B85158D3 |

The WSC version's battle animation runs in two stages and gets a dedicated pre-skip; a dialog box overlapping the animation during its first second is an original-game issue, not introduced by the patch.
WSC 版战斗动画分两段，补丁做了专门的预跳过；战斗动画开始约 1 秒内对话框可能覆盖在动画上，这是原版自身的问题，不是补丁引入。

Full patch notes / 完整补丁说明: [compact1/README.md](compact1/README.md)

---

## Super Robot Wars Compact 2 (WonderSwan) · 超级机器人大战COMPACT 2 — V1

**Patch page / 补丁页**: <https://srw.cc.cd/compact2> · **Patch notes / 补丁说明**: [compact2/README.md](compact2/README.md)

Covers the three-part game — Part 1 *Chijou Gekidou Hen*, Part 2 *Uchuu Gekishin Hen*, Part 3 *Ginga Kessen Hen* — in Japanese and Chinese fan translations, six versions in total (4 MB `.ws` / `.wsc`).
覆盖三部曲全部作品：第1部·地上激動編 / 第2部·宇宙激震編 / 第3部·銀河決戦篇，日版与汉化版共 6 个版本（4MB `.ws` / `.wsc`）。

### Features / 功能

**English**

- New 6th entry `ON/OFF` in the system menu, rendered with the game's own native font (height and spacing match the other entries)
- ON: battle animations play normally; hold **B** during an animation to end it right away and go into settlement
- OFF: all battle animations are skipped by default — battle goes straight to settlement and back to the map
- Press **A** on the 6th entry to toggle and close the menu cleanly; press **B** to close without toggling
- The toggle state is kept in RAM: reopening the menu shows the current state, and no ON/OFF glyphs leak into other menus

**中文**

- 系统菜单第 6 项显示原生 `ON / OFF`（用游戏原生字体渲染，字高字距与其他项一致）
- ON：战斗动画正常播放；动画中按住 **B** 立即结束当前动画进入结算
- OFF：默认跳过全部战斗动画，直接结算并回到地图
- 第 6 项按 **A**：切换 ON/OFF 并干净关闭菜单；按 **B**：只关闭菜单，不切换
- 开关状态保存在 RAM：重开菜单显示当前状态，其他菜单不会出现 ON/OFF 字形残留

### Supported ROMs / 支持的 ROM（CRC32: original → patched / 原版 → 打补丁后）

| ROM | Original | Patched (V1) |
|---|---|---|
| Part 1 Japanese · 日版第1部 `Compact_2_1 Rev1` | 782877BC | B90AEDEF |
| Part 2 Japanese · 日版第2部 `Compact_2_2 Rev4` | ECBB46DE | 4F7EC0DE |
| Part 3 Japanese · 日版第3部 `Compact_2_3 Rev2` | 0B0F8981 | 0BEB9A34 |
| Part 1 Chinese · 汉化版「地上激震篇 v1.5汉化版」 | BE3CFC94 | 650C5F51 |
| Part 2 Chinese · 汉化版「宇宙激震篇 v1.2汉化版」 | 28EEF4E7 | 404D31D0 |
| Part 3 Chinese · 汉化版「银河决战篇 v1.4汉化版」 | 13D961B2 | 227DA01F |

The page identifies ROMs by CRC32; ROMs already patched (output CRC) are recognized as "already patched" and never written twice.
页面按 CRC32 自动识别；已是输出 CRC 的 ROM 会被识别为“已打补丁”，不会重复写入。

Full patch notes (address tables for both engine families, verification) / 完整补丁说明（两个引擎家族的地址表、校验）: [compact2/README.md](compact2/README.md)

---

## Repository / 仓库结构

```
├── README.md        ← this page / 本页（站点主页）
├── CNAME            ← custom domain / 自定义域名 srw.cc.cd
├── srwa/            Super Robot Wars A · 超级机器人大战A
│   ├── index.html   online patcher (20 embedded packages, zh/ja UI) / 在线补丁工具
│   ├── README.md    reverse-engineering notes V5 / 逆向解析笔记 V5
│   ├── build_rom/   local build scripts build_rom_{cn,jp,rc,le,db}_v1…v5.py (capstone-verified) / 本地构建脚本
│   └── tools/emu/   debugging environment: mGBA GDB harness / 调试环境
├── srwr/            Super Robot Wars R · 超级机器人大战R
│   ├── index.html   online patcher (XDF1 diff format) / 在线补丁工具
│   ├── README.md    reverse-engineering notes V1 / 逆向解析笔记 V1
│   ├── build_rom/   build_rom.py (3-ROM build + self-check) / 构建脚本
│   └── tools/emu/   same as above / 同上
├── compact1/        Super Robot Wars Compact 1 · 超级机器人大战COMPACT 1 (WonderSwan)
│   ├── index.html   online patcher (3 versions, zh/ja UI) / 在线补丁工具
│   ├── README.md    patch notes V1 / 补丁说明 V1
│   └── build_rom/   build_rom.py (3-ROM build, MD5-verified) / 构建脚本
└── compact2/        Super Robot Wars Compact 2 · 超级机器人大战COMPACT 2 (WonderSwan)
    ├── index.html   online patcher (6 versions, zh/ja UI) / 在线补丁工具
    ├── README.md    patch notes V1 (both engine families) / 补丁说明 V1
    └── build_rom/   build_rom.py (6-ROM build, MD5-identified) / 构建脚本
```

Each game lives in its own folder; new titles are added as new folders and a row in the catalog above.
每个游戏一个独立目录；后续新增作品即新增目录，并在上方目录表中加一行。

## Technical notes / 技术说明

The patchers are single-file, pure front-end HTML: patch data is embedded as XOR diffs + deflate, verified with source/target CRC32 in both directions, and decompressed with the browser-native `DecompressionStream('deflate-raw')`. Local build scripts produce byte-identical ROMs to the online tools.

补丁工具为纯前端单文件 HTML：补丁数据以 XOR 差分 + deflate 内嵌，源/目标 CRC32 双向校验，用浏览器原生 `DecompressionStream('deflate-raw')` 解压；本地构建脚本与在线工具产出逐字节相同的 ROM。

---

Made by **lcdyk** · Tested by **Lily** / 制作：lcdyk · 测试：Lily
