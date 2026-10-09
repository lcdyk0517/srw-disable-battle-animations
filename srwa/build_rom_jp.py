# -*- coding: utf-8 -*-
"""
构建 SRW-A 日文原版 菜单动画开关ROM (V1-JP)
# 日版与汉化版代码区100%一致(实测0差异), 全部补丁原样平移; 仅数据区文本/图形不同

功能总览:
  菜单第6项 "动画 ＯＮ/ＯＦＦ" 开关, 按Ａ即时切换:
    FLAG=0   (ＯＮ)  完全原版动画
    FLAG=0xA5(ＯＦＦ) 普攻/反击动画全跳过(原生结算, 不损失伤害)
  动画播放中按住Ｂ → 立即跳过当前动画(原生R+A场景跳过机制)

补丁清单 (cave 顺序编号, 全部经用户实测验证):
  cave1  @0x08076A78+0x00  普攻规划器门控   (站点 0x0802BEB8)
  cave2  @0x08076A78+0x28  普攻黑场门控     (站点 0x0802DBAE + 2×NOP)
  cave3  @0x08076A78+0x48  普攻停靠站门控   (站点 0x0802DBB6) → A5 跳原生完成段 0x0802DC5B
  cave4  @0x080994F4       菜单第6项开关    (站点 0x0802C876 + 项数6 @0x08026BFC)
          切换FLAG后立即同步ＯＮ/ＯＦＦ字符串 + 重绘菜单窗口(即时显示新状态)
  cave5  @0x08099630       反击动画启动门控 (站点 0x0802DE70 + NOP) — A5 改发原生
          无动画结算续行(相位0x18+状态0x19), 伤害在按A前已算完, 选择画面不受影响
  cave6s @0x08099728       B键动画跳过 + 第6项字符串每帧同步 (站点 0x0800225C 键盘读取)
  menu6  @0x08099798       系统菜单条目数组副本(8条, 第8条指向RAM字符串)
  menu6rec@0x080997E0      加高菜单画布记录(h13→15, 左框体+2行) ECD重压缩

站点补丁:
  0x08026BFC 项数5→6 | 0x080A0D92 描述符count 7→8 | 0x080A0D94 itemPtr→menu6
  0x08077E90 样式指针表[0x49B]→menu6rec (偏移mod 2^32回绕)

菜单窗口原理 (GDB实测定案):
  系统菜单 = 描述符@0x080A0D90{flags=0x049B, count, itemPtr}→条目数组(8B/条:
  x,y,调色板,_,串指针)。原数组@0x080A0AEC仅7条(标题y0 + y2x18后缀 + 5菜单项y2-y10),
  第6行(y12)无条目→空白; 项数6补丁只放开光标不产生文本。
  画布(ECD压缩资源): 全宽w30×h13, 左框rows2-12=菜单本体, 右框rows0-4=回合/资金
  信息框。第6项文本画在canvas row13=画布外→加高到15行(框体模板取row5: 左框体+右空白)。
  第6项字符串 = RAM@0x0203FF10(与FLAG同属0x0203FF00空闲区):
    FLAG=0→ＯＮ=826E 826D, FLAG=0xA5→ＯＦＦ=826E 8265 8265
  编码规律: 字库拉丁区连续排布 字母=0x8260+序号 (826F=Ｐ 826E=Ｏ 实视"PO"确认)

ECD压缩格式 (完全破解, 解码器/编码器均有, 回验780/780+900/900):
  窗口1KB@0x3000C30预零, 写指针初值0x3BE, flag字节LSB先: 1=字面量(1字节),
  0=匹配(2字节: off=n1|((n2&0xC0)<<2) 绝对窗口位10bit, len=(n2&0x3F)+3),
  复制时窗口同步更新(可自引用重叠复制)。记录="ECD"+BE32(SCR头8B)+BE32(流总长)
  +BE16?+BE16(解压尺寸)+"SCR\0"+w+h+LZ流。

FLAG @0x0203FF00: 0xA5 = 动画关(普攻+反击全跳过), 其他(默认0) = 完全原版
洞区原版全零已断言: 0x76A78-0x76B78 / 0x994F4-0x996D1 / 0x99728-0x99840
失败方案与教训见 逆向解析笔记.md §失败记录。
写入: r+b 就地覆盖 run/srwa.gba (mGBA 未运行时), 构建后 capstone 全量自验。
"""
import struct, sys, os
import capstone

ORIG_PATH = r"xxx.gba"
ROM_PATH = r"xxx_patch.gba"

FLAG = 0x0203FF00
STRBUF = FLAG + 0x10            # ＯＮ/ＯＦＦ 字符串缓冲 (与FLAG同属0x0203FF00空闲区)
ON_W0  = 0x6D826E82             # 内存字节 82 6E 82 6D = "ＯＮ"
OFF_W0 = 0x65826E82             # 内存字节 82 6E 82 65 82 65 = "ＯＦＦ"
OFF_W1 = 0x00006582
# FLAG地址定版说明 (2026-10-09):
# 0x0203FF00 = 上午版通宵实测位置(多场战斗+菜单存档均正常), 维持不动。
# 曾短暂迁往IWRAM 0x03004200 — 实测该处属于存档工作缓冲区:
#   菜单存档/新游戏建档/回合自动存档时游戏读写该区, FLAG字节污染存档镜像→写存档即冻结。
CAVE = 0x08076A78          # 256B 零填充区

H = lambda *v: struct.pack("<%dH" % len(v), *v)
W = lambda *v: struct.pack("<%dI" % len(v), *v)

def bl_enc(src, dst):
    off = (dst - (src + 4)) >> 1
    assert -0x400000 <= off < 0x400000, "bl range: 0x%X->0x%X" % (src, dst)
    return H(0xF000 | ((off >> 11) & 0x7FF), 0xF800 | (off & 0x7FF))

