# SRW Compact 2 跳过动画 Hack 说明（V1 · 六版本定版）

> 补丁正式名称：**跳过动画 V1**
> 制作：**lcdyk**
> 本文覆盖 Compact 2 第 1/2/3 部日版与三个汉化版，共 6 个受支持版本。

## 1. 功能定义（V1）

- 系统菜单第 6 项显示原生英文 **ON / OFF**。
- **ON**：战斗动画正常播放；动画中按住 **B** 可立即结束当前动画进入结算。
- **OFF**：默认跳过全部战斗动画，直接结算并回到地图。
- 第 6 项按 **A**：切换 ON/OFF 并干净关闭菜单；按 **B**：只关闭菜单，不切换。
- 开关状态保存在 RAM，重新打开菜单会显示当前状态。
- 其他菜单不会出现 ON/OFF 字形残留。

两条战斗路径的共同点是“跳过动画”，区别只是 ON 保留动画并允许 B 跳过，OFF 从战斗开始就跳过：

```
ON  : 战斗动画正常播放 ──按住 B──> 结束动画 ──> 结算
OFF : 战斗开始 ──> 直接结算（无动画）
```

## 2. 支持版本与输出文件

文件大小均为 4,194,304 字节（4MB）。

| 键 | 页面显示版本 | 源文件 | 输出文件 | 源 MD5 | 输出 MD5 | 源 CRC32 → 输出 CRC32 |
|---|---|---|---|---|---|---|
| 1j | `Compact_2_1 Rev1` | `Super Robot Taisen Compact 2 - Dai-1-bu - Chijou Gekidou Hen (Japan).ws` | `Super Robot Taisen Compact 2 - Dai-1-bu - Chijou Gekidou Hen (Japan)(Skip).ws` | `af355adec937a9db1d447980bf85aa2e` | `981a72fad7c058a6312f12b36d146992` | `782877BC → B90AEDEF` |
| 2j | `Compact_2_2 Rev4` | `Super Robot Taisen Compact 2 - Dai-2-bu - Uchuu Gekishin Hen (Japan) (Rev 4).ws` | `Super Robot Taisen Compact 2 - Dai-2-bu - Uchuu Gekishin Hen (Japan) (Rev 4)(Skip).ws` | `bb1cf0d7237d7ae2c8aac562fc62906d` | `7789c3189adac3ee9183eb60443befa6` | `ECBB46DE → 4F7EC0DE` |
| 3j | `Compact_2_3 Rev2` | `Super Robot Taisen Compact 2 - Dai-3-bu - Ginga Kessen Hen (Japan) (Rev 2).ws` | `Super Robot Taisen Compact 2 - Dai-3-bu - Ginga Kessen Hen (Japan) (Rev 2)(Skip).ws` | `44f63dcb11c916df900a128a6f2e3839` | `cca7150ee0136c7c2e2b13f15198b08d` | `0B0F8981 → 0BEB9A34` |
| 1h | `地上激震篇 名称修复版` | `第2次机器人大战-地上激震篇_汉化版.wsc` | `第2次机器人大战-地上激震篇_汉化版_跳过动画.ws` | `440f1eb64702f5b3b7777c6af35a6c2c` | `d1d101bf43e8b2513583d69d375a88e9` | `11DDBB87 → CAED1842` |
| 2h | `宇宙激震篇 名称剧情补全版` | `第2次机器人大战-宇宙激震篇_汉化版.wsc` | `第2次机器人大战-宇宙激震篇_汉化版_跳过动画.ws` | `d3ecc55cda50f98dc7cdc1b0708b0e90` | `22c13214c958e0f36d5abbbe1f6eef45` | `75AFC3F0 → 1D0C06C7` |
| 3h | `银河决战篇 V1.3汉化版` | `第2次机器人大战-银河决战篇_汉化版.wsc` | `第2次机器人大战-银河决战篇_汉化版_跳过动画.ws` | `725b2f61448eb7ed8a8cb3ece05366ec` | `aae713dae3f413c4c64dcee0ccc485c1` | `42BEFC0E → 425AEFBB` |

页面和构建器都只接受上表的源 MD5；已经是输出 MD5 的文件会被识别为“已打补丁”，不会重复写入。

## 3. 两个引擎家族

六个版本分成两套地址布局：

