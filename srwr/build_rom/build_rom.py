# SRW-R V7: 动画中按B → 复刻官方完成回调的模式切换
# 机制(2026-10-07全链路实测确认):
#   [0x03001320] = 当前模式(slot), [0x03001080+i] = 模式i的状态字节
#   模式2=战斗动画显示(状态9=播放中), 模式1=战斗编排(序列器0x8013280在此模式运行)
#   自然结束: 完成回调0x803AD88: getter()==9 → setter(1,3)
#             = [0x03001081]=3 + [0x03001320]=1 → 模式1帧驱动跑序列器 → case3 → animend(1) → 结算
#   V5教训: 只写phase[2]=3不切模式 → 完成回调cmp#9失败 → 死循环 (已废弃)
#   V6教训: 0x02000C2C标志只在场景检查点被消费, 动画中无人轮询 (已废弃)
# 本版: B + REQ==2 + slot==2 + phase==9 → strb 3,[0x03001081] + str 1,[0x03001320]
# 钩子: 0x080028AA (原4字节= mov r1,ip + strh r0,[r1], ip=0x03002AA8)
import struct, sys, capstone
import capstone.arm as ARM

VARIANTS = [
    (r"D:/GBA/超级机器人大战R[星组](v1.2+)(简)(JP)(68.92Mb).gba",
     r"D:/GBA/emu/run_r/srwr_bskip.gba", 9034688),
    (r"D:/GBA/超级机器人大战R(震动).gba",
     r"D:/GBA/emu/run_r/srwr_zd.gba", 9175040),
    (r"D:/GBA/Super Robot Taisen R (Japan).gba",
     r"D:/GBA/emu/run_r/srwr_jp.gba", 8388608),
]

H = lambda *v: struct.pack("<%dH" % len(v), *v)
W = lambda *v: struct.pack("<%dI" % len(v), *v)

def bl_enc(s, d):
    o = (d - (s + 4)) >> 1
    return H(0xF000 | ((o >> 11) & 0x7FF), 0xF800 | (o & 0x7FF))

def b_enc(a, d, c=None):
    o = (d - (a + 4)) >> 1
    if c is None:
        return struct.pack("<H", 0xE000 | (o & 0x7FF))
    return struct.pack("<H", 0xD000 | (c << 8) | (o & 0xFF))

def ldrpc(a, r, l):
    p = (a + 4) & ~3
    imm = (l - p) >> 2
    assert 0 <= imm <= 0xFF, "ldr立即数超范围"
    return struct.pack("<H", 0x4800 | imm | (r << 8))

def put(rom, a, d):
    rom[a - 0x08000000:a - 0x08000000 + len(d)] = d

C = 0x08093670  # 洞地址

# 洞布局 (池4项@C+0x38: KEYMIR/REQ/SLOT/PHBASE):
# +00 push {lr}
# +02 ldr r1,=KEYMIR(03002AA8)
# +04 strh r0,[r1]              复刻原指令
# +06 movs r1,#2
# +08 ands r0,r1                B?
# +0A beq done(+34)
# +0C ldr r2,=REQ(02014AF0)
# +0E ldrb r0,[r2]
# +10 cmp r0,#2                 动画场景?
# +12 bne done
# +14 ldr r1,=SLOT(03001320)
# +16 ldr r1,[r1]               当前模式
# +18 cmp r1,#2                 战斗动画模式?
# +1A bne done
# +1C ldr r2,=PHBASE(03001080)
# +1E adds r1,r2,r1             模式2状态字节地址
# +20 ldrb r0,[r1]
# +22 cmp r0,#9                 播放中? (官方回调同款检查)
# +24 bne done
# +26 ldr r2,=PHBASE
# +28 adds r2,#1                → 0x03001081 (模式1状态)
# +2A movs r1,#3
# +2C strb r1,[r2]              phase[1]=3
# +2E ldr r2,=SLOT
# +30 movs r1,#1
# +32 str r1,[r2]               模式=1 (官方setter顺序: 先值后切)
# +34 pop {r1}        ← done
# +36 bx r1
c  = H(0xB500)                        # +00 push {lr}
c += ldrpc(C + 0x02, 1, C + 0x40)     # +02 ldr r1,=KEYMIR
c += H(0x8008)                        # +04 strh r0,[r1]
c += H(0x2102)                        # +06 movs r1,#2
c += H(0x4008)                        # +08 ands r0,r1
c += b_enc(C + 0x0A, C + 0x3A, 0)     # +0A beq done
c += ldrpc(C + 0x0C, 2, C + 0x44)     # +0C ldr r2,=REQ
c += H(0x7810)                        # +0E ldrb r0,[r2]
c += H(0x2802)                        # +10 cmp r0,#2
c += b_enc(C + 0x12, C + 0x3A, 1)     # +12 bne done
c += ldrpc(C + 0x14, 1, C + 0x48)     # +14 ldr r1,=SLOT
c += H(0x6809)                        # +16 ldr r1,[r1]
c += H(0x2902)                        # +18 cmp r1,#2
c += b_enc(C + 0x1A, C + 0x3A, 1)     # +1A bne done
c += ldrpc(C + 0x1C, 2, C + 0x4C)     # +1C ldr r2,=PHBASE
c += H(0x1851)                        # +1E adds r1,r2,r1
c += H(0x7808)                        # +20 ldrb r0,[r1]
c += H(0x2809)                        # +22 cmp r0,#9
c += b_enc(C + 0x24, C + 0x3A, 1)     # +24 bne done
c += ldrpc(C + 0x26, 2, C + 0x4C)     # +26 ldr r2,=PHBASE
c += H(0x3201)                        # +28 adds r2,#1
c += H(0x2103)                        # +2A movs r1,#3
c += H(0x7011)                        # +2C strb r1,[r2]   phase[1]=3
c += ldrpc(C + 0x2E, 2, C + 0x48)     # +2E ldr r2,=SLOT
c += H(0x2101)                        # +30 movs r1,#1
c += H(0x6011)                        # +32 str r1,[r2]    slot=1
c += ldrpc(C + 0x34, 2, C + 0x54)     # +34 ldr r2,=0x08013B21(战斗帧处理器)
c += ldrpc(C + 0x36, 1, C + 0x50)     # +36 ldr r1,=0x03001108(task0.func)
c += H(0x600A)                        # +38 str r2,[r1]    task0.func=战斗帧
c += H(0xBC02)                        # +3A pop {r1}
c += H(0x4708)                        # +3C bx r1
c += H(0x0000)                      # +3E pad
c += W(0x03002AA8, 0x02014AF0, 0x03001320, 0x03001080, 0x03001108, 0x08013B21)  # +40 池×6

