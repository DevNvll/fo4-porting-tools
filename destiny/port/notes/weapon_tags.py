"""Find the weapon tags that a weapon pattern entity lists: each 32-bit word of its resources
that is a tag of the weapon tag tree of its first-person rigs. Read-only.

    ./port destiny notes weapon-tags MANIFEST.json

The program imports d2x (destiny/extract). With no ./port, run destiny/port/notes/weapon_tags.py
with the Python of the d2x environment (data/destiny/extract/venv/bin/python) and with
PYTHONPATH=destiny/extract.
"""
import json
import sys

if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip())
    raise SystemExit(0 if len(sys.argv) > 1 else 2)

import numpy as np

from d2x import pkg, entity as ent, graph as gr
from d2x.tag import fnv1

m = json.load(open(sys.argv[1]))
pm = pkg.PackageManager()
names = {fnv1(w): w for w in list(gr.TAG_WORDS) + ['auto', 'carbine']}
rig = ent.read_entity(pm, int(m['first_person'][0]['entity'], 16))
tree = None
for resource in rig.by_kind(ent.ANIMATION):
    t = gr.find_tag_tree(pm, resource.data)
    if t:
        tree = gr.read_tag_tree(pm.read(t))
index = {tag: i for i, (tag, _) in enumerate(tree)}


def path(tag):
    out = []
    i = index[tag]
    while i != 65535 and i < len(tree):
        out.append(names.get(tree[i][0], '%08X' % tree[i][0]))
        i = tree[i][1]
    return '/'.join(reversed(out))


for label, tag in (('pattern', int(m['pattern']['entity'], 16)),):
    e = ent.read_entity(pm, tag)
    print(label, '%08X' % tag, 'resources', len(e.resources))
    for n, resource in enumerate(e.resources):
        words = np.frombuffer(resource.data[:len(resource.data) & ~3], dtype='<u4')
        hits = [(int(i) * 4, int(w)) for i, w in enumerate(words) if int(w) in index and int(w) != tree[0][0]]
        kind = getattr(resource, 'kind', None)
        print('  resource %d kind %s bytes %d: %d words of the tag tree' % (n, ('%08X' % kind) if isinstance(kind, int) else kind, len(resource.data), len(hits)))
        for offset, w in hits:
            print('      +0x%04X %08X %s' % (offset, w, path(w)))