| 家族 | 版本 | 战斗补丁区 | 菜单补丁区 |
|---|---|---|---|
| C2-1 引擎 | 1j、1h | bank `0x3E`：`0x3ED0A5` / `0x3EFC20` / `0x3EFCA0` | bank `0x3F`：`0x3FE100` / `0x3FE180` / `0x3FE260` / `0x3FF600` |
| C2-2/C2-3 引擎 | 2j、3j、2h、3h | 空闲区：`0x3C8000` 或 `0x3CB54C` | bank `0x3F`：`0x3FF000` / `0x3FF100` / `0x3FF400` / `0x3FF600` |

所有 hook 都用同 bank 的 `E9` near jump 或 far `lcall` 到固定 bank `0xF000`，不把可变 bank 段值写死到战斗代码里。

## 4. C2-1 引擎（1j / 1h）

### 4.1 菜单地址

| 地址 | 长度 | 内容 |
|---|---:|---|
| `0x3528E7` | 2B | 菜单绘制调用 1 的 far 地址：`F000:E260`（wrapperA） |
| `0x352A03` | 2B | 菜单绘制调用 2 的 far 地址：`F000:E260`（wrapperA） |
| `0x352AF1` | 4B | 第 6 项标签调用从 `5000:0068` 改为 `F000:F600`（原生 ON/OFF wrapper） |
| `0x35F6D4`（1j）/ `0x35F95C`（1h） | 8B | 原生 ON/OFF 字符串（见第 6 节） |
| `0x36000E` | 2B | 系统菜单条目帧指针：`0xE920` |
| `0x36E920` | 256B | 9×14 扩展帧（原生 9×12 插入两行） |
| `0x3FB3BD` | 3B | 菜单输入 hook：`E9 → 0x3FE100` |
| `0x3FE100` | 66B | M5：六重门控 + `XOR [0x474],1` + 原生取消/关闭链 |
| `0x3FE180` | 70B | WRITE：按 `[0x474]` 选 ON/OFF 字模写入 `0x3C00` |
| `0x3FE1C6` | 128B | 自定义 4-plane 字模（O+N / O+F 两套 64B 单元） |
| `0x3FE246` | 16B | 字模字符串索引表 |
| `0x3FE260` | 26B | wrapperA：绘制后调用 WRITE，补 `[0x383]=6`；非系统菜单跳清理 |
| `0x3FE280` | 24B | 清 `0x3C00` 字形，防止泄漏到其他菜单 |
| `0x3FF600` | 81B | 原生 ON/OFF wrapper（fixed bank） |

菜单门控值（M5）：

```
[0x373] == 0x03AA     系统菜单身份
[0x383] == 6          当前第 6 项
[0x385] == 5          光标在第 6 行（0 基）
[0x264] == 0x0B       菜单输入态
[0x3AA] == 0x00DB     系统菜单独有掩码
[0x13D] & 0x0400      真实 A 按下（拦截 attract 演示的模拟按键）
```

六门全过才 `XOR byte [0x474],1`，然后走原生 B 收尾链；任一失败按原生 `mov al,[si]` 路径继续。

### 4.2 战斗地址

| 地址 | 长度 | 内容 |
|---|---:|---|
| `0x3EB2B6` | 5B | hook1：`E9 → 0x3EFC40`（d1 分发） |
| `0x3EB410` | 5B | hook2：`E9 → 0x3EFC58`（d2 分发） |
| `0x3ED0A5` | 130B | V2 瞬切例程（OFF） |
| `0x3EFC20` | 20B | mode11 补丁（V3 原样） |
| `0x3EFC40` | 21B | d1：`test [0x474],1`；1→V2，0→V1PATCH |
| `0x3EFC58` | 21B | d2：`test [0x474],1`；1→mode11，0→原生 hook2+5 |
| `0x3EFCA0` | 140B | V1PATCH（ON）：B 键扫描，尾 `E9` 回 hook1+8 |

- 开关：`0=ON`，`1=OFF`。
- OFF 时 d1 直接进 V2，清空动画队列并切到结算；d2 进 mode11 原生结算补丁。
- ON 时 d1 进 V1PATCH，战斗动画照常；V1PATCH 在动画段检查 B 键，命中后结束动画。
- B 键不是读普通键镜像，而是直接操作 I/O `0xB5`：写 `0x40` 选 buttons 行，读回后 `test al,8`。这是因为真实战斗任务链会绕过系统按键扫描器。

V1PATCH 首部门的判断：

```asm
cmp byte ss:[0x134],0x10   ; 只在演出段响应，避免过渡帧误触
jne .orig
mov al,0x40                ; 选 buttons 行
out 0xB5,al
in  al,0xB5
test al,8                  ; B 键 bit3
jz  .orig
...
```

尾部的 `E9` 必须保留；它负责跳回 hook1 后面的原生指令。旧版曾把 140B 截成 137B，直接导致 ON 路径白屏。

