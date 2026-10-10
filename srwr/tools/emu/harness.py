# -*- coding: utf-8 -*-
"""
mGBA Windows 自动化测试台 (SRW-A 逆向)
- 托管 mgba-sdl.exe -g (GDB stub :2345)
- GDB 远程协议客户端 (断点/观察点/内存读写/寄存器)
- SendInput 按键注入 (发给 mGBA 窗口)
- 截图 (PIL ImageGrab 窗口区域)
用法:
  python harness.py serve          # 启动守护: 托管模拟器+命令轮询 (q/cmd.txt -> log/out.txt)
  (serve 循环支持的命令见 handle())
"""
import os, sys, time, socket, struct, subprocess, ctypes, json, threading
from ctypes import wintypes

ROOT = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(ROOT, "run")
MGBA = os.path.join(ROOT, "mgba-dbg", "mgba-sdl.exe")
QFILE = os.path.join(ROOT, "q", "cmd.txt")
OUT = os.path.join(ROOT, "log", "out.txt")
EVT = os.path.join(ROOT, "log", "events.txt")
PORT = 2345

# mGBA 默认键位: X=A Z=B 回车=START 退格=SELECT A=L S=R 方向键
SCAN = {"A":0x2D, "B":0x2C, "START":0x1C, "SELECT":0x0E,
        "L":0x1E, "R":0x1F, "UP":0x48, "DOWN":0x50, "LEFT":0x4B, "RIGHT":0x4D}

user32 = ctypes.windll.user32

def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)

def evlog(msg):
    os.makedirs(os.path.dirname(EVT), exist_ok=True)
    with open(EVT, "a", encoding="utf-8") as f:
        f.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), msg))

# ---------------- 按键注入 ----------------
PUL = ctypes.POINTER(ctypes.c_ulong)
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", PUL)]
class INPUT(ctypes.Structure):
    class _I(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _anonymous_ = ("i",)
    _fields_ = [("type", wintypes.DWORD), ("i", _I)]

# 虚拟键码 (PostMessage直发SDL窗口, 无需焦点, 不干扰用户前台)
VK = {"A":0x58, "B":0x5A, "START":0x0D, "SELECT":0x08,
      "L":0x41, "R":0x53, "UP":0x26, "DOWN":0x28, "LEFT":0x25, "RIGHT":0x27}

def find_mgba_window(pid):
    res = []
    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, lp):
        pid_ = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid_))
        if pid_.value == pid and user32.IsWindowVisible(hwnd):
            res.append(hwnd)
        return True
    user32.EnumWindows(cb, 0)
    return res[0] if res else None

def tap_key(name, hold=0.12):
    vk = VK[name.upper()]
    sc = SCAN[name.upper()]
    hwnd = STATE.get("hwnd")
    if not hwnd:
        return "key FAIL: 无窗口"
    WM_KEYDOWN, WM_KEYUP = 0x100, 0x101
    lp_down = (sc << 16) | 1
    lp_up = (sc << 16) | (1 << 30) | (1 << 31) | 1
    user32.PostMessageW(hwnd, WM_KEYDOWN, vk, lp_down)
    time.sleep(hold)
    user32.PostMessageW(hwnd, WM_KEYUP, vk, lp_up)
    return "key %s posted" % name

