"""Measure how far the hand meshes go into the gun meshes, for the source and for the result.

sh destiny/port/check/bl.sh destiny/port/check/contact.py -- \
    --glb FILE.glb --bake WORK/bake/CLIP.npz --poses WORK/fo4/poses/CLIP.npz \
    --parts WORK/parts.json [--frames 0,30 | all] [--out FILE.json]

The program runs in Blender. WORK is the work folder of the weapon
(data/destiny/port/work/NAME).

For each frame: the count of hand skin vertices inside a gun part and the largest depth (game
units), for the Destiny hand of the source and for the Fallout 4 hand of the result. The gun
is the same for the two: the shapes of the parts file on the Fallout 4 weapon bones of the
result. A vertex belongs to the bone with its largest weight. The rules are those of
fnv-fo4-port-checks/blender/hand_contact.py.
"""
import argparse
import json
import os
import sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))
import fo4clip  # noqa: E402
from glb import Glb  # noqa: E402
from d2bake import Rig  # noqa: E402
from d2hands import SourceHands  # noqa: E402
from d2rig import SCALE  # noqa: E402
from fo4mesh import SkinnedMesh, Helpers  # noqa: E402

DIRS = [Vector((0.577, 0.577, 0.577)), Vector((-0.8, 0.27, 0.53)), Vector((0.2, -0.9, 0.38))]


def inside(tree, p):
    """Parity of ray hits in three directions."""
    votes = 0
    for d in DIRS:
        n = 0
        o = Vector(p)
        for _ in range(64):
            loc, nrm, idx, dist = tree.ray_cast(o, d)
            if loc is None:
                break
            n += 1
            o = loc + d * 1e-4
        votes += n & 1
    return votes >= 2


class Parts:
    def __init__(self, data, poses, idx, skip=()):
        self.items = []
        self.poses = poses
        for s in data['shapes']:
            if s['name'] in skip:
                continue
            verts = np.array(s['positions'])
            tree = BVHTree.FromPolygons([tuple(v) for v in verts], [tuple(t) for t in s['triangles']], epsilon=0.0)
            self.items.append((s['name'], tree, verts.min(0) - 0.05, verts.max(0) + 0.05, idx[s['bone']]))

    def depth(self, pts, frame):
        depth = np.zeros(len(pts))
        which = np.full(len(pts), -1)
        for k, (name, tree, lo, hi, bone) in enumerate(self.items):
            m = np.linalg.inv(self.poses[frame, bone])
            loc = pts @ m[:3, :3].T + m[:3, 3]
            for i in np.nonzero(np.all((loc >= lo) & (loc <= hi), axis=1))[0]:
                p = Vector(loc[i])
                if inside(tree, p):
                    near = tree.find_nearest(p)
                    d = near[3] if near[0] is not None else 0.0
                    if d > depth[i]:
                        depth[i] = d
                        which[i] = k
        return depth, which