## 5. C2-2 / C2-3 引擎（2j / 3j / 2h / 3h）

### 5.1 菜单地址（四个版本相同）

| 地址 | 长度 | 内容 |
|---|---:|---|
| `0x3528A7` | 2B | 菜单绘制调用 1 的 far 地址：`F000:F400`（wrapperA） |
| `0x3529C3` | 2B | 菜单绘制调用 2 的 far 地址：`F000:F400`（wrapperA） |
| `0x352AB1` | 4B | 第 6 项标签调用从 `5000:0068` 改为 `F000:F600` |
| `0x35F8F4`（2j）/ `0x35FFBD`（2h）/ `0x35F9CC`（3j、3h） | 8B | 原生 ON/OFF 字符串 |
| `0x36000E` | 2B | 系统菜单条目帧指针：`0xF000` |
| `0x36F000` | 256B | 9×14 扩展帧 |
| `0x3FF000` | 66B | M5：六重门控 + `XOR [0x700],1` + 原生关闭 |
| `0x3FF042` | 6B | `call 0x3FF100` 后跳原生关闭链 |
| `0x3FF100` | 47B | WRITE：按 `[0x700]` 选字模写 `0x3C00` |
| `0x3FF140` | 640B | 4-plane 字模表（O+N / O+F，各 320B） |
| `0x3FF400` | 26B | wrapperA：绘制后调用 WRITE、补 `[0x383]=6` |
| `0x3FF420` | 24B | 清 `0x3C00` 字形 |
| `0x3FF500` | 10B | 菜单关闭收尾：恢复 `[0x264]=2` 并刷新第 6 项 |
| `0x3FF600` | 81B | 原生 ON/OFF wrapper |

菜单 hook：

| 版本 | 关闭 hook | M5 hook |
|---|---|---|
| 2j / 2h | `0x3FB71E → 0x3FF500` | `0x3FB74D → 0x3FF000` |
| 3j / 3h | `0x3FB7F4 → 0x3FF500` | `0x3FB823 → 0x3FF000` |

门控与 C2-1 相同，只是 XOR 的开关变量换成 `[0x700]`。

### 5.2 战斗地址

四个版本的布局相同，只是空闲区基址不同：

| 内容 | 2j / 2h | 3j / 3h |
|---|---|---|
| hook1 | `0x3C2C12 → 0x3C8000` | `0x3C6512 → 0x3CB54C` |
| hook2 | `0x3C2D86 → 0x3C8020` | `0x3C6686 → 0x3CB56C` |
| d1 | `0x3C8000` (21B) | `0x3CB54C` (21B) |
| d2 | `0x3C8020` (21B) | `0x3CB56C` (21B) |
| mode11 | `0x3C8040` (20B) | `0x3CB58C` (20B) |
| V2 瞬切 | `0x3C8080` (130B) | `0x3CB5CC` (130B) |
| V1PATCH | `0x3C8120` (140B) | `0x3CB66C` (140B) |

开关变量为 `[0x700]`，`0=ON`，`1=OFF`。

- d1：`test [0x700],1`。=1（OFF）跳到 V1PATCH+0x12，跳过 B 键检查；=0（ON）进入 V1PATCH 正常扫描 B。
- d2：`test [0x700],1`。=1（OFF）进 mode11 瞬切；=0（ON）回原生 `hook2+5`。
- V1PATCH/V2 的字节来自 C2-1 已验证版本，只重算 near 跳转目标；尾 `E9` 回 hook1+8。
- 两种家族的 V1PATCH 都保留 140B 完整长度。

## 6. 原生 ON/OFF 文本

六个版本都使用游戏原生 8×16 文本渲染器，不再使用 5×7 自绘半高字形。

原生字体码：

| 字符 | 码 |
|---|---|
| `O` | `0x91` |
| `N` | `0x90` |
| `F` | `0x88` |
| 结束 | `0xFF` |

字符串布局：

```
ON  : 91 90 FF
OFF : 91 88 88 FF
```

OFF 字符串显式写入 `FF` 终止符，避免渲染器越过字符串末尾继续读取后方的空闲字节或其他文本数据。六个版本都按 `ON=91 90 FF FF`、`OFF=91 88 88 FF` 的 8 字节块写入（ON 与 OFF 之间保留一个 `FF` 间隔）。

六个版本的实际位置：

| 版本 | 字符串地址 |
|---|---|
| 1j | `0x35F6D4` |
| 1h | `0x35F95C` |
| 2j | `0x35F8F4` |
| 2h | `0x35FFBD` |
| 3j / 3h | `0x35F9CC` |

