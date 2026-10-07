#!/usr/bin/env python3
"""Find the tags of Marathon that have a 32-bit value (a tag, a string hash, ...).

    ./port marathon notes find-value VALUE [VALUE ...] [--all] [--pkg PREFIX]
    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/notes/find_value.py VALUE [VALUE ...] [--all] [--pkg PREFIX]

It reads each entry of type 8 (with --all: each entry below 64 MB) and prints the tag, its class,
its size, its package and each offset of the value. The value can be at an offset that is not
a multiple of 4.
"""
import struct
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # marathon/extract: the module m2x
import m2x  # noqa: E402

args = sys.argv[1:]
everything = '--all' in args
prefix = args[args.index('--pkg') + 1] if '--pkg' in args else ''
values = [int(a, 16) for a in args if not a.startswith('--') and a != prefix]
needles = [struct.pack('<I', v) for v in values]
pm = m2x.open_packages()
e = pm.entries
names = {}
for i in range(len(e)):
    if (not everything and e['type'][i] != 8) or e['size'][i] > 64 << 20 or e['size'][i] < 4:
        continue
    pkg_id = int(e['pkg_id'][i])
    if pkg_id not in names:
        names[pkg_id] = pm.pkg_name(pkg_id)
    if 'sr_audio' in names[pkg_id] or not names[pkg_id].startswith('w64_' + prefix if prefix and not prefix.startswith('w64') else prefix):
        continue
    tag = int(e['tag'][i])
    try:
        data = pm.read(tag, cache=False)
    except Exception:
        continue
    for v, needle in zip(values, needles):
        at, places = data.find(needle), []
        while at >= 0 and len(places) < 12:
            places.append(at)
            at = data.find(needle, at + 1)
        if places:
            print('%08X class %08X type %d/%d size %d %s has %08X at %s' % (tag, int(e['reference'][i]), e['type'][i], e['subtype'][i], len(data),
                                                                       names[pkg_id], v, ' '.join('0x%X' % p for p in places)), flush=True)