def b_enc(addr, dst, cond=None):
    """cond: None/0xE=无条件b, 0=beq 1=bne 3=blo ..."""
    off = (dst - (addr + 4)) >> 1
    assert -0x1000 <= off < 0x1000, "b range: 0x%X->0x%X" % (addr, dst)
    if cond is None or cond == 0xE:
        return struct.pack("<H", 0xE000 | (off & 0x7FF))
    return struct.pack("<H", 0xD000 | (cond << 8) | (off & 0xFF))

def ldrpc_enc(addr, reg, litaddr):
    pc_al = (addr + 4) & ~3
    imm = litaddr - pc_al
    assert 0 <= imm < 1024 and imm % 4 == 0, "ldr lit: 0x%X -> 0x%X" % (addr, litaddr)
    return struct.pack("<H", 0x4800 | (imm >> 2) | ((reg & 7) << 8))

def put(rom, romaddr, data):
    off = romaddr - 0x08000000
    assert 0 <= off < len(rom), hex(romaddr)
    rom[off:off+len(data)] = data

# ---------------- 代码洞 ----------------
# 每个洞: (基地址偏移, [(偏移, 字节)], 验证信息)
ORIG = open(ORIG_PATH, "rb").read()   # menu6rec解码需要, 提前加载
caves = {}

# ===== cave1 @+0x00: 规划器 0x10->0x11 门控 =====
# 入参 r0=演出标志([状态+0x4E]); 语义: 置 r5=0x11 当且仅当 FLAG==A5 或 r0==0
# r0!=0 且 FLAG!=A5 -> 不置(跳到 0x0802BEBF = bl 0x800EA98)
o = CAVE
c1 = b""
c1 += H(0xB510)                                  # +00 push {r4,lr}
c1 += H(0x2800)                                  # +02 cmp r0,#0
c1 += b_enc(o+0x04, o+0x08, 1)                   # +04 bne +0x08   (r0!=0 -> 查FLAG)
c1 += H(0xBD10)                                  # +06 pop {r4,pc} (r0==0: 原版即置0x11)
c1 += ldrpc_enc(o+0x08, 4, o+0x20)               # +08 ldr r4,=FLAG
c1 += H(0x7824)                                  # +0A ldrb r4,[r4]
c1 += H(0x2CA5)                                  # +0C cmp r4,#0xA5
c1 += b_enc(o+0x0E, o+0x14, 1)                   # +0E bne +0x14   (FLAG!=A5: 不置)
c1 += H(0xBD10)                                  # +10 pop {r4,pc} (FLAG==A5: 置)
c1 += H(0x0000)                                  # +12 pad
c1 += H(0xBC10)                                  # +14 pop {r4}
c1 += H(0xB001)                                  # +16 add sp,#4
c1 += ldrpc_enc(o+0x18, 3, o+0x24)               # +18 ldr r3,=0x0802BEBF
c1 += H(0x4718)                                  # +1A bx r3
c1 += H(0x0000, 0x0000)                          # +1C pad
c1 += W(FLAG)                                    # +20
c1 += W(0x0802BEBF)                              # +24
caves["cave1"] = (o, c1)

# ===== cave2 @+0x28: 黑场淡入淡出门控 =====
# FLAG==A5 -> 什么都不做; 否则复刻 movs r0,#0/r1,#0/r2,#1E/r3,#14; bl 8B28; bl 8A94
o = CAVE + 0x28
c2  = H(0xB510)                                  # +00 push {r4,lr}
c2 += ldrpc_enc(o+0x02, 4, o+0x1C)               # +02 ldr r4,=FLAG
c2 += H(0x7824)                                  # +04 ldrb r4,[r4]
c2 += H(0x2CA5)                                  # +06 cmp r4,#0xA5
c2 += b_enc(o+0x08, o+0x1A, 0)                   # +08 beq +0x1A   (跳过黑场)
c2 += H(0x2000, 0x2100, 0x221E, 0x2314)          # +0A..+0x10 movs r0..r3
c2 += bl_enc(o+0x12, 0x08008B28)                 # +12
c2 += bl_enc(o+0x16, 0x08008A94)                 # +16
c2 += H(0xBD10)                                  # +1A pop {r4,pc}
c2 += W(FLAG)                                    # +1C
caves["cave2"] = (o, c2)

# ===== cave3 @+0x48: 停靠站门控 =====
# FLAG==A5 -> 0x0802DC5B (原生完成段, 定版3补丁行为)
# 否则复刻原版: movs r0,#0x11; bl 0x800CD8C; -> 0x0802DC89 (原版 b 0x802DC88)
o = CAVE + 0x48
c3  = H(0xB510)                                  # +00 push {r4,lr}
c3 += ldrpc_enc(o+0x02, 4, o+0x20)               # +02 ldr r4,=FLAG
c3 += H(0x7824)                                  # +04 ldrb r4,[r4]
c3 += H(0x2CA5)                                  # +06 cmp r4,#0xA5
c3 += b_enc(o+0x08, o+0x18, 0)                   # +08 beq +0x18
c3 += H(0x2011)                                  # +0A movs r0,#0x11
c3 += bl_enc(o+0x0C, 0x0800CD8C)                 # +0C bl 0x800CD8C
c3 += H(0xBC10)                                  # +10 pop {r4}
c3 += H(0xB001)                                  # +12 add sp,#4
c3 += ldrpc_enc(o+0x14, 3, o+0x28)               # +14 ldr r3,=0x0802DC89
c3 += H(0x4718)                                  # +16 bx r3
c3 += H(0xBC10)                                  # +18 pop {r4}  (skip 路径)
c3 += H(0xB001)                                  # +1A add sp,#4
c3 += ldrpc_enc(o+0x1C, 3, o+0x2C)               # +1C ldr r3,=0x0802DC5B
c3 += H(0x4718)                                  # +1E bx r3
c3 += W(FLAG)                                    # +20
c3 += H(0x0000, 0x0000)                          # +24 pad
c3 += W(0x0802DC89)                              # +28
c3 += W(0x0802DC5B)                              # +2C
caves["cave3"] = (o, c3)


