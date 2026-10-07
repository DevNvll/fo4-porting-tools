"""Find the dye tables of this game build. Read-only.

    ./port destiny notes dyes-explore ITEM_HASH ...

The program imports d2x (destiny/extract). With no ./port, run destiny/port/notes/dyes_explore.py
with the Python of the d2x environment (data/destiny/extract/venv/bin/python) and with
PYTHONPATH=destiny/extract.
"""
import sys
import struct

if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip())
    raise SystemExit(0 if len(sys.argv) > 1 else 2)

import numpy as np

from d2x import pkg, investment
from d2x.tag import Reader

CHANNELS = 0x80805BDE            # SDyeChannels of Shadowkeep in the Charm source ("DE5B8080")
NAMES = {662199250: 'ArmorPlate', 1367384683: 'ArmorSuit', 218592586: 'ArmorCloth', 1667433279: 'Weapon1',
         1667433278: 'Weapon2', 1667433277: 'Weapon3'}

pm = pkg.PackageManager()
inv = investment.Investment(pm)
entries = pm.entries
print('entries dtype', entries.dtype.names)

# 1. the dye arrays of each item
used = set()
for text in sys.argv[1:]:
    item = inv.item(int(text))
    r = Reader(pm.read(item.definition, cache=False))
    block = r.rel(0x88)
    print('item %s %s: translation block at 0x%X' % (text, item.name, block))
    for label, off in (('custom', 0x28), ('default', 0x38), ('locked', 0x48)):
        rows = [(r.i16(o), r.i16(o + 2)) for o in r.array_items(block + off, 4)]
        used.update(d for _, d in rows)
        print('   %-8s dyes (channel index, dye index): %s' % (label, rows))

# 2. the channel table
rows = entries[(entries['reference'] == CHANNELS) & (entries['type'] == 8)]
print('tags of the class %08X: %d' % (CHANNELS, len(rows)))
channels = []
for tag in rows['tag']:
    r = Reader(pm.read(int(tag)))
    count, start, cls = r.array(0x08)
    channels = [r.u32(start + i * 4) for i in range(count)]
    print('   tag %08X: %d channels, element class %08X: %s' % (int(tag), count, cls, [NAMES.get(c, '%d' % c) for c in channels][:40]))

# 3. the art dye reference table: 8-byte rows whose second word is a key of the global tag assignments
assign = inv._assignments
keys = np.array(sorted(assign), dtype=np.uint64)
classes, counts = np.unique(entries['reference'][entries['type'] == 8], return_counts=True)
rare = set(int(c) for c, n in zip(classes, counts) if n <= 4)
need = max(used) if used else 0
print('dye indexes of the items: %s (the table needs more than %d rows); rare classes: %d' % (sorted(used), need, len(rare)))
cands = entries[(entries['type'] == 8) & np.isin(entries['reference'], np.array(sorted(rare), dtype=entries['reference'].dtype))]
for row in cands:
    tag = int(row['tag'])
    if row['size'] < 0x18 + (need + 1) * 8:
        continue
    try:
        data = pm.read(tag, cache=False)
    except Exception:
        continue
    r = Reader(data)
    try:
        count, start, cls = r.array(0x08)
    except Exception:
        continue
    if count <= need or start + count * 8 > len(data):
        continue
    words = np.frombuffer(data, dtype='<u4', count=count * 2, offset=start).reshape(count, 2).astype(np.uint64)
    hit = np.isin(words[:, 1], keys).mean()
    if hit > 0.5:
        print('   candidate tag %08X class %08X: %d rows, element class %08X, %.0f %% of the second words are assignment keys' % (
            tag, int(row['reference']), count, cls, 100 * hit))
        for d in sorted(used):
            a, b = int(words[d, 0]), int(words[d, 1])
            t = assign.get(b, 0)
            print('      dye %5d: art dye hash %08X, manifest hash %08X -> tag %08X (class %08X, %d bytes)' % (
                d, a, b, t, pm.reference(t) if t and pm.exists(t) else 0, len(pm.read(t)) if t and pm.exists(t) else 0))