`0x3FF600` 的原生 wrapper 流程：

1. `push ds; push 0; pop ds`，切回系统数据段。
2. `lcall 5000:0068` 绘制游戏原生菜单标签。
3. 清 `0x3C00` 的旧自定义字形区（`0xA0` words）。
4. 光标地址设为 `[0x386] + 0x3C0`，指向第 6 行。
5. 设置 `[0x20A]=0`、`[0x366]=1`、`ES=0x3000`。
6. 按开关变量选 ON 或 OFF 字符串，写入 `[0x35D]`。
7. C2-1 调 `5000:2664`，C2-2/3 调 `5000:2624` 绘制原生文本。

因此 ON/OFF 的字高、字距、高亮和原生菜单一致，不会出现半高或字距被拉开的问题。

## 7. 菜单第 6 项与残留防护

- 系统菜单描述符 `0x360008` 的原生条目数保持 7 项，不改条目数；只把帧指针从原生帧换成 9×14 扩展帧。
- 扩展帧表头为 `09 00 0E 00`（9 列 × 14 行），在原生 9×12 的第 4/5 行位置插入两行，让第 6 项有完整高度。
- 第 6 项文字由 `0x3FF600` wrapper 覆盖绘制，不依赖原标签表里是否有文本。
- 菜单绘制后 wrapperA 会调用 WRITE 写自定义字形；原生 wrapper 绘制前会清 `0x3C00`。进入非系统菜单时 wrapperA 跳到清字形例程，因此其他菜单不会看到 ON/OFF 残留。
- C2-2/3 另有菜单关闭 hook：关闭时执行 `[0x264]=2` 并再次调用 WRITE，保证重新打开菜单时状态立即正确。

## 8. 构建

### 8.1 构建六个 ROM

```bash
python compact2/build_rom/build_rom.py "<源 ROM>" [输出路径] [--force]
```

- 只读源 ROM，所有补丁字节内嵌在脚本的 `VARIANTS` 中。
- 按源 MD5 自动识别版本；已打补丁的 ROM 会提示并退出。
- 不指定输出路径时，默认写到源 ROM 同目录并使用本文第 2 节的正式文件名。
- `--force` 才允许覆盖已存在的不同文件；若输出已存在且 MD5 一致则直接跳过。
- `VARIANTS` 的每个 `regions` 项都是 `(文件偏移, 补丁后字节, 注释)`，注释说明该地址写入的内容；这是地址表的权威来源。
- 当前脚本每个版本有 21（C2-1）或 23（C2-2/3）个区域，全部区域写完后会校验输出 MD5，不匹配则拒绝写出。

重新生成六个输出：

```bash
python compact2/build_rom/build_rom.py "Super Robot Taisen Compact 2 - Dai-1-bu - Chijou Gekidou Hen (Japan).ws" --force
python compact2/build_rom/build_rom.py "Super Robot Taisen Compact 2 - Dai-2-bu - Uchuu Gekishin Hen (Japan) (Rev 4).ws" --force
python compact2/build_rom/build_rom.py "Super Robot Taisen Compact 2 - Dai-3-bu - Ginga Kessen Hen (Japan) (Rev 2).ws" --force
python compact2/build_rom/build_rom.py "第2次机器人大战-地上激震篇_汉化版.wsc" --force
python compact2/build_rom/build_rom.py "第2次机器人大战-宇宙激震篇_汉化版.wsc" --force
python compact2/build_rom/build_rom.py "第2次机器人大战-银河决战篇_汉化版.wsc" --force
```

### 8.2 重新生成网页补丁

由本仓库外的生成器脚本完成（生成器未随仓库发布，生成结果已提交为 `index.html`）：

1. 按 MD5 校验六个源 ROM 和六个输出 ROM；
2. 现场计算 XOR 差分并用 raw deflate 压缩；
3. 生成 `XDF1` 数据（源 CRC32、输出 CRC32、大小、压缩长度、差分）；
4. 写入 `patch_ws.html`（即仓库内的 `compact2/index.html`）。

## 9. 网页补丁

`index.html`（原 `patch_ws.html`）支持六个版本：

