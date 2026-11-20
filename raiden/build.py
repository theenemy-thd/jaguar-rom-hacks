#!/usr/bin/env python3
"""Build the Raiden (World) Jaguar trainer.

usage: build.py <clean Raiden (World).j64> [out.j64]

Assembles src/trainer.s at $A00000, grows the ROM from 2 MB to 4 MB, puts the
code at file offset $200000, patches the boot stub's "jmp $3000" to enter the
menu, and writes release/ (patched ROM + IPS).
"""
import os, re, subprocess, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, 'build')
os.makedirs(B, exist_ok=True)

CLEAN_CRC = 0x0509C85E
BASE = 0x801000                 # cart address of our code: spare FF space
                                # inside the universal header ($801000-$801FFF)
FOFS = BASE - 0x800000          # file offset
STUB_PATCH = 0x2138             # file offset of "st.b $2c6(a4) / jmp $3000.w"
STUB_ORIG = bytes.fromhex('50ec02c64ef83000')

CONFIG = {
    'TITLE': '"RAIDEN+5H BY TREX"',
    'DEF_AUTOFIRE': 1,          # autofire ON by default
    'NOMENU': 0,                # 1: no menu, autofire only (forced on)
}
for a in sys.argv[3:]:          # KEY=VALUE overrides (tests)
    k, v = a.split('=', 1); CONFIG[k] = v

def font_inc():
    src = os.path.join(HERE, 'font.inc')
    out = []
    for line in open(src):
        m = re.match(r'\s*\.byte\s+(.*?)\s*;', line)
        if m:
            out.append('        .byte ' + m.group(1).replace('$', '0x'))
    assert len(out) == 64, len(out)
    return '\n'.join(out) + '\n'

def objlist():
    OBJ = 0x0F0000; FB = 0x100000; W, H = 320, 240
    stop = OBJ + 16
    ypos = 54                   # half-lines, as the game's boot logo
    p0 = (0) | (ypos << 3) | (H << 14) | ((stop >> 3) << 24) | ((FB >> 3) << 43)
    dw = W // 8                 # 8 bpp: 8 pixels per phrase
    p1 = (0) | (3 << 12) | (1 << 15) | (dw << 18) | (dw << 28)
    p2 = 4                      # stop object
    L = []
    for p in (p0, p1, p2):
        L.append('        .long 0x%08x,0x%08x' % (p >> 32, p & 0xffffffff))
    return '\n'.join(L) + '\n'

def sh(*cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(' '.join(cmd) + '\n' + r.stdout + r.stderr)

def main():
    clean = open(sys.argv[1], 'rb').read()
    assert zlib.crc32(clean) == CLEAN_CRC, 'not Raiden (World) [CRC32 0509C85E]'
    assert clean[STUB_PATCH:STUB_PATCH + 8] == STUB_ORIG
    open(os.path.join(B, 'font.inc'), 'w').write(font_inc())
    open(os.path.join(B, 'objlist.inc'), 'w').write(objlist())
    open(os.path.join(B, 'config.inc'), 'w').write(
        ''.join('        .equ %s,%s\n' % (k, v) for k, v in CONFIG.items() if k != 'TITLE')
        + '#define TITLE %s\n' % CONFIG['TITLE'])
    # TITLE goes through the C preprocessor-free path: substitute it directly
    s = open(os.path.join(HERE, 'src', 'trainer.s')).read()
    s = s.replace('.asciz TITLE', '.asciz %s' % CONFIG['TITLE'])
    cfg = ''.join('        .equ %s,%s\n' % (k, v) for k, v in CONFIG.items() if k != 'TITLE')
    open(os.path.join(B, 'config.inc'), 'w').write(cfg)
    open(os.path.join(B, 'trainer.s'), 'w').write(s)
    os.chdir(HERE)
    sh('m68k-linux-gnu-as', '-m68000', '--register-prefix-optional', '-I', '.',
       '-o', 'build/trainer.o', 'build/trainer.s', '-al=build/trainer.lst')
    sh('m68k-linux-gnu-ld', '-Ttext=0x%x' % BASE, '-e', 'TrainerEntry', '--no-relax',
       '-o', 'build/trainer.elf', 'build/trainer.o')
    sh('m68k-linux-gnu-objcopy', '-O', 'binary', '-j', '.text', 'build/trainer.elf', 'build/trainer.bin')
    nm = subprocess.run(['m68k-linux-gnu-nm', 'build/trainer.elf'], capture_output=True, text=True).stdout
    syms = {l.split()[2]: int(l.split()[0], 16) for l in nm.splitlines() if len(l.split()) == 3}
    open('build/trainer.sym', 'w').write(''.join('%06X %s\n' % (v, k) for k, v in sorted(syms.items(), key=lambda x: x[1])))
    code = open('build/trainer.bin', 'rb').read()
    entry = syms['TrainerEntry']
    rom = bytearray(clean)          # stays 2 MB
    rom[STUB_PATCH:STUB_PATCH + 8] = b'\x4e\xf9' + entry.to_bytes(4, 'big') + b'\x4e\x71'
    # The boot ROM checks the commercial header against the whole 2 MB, so any
    # change gives the red "Jaguar" screen on real hardware.  The universal
    # header (same ROM config and $802000 start) boots any cart code.
    uh = open(os.path.join(HERE, 'universal_header.bin'), 'rb').read()
    assert len(uh) == 0x2000 and uh[0x400:0x408] == clean[0x400:0x408]
    assert set(clean[0x408:0x2000]) <= {0, 0xff}
    rom[0:0x2000] = uh
    assert len(code) <= 0x1000 and set(uh[FOFS:FOFS + len(code)]) == {0xff}
    rom[FOFS:FOFS + len(code)] = code
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'release', 'Raiden (World) [Trainer].j64')
    open(out, 'wb').write(rom)
    print('code %d bytes at $%06X, entry $%06X -> %s' % (len(code), BASE, entry, out))
    print('CRC32 %08X' % zlib.crc32(rom))

if __name__ == '__main__':
    main()
