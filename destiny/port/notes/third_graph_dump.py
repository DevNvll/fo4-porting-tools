"""Each state of the third-person graph of the player body, with each leaf and its conditions.

    ./port destiny notes third-graph-dump OUT.json

The program imports d2x (destiny/extract). With no ./port, run destiny/port/notes/third_graph_dump.py
with the Python of the d2x environment (data/destiny/extract/venv/bin/python) and with
PYTHONPATH=destiny/extract.
"""
import json, sys, struct, collections
if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip())
    raise SystemExit(0 if len(sys.argv) > 1 else 2)

import numpy as np
from d2x import pkg, entity as ent, graph as gr
from d2x.tag import Reader, fnv1
pm = pkg.PackageManager()
BODY, RES, SET, GRAPH = 0x80BAB778, 0x80EF62E5, 0x80C0CA92, 0x80BB2C46
clips = ent.animation_set_clips(pm, SET)
entries = gr.read_set_entries(pm.read(SET))        # (name hash, seconds, clip index)
data = pm.read(GRAPH); r = Reader(data)
name_count, names_at, _ = r.array(0x08)
state_count, states_at, _ = r.array(0x18)
names = collections.defaultdict(list)
for i in range(name_count):
    names[r.u32(names_at + i * 8 + 4)].append(r.u32(names_at + i * 8))
out = []
for index in range(state_count):
    kind = r.u64(states_at + index * 16)
    base = r.rel(states_at + index * 16 + 8)
    st = {'index': index, 'names': ['%08X' % h for h in names.get(index, [])], 'kind': int(kind), 'leaves': []}
    out.append(st)
    if kind == 1:
        st['leaves'].append({'conditions': [], 'clips': gr._clip_list(r, base)})
        continue
    leaf = [gr._clip_list(r, o) for o in r.array_items(base, 16)]
    dims = [r.u8(o) for o in r.array_items(base + 0x10, 1)]
    node_count, nodes_at, _ = r.array(base + 0x20)
    group_count, groups_at, _ = r.array(base + 0x30)
    groups = [(r.u16(groups_at + i * 4), r.u16(groups_at + i * 4 + 2)) for i in range(group_count)]
    st['dimensions'] = dims
    def node(i):
        o = nodes_at + i * 0x1C
        return r.u32(o + 16), r.i16(o + 20), r.i16(o + 22), r.i16(o + 24)
    def walk(group, conditions, depth=0):
        if not 0 <= group < len(groups) or depth > 12: return
        dimension, first = groups[group]
        def level(i, conds, guard):
            seen = set()
            while 0 <= i < node_count and i not in seen and guard < 4000:
                seen.add(i); guard += 1
                value, child, sibling, link = node(i)
                here = conds + [(dimension, value)]
                if link > 0: walk(link - 1, here, depth + 1)
                elif link < 0 and -link - 1 < len(leaf): st['leaves'].append({'conditions': here, 'clips': leaf[-link - 1]})
                if child >= 0: level(child, here, guard)     # a tag below this tag (the same dimension)
                i = sibling
        level(first, conditions, 0)
    walk(0, [])
json.dump({'clips': ['%08X' % c for c in clips], 'entries': [['%08X' % h, s, c] for h, s, c in entries], 'states': out}, open(sys.argv[1], 'w'))
print('states', len(out), 'leaves', sum(len(s['leaves']) for s in out), 'clips', len(clips), 'entries', len(entries))
dimc = collections.Counter(d for s in out for d in s.get('dimensions', []))
print('dimensions used (id: states):', sorted(dimc.items()))
