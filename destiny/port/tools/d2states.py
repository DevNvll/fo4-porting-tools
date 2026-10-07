#!/usr/bin/env python3
"""The clip of each game state of a Destiny 2 weapon, from the animation graph of its first-person rig.

    ./port destiny states MANIFEST.json [-o states.json]
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python \
        destiny/port/tools/d2states.py ...          (the same program with no ./port)

MANIFEST.json is the manifest of an extraction (`./port destiny extract`). The program reads
the game packages with the modules of destiny/extract/d2x (it does not change them), so it
runs with the Python environment of d2x.

The manifest of the extraction has a state table too, but its rule for the weapon tags is
proved for a hand cannon only, and it does not find the states of a rifle such as `idle` and
`reload`. This program has two differences:

* The tags of the weapon come from the game data. The weapon pattern entity has one row for
  each weapon (content group): the row has the tag pair (class, weapon) and the first-person
  rig entity. The weapon tag is the content group (the Khvostov) or the tag of a weapon class
  (Hammerhead: machine_gun). The tag list is the weapon tag, each tag above it in the tag
  tree, and the top of the tree (the node that each weapon has).
* A node of the weapon dimension can lead to a group of a different dimension (the idle of a
  rifle: player condition, then weapon, then a second player condition). The walk follows it.

A state with no node for a tag of the weapon has no clip: the game does not play a clip of
the first-person rig in that state (the shot of the Khvostov, for example).
"""
import argparse
import json
import struct
import sys

import numpy as np

from d2x import pkg, entity as ent, graph as gr
from d2x.tag import Reader

WEAPON = gr.WEAPON_DIMENSION


def pattern_row(pm, pattern, content_group, tree):
    """The rows of a content group in the pattern entity: (class tag, weapon tag, rig entity or 0).

    A row of the weapon table has the content group, then the tag pair (class, weapon). The
    weapon tag can be the content group (the Khvostov: rifle / 879A579B) or a tag of a weapon
    class (Hammerhead: rifle / machine_gun). A second table has the tag pair and then the rig
    entity of the row."""
    index = {tag for tag, _ in tree}
    top = {tag for tag, parent in tree if parent == 0}
    rows = []
    for resource in pattern.resources:
        data = resource.data
        words = np.frombuffer(data[:len(data) & ~3], dtype='<u4')
        for i in np.nonzero(words == content_group)[0].tolist():
            if i + 2 < len(words) and int(words[i + 1]) in top and int(words[i + 2]) in index:
                rows.append((int(words[i + 1]), int(words[i + 2]), 0))
            if i == 0 or int(words[i - 1]) not in top:
                continue
            # the rig entity is the next entity tag after the tag pair
            for j in range(i + 1, min(i + 8, len(words))):
                value = int(words[j])
                if 0x80800000 < value <= 0x81FFFFFF and pm.exists(value) and pm.reference(value) == ent.ENTITY:
                    rows.append((int(words[i - 1]), content_group, value))
                    break
    return rows


def tag_list(tree, tag):
    index = {t: i for i, (t, _) in enumerate(tree)}
    out = []
    i = index.get(tag, -1)
    while 0 <= i < len(tree) and tree[i][0] not in out:
        out.append(tree[i][0])
        i = tree[i][1]
    return out


