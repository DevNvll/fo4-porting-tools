#!/usr/bin/env python3
"""For each full-pose clip of a first-person file: how far is the gun bone from the grip bone?

    python3 .claude/skills/write-set-file/scripts/gun_on_grip.py MANIFEST.json [--rig N] [--clip CLIP ...] [--limit M]

MANIFEST.json is the manifest of an extraction of d2x or m2x (it is beside the .glb files):

    data/destiny/port/extract/NAME/manifest.json
    data/marathon/extract/out/NAME/manifest.json

In a correct clip the gun bone (b_handle) is on the grip bone of the right hand (b_r_grip):
0.000 m on each frame. A clip in which the gun is at another place is a clip of another rig
(the gun bone is then at the origin of the world). A set file that uses such a clip needs
`[gun] rest = true` (destiny/port/README.md, "The Huckleberry").

The program prints one line for each full-pose clip of the file: the frames, the node count
and the largest distance. Then it prints the count of clips with the gun on the grip bone,
for each node count. An additive clip has offsets only and is not in the list.

With --clip the program does only these clips (give each clip that the set file will use).
The exit code is then 1 when a clip of the list is not in the file, or has the gun more
than --limit meters from the grip bone (default 0.001).

The program reads files below data/ and writes no file. It needs numpy.
"""
import argparse
import json
import os
import sys

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

sys.path.insert(0, paths.repo('destiny', 'port', 'tools'))
import numpy as np  # noqa: E402
from glb import Glb  # noqa: E402
from d2bake import Rig  # noqa: E402

GUN = 'b_handle'
GRIP = 'b_r_grip'


def main():
    ap = argparse.ArgumentParser(description='The distance of the gun bone to the grip bone in each full-pose clip of a first-person file.')
    ap.add_argument('manifest', help='manifest.json of an extraction of d2x or m2x')
    ap.add_argument('--rig', type=int, default=0, help='the number of the first-person rig in the manifest (default 0)')
    ap.add_argument('--clip', action='append', default=[], help='only this clip (give it again for more)')
    ap.add_argument('--limit', type=float, default=0.001, help='the largest distance of a correct clip, in meters (default 0.001)')
    a = ap.parse_args()

    with open(a.manifest) as f:
        manifest = json.load(f)
    rigs = manifest.get('first_person') or []
    if not 0 <= a.rig < len(rigs):
        sys.exit('gun_on_grip: the manifest has %d first-person rigs; --rig %d is not one of them' % (len(rigs), a.rig))
    first = rigs[a.rig]
    rig = Rig(Glb(os.path.join(os.path.dirname(os.path.abspath(a.manifest)), first['file'])))
    for bone in (GUN, GRIP):
        if bone not in rig.index:
            sys.exit('gun_on_grip: the rig of %s has no bone %s' % (first['file'], bone))
    in_file = set(rig.clip_names())
    records = {r['name']: r for r in first['clips']}
    print('%s: %d bones in the rig, %d animations in the file' % (first['file'], len(first['bones']), len(in_file)))

    wanted = a.clip or [r['name'] for r in first['clips']]
    faults = 0
    counts = {}
    for name in wanted:
        record = records.get(name, {})
        if name not in in_file:
            if a.clip:
                print('%-24s is not an animation of the file' % name)
                faults += 1
            continue
        if record.get('additive') or name.endswith('_add'):
            if a.clip:
                print('%-24s is an additive clip (offsets only): it has no place of the gun' % name)
            continue
        world, _ = rig.bake(name)
        gap = float(np.linalg.norm(world[:, rig.index[GUN], :3, 3] - world[:, rig.index[GRIP], :3, 3], axis=1).max())
        nodes = record.get('nodes')
        on_grip = gap <= a.limit
        total, good = counts.get(nodes, (0, 0))
        counts[nodes] = (total + 1, good + (1 if on_grip else 0))
        if not on_grip and a.clip:
            faults += 1
        print('%-24s %3d frames, %s nodes, the gun is %.3f m from the grip bone%s' % (
            name, world.shape[0], nodes if nodes is not None else '?', gap, '' if on_grip else '   <- not on the grip bone'))

    total = sum(t for t, _ in counts.values())
    good = sum(g for _, g in counts.values())
    print('%d of %d full-pose clips have the gun on the grip bone (%.3f m or less)' % (good, total, a.limit))
    for nodes in sorted(counts, key=lambda n: (n is None, n)):
        t, g = counts[nodes]
        print('    clips with %s nodes: %d of %d' % (nodes if nodes is not None else '?', g, t))
    if a.clip and faults:
        print('%d of the %d clips of --clip are not correct: a set file with them needs `[gun] rest = true`, or other clips' % (faults, len(a.clip)))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
