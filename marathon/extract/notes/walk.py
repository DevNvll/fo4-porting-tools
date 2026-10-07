#!/usr/bin/env python3
"""Walk the tags below an entity of Marathon and print those of the interesting classes.

    ./port marathon notes walk ENTITY [--depth N]
    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/notes/walk.py ENTITY [--depth N]

The walk follows each 32-bit tag of the classes entity (8080BAAD) and component (8080BADB), and
each 64-bit tag hash. It prints the tree of entities, and for each one the models, the
animation graphs, the clips and the components with a skeleton or a rig.
"""
import collections
import struct
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))      # marathon/extract: the module m2x
import numpy as np  # noqa: E402
import m2x  # noqa: E402

ENTITY, COMPONENT, MESSAGE = 0x8080BAAD, 0x8080BADB, 0x8080BAF8
NAMES = {0x8080881C: 'model', 0x8080AE2E: 'animation graph', 0x8080AE01: 'clip', 0x808025AA: 'pattern list', 0x8080AE72: 'rig data',
         0x80808557: 'decal', 0x808081EF: 'effect', 0x808031D8: 'material', 0x808080D5: 'class 808080D5', 0x8080AEAA: 'class 8080AEAA'}
args = sys.argv[1:]
depth_limit = int(args[args.index('--depth') + 1]) if '--depth' in args else 3
pm = m2x.open_packages()
t64 = m2x.tag64_table()
seen = set()


def refs(tag):
    d = pm.read(tag, cache=False)
    w = np.frombuffer(d[:len(d) & ~3], dtype='<u4')
    out32 = []
    for v in np.unique(w[(w > 0x80810000) & (w <= 0x81FFFFFF)]).tolist():
        if pm.exists(v):
            out32.append(v)
    out64 = []
    for o in range(0, len(d) - 8, 4):
        h = struct.unpack_from('<Q', d, o)[0]
        if h in t64 and t64[h][0] not in out64:
            out64.append(t64[h][0])
    inner = set(int(v) for v in w if (v & 0xFFFF0000) == 0x80800000)
    return d, out32, out64, inner


def cls(tag):
    r = pm.entry(tag)
    return int(r['reference']) if r['type'] == 8 else -(int(r['type']) * 16 + int(r['subtype']))


def walk(entity, depth, via):
    pad = '  ' * depth
    if entity in seen:
        print('%s%08X (again)' % (pad, entity))
        return
    seen.add(entity)
    d, r32, r64, inner = refs(entity)
    print('%sentity %08X size %d %s %s' % (pad, entity, len(d), pm.pkg_name(entity)[4:-4], via))
    found = collections.defaultdict(list)
    children = list(r64)
    for c in r32:
        k = cls(c)
        if k == COMPONENT:
            cd, c32, c64, cin = refs(c)
            notes = []
            if 0x80809FB6 in cin:
                notes.append('skeleton')
            if 0x8080AD85 in cin:
                notes.append('rig')
            for x in c32:
                kx = cls(x)
                if kx in NAMES:
                    notes.append('%s %08X' % (NAMES[kx], x))
            for x in c64:
                if x not in children:
                    children.append(x)
                kx = cls(x)
                if kx in NAMES:
                    notes.append('%s %08X (64-bit)' % (NAMES[kx], x))
            if notes:
                print('%s  component %08X size %d: %s' % (pad, c, len(cd), ', '.join(notes[:14]) + (' ...' if len(notes) > 14 else '')))
        elif k in NAMES:
            found[NAMES[k]].append(c)
    for name, tags in found.items():
        print('%s  %s: %s' % (pad, name, ' '.join('%08X' % t for t in tags[:12])))
    if depth < depth_limit:
        for c in children:
            if cls(c) == ENTITY:
                walk(c, depth + 1, '')
            elif cls(c) in NAMES:
                print('%s  %s %08X (64-bit)' % (pad, NAMES[cls(c)], c))


for a in args:
    if len(a) == 8 and not a.startswith('--'):
        walk(int(a, 16), 0, '')
