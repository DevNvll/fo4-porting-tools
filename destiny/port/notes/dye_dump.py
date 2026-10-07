"""Dump the tag of a dye of this game build. Read-only.

    ./port destiny notes dye-dump WRAPPER_TAG ...

The program imports d2x (destiny/extract). With no ./port, run destiny/port/notes/dye_dump.py
with the Python of the d2x environment (data/destiny/extract/venv/bin/python) and with
PYTHONPATH=destiny/extract.
"""
import sys
import struct
if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip())
    raise SystemExit(0 if len(sys.argv) > 1 else 2)

import numpy as np
from d2x import pkg
from d2x.tag import Reader

pm = pkg.PackageManager()
for text in sys.argv[1:]:
    tag = int(text, 16)
    data = pm.read(tag)
    print('=== wrapper %08X class %08X %d bytes: %s' % (tag, pm.reference(tag), len(data), ' '.join('%08X' % w for w in struct.unpack_from('<%dI' % (len(data) // 4), data))))
    inner = struct.unpack_from('<I', data, 0x10)[0]
    while True:
        d = pm.read(inner)
        print('  inner %08X class %08X type %s %d bytes' % (inner, pm.reference(inner), None, len(d)))
        words = struct.unpack_from('<%dI' % (len(d) // 4), d)
        if len(d) > 64:
            break
        print('     ', ' '.join('%08X' % w for w in words))
        nxt = [w for w in words if 0x80800000 < w <= 0x81FFFFFF and pm.exists(w) and w != inner]
        if not nxt:
            break
        inner = nxt[0]
    r = Reader(d)
    for o in range(0, min(len(d), 0x400), 16):
        row = struct.unpack_from('<4I', d, o) if o + 16 <= len(d) else ()
        fl = struct.unpack_from('<4f', d, o) if o + 16 <= len(d) else ()
        notes = []
        for w in row:
            if 0x80800000 < w <= 0x81FFFFFF and pm.exists(w):
                notes.append('%08X->class %08X' % (w, pm.reference(w)))
        print('   +0x%03X  %s   %s  %s' % (o, ' '.join('%08X' % w for w in row), ' '.join('%9.4f' % f if abs(f) < 1e6 and (abs(f) > 1e-6 or f == 0) else '        .' for f in fl), '; '.join(notes)))
