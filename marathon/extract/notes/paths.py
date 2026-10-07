#!/usr/bin/env python3
"""List the development paths in the tags of Marathon (texts such as content\\sandbox\\...\\NAME.pattern.tft).

    ./port marathon notes paths PREFIX [PREFIX ...] > data/marathon/extract/notes/paths.tsv
    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/notes/paths.py PREFIX [PREFIX ...] > ...

It reads each entry of type 8 in the packages whose name starts with a PREFIX (w64_sr_gear, ...)
and prints: tag, class, size, package, offset, text. A text is 8 or more printable characters
with a `\\`, a `/` or a `.tft`.
"""
import sys

if '-h' in sys.argv[1:] or '--help' in sys.argv[1:]:
    print(__doc__.strip())
    sys.exit(0)
import re
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # marathon/extract: the module m2x
import numpy as np  # noqa: E402
import m2x  # noqa: E402

prefixes = tuple(sys.argv[1:])
pm = m2x.open_packages()
e = pm.entries
text = re.compile(rb'[\x20-\x7e]{8,}')
names = {}
for i in np.nonzero(e['type'] == 8)[0]:
    pkg_id = int(e['pkg_id'][i])
    if pkg_id not in names:
        names[pkg_id] = pm.pkg_name(pkg_id)
    if not names[pkg_id].startswith(prefixes):
        continue
    tag = int(e['tag'][i])
    try:
        data = pm.read(tag, cache=False)
    except Exception:
        continue
    for m in text.finditer(data):
        s = m.group()
        if b'\\' in s or b'/' in s or b'.tft' in s:
            print('%08X\t%08X\t%d\t%s\t0x%X\t%s' % (tag, int(e['reference'][i]), len(data), names[pkg_id], m.start(), s.decode('latin1')))