def resolve(pm, graph_tag, tags):
    """State index -> (name hashes, [(conditions, weapon tag, [(set entry, weight)])])."""
    r = Reader(pm.read(graph_tag))
    name_count, names_at, _ = r.array(0x08)
    state_count, states_at, _ = r.array(0x18)
    names = {}
    for i in range(name_count):
        names.setdefault(r.u32(names_at + i * 8 + 4), []).append(r.u32(names_at + i * 8))
    rank = {tag: position for position, tag in enumerate(tags)}
    states = {}
    for index in range(state_count):
        kind = r.u64(states_at + index * 16)
        base = r.rel(states_at + index * 16 + 8)
        choices = []
        states[index] = (names.get(index, []), choices)
        if kind == 1:
            choices.append(((), 0, gr._clip_list(r, base)))
            continue
        entries = [gr._clip_list(r, o) for o in r.array_items(base, 16)]
        node_count, nodes_at, _ = r.array(base + 0x20)
        group_count, groups_at, _ = r.array(base + 0x30)
        groups = [(r.u16(groups_at + i * 4), r.u16(groups_at + i * 4 + 2)) for i in range(group_count)]

        def node(i):
            o = nodes_at + i * 0x1C
            return r.u32(o + 16), r.i16(o + 20), r.i16(o + 22), r.i16(o + 24)

        def weapon_node(first):
            """The node of the most specific tag of the weapon: (tag, link)."""
            best = None
            stack = [first]
            while stack:
                i = stack.pop()
                if not 0 <= i < node_count:
                    continue
                tag, child, sibling, link = node(i)
                if sibling >= 0:
                    stack.append(sibling)
                if tag in rank:
                    if link != 0 and (best is None or rank[tag] < rank[best[0]]):
                        best = (tag, link)
                    if child >= 0:
                        stack.append(child)
            return best

        def follow(link, conditions, tag):
            if link > 0:
                walk(link - 1, conditions, tag)
            elif link < 0 and -link - 1 < len(entries):
                choices.append((conditions, tag, entries[-link - 1]))

        def walk(group, conditions, tag):
            if not 0 <= group < len(groups):
                return
            dimension, first = groups[group]
            if dimension == WEAPON:
                found = weapon_node(first)
                if found:
                    follow(found[1], conditions, found[0])
                return
            i = first
            seen = set()
            while 0 <= i < node_count and i not in seen:
                seen.add(i)
                value, child, sibling, link = node(i)
                follow(link, conditions + ((dimension, value),), tag)
                i = sibling

        walk(0, (), 0)
    return states


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest')
    ap.add_argument('-o', '--output')
    a = ap.parse_args()
    m = json.load(open(a.manifest))
    pm = pkg.PackageManager()
    content_group = int(m['pattern']['content_group'], 16)
    pattern = ent.read_entity(pm, int(m['pattern']['entity'], 16))
    out = {'name': m['name'], 'content_group': '%08X' % content_group, 'rigs': []}
    tag_names = dict(gr.TAG_NAMES)
    for rig in m['first_person']:
        entity = ent.read_entity(pm, int(rig['entity'], 16))
        by_key = {(c['set'], c['order']): c for c in rig['clips'] if 'error' not in c}
        for resource in entity.by_kind(ent.ANIMATION):
            graph_tag = gr.find_graph(pm, resource.data)
            tree_tag = gr.find_tag_tree(pm, resource.data)
            if not graph_tag or not tree_tag:
                continue
            tree = gr.read_tag_tree(pm.read(tree_tag))
            rows = pattern_row(pm, pattern, content_group, tree)
            linked = sorted({row[2] for row in rows if row[2]})
            # the rig of the weapon: the rig entity of its row, or the only rig that the pattern has
            own = int(rig['entity'], 16) in linked or (not linked and len(m['first_person']) == 1)
            record = {'file': rig['file'], 'entity': rig['entity'], 'graph': '%08X' % graph_tag,
                      'pattern_rows': [{'class': tag_names.get(c, '%08X' % c), 'weapon': tag_names.get(w, '%08X' % w),
                                        'rig': ('%08X' % e) if e else None} for c, w, e in rows],
                      'is_rig_of_the_weapon': own, 'states': []}
            weapon_tags = [w for _, w, _ in rows]
            tags = tag_list(tree, weapon_tags[0] if weapon_tags else content_group)
            record['tags'] = [tag_names.get(t, '%08X' % t) for t in tags]
            for set_tag in ent.animation_sets(pm, resource):
                entries = gr.read_set_entries(pm.read(set_tag))
                for index, (hashes, choices) in sorted(resolve(pm, graph_tag, tags).items()):
                    known = sorted(gr.STATE_NAMES[h] for h in hashes if h in gr.STATE_NAMES)
                    state = {'index': index, 'names': known, 'hashes': ['%08X' % h for h in hashes], 'choices': []}
                    for conditions, tag, clips in choices:
                        items = []
                        for entry, weight in clips:
                            if entry >= len(entries):
                                continue
                            clip = by_key.get(('%08X' % set_tag, entries[entry][2]))
                            if clip:
                                items.append({'clip': clip['name'], 'threshold': weight, 'frames': clip['frames'],
                                              'additive': bool(clip.get('additive')),
                                              'moving_weapon_bones': clip.get('moving_weapon_bones', [])})
                        if items:
                            state['choices'].append({'condition': gr.condition_label(conditions),
                                                     'condition_hashes': ['%X:%08X' % c for c in conditions],
                                                     'weapon_tag': tag_names.get(tag, '%08X' % tag) if tag else '', 'clips': items})
                    record['states'].append(state)
            out['rigs'].append(record)
    text = json.dumps(out, indent=1)
    if a.output:
        with open(a.output, 'w') as f:
            f.write(text + '\n')
    for record in out['rigs']:
        print('rig %s entity %s: rig of the weapon %s, tags %s' % (record['file'], record['entity'], record['is_rig_of_the_weapon'], record['tags']))
        if not record['is_rig_of_the_weapon']:
            continue
        for state in record['states']:
            label = '/'.join(state['names']) or 'state_' + (min(state['hashes']) if state['hashes'] else str(state['index']))
            if not state['choices']:
                print('  %-36s (no clip for this weapon)' % label)
            for choice in state['choices']:
                for clip in choice['clips']:
                    print('  %-36s %-16s tag %-10s %-22s %4d frames  w %.3f %s %s' % (
                        label, choice['condition'] or '-', choice['weapon_tag'] or '-', clip['clip'], clip['frames'], clip['threshold'],
                        'additive' if clip['additive'] else '', ','.join(clip['moving_weapon_bones'])))


if __name__ == '__main__':
    main()