# ===== cave4 @0x080994F4: 系统菜单第6项(动画开关) =====
# (独占0x080994F4区, 原版全零已断言)
# r0=光标: 0-4 -> pop 返回 0x0802C87A (原版查表分发继续)
#          5   -> FLAG 0xA5<->0 切换 + 发0x58 + 重绘菜单窗口(新状态立即显示) + 跳 0x0802C965
#          >5  -> 发0x58 + 重绘 + 跳 0x0802C965 (复刻原版越界路径+重绘, 光标限6不会到达)
# V4.1: 切换后调 0x800C89C(0,1,0x1B,0) = 菜单窗口#27重绘 (与0x0802BFD8开窗调用同参),
#       cave6s每帧已把ＯＮ/ＯＦＦ字节写入STRBUF, 重绘即显示新状态, 菜单保持打开
o = 0x080994F4
c4  = H(0xB510)                                  # +00 push {r4,lr}
c4 += H(0x2805)                                  # +02 cmp r0,#5
c4 += b_enc(o+0x04, o+0x0A, 3)                   # +04 blo +0x0A  (0-4: 返回走原版分发)
c4 += b_enc(o+0x06, o+0x0C, 0)                   # +06 beq +0x0C  (==5: 切换, 从ldr FLAG起)
c4 += b_enc(o+0x08, o+0x1C, None)                # +08 b   +0x1C  (>5: 不切换)
c4 += H(0xBD10)                                  # +0A pop {r4,pc} -> 0x0802C87A
c4 += ldrpc_enc(o+0x0C, 4, o+0x50)               # +0C ldr r4,=FLAG
c4 += H(0x7821)                                  # +0E ldrb r1,[r4]
c4 += H(0x29A5)                                  # +10 cmp r1,#0xA5
c4 += b_enc(o+0x12, o+0x18, 1)                   # +12 bne +0x18
c4 += H(0x2100)                                  # +14 movs r1,#0    (A5->0 动画开)
c4 += b_enc(o+0x16, o+0x1A, None)                # +16 b +0x1A
c4 += H(0x21A5)                                  # +18 movs r1,#0xA5 (0->A5 动画关)
c4 += H(0x7021)                                  # +1A strb r1,[r4]
# 立即同步STRBUF(每帧cave6s同步在本帧菜单处理之前, 不补写则重绘看到旧串慢一拍)
c4 += ldrpc_enc(o+0x1C, 2, o+0x54)               # +1C ldr r2,=STRBUF
c4 += H(0x2900)                                  # +1E cmp r1,#0
c4 += b_enc(o+0x20, o+0x2C, 0)                   # +20 beq w_on (FLAG=0→ＯＮ)
c4 += ldrpc_enc(o+0x22, 1, o+0x58)               # +22 ldr r1,=OFF_W0
c4 += H(0x6011)                                  # +24 str r1,[r2]
c4 += ldrpc_enc(o+0x26, 1, o+0x5C)               # +26 ldr r1,=OFF_W1
c4 += H(0x6051)                                  # +28 str r1,[r2,#4]
c4 += b_enc(o+0x2A, o+0x34, None)                # +2A b sync_ok
c4 += ldrpc_enc(o+0x2C, 1, o+0x60)               # +2C ldr r1,=ON_W0  (w_on:)
c4 += H(0x6011)                                  # +2E str r1,[r2]
c4 += H(0x2100)                                  # +30 movs r1,#0
c4 += H(0x6051)                                  # +32 str r1,[r2,#4]
c4 += H(0x2058)                                  # +34 movs r0,#0x58  (sync_ok:)
c4 += bl_enc(o+0x36, 0x08003594)                 # +36 bl 0x8003594 (确认音) [4B]
c4 += H(0x2000)                                  # +3A movs r0,#0
c4 += H(0x2101)                                  # +3C movs r1,#1
c4 += H(0x221B)                                  # +3E movs r2,#0x1B (窗口27=系统菜单)
c4 += H(0x2300)                                  # +40 movs r3,#0
c4 += bl_enc(o+0x42, 0x0800C89C)                 # +42 bl 0x800C89C (重绘→立即更新) [4B]
c4 += H(0xBC10)                                  # +46 pop {r4}
c4 += H(0xB001)                                  # +48 add sp,#4
c4 += ldrpc_enc(o+0x4A, 3, o+0x64)               # +4A ldr r3,=0x0802C965
c4 += H(0x4718)                                  # +4C bx r3
c4 += H(0x0000)                                  # +4E pad
c4 += W(FLAG, STRBUF, OFF_W0, OFF_W1, ON_W0)     # +50 池×5
c4 += W(0x0802C965)                              # +64
caves["cave4"] = (o, c4)

