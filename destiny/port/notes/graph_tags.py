"""Print the weapon tag tree and the weapon-tag leaves of the main states of each first-person
rig of a weapon. Read-only: it imports the modules of destiny/extract/d2x and reads the game packages.

    ./port destiny notes graph-tags MANIFEST.json

The program imports d2x (destiny/extract). With no ./port, run destiny/port/notes/graph_tags.py
with the Python of the d2x environment (data/destiny/extract/venv/bin/python) and with
PYTHONPATH=destiny/extract.
"""
import json
import sys

if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
    print(__doc__.strip())
    raise SystemExit(0 if len(sys.argv) > 1 else 2)

from d2x import pkg, entity as ent, graph as gr
from d2x.tag import fnv1, Reader

m = json.load(open(sys.argv[1]))
pm = pkg.PackageManager()
content_group = int(m['pattern']['content_group'], 16)
weapon_type = int(m['pattern']['weapon_type'], 16)
words = list(gr.TAG_WORDS) + ['auto_rifle', 'pulse_rifle', 'scout_rifle', 'assault_rifle', 'automatic', 'auto', 'pulse', 'scout',
                              'khvostov', 'rifle_auto', 'rifle_pulse', 'rifle_scout', 'trace_rifle', 'linear_fusion_rifle',
                              'burst', 'semi_auto', 'full_auto', 'rifle_burst', 'rifle_semi', 'lmg', 'carbine', 'default']
names = {fnv1(w): w for w in words}
snames = dict(gr.STATE_NAMES)
print('content group %08X %s; weapon type %08X %s' % (content_group, names.get(content_group, '?'), weapon_type, names.get(weapon_type, '?')))
WANT = ('idle', 'fire', 'fire_1', 'iron_sight_fire', 'reload_empty', 'reload_full', 'ready', 'put_away', 'iron_sight_idle', 'sprint_loop')
for rig in m['first_person']:
    e = ent.read_entity(pm, int(rig['entity'], 16))
    print('==== rig', rig['file'], rig['entity'])
    for resource in e.by_kind(ent.ANIMATION):
        graph_tag = gr.find_graph(pm, resource.data)
        tree_tag = gr.find_tag_tree(pm, resource.data)
        sets = list(ent.animation_sets(pm, resource))
        print('  graph %08X tag tree %08X sets %s' % (graph_tag, tree_tag, ['%08X' % s for s in sets]))
        if not graph_tag or not tree_tag:
            continue
        rows = gr.read_tag_tree(pm.read(tree_tag))
        print('  tag tree (%d rows):' % len(rows))
        for i, (tag, parent) in enumerate(rows):
            mark = ' <== content group' if tag == content_group else (' <== weapon type' if tag == weapon_type else '')
            print('     %3d %08X %-22s parent %3d%s' % (i, tag, names.get(tag, ''), parent, mark))
        print('  tags by the rule of the tool:', [names.get(t, '%08X' % t) for t in gr.weapon_tags(rows, content_group)])
        # every state: which tags have a leaf, and which other dimensions
        data = pm.read(graph_tag)
        r = Reader(data)
        name_count, names_at, _ = r.array(0x08)
        state_count, states_at, _ = r.array(0x18)
        by_state = {}
        for i in range(name_count):
            by_state.setdefault(r.u32(names_at + i * 8 + 4), []).append(r.u32(names_at + i * 8))
        entries_of_set = gr.read_set_entries(pm.read(sets[0])) if sets else []
        for index in range(state_count):
            hashes = by_state.get(index, [])
            known = [snames[h] for h in hashes if h in snames]
            if not any(k in WANT for k in known):
                continue
            kind = r.u64(states_at + index * 16)
            base = r.rel(states_at + index * 16 + 8)
            print('  state %d %s kind %d' % (index, known, kind))
            if kind == 1:
                print('      plain clip list', gr._clip_list(r, base))
                continue
            entries = [gr._clip_list(r, o) for o in r.array_items(base, 16)]
            node_count, nodes_at, _ = r.array(base + 0x20)
            group_count, groups_at, _ = r.array(base + 0x30)
            groups = [(r.u16(groups_at + i * 4), r.u16(groups_at + i * 4 + 2)) for i in range(group_count)]
            dims = [r.u8(o) for o in r.array_items(base + 0x10, 1)] if hasattr(r, 'u8') else []
            print('      dimensions %s groups %s nodes %d leaves %d' % (dims, groups, node_count, len(entries)))
            for i in range(node_count):
                o = nodes_at + i * 0x1C
                value, child, sibling, link = r.u32(o + 16), r.i16(o + 20), r.i16(o + 22), r.i16(o + 24)
                leaf = ''
                if link < 0 and -link - 1 < len(entries):
                    leaf = ' leaf %s' % [(c, w, ('%08X' % entries_of_set[c][0]) if c < len(entries_of_set) else '?') for c, w in entries[-link - 1]]
                print('      node %2d value %08X %-18s child %3d sibling %3d link %3d%s' % (
                    i, value, names.get(value, gr.CONDITION_LABELS.get((0x0A, value), '')), child, sibling, link, leaf))
