"""Print the values of the dyes of an item of this game build. Read-only.

    ./port destiny notes dye-values ITEM_HASH ...

The program imports d2x (destiny/extract). With no ./port, run destiny/port/notes/dye_values.py
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

ART_DYES = 0x80805DE8
CHANNELS = 0x80805BDE
NAMES = {1667433279: 'Weapon1', 1667433278: 'Weapon2', 1667433277: 'Weapon3'}
FIELDS = ['DetailDiffuseTransform', 'DetailNormalTransform', 'SpecAaTransform', 'PrimaryAlbedoTint', 'PrimaryEmissiveTintColorAndIntensityBias',
          'PrimaryMaterialParams', 'PrimaryMaterialAdvancedParams', 'PrimaryRoughnessRemap', 'PrimaryWornAlbedoTint', 'PrimaryWearRemap',
          'PrimaryWornRoughnessRemap', 'PrimaryWornMaterialParameters', 'SecondaryAlbedoTint', 'SecondaryEmissiveTintColorAndIntensityBias',
          'SecondaryMaterialParams', 'SecondaryMaterialAdvancedParams', 'SecondaryRoughnessRemap', 'SecondaryWornAlbedoTint', 'SecondaryWearRemap',
          'SecondaryWornRoughnessRemap', 'SecondaryWornMaterialParameters']
pm = pkg.PackageManager()
inv = investment.Investment(pm)
r = Reader(pm.read(inv._largest(CHANNELS)))
count, start, _ = r.array(0x08)
channels = [r.u32(start + i * 4) for i in range(count)]
data = pm.read(inv._largest(ART_DYES))
r = Reader(data)
count, start, _ = r.array(0x08)
art = np.frombuffer(data, dtype='<u4', count=count * 2, offset=start).reshape(count, 2)


def dye_tag(index):
    wrapper = inv._assignments.get(int(art[index, 1]), 0)
    tag = wrapper
    for _ in range(4):
        d = pm.read(tag)
        if len(d) > 64:
            return tag
        words = struct.unpack_from('<%dI' % (len(d) // 4), d)
        nxt = [w for w in words if 0x80800000 < w <= 0x81FFFFFF and pm.exists(w) and w != tag]
        if not nxt:
            return 0
        tag = nxt[0]
    return 0


for text in sys.argv[1:]:
    item = inv.item(int(text))
    rr = Reader(pm.read(item.definition, cache=False))
    block = rr.rel(0x88)
    print('======== %s' % item.name)
    for label, off in (('default', 0x38), ('locked', 0x48), ('custom', 0x28)):
        for o in rr.array_items(block + off, 4):
            ch, di = rr.i16(o), rr.i16(o + 2)
            tag = dye_tag(di)
            d = pm.read(tag)
            r = Reader(d)
            name_at = r.rel(0x08)
            name = d[name_at:d.index(b'\0', name_at)].decode('ascii', 'replace') if name_at else ''
            tex = [(r.u32(o2), '%08X' % r.u32(o2 + 4)) for o2 in r.array_items(0x40, 8)]
            n, at, cls = r.array(0x88)
            vals = np.frombuffer(d, dtype='<f4', count=n * 4, offset=at).reshape(n, 4)
            print('--- %s dye, channel %s, dye index %d, tag %08X (class %08X), name "%s", textures %s, %d values (class %08X)' % (
                label, NAMES.get(channels[ch], channels[ch]), di, tag, pm.reference(tag), name, tex, n, cls))
            for i in range(n):
                print('     %2d %-42s %s' % (i, FIELDS[i] if i < len(FIELDS) else '', np.round(vals[i], 4).tolist()))
            for lab2, off2 in (('array 0x58', 0x58), ('array 0x68', 0x68)):
                n2, at2, cls2 = r.array(off2)
                print('     %s: count %d class %08X: %s' % (lab2, n2, cls2, d[at2:at2 + min(n2 * 8, 64)].hex()))