# ===== cave5 @0x08099630: 反击动画启动点门控(2026-10-09 干净环境重设计) =====
# 站点: 0x0802DE70 (movs r0,#0x11 + bl 0x800CD8C, 6字节→bl+NOP)
# 实证(2026-10-09 干净基线+17点观察网, 两场反击各命中1次):
#   步19编排器选择阶段逐帧轮询(等玩家输入, 不可跳) → 按A → 本站点发场景0x11
#   → 17秒全屏动画(纯演出; 步19不运行; 伤害已在0x2DE08块算完) → 0x00→0x0E→0x13→结算
#   游戏原生无动画结算段(0x2E0BA): 0x800e2b8(0,-1)→相位0x18→0x800d9d0→0x802574c→
#   0x8030858(0)→发状态0x19→0x8015afc — 与cave3已验证普攻完成段同构
# FLAG=0xA5: 复刻该结算续行(不重复0x2DE08已做的伤害/stores/0x803483c条件调用;
#            不再淡入淡出——0x2DE60已黑场; 引擎淡出是续行式, 二次调用有断链风险)
# FLAG≠0xA5: 原样复刻 movs 0x11 + bl 状态设置器, bx lr返回0x0802DE76(b 0x802e0f2收尾)
# 寄存器: 入口r6=单位结构/r7=战斗状态区0x02006BF0/sb=r7+0x4E/sp帧有效;
#         cave用r0/r1/r4(r4此处为死寄存器——后续仅pop)
# 尾返回教训(v1死循环实证: PC卡+0x2E bx lr): A5路径的bl会覆盖lr,
#         必须push{r4,lr}入口保存, 出口pop{r4};pop{r0};bx r0
C5 = 0x08099630
c5  = H(0xB510)                                  # +00 push {r4,lr}
c5 += ldrpc_enc(C5+0x02, 0, C5+0x40)           # +02 ldr r0,=FLAG
c5 += H(0x7800)                                  # +04 ldrb r0,[r0]
c5 += H(0x28A5)                                  # +06 cmp r0,#0xA5
c5 += b_enc(C5+0x08, C5+0x36, 1)               # +08 bne +0x36 (原版)
c5 += H(0x463C)                                  # +0A mov r4,r7
c5 += H(0x344E)                                  # +0C adds r4,#0x4E (相位字节地址)
c5 += H(0x2101)                                  # +0E movs r1,#1
c5 += H(0x4249)                                  # +10 rsbs r1,r1,#0 (r1=-1)
c5 += H(0x2000)                                  # +12 movs r0,#0
c5 += bl_enc(C5+0x14, 0x0800E2B8)               # +14 bl 0x800e2b8(0,-1)
c5 += bl_enc(C5+0x18, 0x0800D9D0)               # +18 bl
c5 += bl_enc(C5+0x1C, 0x0802574C)               # +1C bl
c5 += H(0x2000)                                  # +20 movs r0,#0
c5 += bl_enc(C5+0x22, 0x08030858)               # +22 bl 0x8030858(0)
c5 += H(0x2019)                                  # +26 movs r0,#0x19
c5 += bl_enc(C5+0x28, 0x0800CD8C)               # +28 bl 发场景状态0x19(原生续行)
c5 += bl_enc(C5+0x2C, 0x08015AFC)               # +2C bl
c5 += H(0xBC10)                                  # +30 pop {r4}
c5 += H(0xBC01)                                  # +32 pop {r0} (取回0x0802DE77)
c5 += H(0x4700)                                  # +34 bx r0 → 0x0802DE76
c5 += H(0x2011)                                  # +36 movs r0,#0x11 (原版)
c5 += bl_enc(C5+0x38, 0x0800CD8C)               # +38 bl 状态设置器
c5 += b_enc(C5+0x3C, C5+0x30, None)            # +3C b +0x30 (共弹出收尾)
c5 += H(0x0000)                                  # +3E pad
c5 += W(FLAG)                                    # +40
caves["cave5"] = (C5, c5)





# ===== cave6s @C6S: 战斗动画B键跳过 + 菜单第6项字符串同步 =====
# B按住且场景==0x12(战斗动画) → 跳过开关=1+键值|=R+A(游戏原生场景跳过)
# +每帧按FLAG同步ＯＮ/ＯＦＦ字符串到STRBUF(菜单第6项显示源, 开机即正确初始化)。
# 移到0x99728区(旧0x99678区后方0x996D2起非零, 无法原地扩展)。
# MAP伤害弹字: 跳过的那场不显示(原生跳过特性), 后续版本再研究
# 寄存器: r4=键值暂存(该站点r4为死寄存器,V3已实测), r0/r1=站点原scratch, r2=洞内临时
C6S = 0x08099728
c6s  = H(0xB500)                                  # +00 push {lr}
c6s += H(0x4604)                                  # +02 mov r4,r0    (保存键值)
c6s += ldrpc_enc(C6S+0x04, 0, C6S+0x48)           # +04 ldr r0,=FLAG
c6s += H(0x7800)                                  # +06 ldrb r0,[r0]
c6s += ldrpc_enc(C6S+0x08, 1, C6S+0x4C)           # +08 ldr r1,=STRBUF
c6s += H(0x28A5)                                  # +0A cmp r0,#0xA5
c6s += b_enc(C6S+0x0C, C6S+0x18, 0)               # +0C beq off
c6s += ldrpc_enc(C6S+0x0E, 0, C6S+0x50)           # +0E ldr r0,=ON_W0
c6s += H(0x6008)                                  # +10 str r0,[r1]
c6s += H(0x2000)                                  # +12 movs r0,#0
c6s += H(0x6048)                                  # +14 str r0,[r1,#4]  (ＯＮ高字=0)
c6s += b_enc(C6S+0x16, C6S+0x20, None)            # +16 b cont
c6s += ldrpc_enc(C6S+0x18, 0, C6S+0x54)           # +18 ldr r0,=OFF_W0   (off:)
c6s += H(0x6008)                                  # +1A str r0,[r1]
c6s += ldrpc_enc(C6S+0x1C, 0, C6S+0x58)           # +1C ldr r0,=OFF_W1
c6s += H(0x6048)                                  # +1E str r0,[r1,#4]
c6s += H(0x2102)                                  # +20 movs r1,#2       (cont:)
c6s += H(0x4620)                                  # +22 mov r0,r4        (恢复键值)
c6s += H(0x4008)                                  # +24 ands r0,r1       (B键?)
c6s += b_enc(C6S+0x26, C6S+0x3A, 0)               # +26 beq store
c6s += ldrpc_enc(C6S+0x28, 0, C6S+0x5C)           # +28 ldr r0,=SCENE
c6s += H(0x6800)                                  # +2A ldr r0,[r0]
c6s += H(0x2812)                                  # +2C cmp r0,#0x12
c6s += b_enc(C6S+0x2E, C6S+0x3A, 1)               # +2E bne store
c6s += ldrpc_enc(C6S+0x30, 1, C6S+0x60)           # +30 ldr r1,=GATE
c6s += H(0x2201)                                  # +32 movs r2,#1
c6s += H(0x700A)                                  # +34 strb r2,[r1]     (跳过开关=1)
c6s += ldrpc_enc(C6S+0x36, 1, C6S+0x64)           # +36 ldr r1,=MASK
c6s += H(0x430C)                                  # +38 orrs r4,r1       (键值|=R+A)
c6s += ldrpc_enc(C6S+0x3A, 1, C6S+0x68)           # +3A ldr r1,=MIRROR   (store:)
c6s += H(0x800C)                                  # +3C strh r4,[r1]     (复刻原站点写)
c6s += H(0x4620)                                  # +3E mov r0,r4
c6s += H(0xBC02)                                  # +40 pop {r1} (取回原lr)
c6s += H(0x4708)                                  # +42 bx r1
c6s += H(0x0000, 0x0000)                          # +44 pad ×2 (对齐池)
c6s += W(FLAG, STRBUF, ON_W0, OFF_W0, OFF_W1,     # +48 池×9
         0x02005408, 0x0200E6A0, 0x00000101, 0x03001148)
