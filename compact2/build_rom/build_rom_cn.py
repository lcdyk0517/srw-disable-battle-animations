#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SRW Compact 2 汉化版跳过动画补丁构建器（V2 机制，重定位版）。

以 srw-disable-battle-animations/compact2 的 V2 跳过动画为蓝本，
把我们汉化 ROM 中与翻译/F1/字模冲突的菜单块、调色板 wrapper、
D3 战斗空跑 stub 和 ON/OFF 字符串搬到空闲区，并同步改指针。

支持 srw-chinese-localization 当前汉化版（宋体/融合像素），按源 CRC 自动识别：
  D1 C31AFCE9 / 49DBB3FA
  D2 339ACD58 / 9C67D73D
  D3 12228B0B / 7BD93CEA

用法:
  python build_rom_cn.py <汉化ROM> --jp-dir <日版目录> \
      --build-root <素材目录> [-o 输出]

--build-root 指向 srw-chinese-localization 的 compact2/assets（需含
Dai1/Dai2/Dai3 的 ws2lib.py、assets/cmap_fixed.json、assets/fonts/）。
宋体 simsun.ttc 因授权不随仓库提供，请自备。
"""
import argparse
import hashlib
import importlib.util
import json
import sys
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("skip_v2", HERE / "build_rom_v2.py")
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)

ROM_SIZE = 4 * 1024 * 1024
BUILD_ROOT = None  # 由 --build-root 指定（srw-chinese-localization 的 compact2/assets）
JP_NAMES = {
    1: "Super Robot Taisen Compact 2 - Dai-1-bu - Chijou Gekidou Hen (Japan).ws",
    2: "Super Robot Taisen Compact 2 - Dai-2-bu - Uchuu Gekishin Hen (Japan) (Rev 4).ws",
    3: "Super Robot Taisen Compact 2 - Dai-3-bu - Ginga Kessen Hen (Japan) (Rev 2).ws",
}
# 源 CRC -> (部, 引擎组, 菜单模板, 字体, 输出后缀)
VARIANTS = {
    0x95F2CCFB: (1, "g1", "1j", "宋体", "_跳过动画"),
    0x1F3383E8: (1, "g1", "1j", "融合像素", "[fusion]_跳过动画"),
    0xE3DA0FF7: (2, "g2", "2j", "宋体", "_跳过动画"),
    0x4C271592: (2, "g2", "2j", "融合像素", "[fusion]_跳过动画"),
    0x46927E0A: (3, "g3", "3j", "宋体", "_跳过动画"),
    0x2F69C9EB: (3, "g3", "3j", "融合像素", "[fusion]_跳过动画"),
    # 2026-11-02 武器名 84px / F3 76px / MKII 重建
    0x2974E8CC: (1, "g1", "1j", "宋体", "_跳过动画"),
    0xA3B5A7DF: (1, "g1", "1j", "融合像素", "[fusion]_跳过动画"),
    0x3C3A9BDA: (2, "g2", "2j", "宋体", "_跳过动画"),
    0x93C781BF: (2, "g2", "2j", "融合像素", "[fusion]_跳过动画"),
    0x72828F50: (3, "g3", "3j", "宋体", "_跳过动画"),
    0x1B7938B1: (3, "g3", "3j", "融合像素", "[fusion]_跳过动画"),
    0xC7E8878C: (3, "g3", "3j", "宋体", "_跳过动画"),
    0x77C35118: (3, "g3", "3j", "宋体", "_跳过动画"),
    0xBB5DB88B: (3, "g3", "3j", "宋体", "_跳过动画"),
    0x2C72562A: (3, "g3", "3j", "宋体", "_跳过动画"),
    0x4EDE545D: (3, "g3", "3j", "宋体", "_跳过动画"),
    # 2026-11-02 FA/FB 8px 武器名 + 跳过补丁落点错开
    0x0BCC79D3: (1, "g1", "1j", "宋体", "_跳过动画"),
    0x33DC3BF2: (2, "g2", "2j", "宋体", "_跳过动画"),
    0x715ADBFF: (3, "g3", "3j", "宋体", "_跳过动画"),
    # 2026-11-02 零距离光束加农炮 88px/11 格
    0xB5CAEB6E: (1, "g1", "1j", "宋体", "_跳过动画"),
    0x80F50817: (2, "g2", "2j", "宋体", "_跳过动画"),
    0x042BD850: (3, "g3", "3j", "宋体", "_跳过动画"),
    0xE0170C4F: (1, "g1", "1j", "宋体", "_跳过动画"),
    # 2026-11-02 融合像素 FA/FB 构建
    0x6AD6435C: (1, "g1", "1j", "融合像素", "[fusion]_跳过动画"),
    0x2F081272: (2, "g2", "2j", "融合像素", "[fusion]_跳过动画"),
    0x6DD06FB1: (3, "g3", "3j", "融合像素", "[fusion]_跳过动画"),
    # 2026-11-03 奥克斯坦发射器 88px
    0x19B2C6FB: (2, "g2", "2j", "宋体", "_跳过动画"),
    0xC1F7A572: (3, "g3", "3j", "宋体", "_跳过动画"),
    0xB64FDC9E: (2, "g2", "2j", "融合像素", "[fusion]_跳过动画"),
    # 2026-11-03 奇迹说明前后 FF 填充 + 跳过字符串槽预留
    0xFAB456D3: (1, "g1", "1j", "宋体", "_跳过动画"),
    0xFD9FE191: (2, "g2", "2j", "宋体", "_跳过动画"),
    0x3B8013C7: (3, "g3", "3j", "宋体", "_跳过动画"),
    0x707519C0: (1, "g1", "1j", "融合像素", "[fusion]_跳过动画"),
    0x5262FBF4: (2, "g2", "2j", "融合像素", "[fusion]_跳过动画"),
    0x527BA426: (3, "g3", "3j", "融合像素", "[fusion]_跳过动画"),
    # 2026-11-03 分配器前后 FF 隔离（4 FF 尾留白）+ 芯片/通关重定位
    0x00E416D6: (1, "g1", "1j", "宋体", "_跳过动画"),
    0x980E78E2: (2, "g2", "2j", "宋体", "_跳过动画"),
    0xD3EAF124: (3, "g3", "3j", "宋体", "_跳过动画"),
    0x8A2559C5: (1, "g1", "1j", "融合像素", "[fusion]_跳过动画"),
    0x37F36287: (2, "g2", "2j", "融合像素", "[fusion]_跳过动画"),
    0xBA1146C5: (3, "g3", "3j", "融合像素", "[fusion]_跳过动画"),
    0xA80C1293: (3, "g3", "3j", "融合像素", "[fusion]_跳过动画"),
    # 2026-11-03 重定位串尾部只留 1 个 FF
    0x638FB3A3: (1, "g1", "1j", "宋体", "_跳过动画"),
    0xC553C5D1: (2, "g2", "2j", "宋体", "_跳过动画"),
    0xC86C6227: (3, "g3", "3j", "宋体", "_跳过动画"),
    0xE94EFCB0: (1, "g1", "1j", "融合像素", "[fusion]_跳过动画"),
    0x6AAEDFB4: (2, "g2", "2j", "融合像素", "[fusion]_跳过动画"),
    0xA197D5C6: (3, "g3", "3j", "融合像素", "[fusion]_跳过动画"),
    # 2026-11 GP03 名称改为「GP03 石斛兰 / GP03S 雄蕊」
    0x12802776: (1, "g1", "1j", "宋体", "_跳过动画"),
    0xC7E41A30: (2, "g2", "2j", "宋体", "_跳过动画"),
    0xC8508F2A: (3, "g3", "3j", "宋体", "_跳过动画"),
    0x98416865: (1, "g1", "1j", "融合像素", "[fusion]_跳过动画"),
    0x68190055: (2, "g2", "2j", "融合像素", "[fusion]_跳过动画"),
    0xA1AB38CB: (3, "g3", "3j", "融合像素", "[fusion]_跳过动画"),
    # 2026-11 停用会误改事件脚本的全局台词引用替换（QR）
    0xC31AFCE9: (1, "g1", "1j", "宋体", "_跳过动画"),
    0x339ACD58: (2, "g2", "2j", "宋体", "_跳过动画"),
    0x12228B0B: (3, "g3", "3j", "宋体", "_跳过动画"),
    0x49DBB3FA: (1, "g1", "1j", "融合像素", "[fusion]_跳过动画"),
    0x9C67D73D: (2, "g2", "2j", "融合像素", "[fusion]_跳过动画"),
    0x7BD93CEA: (3, "g3", "3j", "融合像素", "[fusion]_跳过动画"),
}
# 汉化 ROM 中被占用的菜单块/字符串/cave 的新落点（均为实测 FF 区）
NEW = {
    "g1": dict(palette=0x3FE9EE, menu_base=None, menu_string=0xFA1C, stub=None),
    "g2": dict(palette=0x3FE520, menu_base=0x3FF979, menu_string=0xFB59, stub=None),
    "g3": dict(palette=0x3FE754, menu_base=0x3FF970, menu_string=0xFC68, stub=0x3CE74C),
}


def near(at, target):
    rel = (target - (at + 3)) & 0xFFFF
    return bytes((0xE9, rel & 0xFF, rel >> 8))


def near_at(site_ip, target_ip):
    return near(site_ip, target_ip)


def rel16(at_next, target):
    return ((target - at_next) & 0xFFFF).to_bytes(2, "little")



def _font_tools(n, font):
    d = BUILD_ROOT / ("Dai%d" % n)
    mspec = importlib.util.spec_from_file_location("ws2lib_skip_%d" % n, d / "ws2lib.py")
    mod = importlib.util.module_from_spec(mspec)
    mspec.loader.exec_module(mod)
    fname = "fusion-pixel-12px-monospaced-zh_hans.ttf" if font == "融合像素" else "simsun.ttc"
    return mod, d / "assets" / "fonts" / fname, d


def _cmap(n):
    return {ch: int(v, 16) for ch, v in
            json.loads((BUILD_ROOT / ("Dai%d" % n) / "assets" / "cmap_fixed.json")
                       .read_text(encoding="utf-8")).items()}


def _label(text, cmap, blank_code):
    text = text.replace("{BLANK}", chr(0))
    b = bytearray()
    for ch in text:
        if ch == chr(0):
            b += blank_code.to_bytes(2, "big")
        else:
            b += cmap[ch].to_bytes(2, "big")
    b.append(0xFF)
    return bytes(b)


def ensure_blank(src, n, cmap):
    """菜单标签中间用一个双字节空白字模，而不是两个 00。"""
    mod, font_path, d = _font_tools(n, "宋体")
    cfg = mod.load_cfg()
    chunks = mod.chunks(cfg)
    used = set(cmap.values())
    for code in range(0xE000, 0xF000):
        if code in used or (code & 0xFF) in (0xFD, 0xFE, 0xFF):
            continue
        loc = code - 0xE000
        ci, off = loc >> 10, loc & 0x3FF
        bank, base = chunks[ci]
        p = bank * 0x10000 + base + (off >> 3) * 0x100 + (off & 7) * 0x10
        if all(b == 0xFF for b in src[p:p + 16]) and all(b == 0xFF for b in src[p + 0x80:p + 0x90]):
            return code, [(p, bytes(16), "菜单双字节空白字模上"),
                          (p + 0x80, bytes(16), "菜单双字节空白字模下")]
    raise RuntimeError("找不到双字节空白字模槽")


def ensure_glyph(src, n, font, cmap, ch):
    """D2 的「画」不在 cmap；在空闲字模槽写一个，仅供跳过菜单使用。"""
    if ch in cmap:
        return cmap, []
    mod, font_path, d = _font_tools(n, font)
    cfg = mod.load_cfg()
    chunks = mod.chunks(cfg)
    used = set(cmap.values())
    for code in range(0xE000, 0xF000):
        if code in used or (code & 0xFF) in (0xFD, 0xFE, 0xFF):
            continue
        loc = code - 0xE000
        ci, off = loc >> 10, loc & 0x3FF
        bank, base = chunks[ci]
        p = bank * 0x10000 + base + (off >> 3) * 0x100 + (off & 7) * 0x10
        if all(b == 0xFF for b in src[p:p + 16]) and all(b == 0xFF for b in src[p + 0x80:p + 0x90]):
            g = mod.pack_glyph(ch, font_path=font_path)
            cmap = dict(cmap); cmap[ch] = code
            return cmap, [(p, g[:16], "跳过菜单缺字「%s」字模上" % ch),
                          (p + 0x80, g[16:], "跳过菜单缺字「%s」字模下" % ch)]
    raise RuntimeError("找不到「%s」的空闲字模槽" % ch)

def ff_extra_at(g, cave):
    """按新 cave 生成调色板包装和入口门控（重算所有相对跳转）。"""
    c = dict(v2.FF_EXTRA[g])
    c["cave"] = cave
    cave_ip = (cave - 0x300000) & 0xFFFF
    pal = bytearray(bytes.fromhex("36803ea00001"))      # cmp ss:[0x00A0],1
    pal += bytes((0x74, 0x15))                          # je done
    pal += bytes.fromhex("b99000")
    pal += bytes((0xBE, c["pal_src"] & 0xFF, c["pal_src"] >> 8))
    pal += bytes((0xBF, c["pal_dst"] & 0xFF, c["pal_dst"] >> 8))
    pal += bytes.fromhex("8b04890583c60283c702")
    pal += bytes.fromhex("e2f4")
    pal += v2._far(0xF000, c["pal_ret"])
    out = [
        (c["pal_site"], v2._far(0xF000, cave_ip), "调色板/滚动拷贝 → 新 cave"),
        (cave, bytes(pal), "调色板包装（空跑跳过）"),
    ]
    for site, orig, back, off in c["gates"]:
        gate_ip = (cave_ip + off) & 0xFFFF
        gate = v2._ff_gate(site & 0xFFFF, orig, back, gate_ip)
        out.append((site, near_at(site & 0xFFFF, gate_ip), "入口门控 → 新 cave"))
        out.append((cave + off, gate, "门控代码"))
    return out


def menu_d1(key, src, cmap, on_b, off_b):
    """D1 菜单块本来就在空闲区，只重定位 ON/OFF 字符串。"""
    new_str = NEW["g1"]["menu_string"]
    out = []
    for off, hexs, desc in v2.MENU[key]:
        b = bytes.fromhex(hexs)
        if off == 0x35F6D4:
            continue  # 该槽被汉化文本占用，改写到新空闲槽
        if off == 0x3FF600:
            bb = bytearray(b)
            if bytes(bb[0x3F:0x42]) != b"\xb8\xd4\xf6" or bytes(bb[0x44:0x47]) != b"\xb8\xd8\xf6":
                raise RuntimeError("D1 原生 ON/OFF wrapper 字符串立即数不符")
            bb[0x40:0x42] = new_str.to_bytes(2, "little")
            bb[0x45:0x47] = (new_str + 10).to_bytes(2, "little")
            out.append((off, bytes(bb), desc + "（字符串改到新槽）"))
        else:
            out.append((off, b, desc))
    out.append((0x350000 + new_str, on_b, "动画 开（新槽）"))
    out.append((0x350000 + new_str + 10, off_b, "动画 关（新槽）"))
    return out


def _chunk_map(key):
    return {off: bytes.fromhex(hexs) for off, hexs, _ in v2.MENU[key]}


def menu_d23(key, src, base, cmap, on_b, off_b):
    """D2/D3 菜单块压紧到空闲区，重算内部/外部相对引用。"""
    chunks = _chunk_map(key)
    # 新布局：保留 M5→WRITE→字模表 的相对位置，后续代码压紧
    A_M5 = base + 0x000
    A_M5W = base + 0x042
    A_WRITE = base + 0x100
    A_GLYPH = base + 0x140
    A_WRAP = base + 0x3C0
    A_CLEAR = base + 0x3DA
    A_CLOSE = base + 0x3F2
    A_NATIVE = base + 0x3FC

    m5 = bytearray(chunks[0x3FF000])
    # M5 末尾 jmp → 原生关闭链（外部，重算）
    old_next = 0x3FF000 + len(m5)
    old_rel = int.from_bytes(m5[-2:], "little")
    close_target = (old_next + old_rel) & 0xFFFF
    m5[-2:] = rel16(A_M5 + len(m5), close_target)

    m5w = bytearray(chunks[0x3FF042])
    old_next = 0x3FF042 + len(m5w)
    old_rel = int.from_bytes(m5w[-2:], "little")
    close2_target = (old_next + old_rel) & 0xFFFF
    m5w[-2:] = rel16(A_M5W + len(m5w), close2_target)

    wr = bytearray(chunks[0x3FF100])
    p280 = bytes.fromhex("be80f2")
    p140 = bytes.fromhex("be40f1")
    i = wr.find(p280)
    if i < 0:
        raise RuntimeError("%s WRITE 未找到 0xF280 字模指针" % key)
    wr[i + 1:i + 3] = ((A_GLYPH + 0x140) & 0xFFFF).to_bytes(2, "little")
    i = wr.find(p140)
    if i < 0:
        raise RuntimeError("%s WRITE 未找到 0xF140 字模指针" % key)
    wr[i + 1:i + 3] = (A_GLYPH & 0xFFFF).to_bytes(2, "little")

    wrap = bytearray(chunks[0x3FF400])
    # jne → clear
    if wrap[0x0D:0x0F] != b"\x75\x11":
        raise RuntimeError("%s wrapperA jne 不符" % key)
    wrap[0x0E] = (A_CLEAR - (A_WRAP + 0x0F)) & 0xFF
    # call WRITE
    wrap[0x10:0x12] = rel16(A_WRAP + 0x12, A_WRITE)

    clear = chunks[0x3FF420]
    close = bytearray(chunks[0x3FF500])
    close[0x07:0x09] = rel16(A_CLOSE + 0x09, A_WRITE)

    native = bytearray(chunks[0x3FF600])
    if key == "2j":
        # D2 的 ON/OFF 字符串也在被汉化占用的槽，改到新槽
        if native[0x3F:0x42] != b"\xb8\xf4\xf8" or native[0x44:0x47] != b"\xb8\xf8\xf8":
            raise RuntimeError("D2 原生 ON/OFF wrapper 字符串立即数不符")
        s = NEW["g2"]["menu_string"]
        native[0x40:0x42] = s.to_bytes(2, "little")
        native[0x45:0x47] = (s + 10).to_bytes(2, "little")
    else:
        # D3 原槽虽然空闲，但中文标签每个占 10 字节，OFF 指针必须同步改到 +10
        if native[0x3F:0x42] != bytes((0xB8,0x68,0xFC)) or native[0x44:0x47] != bytes((0xB8,0x6C,0xFC)):
            raise RuntimeError("D3 ON/OFF wrapper 字符串立即数不符")
        s = NEW["g3"]["menu_string"]
        native[0x40:0x42] = s.to_bytes(2, "little")
        native[0x45:0x47] = (s + 10).to_bytes(2, "little")

    out = [
        (A_M5, bytes(m5), "M5（重定位）"),
        (A_M5W, bytes(m5w), "M5→WRITE（重定位）"),
        (A_WRITE, bytes(wr), "WRITE（重定位，字模指针更新）"),
        (A_GLYPH, chunks[0x3FF140], "ON/OFF 字模表（重定位）"),
        (A_WRAP, bytes(wrap), "wrapperA（重定位）"),
        (A_CLEAR, clear, "清 0x3C00（重定位）"),
        (A_CLOSE, bytes(close), "关闭刷新（重定位）"),
        (A_NATIVE, bytes(native), "原生 ON/OFF wrapper（重定位）"),
        # 外部入口：菜单绘制/关闭/第6项
        (0x3528A7, (A_WRAP & 0xFFFF).to_bytes(2, "little"), "菜单绘制调用1 → 新 wrapperA"),
        (0x3529C3, (A_WRAP & 0xFFFF).to_bytes(2, "little"), "菜单绘制调用2 → 新 wrapperA"),
        (0x352AB1, (A_NATIVE & 0xFFFF).to_bytes(2, "little") + b"\x00\xf0",
         "第6项标签 → 新原生 wrapper"),
        (0x3FB71E if key == "2j" else 0x3FB7F4,
         near_at(0xFB71E if key == "2j" else 0xFB7F4, A_CLOSE & 0xFFFF),
         "菜单关闭 hook → 新刷新"),
        (0x3FB74D if key == "2j" else 0x3FB823,
         near_at(0xFB74D if key == "2j" else 0xFB823, A_M5 & 0xFFFF),
         "菜单 M5 hook → 新 M5"),
        (0x36000E, bytes.fromhex("00f0"), "菜单帧指针"),
        (0x36F000, chunks[0x36F000], "9×14 菜单帧表"),
        (0x350000 + NEW["g2" if key == "2j" else "g3"]["menu_string"],
         on_b, "动画 开（新槽）"),
        (0x350000 + NEW["g2" if key == "2j" else "g3"]["menu_string"] + 10,
         off_b, "动画 关（新槽）"),
    ]
    return out



def protect_empty_f1(src, game):
    """D2/D3 菜单块会落在两个空 F1 宏的旧目标上；把它们改指公共空槽。"""
    if game not in ("g2", "g3"):
        return []
    out = []
    for idx in (0x2B, 0x2C):
        site = 0x3FFF00 + 2 * idx
        old = int.from_bytes(src[site:site + 2], "little")
        target = 0x3F0000 + old
        if old in (0xFBF5, 0xFCF5) and all(b == 0xFF for b in src[target:target + 8]):
            out.append((site, (0xFFE6).to_bytes(2, "little"),
                        "F1空宏 F1%02X 改指公共空槽" % (0xD0 + idx)))
    return out

def build(src, jp, game, key, n, font):
    regs = []
    cmap = _cmap(n)
    cmap, greg = ensure_glyph(src, n, font, cmap, "画")
    regs += greg
    blank_code, breg = ensure_blank(src, n, cmap)
    regs += breg
    on_b = _label("动画{BLANK}开", cmap, blank_code)
    off_b = _label("动画{BLANK}关", cmap, blank_code)
    d = v2.GAMES[game]
    # 战斗每帧 hook + 空跑 stub
    if game == "g3":
        stub = NEW["g3"]["stub"]
        stub_ip = (stub - 0x300000 - 0xC0000) & 0xFFFF
    else:
        stub = d["hstub"]
        stub_ip = d["hstub_ip"]
    hs = v2.hook_stub_int_ff(d["flag"], d["tick"], d["disp"], d["native"][0],
                             d["native"][1], d["hook1_next_ip"], stub_ip,
                             script=d.get("script"), script2=d.get("script2"),
                             sel=d.get("sel"), wait=d.get("wait"),
                             unit_ptr=d.get("unit_ptr"))
    regs.append((d["hook1"], v2._near(d["hook1_ip"], stub_ip) + b"\x90\x90",
                 "战斗每帧 hook"))
    regs.append((stub, hs, "援护空跑 stub"))
    regs += ff_extra_at(game, NEW[game]["palette"])
    regs += protect_empty_f1(src, game)
    if game == "g1":
        regs += menu_d1(key, src, cmap, on_b, off_b)
    else:
        regs += menu_d23(key, src, NEW[game]["menu_base"], cmap, on_b, off_b)
    return regs


def check_regions(src, jp, regs):
    for off, data, desc in regs:
        b = data
        if desc.startswith("F1空宏"):
            continue
        if off in (0x3528E7, 0x352A03, 0x352AF1, 0x352A03, 0x3528A7, 0x3529C3,
                   0x352AB1, 0x36000E, 0x3FB3BD, 0x3FB71E, 0x3FB74D,
                   0x3FB7F4, 0x3FB823, 0x3F023D, 0x3F0242, 0x3F0790,
                   0x3FCA3A, 0x3FCDD8, 0x3F0F62, 0x3FCF76, 0x3EB2B6,
                   0x3C2C12, 0x3C6512):
            if src[off:off + len(b)] != jp[off:off + len(b)]:
                raise RuntimeError("引擎字节已变，拒绝打补丁: 0x%06X %s" % (off, desc))
        else:
            # 新 cave/菜单块/字符串槽必须是空闲 FF
            if not all(x == 0xFF for x in src[off:off + len(b)]):
                raise RuntimeError("目标区不是空闲 FF: 0x%06X %s" % (off, desc))


def main():
    global BUILD_ROOT
    ap = argparse.ArgumentParser(description="汉化版 Compact2 跳过动画补丁")
    ap.add_argument("rom")
    ap.add_argument("-o", "--out")
    ap.add_argument("--jp-dir", default=".", help="原版日文 ROM 所在目录")
    ap.add_argument("--build-root", required=True,
                    help="srw-chinese-localization 的 compact2/assets 目录")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    BUILD_ROOT = Path(args.build_root).expanduser().resolve()
    if not (BUILD_ROOT / "Dai1" / "ws2lib.py").is_file():
        raise SystemExit("--build-root 不正确，缺少 Dai1/ws2lib.py: %s" % BUILD_ROOT)
    p = Path(args.rom)
    src = p.read_bytes()
    if len(src) != ROM_SIZE:
        raise SystemExit("ROM 大小不是 4MB: %d" % len(src))
    crc = zlib.crc32(src) & 0xFFFFFFFF
    meta = VARIANTS.get(crc)
    if not meta:
        raise SystemExit("未识别的汉化 ROM: CRC %08X" % crc)
    n, game, key, font, suffix = meta
    jp_path = Path(args.jp_dir) / JP_NAMES[n]
    jp = jp_path.read_bytes()
    regs = build(src, jp, game, key, n, font)
    check_regions(src, jp, regs)
    # 重叠检查
    placed = []
    for off, data, desc in regs:
        for a, b in placed:
            if off < b and a < off + len(data):
                raise RuntimeError("补丁区重叠 0x%06X %s" % (off, desc))
        placed.append((off, off + len(data)))
    out = bytearray(src)
    for off, data, desc in regs:
        out[off:off + len(data)] = data
    out_crc = zlib.crc32(out) & 0xFFFFFFFF
    out_md5 = hashlib.md5(out).hexdigest()
    if args.out:
        dst = Path(args.out)
    else:
        dst = p.with_name(p.stem + suffix + p.suffix)
    if dst.exists() and not args.force:
        raise SystemExit("输出已存在，用 --force 覆盖: %s" % dst)
    dst.write_bytes(out)
    print("识别: D%d %s" % (n, font))
    print("源 CRC32: %08X" % crc)
    print("输出 CRC32: %08X" % out_crc)
    print("输出 MD5:", out_md5)
    print("已写入:", dst)


if __name__ == "__main__":
    main()