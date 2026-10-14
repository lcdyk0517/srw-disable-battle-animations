# SRW Animation Skip Patches · 超级机器人大战 动画跳过补丁

Battle animation skip patches for the **Super Robot Wars** series (スーパーロボット大戦).
**For games in the series that don't let you skip battle animations — we add it.** Every patch is applied in your browser: drop in a ROM, get a patched ROM back. Nothing to install.

为**超级机器人大战**系列作品添加**战斗动画跳过**功能：原作跳不了动画的，用 ROM 补丁给它加上。补丁页在浏览器里拖入 ROM 即可完成，无需安装任何工具。

## Patch Catalog / 补丁目录

| Game / 游戏 | Version / 版本 | Patch page / 补丁页 |
|---|---|---|
| Super Robot Wars A (GBA) · 超级机器人大战A | V5 (2026-10-13) | **<https://srw.cc.cd/srwa>** |
| Super Robot Wars R (GBA) · 超级机器人大战R | V1 (2026-10-07) | **<https://srw.cc.cd/srwr>** |

*This catalog keeps growing — more titles will be added.*
*收录持续扩充中，更多作品陆续添加。*

---

## How to use / 使用方法

1. Open the patch page of your game / 打开对应游戏的补丁页
2. Drop your GBA ROM onto the page (or click to choose a file) / 把 GBA ROM 拖入页面（或点击选择文件）
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

## Repository / 仓库结构

```
├── README.md        ← this page / 本页（站点主页）
├── CNAME            ← custom domain / 自定义域名 srw.cc.cd
├── srwa/            Super Robot Wars A · 超级机器人大战A
│   ├── index.html   online patcher (20 embedded packages, zh/ja UI) / 在线补丁工具
│   ├── README.md    reverse-engineering notes V5 / 逆向解析笔记 V5
│   ├── build_rom/   local build scripts build_rom_{cn,jp,rc,le,db}_v1…v5.py (capstone-verified) / 本地构建脚本
│   └── tools/emu/   debugging environment: mGBA GDB harness / 调试环境
└── srwr/            Super Robot Wars R · 超级机器人大战R
    ├── index.html   online patcher (XDF1 diff format) / 在线补丁工具
    ├── README.md    reverse-engineering notes V1 / 逆向解析笔记 V1
    ├── build_rom/   build_rom.py (3-ROM build + self-check) / 构建脚本
    └── tools/emu/   same as above / 同上
```

Each game lives in its own folder; new titles are added as new folders and a row in the catalog above.
每个游戏一个独立目录；后续新增作品即新增目录，并在上方目录表中加一行。

## Technical notes / 技术说明

The patchers are single-file, pure front-end HTML: patch data is embedded as XOR diffs + deflate, verified with source/target CRC32 in both directions, and decompressed with the browser-native `DecompressionStream('deflate-raw')`. Local build scripts produce byte-identical ROMs to the online tools.

补丁工具为纯前端单文件 HTML：补丁数据以 XOR 差分 + deflate 内嵌，源/目标 CRC32 双向校验，用浏览器原生 `DecompressionStream('deflate-raw')` 解压；本地构建脚本与在线工具产出逐字节相同的 ROM。

---

Made by **lcdyk** · Tested by **Lily** / 制作：lcdyk · 测试：Lily
