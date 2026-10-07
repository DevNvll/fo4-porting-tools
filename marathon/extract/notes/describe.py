#!/usr/bin/env python3
"""Describe tags of Marathon: the texts, the tags that each one names (32-bit and 64-bit) and its inner class numbers.

    ./port marathon notes describe TAG [TAG ...] [--limit N]
    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/notes/describe.py TAG [TAG ...] [--limit N]

The table data/marathon/extract/notes/tag64.tsv must be there (setup.sh makes it).
"""
import sys

if '-h' in sys.argv[1:] or '--help' in sys.argv[1:]:
    print(__doc__.strip())
    sys.exit(0)
import collections
import re
import struct
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # marathon/extract: the module m2x
import numpy as np  # noqa: E402
import m2x  # noqa: E402

args = sys.argv[1:]
limit = int(args[args.index('--limit') + 1]) if '--limit' in args else 60
tags = [int(a, 16) for a in args if not a.startswith('--') and len(a) == 8]
pm = m2x.open_packages()
t64 = m2x.tag64_table()


def lab(v):
    r = pm.entry(int(v))
    return '%08X' % int(r['reference']) if r['type'] == 8 else 't%d/%d' % (r['type'], r['subtype'])


for tag in tags:
    d = pm.read(tag)
    r = pm.entry(tag)
    print('== %08X class %08X size %d %s' % (tag, int(r['reference']), len(d), pm.pkg_name(tag)))
    for m in re.finditer(rb'[\x20-\x7e]{8,}', d):
        s = m.group()
        if b'\\' in s or b'/' in s or b'.tft' in s:
            print('   text 0x%04X %s' % (m.start(), s.decode('latin1')[:170]))
    w = np.frombuffer(d[:len(d) & ~3], dtype='<u4')
    found = [(i * 4, int(v)) for i, v in enumerate(w) if 0x80810000 < v <= 0x81FFFFFF and pm.exists(int(v))]
    print('   tags (32-bit): %s' % dict(collections.Counter(lab(v) for o, v in found)))
    for o, v in found[:limit]:
        print('      0x%04X %08X %s size %d %s' % (o, v, lab(v), int(pm.entry(v)['size']), pm.pkg_name(v)[4:]))
    found = [(o, h) for o in range(0, len(d) - 8, 4) for h in [struct.unpack_from('<Q', d, o)[0]] if h in t64]
    print('   tags (64-bit): %d' % len(found))
    for o, h in found[:limit]:
        t, cl = t64[h]
        print('      0x%04X %016X -> %08X class %08X size %d %s' % (o, h, t, cl, int(pm.entry(t)['size']) if pm.exists(t) else -1, pm.pkg_name(t)[4:]))
    inner = collections.Counter(int(v) for v in w if (v & 0xFFFF0000) == 0x80800000 and v != 0x8080BFCD)
    print('   class numbers: ' + ' '.join('%08X x%d' % kv for kv in inner.most_common(60)))
