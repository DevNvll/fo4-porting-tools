#!/usr/bin/env python3
"""For each tag class of Marathon: the count, the sizes, the package groups, and the classes of the tags that its entries name.

    ./port marathon notes class-graph [SAMPLES] > data/marathon/extract/notes/class_graph.txt
    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/notes/class_graph.py [SAMPLES] > ...

A value of an entry is a tag when it has the form of a tag hash and the packages have it. The
program reads SAMPLES entries of each class (default 12).
"""
import sys

if '-h' in sys.argv[1:] or '--help' in sys.argv[1:]:
    print(__doc__.strip())
    sys.exit(0)
import collections
import re
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # marathon/extract: the module m2x
import numpy as np  # noqa: E402
import m2x  # noqa: E402

samples = int(sys.argv[1]) if len(sys.argv) > 1 else 12
pm = m2x.open_packages()
e = pm.entries
tags = np.ascontiguousarray(e['tag'])
by_class = collections.defaultdict(list)
for i in np.nonzero(e['type'] == 8)[0]:
    by_class[int(e['reference'][i])].append(i)
kind = {}
for i in range(len(e)):
    pass


def label(tag):
    row = pm.entry(tag)
    if row is None:
        return None
    if row['type'] == 8:
        return '%08X' % int(row['reference'])
    return 't%d/%d' % (row['type'], row['subtype'])


rng = np.random.default_rng(7)
for cls, rows in sorted(by_class.items(), key=lambda kv: -len(kv[1])):
    sizes = np.array([int(e['size'][i]) for i in rows])
    groups = collections.Counter(re.sub(r'(_unp\d+)?_[0-9a-f]{4}(_\w\w)?_\d+\.pkg$|_unp\d+_\d+\.pkg$', '', pm.pkg_name(int(e['pkg_id'][i]))) for i in rows[:2000])
    pick = rows if len(rows) <= samples else [rows[j] for j in rng.choice(len(rows), samples, replace=False)]
    out = collections.Counter()
    inner = collections.Counter()
    for i in pick:
        try:
            data = pm.read(int(e['tag'][i]), cache=False)
        except Exception:
            continue
        words = np.frombuffer(data[:len(data) & ~3], dtype='<u4')
        cand = words[(words > 0x80800000) & (words <= 0x81FFFFFF)]
        seen = set()
        for v in cand.tolist():
            if (v & 0xFFFF0000) == 0x80800000:
                inner[v] += 1            # a class number inside the entry (the class of a table or of a block)
                continue
            lab = label(v)
            if lab and (lab, v) not in seen:
                seen.add((lab, v))
                out[lab] += 1
    print('%08X  count %6d  size min %d median %d max %d  %s' % (cls, len(rows), sizes.min(), int(np.median(sizes)), sizes.max(),
                                                             ', '.join('%s %d' % kv for kv in groups.most_common(4))))
    if out:
        print('    names tags of: ' + ', '.join('%s x%d' % kv for kv in out.most_common(14)))
    if inner:
        print('    has the class numbers: ' + ', '.join('%08X x%d' % kv for kv in inner.most_common(14)))
