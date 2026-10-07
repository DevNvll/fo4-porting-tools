"""Index of each animation clip tag of the game: tag, name hash, frames, nodes, controls, package.

    ./port destiny notes third-clip-index OUT.npy

The program imports d2x (destiny/extract). With no ./port, run destiny/port/notes/third_clip_index.py
with the Python of the d2x environment (data/destiny/extract/venv/bin/python) and with
PYTHONPATH=destiny/extract.

The body reload of a weapon is a clip of 72 nodes with the frame count of the reload clip of
the gun parts (the clip 80BB277E has the name hash 7A937C43 of the reload of the Khvostov gun).
"""
import struct, sys, time
if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip())
    raise SystemExit(0 if len(sys.argv) > 1 else 2)

import numpy as np
from d2x import pkg, entity as ent
pm = pkg.PackageManager()
tags = pm.by_reference(ent.ANIMATION_CLIP)
print('clip tags', len(tags), flush=True)
rows = []
t0 = time.time()
for i, tag in enumerate(tags):
    try:
        data = pm.read(tag, cache=False)
    except KeyError:
        continue
    if len(data) < 0x142:
        continue
    h, = struct.unpack_from('<I', data, 0x120)
    frames, nodes, controls = struct.unpack_from('<3H', data, 0x13C)
    rows.append((tag, h, frames, nodes, controls, (tag - 0x80800000) >> 13, len(data)))
    if i % 20000 == 0:
        print(i, round(time.time() - t0), 's', flush=True)
a = np.array(rows, dtype=np.int64)
np.save(sys.argv[1], a)
print('saved', a.shape, round(time.time() - t0), 's')