assert len(c6s) == 0x6C, hex(len(c6s))
caves["cave6s"] = (C6S, c6s)

# ===== menu6: 系统菜单条目数组副本(8条) @0x08099798 =====
# 原数组@0x080A0AEC仅7条(标题y0 + y2x18后缀 + 5个菜单项y2-y10), 第6行(y12)无条目
# → 永远空白(项数6补丁只放开光标不产生文本)。追加第8条指向RAM字符串。
# 站点: 描述符@0x080A0D90: +2 count 7→8, +4 itemPtr 0x080A0AEC→本副本
ITEMS = 0x08099798
MENU6_ITEMS = (b"\x12\x00\x0f\x00\xd8\xf2\x06\x08"   # 标题(y0,x18)
               b"\x12\x02\x0f\x00\x60\xf1\x06\x08"   # y2后缀(x18)
               b"\x00\x02\x0f\x00\x10\xf3\x06\x08"   # 菜单项1(y2)
               b"\x00\x04\x0f\x00\x04\xf3\x06\x08"   # 菜单项2(y4)
               b"\x00\x06\x0f\x00\xf8\xf2\x06\x08"   # 菜单项3(y6)
               b"\x00\x08\x0f\x00\xec\xf2\x06\x08"   # 菜单项4(y8)
               b"\x00\x0a\x0f\x00\xe4\xf2\x06\x08"   # 菜单项5(y10)
               b"\x00\x0c\x0f\x00") + W(STRBUF)      # 第6行(y12)→RAM字符串
assert len(MENU6_ITEMS) == 0x40
caves["menu6"] = (ITEMS, MENU6_ITEMS)

# ===== ECD画布LZ编解码 (2026-10-09 全破译+回验780/780) =====
# 窗口1KB@0x3000C30预零, 写指针初值0x3BE, flag字节LSB先: 1=字面量(1字节),
# 0=匹配(2字节: off = n1|((n2&0xC0)<<2) 绝对窗口位10bit, len=(n2&0x3F)+3),
# 复制时窗口同步更新(可自引用重叠复制, RLE特性)
def ecd_lz_decode(stream, outlen):
    win = bytearray(1024); sb = 0x3BE; out = bytearray(); pos = 0
    bits = 0; nb = 0
    def rd():
        nonlocal pos
        if pos >= len(stream): return None
        b = stream[pos]; pos += 1; return b
    while len(out) < outlen:
        if nb == 0:
            f = rd()
            if f is None: break
            bits = f; nb = 8
        bit = bits & 1; bits >>= 1; nb -= 1
        if bit:
            b = rd()
            if b is None: break
            out.append(b); win[sb & 0x3FF] = b; sb += 1
        else:
            n1 = rd(); n2 = rd()
            if n1 is None or n2 is None: break
            off = n1 | ((n2 & 0xC0) << 2); ln = (n2 & 0x3F) + 3
            for k in range(ln):
                b = win[(off + k) & 0x3FF]
                out.append(b); win[sb & 0x3FF] = b; sb += 1
                if len(out) >= outlen: break
    return bytes(out)

def ecd_lz_encode(data):
    win = bytearray(1024); sb = 0x3BE
    out = bytearray(); nbits = 0; flagpos = -1
    def emit(bit, payload):
        nonlocal nbits, flagpos
        if nbits == 0:
            flagpos = len(out); out.append(0); nbits = 8
        if bit: out[flagpos] |= (1 << (8 - nbits))
        nbits -= 1
        out.extend(payload)
    i = 0
    while i < len(data):
        best = None
        for off in range(1024):
            if win[off] != data[i]: continue
            w2 = bytearray(win); s2 = sb; ln = 0
            while ln < 66 and i + ln < len(data):
                b = w2[(off + ln) & 0x3FF]
                if b != data[i + ln]: break
                w2[s2 & 0x3FF] = b; s2 += 1; ln += 1
            if ln >= 3 and (best is None or ln > best[1]):
                best = (off, ln)
                if ln == 66: break
        if best:
            off, ln = best
            seg = []
            w2 = bytearray(win); s2 = sb
            for k in range(ln):
                b = w2[(off + k) & 0x3FF]; seg.append(b); w2[s2 & 0x3FF] = b; s2 += 1
            assert bytes(seg) == data[i:i+ln]
            emit(0, bytes([off & 0xFF, (((off >> 8) & 3) << 6) | (ln - 3)]))
            for b in seg: win[sb & 0x3FF] = b; sb += 1
            i += ln
        else:
            emit(1, bytes([data[i]])); win[sb & 0x3FF] = data[i]; sb += 1; i += 1
    return bytes(out)

