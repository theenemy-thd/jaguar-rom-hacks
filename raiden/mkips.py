#!/usr/bin/env python3
"""Make an IPS patch from an original and a patched ROM.
usage: mkips.py original.smc patched.sfc out.ips

The patched ROM may be bigger than the original (e.g. R-Type III 2 MiB ->
4 MiB SA-1): every byte past the original's end is written, with RLE records
for runs of one value, so the patched file always comes out at full size."""
import sys

a = open(sys.argv[1], 'rb').read()
b = open(sys.argv[2], 'rb').read()
if len(a) % 0x8000 == 512:
    a = a[512:]
assert len(b) >= len(a), 'patched ROM is smaller than the original'
out = bytearray(b'PATCH')

def rec(i, data):
    if i == 0x454F46:                   # offset spelling "EOF" is reserved
        i -= 1; data = b[i:i + 1] + data
    out.extend(i.to_bytes(3, 'big') + len(data).to_bytes(2, 'big') + data)

i = 0
while i < len(a):                       # changed bytes inside the original
    if a[i] == b[i]:
        i += 1
        continue
    j = i
    while j < len(a) and j - i < 0xFFFF and a[j] != b[j]:
        j += 1
    rec(i, b[i:j])
    i = j
while i < len(b):                       # new data past the original's end
    j = i
    while j < len(b) and j - i < 0xFFFF and b[j] == b[i]:
        j += 1
    if j - i >= 16 and i != 0x454F46:   # RLE record: size 0, run length, value
        out += i.to_bytes(3, 'big') + b'\0\0' + (j - i).to_bytes(2, 'big') + b[i:i + 1]
        i = j
        continue
    j = i
    while j < len(b) and j - i < 0xFFFF:
        if j + 16 <= len(b) and b[j:j + 16] == b[j:j + 1] * 16 and j > i:
            break
        j += 1
    rec(i, b[i:j])
    i = j
out += b'EOF'
open(sys.argv[3], 'wb').write(out)
print('%s: %d bytes' % (sys.argv[3], len(out)))