# ---------------- GDB 客户端 ----------------
class Gdb:
    def __init__(self):
        self.s = None
        self.running = False
        self.stop_pkt = None

    def connect(self, tries=40):
        for _ in range(tries):
            try:
                self.s = socket.create_connection(("127.0.0.1", PORT), timeout=2)
                break
            except OSError:
                time.sleep(0.5)
        else:
            raise RuntimeError("GDB端口连不上")
        self.s.settimeout(0.05)
        self.send("")  # 启动包

    def _read_pkt(self, timeout=3.0):
        buf = b""
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                d = self.s.recv(4096)
                if not d: raise ConnectionError("对端关闭")
                buf += d
            except socket.timeout:
                continue
            # 解析 $...#xx, 忽略ACK; 不完整数据保留等待续传
            while True:
                i = buf.find(b"$")
                if i < 0:
                    break
                j = buf.find(b"#", i)
                if j < 0 or len(buf) < j + 3:
                    buf = buf[i:]
                    break
                pkt = buf[i+1:j]
                buf = buf[j+3:]
                return pkt.decode("ascii", "replace")
        return None

    def send(self, payload, expect=True, timeout=3.0):
        csum = sum(payload.encode()) & 0xFF
        raw = b"$" + payload.encode() + ("#%02x" % csum).encode()
        self.s.sendall(raw)
        if expect:
            return self._read_pkt(timeout)
        return None

    def cmd(self, p, timeout=3.0):
        r = self.send(p, timeout=timeout)
        return r

    def cont(self):
        self.s.sendall(b"$c#63")
        self.running = True

    def wait_stop(self, timeout=30.0):
        """等待断点/观察点命中, 返回stop包"""
        self.s.settimeout(0.2)
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                d = self.s.recv(4096)
                if not d: raise ConnectionError("对端关闭")
                STATE["rbuf"] = STATE.get("rbuf", b"") + d
                while True:
                    b = STATE["rbuf"]
                    i = b.find(b"$")
                    if i < 0:
                        break
                    j = b.find(b"#", i)
                    if j < 0 or len(b) < j+3:
                        STATE["rbuf"] = b[i:]
                        break
                    pkt = b[i+1:j].decode("ascii", "replace")
                    STATE["rbuf"] = b[j+3:]
                    self.running = False
                    self._ack_stop()
                    return pkt
            except socket.timeout:
                continue
        return None

    def _ack_stop(self):
        try:
            self.s.sendall(b"+")
        except OSError:
            pass

    def halt(self):
        self.s.sendall(b"\x03")
        pkt = self.wait_stop(5)
        return pkt

    def regs(self):
        r = self.cmd("g")
        if not r: return None
        # mGBA按内存字节序(小端)返回寄存器, 8字符切分后需字节交换
        vals = []
        for i in range(min(16, len(r)//8)):
            x = int(r[i*8:(i+1)*8], 16)
            vals.append(int.from_bytes(x.to_bytes(4, "big"), "little"))
        return vals

    def read(self, addr, length):
        r = self.cmd("m%x,%x" % (addr, length))
        if r is None or "E" == r[:1] and len(r) < 20:
            return None
        try:
            return bytes.fromhex(r)
        except ValueError:
            return None

    def write(self, addr, data):
        return self.cmd("M%x,%x:%s" % (addr, len(data), data.hex()))

    def bp(self, addr, on=True, kind=1):
        if on:
            return self.cmd("Z0,%x,%d" % (addr, kind))
        return self.cmd("z0,%x,%d" % (addr, kind))

    def wp(self, addr, length, on=True):
        if on:
            return self.cmd("Z2,%x,%d" % (addr, length))
        return self.cmd("z2,%x,%d" % (addr, length))

STATE = {"gdb": None, "hwnd": None, "proc": None, "rbuf": b"", "autobp": {}}

# ---------------- 截图 ----------------
def screenshot(path):
    hwnd = STATE.get("hwnd")
    if not hwnd:
        return "shot FAIL: 无窗口"
    # PrintWindow 可抓被遮挡的窗口, 无需前台
    PW_RENDERFULLCONTENT = 2
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    try:
        from PIL import Image
        hwnd_dc = user32.GetWindowDC(hwnd)
        gdi32 = ctypes.windll.gdi32
        mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
        bmp = gdi32.CreateCompatibleBitmap(hwnd_dc, w, h)
        gdi32.SelectObject(mem_dc, bmp)
        user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT)
        # BMP数据提取
        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                        ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                        ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                        ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                        ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                        ("biClrImportant", ctypes.c_uint32)]
        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth, bmi.biHeight, bmi.biPlanes, bmi.biBitCount = w, -h, 1, 32
        bmi.biCompression = 0
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(mem_dc, bmp, 0, h, buf, ctypes.byref(bmi), 0)
        img = Image.frombuffer("RGB", (w, h), buf.raw, "raw", "BGRX", 0, 1)
        img = img.convert("RGB")
        img.save(path)
        gdi32.DeleteObject(bmp); gdi32.DeleteDC(mem_dc); user32.ReleaseDC(hwnd, hwnd_dc)
        return "shot %s %dx%d" % (path, w, h)
    except Exception as e:
        return "shot FAIL: %r" % e