# ===== menu6rec: 加高系统菜单画布记录 @0x080997E0 =====
# 画布=窗口背景(w30×h13全宽, 左框rows2-12=菜单本体, 右框rows0-4=回合/资金信息)。
# 第6项文本画在canvas row13=画布外→框外。新画布h=15: 左框体延2行, 底边12→14。
# 记录格式: "ECD\1"+BE32(8)+BE32(总流长)+BE16?(+0xC)+BE16(解压尺寸)+SCR头8B+LZ流。
# 解码自原ROM记录0x0823E5D0(flags0x49B)的画布, 加高后重编码; 指针表项
# [0x08076C24+0x49B*4]=0x08077E90 重定向到本记录(偏移mod 2^32回绕)。
MENU6REC = 0x080997E0
_old_rec_off = struct.unpack('<I', ORIG[0x77E90:0x77E94])[0]
_old_rec = 0x0810FA20 + _old_rec_off
assert _old_rec == 0x0823E5D0, "原画布记录位置异常"
assert ORIG[0x23E5D0:0x23E5D4] == b"ECD\x01"
# 记录头: BE32(+4)=SCR头原样字节数, BE32(+8)=数据流总长(含SCR头), BE16(+0xE)=解压总尺寸
_hdr8 = struct.unpack_from(">I", ORIG, 0x23E5D0 + 4)[0]
_tot  = struct.unpack_from(">I", ORIG, 0x23E5D0 + 8)[0]
_sz   = struct.unpack_from(">H", ORIG, 0x23E5D0 + 0xE)[0]
_old_lz = ORIG[0x23E5D0+0x18 : 0x23E5D0+0x10+_tot]   # LZ流 = 数据流去掉8字节SCR头
_old_map = ecd_lz_decode(_old_lz, _sz - 8)           # 780B, 存储形(0=空白,无+d300)
assert len(_old_map) == 780 and _hdr8 == 8 and _sz == 788
assert ecd_lz_decode(ecd_lz_encode(_old_map), 780) == _old_map, "原画布重编码回验失败"
_body, _bot = _old_map[5*60:6*60], _old_map[12*60:13*60]  # 体=row5(左框体+右侧空白, row3右侧还带信息框), 底=row12
_new_map = _old_map[:12*60] + _body + _body + _bot  # h: 13→15, 左框体+2行底边下移
_new_scr = b"SCR\x00\x00\x1e\x0f\x00" + _new_map
_new_lz = ecd_lz_encode(_new_map)
assert ecd_lz_decode(_new_lz, len(_new_map)) == _new_map, "新画布回验失败"
MENU6_REC = (b"ECD\x01" + struct.pack(">II", 8, 8 + len(_new_lz)) + b"\x00\x00"
             + struct.pack(">H", len(_new_scr)) + _new_scr[:8] + _new_lz)
caves["menu6rec"] = (MENU6REC, MENU6_REC)

# ---------------- 构建 ----------------
assert len(ORIG) == 8388608  # JP版8MB

# 洞区原版必须全零
assert ORIG[0x76A78:0x76B78] == bytes(0x100), "洞区 0x76A78 不是全零!"
assert ORIG[0x994F4:0x994F4+0x1DD] == bytes(0x1DD), "cave4/9/15/16区不是全零!"
assert ORIG[0x99728:0x99728+0xB0] == bytes(0xB0), "cave6s/menu6区(0x99728)不是全零!"
assert ORIG[0x997D8:0x99840] == bytes(0x99840-0x997D8), "menu6rec区(0x997D8)不是全零!"
# 数据源断言: menu6副本前7条 == 原版条目数组; 描述符原值
assert MENU6_ITEMS[:0x38] == ORIG[0x0A0AEC:0x0A0AEC+0x38], "menu6副本 != 原版条目数组!"
assert ORIG[0x0A0D90:0x0A0D98] == bytes.fromhex("9b040700ec0a0a08"), "描述符原值异常!"

rom = bytearray(ORIG)
for name, (base, code) in caves.items():
    put(rom, base, code)

# 站点补丁
put(rom, 0x0802BEB8, bl_enc(0x0802BEB8, CAVE + 0x00))            # -> cave1
put(rom, 0x0802DBAE, bl_enc(0x0802DBAE, CAVE + 0x28) + H(0xC046, 0xC046))  # -> cave2 + 2×NOP
put(rom, 0x0802DBB6, bl_enc(0x0802DBB6, CAVE + 0x48))            # -> cave3
put(rom, 0x08026BFC, H(0x2006))                                  # 项数 5->6
put(rom, 0x0802C876, bl_enc(0x0802C876, 0x080994F4))            # -> cave4
put(rom, 0x0802DE70, bl_enc(0x0802DE70, C5) + H(0xC046))        # -> cave5 + NOP
put(rom, 0x0800225C, bl_enc(0x0800225C, C6S))                    # -> cave6s (B跳过+字符串同步)
put(rom, 0x080A0D92, H(0x0008))                                  # 描述符count 7->8
put(rom, 0x080A0D94, W(ITEMS))                                   # itemPtr->8条副本
# 样式指针表[0x49B]重定向到加高画布记录 (偏移mod 2^32, adds回绕)
put(rom, 0x08077E90, W((MENU6REC - 0x0810FA20) & 0xFFFFFFFF))

# ---------------- capstone 全量自验 ----------------
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
errors = []

def disasm_one(buf, off):
    ins = list(md.disasm(bytes(buf[off:off+4]), 0x08000000 + off))
    return ins[0] if ins else None

# 每洞: 字面量池起始偏移 + {池偏移: 期望值}
LIT = {
    "cave1": (0x20, {0x20: FLAG, 0x24: 0x0802BEBF}),
    "cave2": (0x1C, {0x1C: FLAG}),
    "cave3": (0x20, {0x20: FLAG, 0x28: 0x0802DC89, 0x2C: 0x0802DC5B}),
    "cave4": (0x50, {0x50: FLAG, 0x54: STRBUF, 0x58: OFF_W0, 0x5C: OFF_W1, 0x60: ON_W0, 0x64: 0x0802C965}),
    "cave5": (0x40, {0x40: FLAG}),
    "cave6s": (0x48, {0x48: FLAG, 0x4C: STRBUF, 0x50: ON_W0, 0x54: OFF_W0, 0x58: OFF_W1,
                      0x5C: 0x02005408, 0x60: 0x0200E6A0, 0x64: 0x00000101, 0x68: 0x03001148}),
    "menu6": (0x40, {}),   # 纯数据洞: 无代码区
}


