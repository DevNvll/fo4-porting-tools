#!/usr/bin/env python3
"""Search each package entry of Marathon for a text (ASCII and UTF-16), in each letter case.

    ./port marathon notes scan-text TEXT [TEXT ...] > data/marathon/extract/notes/scan_NAME.txt
    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/notes/scan_text.py TEXT [TEXT ...] > ...

It prints the tag, its class, its type, its size and its package for each entry with a text.
It reads each entry of each package but the audio packages (w64_sr_audio): this needs minutes.
A short text (M77) gives random matches in binary data: use a long one (Omnipositor, ar_m77).
"""
import sys

if '-h' in sys.argv[1:] or '--help' in sys.argv[1:]:
    print(__doc__.strip())
    sys.exit(0)
import re
import time
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # marathon/extract: the module m2x
import numpy as np  # noqa: E402
import m2x  # noqa: E402

texts = [a for a in sys.argv[1:] if not a.startswith('--')]
skip = ('w64_sr_audio',)
pm = m2x.open_packages()
e = pm.entries
pattern = re.compile(b'|'.join(re.escape(t.encode()) for t in texts) + b'|' + b'|'.join(re.escape(t.encode('utf-16-le')) for t in texts), re.I)
names = {}
start = time.time()
done = found = total = 0
order = np.argsort(e['pkg_id'], kind='stable')
for i in order:
    pkg_id = int(e['pkg_id'][i])
    if pkg_id not in names:
        names[pkg_id] = pm.pkg_name(pkg_id)
    if names[pkg_id].startswith(skip) or e['size'][i] < 8:
        continue
    tag = int(e['tag'][i])
    try:
        data = pm.read(tag, cache=False)
    except Exception:
        continue
    done += 1
    total += len(data)
    for m in pattern.finditer(data):
        found += 1
        print('%08X class %08X type %d/%d size %d %s at 0x%X: %r' % (tag, int(e['reference'][i]), e['type'][i], e['subtype'][i], len(data), names[pkg_id], m.start(), data[max(0, m.start() - 24):m.end() + 40]), flush=True)
print('entries read: %d, %.1f GB, %d places, %.0f s' % (done, total / 1e9, found, time.time() - start), file=sys.stderr)
