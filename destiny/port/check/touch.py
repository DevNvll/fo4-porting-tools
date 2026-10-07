"""Measure how near each hand is to the gun, for the source and for the result.

./port destiny check touch --glb FILE.glb --bake WORK/bake/CLIP.npz --poses OUT/WPNIdleReady.hkx \
    --parts WORK/parts.json [--frames 0,30 | all] [--out FILE.json]
sh destiny/port/check/bl.sh destiny/port/check/touch.py -- ...     (the same program with no ./port)

The program runs in Blender. WORK is the work folder of the weapon
(data/destiny/port/work/NAME) and OUT is the folder of its clips (data/destiny/port/out/NAME,
or the animation folder of the mod project).

check/contact.py counts the hand vertices that are inside the gun. A hand that is 1 cm away
from the gun has none, and that check does not show it. This program prints, for each hand
and each frame, the distance of the nearest hand vertex to the surface of the gun and the
count of hand vertices that are nearer than 0.5 cm and nearer than 1.5 cm (a vertex inside
the gun has the distance 0). A hand that holds the gun has hundreds of such vertices.

The source is the Destiny hand mesh with the baked pose; the result is the Fallout 4 hand
mesh with the poses of the clip. The gun is the same for the two: the shapes of the parts file
on the Fallout 4 weapon bones of the result. The two meshes have other vertex counts, so
compare the percent values.
"""
import argparse
import json
import os
import sys
import numpy as np
from mathutils import Vector

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))
import fo4clip  # noqa: E402
from glb import Glb  # noqa: E402
from d2bake import Rig  # noqa: E402
from d2hands import SourceHands  # noqa: E402
from d2rig import SCALE  # noqa: E402
from fo4mesh import SkinnedMesh, Helpers  # noqa: E402
from contact import Parts, inside  # noqa: E402

NEAR = (0.5, 1.5)   # cm


def distance(parts, pts, frame, limit):
    """The distance of each point to the nearest gun shape (0 inside a shape; `limit` if it is farther)."""
    out = np.full(len(pts), limit)
    for name, tree, lo, hi, bone in parts.items:
        m = np.linalg.inv(parts.poses[frame, bone])
        loc = pts @ m[:3, :3].T + m[:3, 3]
        for i in np.nonzero(np.all((loc >= lo - limit) & (loc <= hi + limit), axis=1))[0]:
            p = Vector(loc[i])
            near = tree.find_nearest(p, limit)
            if near[0] is None:
                continue
            d = 0.0 if inside(tree, p) else near[3]
            if d < out[i]:
                out[i] = d
    return out


def report(label, frames, sides, points, parts, show):
    rows = []
    limit = NEAR[-1] / 100.0 * SCALE * 2.0
    for f in frames:
        d = distance(parts, points(f), f, limit) / SCALE * 100.0
        row = {'frame': int(f)}
        for side, sel in sides.items():
            x = d[sel]
            row[side] = {'nearest_cm': round(float(x.min()), 2), 'vertices': int(len(x)),
                         'near': [int((x < n).sum()) for n in NEAR]}
        rows.append(row)
        if show:
            print('%s frame %3d: %s' % (label, f, '; '.join(
                '%s hand: nearest %.2f cm, %d (%.1f %%) nearer than %.1f cm, %d (%.1f %%) nearer than %.1f cm' % (
                    side, row[side]['nearest_cm'], row[side]['near'][0], 100.0 * row[side]['near'][0] / row[side]['vertices'], NEAR[0],
                    row[side]['near'][1], 100.0 * row[side]['near'][1] / row[side]['vertices'], NEAR[1]) for side in sides)))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--glb', required=True)
    ap.add_argument('--bake', required=True)
    ap.add_argument('--poses', required=True)
    ap.add_argument('--parts', required=True)
    ap.add_argument('--frames', default='0')
    ap.add_argument('--out')
    ap.add_argument('--quiet', action='store_true')
    ap.add_argument('--rig', default=fo4clip.PORT_RIG, help='the rig folder of fnv (default: data/fnv/rig)')
    a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
    poses, names = fo4clip.load_poses(a.poses)
    idx = {n: i for i, n in enumerate(names)}
    parts = Parts(json.load(open(a.parts)), poses, idx)
    n = poses.shape[0]
    frames = list(range(n)) if a.frames == 'all' else [min(int(x), n - 1) for x in a.frames.split(',')]

    # the result: the Fallout 4 hand mesh (the vertices of the hand and of the fingers)
    sm = SkinnedMesh(os.path.join(a.rig, '1stpersonmalehands.glb'))
    rules = sm.rules(names, Helpers(a.rig, names))
    hand = np.array([('Finger' in jn or 'Hand' in jn) for jn in sm.joint_names])[sm.main]
    left = np.array([jn.startswith('L') for jn in sm.joint_names])[sm.main]
    fo4 = report('FO4', frames, {'left': np.nonzero(hand & left)[0], 'right': np.nonzero(hand & ~left)[0]},
                 lambda f: sm.skinned(poses[f], rules), parts, not a.quiet)

    # the source: the Destiny hand mesh with the baked pose (Fallout 4 world space)
    glb = Glb(a.glb)
    rig = Rig(glb)
    hands = SourceHands(glb, rig)
    bake = np.load(a.bake)
    world = bake['world']
    bidx = {str(x): i for i, x in enumerate(bake['names'])}
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
    main_names = np.array(rig.skin_joints)[hands.main]
    shand = np.array(['forearm' not in x for x in main_names])
    sleft = np.array([x.startswith('b_l_') for x in main_names])
    src = report('SRC', frames, {'left': np.nonzero(shand & sleft)[0], 'right': np.nonzero(shand & ~sleft)[0]},
                 source_points, parts, not a.quiet)

    for label, rows in (('source', src), ('result', fo4)):
        for side in ('left', 'right'):
            v = rows[0][side]['vertices']
            near = np.array([r[side]['near'] for r in rows], float)
            print('%s, %-5s hand, %d frames: nearest %.2f to %.2f cm; nearer than %.1f cm: %.1f %% (mean), %.1f %% (least); nearer than %.1f cm: %.1f %% (mean)' % (
                label, side, len(rows), min(r[side]['nearest_cm'] for r in rows), max(r[side]['nearest_cm'] for r in rows),
                NEAR[0], 100.0 * near[:, 0].mean() / v, 100.0 * near[:, 0].min() / v, NEAR[1], 100.0 * near[:, 1].mean() / v))
    if a.out:
        with open(a.out, 'w') as f:
            json.dump({'frames': frames, 'near_cm': NEAR, 'source': src, 'result': fo4}, f, indent=1)


if __name__ == '__main__':
    main()