# 每洞期望的指令助记符序列(代码区, 按顺序); "pad"=0x0000
EXPECT_SEQ = {
    "cave1": ("push","cmp","bne","pop","ldr","ldrb","cmp","bne","pop","pad",
              "pop","add","ldr","bx","pad","pad"),
    "cave2": ("push","ldr","ldrb","cmp","beq","movs","movs","movs","movs","bl","bl","pop"),
    "cave3": ("push","ldr","ldrb","cmp","beq","movs","bl","pop","add","ldr","bx",
              "pop","add","ldr","bx"),
    "cave4": ("push","cmp","blo","beq","b","pop","ldr","ldrb","cmp","bne","movs","b",
              "movs","strb","ldr","cmp","beq","ldr","str","ldr","str","b","ldr","str",
              "movs","str","movs","bl","movs","movs","movs","movs","bl","pop","add","ldr","bx","pad"),
    "cave5": ("push","ldr","ldrb","cmp","bne","mov","adds","movs","rsbs","movs","bl","bl","bl",
               "movs","bl","movs","bl","bl","pop","pop","bx","movs","bl","b","pad"),
    "cave6s": ("push","mov","ldr","ldrb","ldr","cmp","beq","ldr","str","movs","str","b",
               "ldr","str","ldr","str","movs","mov","ands","beq","ldr","ldr","cmp","bne",
               "ldr","movs","strb","ldr","orrs","ldr","strh","mov","pop","bx","pad","pad"),
}
# 每洞期望的 ldr 字面量引用 {指令偏移: 字面量池偏移}
EXPECT_OPSTR = {
}

EXPECT_LIT = {
    "cave1": {0x08: 0x20, 0x18: 0x24},
    "cave2": {0x02: 0x1C},
    "cave3": {0x02: 0x20, 0x14: 0x28, 0x1C: 0x2C},
    "cave4": {0x0C: 0x50, 0x1C: 0x54, 0x22: 0x58, 0x26: 0x5C, 0x2C: 0x60, 0x4A: 0x64},
    "cave5": {0x02: 0x40},
    "cave6s": {0x04: 0x48, 0x08: 0x4C, 0x0E: 0x50, 0x18: 0x54, 0x1C: 0x58,
               0x28: 0x5C, 0x30: 0x60, 0x36: 0x64, 0x3A: 0x68},
}

# 每洞期望的分支目标 {代码区偏移: 目标绝对地址}
EXPECT_BRANCH = {
    "cave1": {0x04: CAVE + 0x08, 0x0E: CAVE + 0x14},
    "cave2": {0x08: CAVE + 0x28 + 0x1A},
    "cave3": {0x08: CAVE + 0x48 + 0x18},
    "cave4": {0x04: 0x080994F4 + 0x0A, 0x06: 0x080994F4 + 0x0C,
              0x08: 0x080994F4 + 0x1C, 0x12: 0x080994F4 + 0x18,
              0x16: 0x080994F4 + 0x1A, 0x20: 0x080994F4 + 0x2C,
              0x2A: 0x080994F4 + 0x34},
    "cave5": {0x08: C5 + 0x36, 0x3C: C5 + 0x30},
    "cave6s": {0x0C: C6S + 0x18, 0x16: C6S + 0x20, 0x26: C6S + 0x3A, 0x2E: C6S + 0x3A},
}

ALLOWED_BL = (0x08008B28, 0x08008A94, 0x0800CD8C, 0x08003594, 0x0800E2B8, 0x0800D9D0, 0x0802574C, 0x08030858, 0x08015AFC, 0x0800C89C)

def walk_cave(name, base, code):
    data = bytes(code)
    lit_start, lit_expect = LIT.get(name, (len(code), {}))
    seq = []
    targets = {}
    pc = 0
    while pc < lit_start:
        raw = struct.unpack_from("<H", data, pc)[0]
        if raw == 0x0000:
            seq.append("pad")
            pc += 2
            continue
        ins = list(md.disasm(data[pc:lit_start], base + pc))
        if not ins:
            errors.append("%s+%02X: 无法解码 %s" % (name, pc, data[pc:pc+2].hex()))
            pc += 2
            continue
        i = ins[0]
        seq.append(i.mnemonic)
        if i.mnemonic in ("b","beq","bne","bcs","bcc","bhs","blo","bmi","bpl","bvs","bvc",
                          "bhi","bls","bge","blt","bgt","ble"):
            t = int(i.op_str.lstrip("#"), 16)
            targets[pc] = t
            if t >= base + lit_start or t < base:
                errors.append("%s+%02X: %s 目标落字面量/越界: 0x%08X" % (name, pc, i.mnemonic, t))
        if i.mnemonic in ("str", "ldr"):
            want = EXPECT_OPSTR.get(name, {}).get(pc)
            if want is not None and i.op_str != want:
                errors.append("%s+%02X: %s %s != 期望 %s" % (name, pc, i.mnemonic, i.op_str, want))
        if i.mnemonic == "ldr" and "[pc," in i.op_str:
            imm = int(i.op_str.split("#")[1].rstrip("]"), 16)
            la = ((i.address + 4) & ~3) + imm
            lo = la - base
            if lo not in lit_expect:
                errors.append("%s+%02X: 字面量 0x%08X 不在期望表" % (name, pc, la))
            want_lo = EXPECT_LIT.get(name, {}).get(pc)
            if want_lo is not None and want_lo != lo:
                errors.append("%s+%02X: ldr 引用字面量 +%02X, 期望 +%02X" % (
                    name, pc, lo, want_lo))
            elif lo in lit_expect and lo + 4 <= len(data) and struct.unpack_from("<I", data, lo)[0] != lit_expect.get(lo):
                errors.append("%s+%02X: 字面量 0x%08X 值错误" % (name, pc, la))
        if i.mnemonic == "bl":
            t = int(i.op_str.lstrip("#"), 16)
            if t not in ALLOWED_BL:
                errors.append("%s+%02X: bl 意外目标 0x%08X" % (name, pc, t))
        pc += i.size
    if pc != lit_start:
        errors.append("%s: 代码区长度 %02X != 字面量起点 %02X" % (name, pc, lit_start))
    # 指令序列全等断言
    if tuple(seq) != EXPECT_SEQ.get(name):
        errors.append("%s 指令序列不符:\n  期望 %s\n  实际 %s" % (name, EXPECT_SEQ.get(name), seq))
    # 分支目标全等断言
    if targets != EXPECT_BRANCH.get(name, {}):
        errors.append("%s 分支目标不符:\n  期望 %s\n  实际 %s" % (
            name, {hex(k): hex(v) for k, v in EXPECT_BRANCH.get(name, {}).items()},
            {hex(k): hex(v) for k, v in targets.items()}))
    # 字面量池完整断言
    for lo, val in lit_expect.items():
        if lo + 4 > len(data):
            errors.append("%s 池+%02X: 越界" % (name, lo))
            continue
        got = struct.unpack_from("<I", data, lo)[0]
        if got != val:
            errors.append("%s 池+%02X: 0x%08X != 0x%08X" % (name, lo, got, val))