# ---------------- serve 主循环 ----------------
def handle(cmdline):
    g = STATE["gdb"]
    parts = cmdline.strip().split()
    if not parts: return
    c, args = parts[0], parts[1:]
    if c == "ping":
        log("pong")
    elif c == "regs":
        v = g.regs()
        if v:
            names = ["r%d" % i for i in range(13)] + ["sp", "lr", "pc"]
            log(" ".join("%s=%08x" % (n, x & 0xFFFFFFFF) for n, x in zip(names, v)))
    elif c == "m" and len(args) == 2:
        d = g.read(int(args[0], 0), int(args[1], 0))
        log("m %s: %s" % (args[0], d.hex() if d else "FAIL"))
    elif c == "M" and len(args) == 2:
        log("M %s: %s" % (args[0], g.write(int(args[0], 0), bytes.fromhex(args[1]))))
    elif c == "bp":
        log("bp %s -> %s" % (args[0], g.bp(int(args[0], 0))))
    elif c == "bp-" and args:
        log("bp- %s -> %s" % (args[0], g.bp(int(args[0], 0), False)))
    elif c == "wp" and len(args) == 2:
        log("wp %s x%s -> %s" % (args[0], args[1], g.wp(int(args[0], 0), int(args[1], 0))))
    elif c == "wp-" and len(args) == 2:
        log("wp- %s -> %s" % (args[0], g.wp(int(args[0], 0), int(args[1], 0), False)))
    elif c == "bpa" and len(args) >= 2:
        # bpa <addr> <标签...>: 自动记录断点, 命中即记录r0-r3/lr并放行
        addr = int(args[0], 0)
        label = " ".join(args[1:])
        STATE["autobp"][addr] = label
        log("bpa %s [%s] -> %s" % (args[0], label, g.bp(addr)))
    elif c == "bpaoff" and args:
        addr = int(args[0], 0)
        STATE["autobp"].pop(addr, None)
        log("bpaoff -> %s" % g.bp(addr, False))
    elif c == "bpflush":
        for a in list(STATE["autobp"]):
            g.bp(a, False)
        STATE["autobp"].clear()
        log("所有自动断点已撤除")
    elif c == "pokeif2" and len(args) == 7:
        # pokeif2 <addr1> <期望1> <addr2> <期望2> <写addr> <新半字> <超时秒> (7参)
        a1, e1, a2, e2, wa, wv, tmo = (int(x,0) for x in args)
        t0 = time.time(); done = False
        while time.time() - t0 < tmo:
            d1, d2 = g.read(a1, 2), g.read(a2, 2)
            if d1 and d2 and struct.unpack("<H", d1)[0] == e1 and struct.unpack("<H", d2)[0] == e2:
                g.write(wa, struct.pack("<H", wv)); done = True
                break
            time.sleep(0.1)
        log("pokeif2: %s" % ("已写入@%.1fs" % (time.time()-t0) if done else "超时"))
    elif c == "pokeif" and len(args) == 4:
        # pokeif <addr> <期望半字hex> <新半字hex> <超时秒>: 轮询[addr]==期望即写新值
        addr, exp, newv, tmo = int(args[0],0), int(args[1],0), int(args[2],0), int(args[3],0)
        t0 = time.time(); done = False
        while time.time() - t0 < tmo:
            d = g.read(addr, 2)
            if d and struct.unpack("<H", d)[0] == exp:
                g.write(addr, struct.pack("<H", newv)); done = True
                break
            time.sleep(0.1)
        log("pokeif %s==%x->%x: %s" % (hex(addr), exp, newv, "已写入@%.1fs" % (time.time()-t0) if done else "超时"))
    elif c == "c":
        g.cont()
        log("continue")
    elif c == "s":  # halt + regs + 关键内存快照
        pkt = g.halt()
        log("halt: %s" % pkt)
        handle("regs")
    elif c == "dump" and len(args) == 3:
        addr, ln, tag = int(args[0], 0), int(args[1], 0), args[2]
        d = g.read(addr, ln)
        path = os.path.join(ROOT, "log", "dump_%s.bin" % tag)
        with open(path, "wb") as f2:
            f2.write(d if d else b"")
        log("dump %s: %d bytes -> %s" % (tag, len(d) if d else 0, path))
    elif c == "key" and args:
        log(tap_key(args[0]))
    elif c == "shot":
        p = args[0] if args else os.path.join(ROOT, "log", "shot.png")
        log(screenshot(p))
    elif c == "steptrace" and len(args) == 1:  # 指令级单步追踪: steptrace N
        n = int(args[0], 0)
        pkt = g.halt()
        r = g.regs()
        pc0 = r[15] if r else 0
        seq = []
        for i in range(n):
            g.cmd("s")
            pkt = g.wait_stop(timeout=2)
            rr = g.regs()
            pc = rr[15] if rr else 0
            seq.append("%06X" % (pc & 0xFFFFFF))
        log("STEPTRACE from %08X (%d条): %s" % (pc0 & ~1, n, " ".join(seq)))
        g.cont()
    elif c == "hold":  # 下一个无标签断点命中后保持暂停
        STATE["stopauto"] = True
        log("已设停驻: 下一个断点命中将暂停")
    elif c == "state":  # 快照: 场景状态+切镜命令+战斗上下文关键值
        pkt = g.halt()
        r = g.regs()
        pc = r[15] if r else 0
        def rd(a, n):
            d = g.read(a, n)
            return d.hex() if d else "??"
        log("STATE: pc=%08x scenestate=%s battlestep=%s cmd@03001150=%s animID@0200D96E=%s ctx0C=%s" % (
            pc, rd(0x02005408, 4), rd(0x0200E644, 1), rd(0x03001150, 1), rd(0x0200D96E, 2), rd(0x0200D91C, 1)))
        g.cont()
    elif c == "quit":
        log("bye")
        os._exit(0)
    else:
        log("unknown cmd: %s" % cmdline)