- 中文 / 日本語界面切换；
- 版本区只有一个标题“本补丁适配以下版本”，不再区分日版/汉化版；
- 页面显示六个受支持版本标签（`Compact_2_1 Rev1`、`Compact_2_2 Rev4`、`Compact_2_3 Rev2`、`地上激震篇 名称修复版`、`宇宙激震篇 名称剧情补全版`、`银河决战篇 V1.3汉化版`）；
- 页面常驻说明“战斗动画跳过 V1”：菜单第 6 项 ON/OFF，ON=正常播放动画+按 B 结束，OFF=默认跳过全部战斗动画；制作 lcdyk；
- 拖入源 ROM 后按 CRC32 自动识别版本；
- 校验源 CRC32 → 解压差分 → XOR 写入 → 校验输出 CRC32 和 MD5；
- 下载文件名严格使用第 2 节的输出文件名；
- 已打补丁的 ROM 会显示“已是跳过动画版”，不会再次应用。

XDF1 格式：

```
"XDF1"
u32 源 CRC32
u32 输出 CRC32
u32 输出大小
u32 压缩数据长度
raw-deflate(XOR 差分)
```

## 10. 校验与验收

### 10.1 已完成的自动校验

- 六个 `build_rom.py` 区域表逐一回放，输出 MD5 与第 2 节全部一致；
- 六个 `XDF1` 页面差分逐一解码回放，输出 CRC32/MD5 与第 2 节全部一致；
- 六个版本的 ON/OFF 字符串区域都显式包含 `FF` 终止符（`ON=91 90 FF FF`、`OFF=91 88 88 FF`）；
- 无头浏览器实测：
  - `1j` 源 ROM 识别为 `Compact_2_1 Rev1`，页面应用后输出 `B90AEDEF / 981a72fad7c058a6312f12b36d146992`，文件名正确；
  - `1h` 源 ROM 识别为 `地上激震篇 名称修复版`，页面应用后输出 `CAED1842 / d1d101bf43e8b2513583d69d375a88e9`，文件名正确；
  - `2h` 源 ROM 识别为 `宇宙激震篇 名称剧情补全版`，页面正确显示“▶ 准备应用补丁”、V1 功能说明和“制作 lcdyk”；
  - 日本語界面切换、已打补丁识别均正常。

### 10.2 建议的游戏内验收

对六个版本分别执行：

1. 进入系统菜单，确认第 6 项为原生 `ON/OFF`，高度与其他项一致。
2. 设为 ON，进入一场战斗：动画应正常播放；动画中按住 B，应在当前帧结束动画并进入结算。
3. 设为 OFF，进入战斗：不应播放动画，直接结算回地图。
4. 重开菜单：ON/OFF 应与上次设置一致。
5. 进入其他子菜单/地图：不应出现 ON/OFF 字形残留。
6. 检查剧情战斗、敌方回合、反击战：切换值不应被误改。

## 11. 关键地址速查

| 项目 | C2-1（1j/1h） | C2-2/3（2j/3j/2h/3h） |
|---|---|---|
| 开关变量 | `[0x474]` bit0 | `[0x700]` bit0 |
| 菜单输入 hook | `0x3FB3BD` | 2j/2h `0x3FB74D`；3j/3h `0x3FB823` |
| M5 | `0x3FE100` | `0x3FF000` |
| WRITE | `0x3FE180` | `0x3FF100` |
| wrapperA | `0x3FE260` | `0x3FF400` |
| 原生 wrapper | `0x3FF600` | `0x3FF600` |
| 扩展帧 | `0x36E920` | `0x36F000` |
| 战斗 hook1 / hook2 | `0x3EB2B6` / `0x3EB410` | 2j/2h `0x3C2C12` / `0x3C2D86`；3j/3h `0x3C6512` / `0x3C6686` |
| d1 / d2 | `0x3EFC40` / `0x3EFC58` | 基址 / 基址+0x20 |
| V1PATCH | `0x3EFCA0` | 基址+0x120 |
| V2 瞬切 | `0x3ED0A5` | 基址+0x80 |
| mode11 | `0x3EFC20` | 基址+0x40 |
| 战斗基址 | — | 2j/2h `0x3C8000`；3j/3h `0x3CB54C` |
| B 键扫描 | I/O `0xB5` 写 `0x40`，读回 `test al,8` | 同左 |
| 原生文本绘制 | `5000:2664` | `5000:2624` |

## 12. 备注

- ON 路径的 B 跳过只在战斗动画演出段生效（`[0x134]==0x10`），过渡帧和结算帧不会误触。
- OFF 路径不依赖按键，也不要求玩家按住 B。
- 页面补丁和命令行构建器是同一套字节；两者输出 MD5 必须一致。
- 若日后修改任何地址或字节，必须同步更新 `build_rom.py` 的注释、本文第 2 节哈希、`gen_patch_ws.py` 重新生成的页面，并重新跑六版本回放校验。