DATA_CAVES = {"menu6", "menu6rec"}   # 纯数据洞, 不做指令走查
for name, (base, code) in caves.items():
    if name not in DATA_CAVES:
        walk_cave(name, base, code)

# 逐洞语义断言: 反汇编第一条必须是 push; 关键分支目标人工核对
expect_first = {
    "cave1": "push {r4, lr}", "cave2": "push {r4, lr}", "cave3": "push {r4, lr}", "cave4": "push {r4, lr}",
}
for name, (base, code) in caves.items():
    ins = disasm_one(code, 0)
    s = "%s %s" % (ins.mnemonic, ins.op_str)
    if s != expect_first.get(name, s):
        errors.append("%s 首指令: %s != %s" % (name, s, expect_first.get(name, s)))

# 站点 bl 断言
site_expect = {
    0x0802BEB8: CAVE + 0x00, 0x0802DBAE: CAVE + 0x28, 0x0802DBB6: CAVE + 0x48,
    0x0802C876: 0x080994F4, 0x0800225C: C6S, 0x0802DE70: C5,
}
for site, target in site_expect.items():
    ins = disasm_one(rom, site - 0x08000000)
    if ins.mnemonic != "bl" or int(ins.op_str.lstrip("#"), 16) != target:
        errors.append("站点 0x%08X: %s %s != bl 0x%08X" % (site, ins.mnemonic, ins.op_str, target))

# 项数补丁断言
ins = disasm_one(rom, 0x08026BFC - 0x08000000)
if not (ins.mnemonic == "movs" and ins.op_str == "r0, #6"):
    errors.append("0x08026BFC: %s %s != movs r0, #6" % (ins.mnemonic, ins.op_str))

# 描述符补丁断言: count=8, itemPtr=ITEMS; menu6 副本第8条指向STRBUF
if struct.unpack_from("<H", rom, 0x0A0D92)[0] != 8:
    errors.append("0x080A0D92: count != 8")
if struct.unpack_from("<I", rom, 0x0A0D94)[0] != ITEMS:
    errors.append("0x080A0D94: itemPtr != 0x%08X" % ITEMS)
last = MENU6_ITEMS[0x38:]
if last != b"\x00\x0c\x0f\x00" + W(STRBUF):
    errors.append("menu6 第8条异常: %s" % last.hex())
# menu6 副本前7条必须与原版一致(构建后ROM中检查)
if bytes(rom[ITEMS-0x08000000:ITEMS-0x08000000+0x38]) != ORIG[0x0A0AEC:0x0A0AEC+0x38]:
    errors.append("ROM中menu6前7条 != 原版条目数组")

# 洞区整体反汇编一致性: 洞字节 = 我们写入的 code
for name, (base, code) in caves.items():
    off = base - 0x08000000
    if bytes(rom[off:off+len(code)]) != code:
        errors.append("%s 写入不一致" % name)

# ---------------- diff 报告 + 写入 ----------------
diffs = []
i = 0
while i < len(ORIG):
    if ORIG[i] != rom[i]:
        j = i
        while j < len(ORIG) and ORIG[j] != rom[j]:
            j += 1
        diffs.append((i, j))
        i = j
    else:
        i += 1

expect_regions = 9 + len(caves) - len(DATA_CAVES)  # 9站点(含描述符2处) + 6代码洞
print("diff 区域数: %d (站点6 + 洞区)" % len(diffs))
for a, b in diffs:
    print("  0x%06X..0x%06X (%dB)" % (a, b - 1, b - a))

if errors:
    print("\n*** 验证失败 ***")
    for e in errors:
        print("  " + e)
    sys.exit(1)

print("\n所有 capstone 自验通过。")
if "--dry" in sys.argv:
    print("(dry run, 未写入)")
    sys.exit(0)

# r+b 就地写 (mGBA 未运行)
with open(ROM_PATH, "w+b") as f:
    f.seek(0)
    f.write(bytes(rom))
    f.flush()
    os.fsync(f.fileno())

# 写后回读验证
chk = open(ROM_PATH, "rb").read()
assert chk == bytes(rom), "写入后回读不一致!"
print("已写入 %s (%d 字节, diff %d 区域)" % (ROM_PATH, len(chk), len(diffs)))
