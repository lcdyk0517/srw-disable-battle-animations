import sys
from capstone import *
ORIG = open(r'D:\GBA\emu\run\srwa.gba', 'rb').read()
md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
start = int(sys.argv[1], 16)
end = int(sys.argv[2], 16)
marks = set(int(m, 16) for m in sys.argv[3:]) if len(sys.argv) > 3 else set()
for i in md.disasm(ORIG[start:end], 0x08000000 + start):
    mark = ' <<<' if i.address in marks else ''
    print('%08x  %-8s %s %s%s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str, mark))