def report(label, frames, groups, points, parts, limit=0.05, show=True):
    rows = []
    for f in frames:
        depth, which = parts.depth(points(f), f)
        per = {}
        for g, sel in groups.items():
            d = depth[sel]
            n = int((d > limit).sum())
            if n:
                per[g] = [n, round(float(d.max()), 2), parts.items[which[sel][np.argmax(d)]][0]]
        total = int((depth > limit).sum())
        rows.append({'frame': int(f), 'inside': total, 'max_depth': round(float(depth.max()), 2), 'bones': per})
        if show:
            print('%s frame %3d: %4d vertices inside, max depth %.2f' % (label, f, total, depth.max()))
            for g in sorted(per, key=lambda g: -per[g][1])[:6]:
                print('      %-18s %4d verts  depth %.2f  in %s' % (g, per[g][0], per[g][1], per[g][2]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--glb', required=True)
    ap.add_argument('--bake', required=True)
    ap.add_argument('--poses', required=True)
    ap.add_argument('--parts', required=True)
    ap.add_argument('--frames', default='0')
    ap.add_argument('--skip', action='append', default=[])
    ap.add_argument('--out')
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--rig', default=fo4clip.PORT_RIG, help='the rig folder of fnv (default: data/fnv/rig)')
    a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
    poses, names = fo4clip.load_poses(a.poses)
    idx = {n: i for i, n in enumerate(names)}
    parts = Parts(json.load(open(a.parts)), poses, idx, a.skip)
    n = poses.shape[0]
    frames = list(range(n)) if a.frames == 'all' else [min(int(x), n - 1) for x in a.frames.split(',')]

    # the result: the Fallout 4 hand mesh
    sm = SkinnedMesh(os.path.join(a.rig, '1stpersonmalehands.glb'))
    rules = sm.rules(names, Helpers(a.rig, names))
    groups = {jn: np.nonzero(sm.main == j)[0] for j, jn in enumerate(sm.joint_names)
              if (sm.main == j).any() and ('Finger' in jn or 'Hand' in jn)}
    fo4 = report('FO4', frames, groups, lambda f: sm.skinned(poses[f], rules), parts, show=not a.quiet)

    # the source: the Destiny hand mesh with the baked pose (Fallout 4 world space)
    glb = Glb(a.glb)
    rig = Rig(glb)
    hands = SourceHands(glb, rig)
    bake = np.load(a.bake)
    world = bake['world']
    bidx = {str(x): i for i, x in enumerate(bake['names'])}
    # the move of a clip in the sights (the retarget step writes it), and the last pose of the
    # source on the frames that a clip has more than the source (hold_end of the set)
    moves = os.path.join(os.path.dirname(os.path.abspath(a.parts)), 'fo4', 'moves.json')
    clip = os.path.splitext(os.path.basename(a.bake))[0]
    move = np.array(json.load(open(moves)).get(clip, [0.0, 0.0, 0.0])) if os.path.exists(moves) else np.zeros(3)
    if n > world.shape[0]:
        world = np.concatenate([world, np.repeat(world[-1:], n - world.shape[0], axis=0)], axis=0)
    local = {j: (hands.verts @ rig.inverse_bind[rig.skin_joints[j]][:3, :3].T + rig.inverse_bind[rig.skin_joints[j]][:3, 3]) * SCALE
             for j in np.unique(hands.joints[hands.weights > 0])}

    def source_points(f):
        out = np.zeros_like(hands.verts)
        for k in range(hands.joints.shape[1]):
            for j in np.unique(hands.joints[:, k]):
                sel = (hands.joints[:, k] == j) & (hands.weights[:, k] > 0)
                if sel.any():
                    m = world[f, bidx[rig.skin_joints[j]]]
                    out[sel] += hands.weights[sel, k, None] * (local[j][sel] @ m[:3, :3].T + m[:3, 3])
        return out + move
    sgroups = {rig.skin_joints[j]: np.nonzero(hands.main == j)[0] for j in np.unique(hands.main)
               if 'forearm' not in rig.skin_joints[j]}
    src = report('SRC', frames, sgroups, source_points, parts, show=not a.quiet)

    fo4_total = sum(r['inside'] for r in fo4)
    src_total = sum(r['inside'] for r in src)
    print('frames %d | source: %d vertices inside (of %d), max depth %.2f, frames with contact %d | result: %d vertices inside (of %d), max depth %.2f, frames with contact %d' % (
        len(frames), src_total, len(hands.verts) * len(frames), max(r['max_depth'] for r in src), sum(1 for r in src if r['inside']),
        fo4_total, len(sm.verts) * len(frames), max(r['max_depth'] for r in fo4), sum(1 for r in fo4 if r['inside'])))
    if a.out:
        with open(a.out, 'w') as f:
            json.dump({'frames': frames, 'source': src, 'result': fo4, 'source_vertices': int(len(hands.verts)), 'result_vertices': int(len(sm.verts))}, f, indent=1)


if __name__ == '__main__':
    main()
