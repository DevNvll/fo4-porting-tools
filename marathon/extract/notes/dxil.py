#!/usr/bin/env python3
"""Print the pixel shader (or the vertex shader) of a material of Marathon as LLVM text.

    ./port marathon notes dxil MATERIAL [--vs] [-o FILE.ll]
    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/notes/dxil.py MATERIAL [--vs] [-o FILE.ll]

A shader of Marathon is a DXBC file with a DXIL part: LLVM bitcode. The program `llvm-dis`
(LLVM 22 here) reads it after one change: the data layout text of DXIL has `i8:32` and
`i16:32`, which a new LLVM does not accept. The text is in the bit stream with 12 bits for each
character (two parts of 6 bits), so the program changes the characters in place (`i8:08`,
`i16:16`). The file of the game is not changed.

How to read the result: `dx.op.sample` reads a texture (the handle gives its slot),
`dx.op.cbufferLoadLegacy` reads a vector of a constant buffer (the buffer 0 is that of the
material: m2x.material_constants), and `dx.op.storeOutput` writes a value of a render target:
target 0 the color, target 1 the normal (its length has the smoothness), target 2 the metal
value (x) and the occlusion (y).
"""
import shutil
import struct
import subprocess
import tempfile
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # marathon/extract: the module m2x

import numpy as np  # noqa: E402

import m2x  # noqa: E402


def bitcode(shader):
    """The LLVM bitcode of a DXBC file with a DXIL part."""
    count, = struct.unpack_from('<I', shader, 0x1C)
    for i in range(count):
        offset, = struct.unpack_from('<I', shader, 0x20 + i * 4)
        size, = struct.unpack_from('<I', shader, offset + 4)
        if shader[offset:offset + 4] == b'DXIL':
            body = shader[offset + 8:offset + 8 + size]
            start, length = struct.unpack_from('<II', body, 16)
            return body[8 + start:8 + start + length]
    raise SystemExit('the shader has no DXIL part')


def patched(code):
    bits = np.unpackbits(np.frombuffer(code, np.uint8), bitorder='little')

    def text(value):
        out = []
        for ch in value.encode():
            v = (ch & 31) | 32 | ((ch >> 5) << 6)
            out += [(v >> i) & 1 for i in range(12)]
        return np.array(out, np.uint8)
    for old, new in (('i8:32', 'i8:08'), ('i16:32', 'i16:16')):
        a, b = text(old), text(new)
        for at in np.nonzero((np.lib.stride_tricks.sliding_window_view(bits, len(a)) == a).all(axis=1))[0]:
            bits[at:at + len(a)] = b
    return np.packbits(bits, bitorder='little').tobytes()


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__.strip())
        raise SystemExit(0 if args else 2)
    if not shutil.which('llvm-dis'):
        raise SystemExit('The program llvm-dis is not in the PATH. It is a part of LLVM: install LLVM.')
    material = int(args[0], 16)
    out = args[args.index('-o') + 1] if '-o' in args else None
    pm = m2x.open_packages()
    data = pm.read(material)
    header, = struct.unpack_from('<I', data, 0x58 if '--vs' in args else 0x278)
    if not pm.exists(header) or not pm.exists(pm.reference(header)):
        raise SystemExit('the material %08X has no such shader' % material)
    with tempfile.NamedTemporaryFile(suffix='.bc') as f:
        f.write(patched(bitcode(pm.read(pm.reference(header)))))
        f.flush()
        result = subprocess.run(['llvm-dis', f.name, '-o', out or '-'], stdin=subprocess.DEVNULL, capture_output=not out, text=True)
    if result.returncode:
        raise SystemExit(result.stderr)
    if not out:
        sys.stdout.write(result.stdout)


if __name__ == '__main__':
    main()