def build(orig_path, out_path, exp_len):
    ORIG = open(orig_path, "rb").read()
    assert len(ORIG) == exp_len, "ROM长度不符: %s" % orig_path
    assert ORIG[0x93670:0x93670 + 0x58] == bytes(0x58), "洞区非零"
    assert ORIG[0x28AA:0x28AE] == bytes.fromhex("61460880"), "钩子点原字节不符"
    # 震动版引擎代码一致性抽查
    assert ORIG[0x13B20:0x13B2C] == bytes.fromhex(
        "00b5eef7ddfff0f779ff7f20"), "战斗帧func不一致"
    rom = bytearray(ORIG)
    put(rom, C, c)
    put(rom, 0x080028AA, bl_enc(0x080028AA, C))
    return bytes(rom)

BUILT = {}

# ---- capstone 全量自验 (对合成rom) ----
rom = bytearray(build(*VARIANTS[0]))
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
md.detail = True
errs = []
ins = list(md.disasm(c[:0x3E], C))
got = [i.mnemonic for i in ins]
exp = ["push", "ldr", "strh", "movs", "ands", "beq",
       "ldr", "ldrb", "cmp", "bne",
       "ldr", "ldr", "cmp", "bne",
       "ldr", "adds", "ldrb", "cmp", "bne",
       "ldr", "adds", "movs", "strb",
       "ldr", "movs", "str",
       "ldr", "ldr", "str", "pop", "bx"]
if got != exp:
    errs.append("指令序列: %s" % got)
# 操作数级断言
OPS = {
    C + 0x04: ("strh", "r0, [r1]"),        # 键值→镜像
    C + 0x1E: ("adds", "r1, r2, r1"),      # 状态地址=PHBASE+模式
    C + 0x2C: ("strb", "r1, [r2]"),        # 值3→phase[1]
    C + 0x32: ("str", "r1, [r2]"),         # 值1→模式
    C + 0x38: ("str", "r2, [r1]"),         # 战斗帧函数→task0.func
}
for a, (m, o) in OPS.items():
    hit = [i for i in ins if i.address == a]
    if not hit or hit[0].mnemonic != m or hit[0].op_str != o:
        errs.append("操作数@%#x: 期望 %s %s, 实际 %s" % (
            a, m, o, ("%s %s" % (hit[0].mnemonic, hit[0].op_str)) if hit else "缺失"))
for i in ins:
    if i.mnemonic in ("beq", "bne"):
        tgt = i.operands[0].imm
        if tgt != C + 0x3A:
            errs.append("%s@%#x 目标 %#x != %#x" % (i.mnemonic, i.address, tgt, C + 0x3A))
LDR_EXP = {C + 0x02: 0x03002AA8, C + 0x0C: 0x02014AF0, C + 0x14: 0x03001320,
           C + 0x1C: 0x03001080, C + 0x26: 0x03001080, C + 0x2E: 0x03001320,
           C + 0x34: 0x08013B21, C + 0x36: 0x03001108}
for i in ins:
    if i.mnemonic == "ldr" and i.operands[1].type == ARM.ARM_OP_MEM        and i.operands[1].mem.base == ARM.ARM_REG_PC:
        tgt = ((i.address + 4) & ~3) + i.operands[1].mem.disp
        want = LDR_EXP.get(i.address)
        if want is None:
            errs.append("意外ldr@%#x" % i.address)
        else:
            val = struct.unpack("<I", rom[tgt - 0x08000000:tgt - 0x08000000 + 4])[0]
            if val != want:
                errs.append("ldr@%#x 池%#x值=%#x 期望%#x" % (i.address, tgt, val, want))
POOL = [(0x40, 0x03002AA8), (0x44, 0x02014AF0), (0x48, 0x03001320),
        (0x4C, 0x03001080), (0x50, 0x03001108), (0x54, 0x08013B21)]
for lo, v in POOL:
    if struct.unpack_from("<I", c, lo)[0] != v:
        errs.append("池@+%#x 错误" % lo)
if bytes(rom[0x28AA:0x28AE]) != bl_enc(0x080028AA, C):
    errs.append("钩子字节不符")
if bytes(rom[0x93670:0x93670 + len(c)]) != c:
    errs.append("洞写入回读不符")
if errs:
    print("\n".join(errs))
    sys.exit(1)
print("自验通过: %d条指令, 操作数OK, 4分支OK, 池4项OK, 钩子OK" % len(ins))

if "--dry" in sys.argv:
    sys.exit(0)
import hashlib
for orig_path, out_path, exp_len in VARIANTS:
    rb = build(orig_path, out_path, exp_len)
    with open(out_path, "w+b") as f:
        f.write(rb)
    BUILT[orig_path] = rb
    print("已写入 %s (md5=%s)" % (out_path, hashlib.md5(rb).hexdigest()[:8]))