def serve(rom="srwa.gba", run=None):
    os.makedirs(os.path.join(ROOT, "q"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "log"), exist_ok=True)
    for f in (QFILE, OUT, EVT):
        if os.path.exists(f): os.remove(f)
    log("启动 mgba-sdl: %s" % MGBA)
    proc = subprocess.Popen([MGBA, "-g", rom], cwd=run or RUN)
    STATE["proc"] = proc
    g = Gdb()
    STATE["gdb"] = g
    g.connect()
    hwnd = None
    for _ in range(40):
        hwnd = find_mgba_window(proc.pid)
        if hwnd: break
        time.sleep(0.5)
    STATE["hwnd"] = hwnd
    log("GDB已连接, 窗口=%s" % hwnd)
    g.cont()  # GDB模式下不continue游戏不跑
    log("游戏运行中")

    # 单线程循环: 命令与断点命中在同一线程处理 (避免双线程抢socket应答)
    while True:
        try:
            if os.path.exists(QFILE):
                with open(QFILE, "r", encoding="utf-8") as f:
                    lines = [l.strip() for l in f if l.strip()]
                os.remove(QFILE)
                for l in lines:
                    try:
                        handle(l)
                    except Exception as e:
                        log("cmd error [%s]: %r" % (l, e))
        except Exception as e:
            log("poll error: %r" % e)
        pkt = g.wait_stop(timeout=0.15)
        if pkt is None:
            continue
        r = g.regs()
        pc = r[15] if r else 0
        hit_addr = pc & ~1
        label = STATE["autobp"].get(hit_addr)
        if label is None:
            for cand in (pc - 1, pc + 1, pc + 2, pc - 2):
                label = STATE["autobp"].get(cand & ~1)
                if label:
                    hit_addr = cand & ~1
                    break
        if label is not None:
            r0 = r[0] & 0xFFFFFFFF if r else 0
            r1 = r[1] & 0xFFFFFFFF if r else 0
            r2 = r[2] & 0xFFFFFFFF if r else 0
            r3 = r[3] & 0xFFFFFFFF if r else 0
            lr = (r[14] - 1) & 0xFFFFFFFF if r else 0
            st = g.read(0x02005408, 4)
            cm = g.read(0x03001150, 1)
            aid = g.read(0x0200D96E, 2)
            evlog("%s | r0=%08x r1=%08x r2=%08x r3=%08x lr=%08x | scenestate=%s cmd=%s animID=%s" % (
                label, r0, r1, r2, r3, lr,
                st.hex() if st else "?", cm.hex() if cm else "?", aid.hex() if aid else "?"))
            g.cont()
        else:
            evlog("STOP %s pc=%08x (无标签断点, 已挂起)" % (pkt, pc))
            if STATE.get("stopauto"):
                STATE["stopauto"] = False
                log("停在断点: pc=%08x" % pc)
                continue
            g.cont()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve(sys.argv[2] if len(sys.argv) > 2 else "srwa.gba",
              sys.argv[3] if len(sys.argv) > 3 else None)
    else:
        print(__doc__)
