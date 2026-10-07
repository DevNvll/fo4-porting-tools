"""Measure the Destiny hand mesh against the Fallout 4 hand mesh. Writes d2_hands.json.

    python3 destiny/port/tools/d2hands.py FILE.glb [-o FILE.json]

FILE.glb is a first-person file of d2x; its mesh `body_hands` is the Destiny hand. The
Fallout 4 hand is data/fnv/rig/1stpersonmalehands.glb.

The tools read the measurements from destiny/port/rig/d2_hands.json, a file of the source
tree. This program does not write into the source tree: its default output is
data/destiny/port/rig/d2_hands.json. Copy the result to destiny/port/rig/ when the
measurements must change (each clip of each weapon then changes: run `./port destiny regress`).

The file has two results:

    source     for each Destiny finger bone, in the axes of the Fallout 4 bone and in game
               units: the tip length (the farthest skin vertex along the bone), the radius of
               the finger segment and the center of its skin about the bone axis. These are
               the values that fnv/rig/finger_tips.json has for the New Vegas
               hand (fnv-fo4-port-checks/blender/finger_tips.py), with the same rules.
    palm_fit   for each side, the rotation that puts the palm skin of the Fallout 4 hand on
               the palm skin of the Destiny hand, with the two wrists at one place (3 x 3,
               in the axes of the Fallout 4 hand bone). The two hand bones do not have the
               same direction in the hand: the Fallout 4 bone points 8 degrees more to the
               palm. The rotation of the Fallout 4 hand bone is
               Destiny rotation @ K_HAND @ palm_fit.
"""
import argparse
import json
import os
import sys
import numpy as np

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glb import Glb  # noqa: E402
from d2bake import Rig  # noqa: E402
from d2rig import SCALE, K_HAND, FINGERS, side_of  # noqa: E402
from fo4mesh import SkinnedMesh  # noqa: E402
import fo4clip  # noqa: E402


class SourceHands:
    """The mesh `body_hands` of a Destiny file: bind positions, triangles and the bone of each vertex."""

    def __init__(self, glb, rig, name='body_hands'):
        node = glb.nodes[glb.node_index(name)]
        pos, joints, weights, tris = [], [], [], []
        base = 0
        for p in glb.json['meshes'][node['mesh']]['primitives']:
            v = glb.accessor(p['attributes']['POSITION'])
            pos.append(v)
            joints.append(glb.accessor(p['attributes']['JOINTS_0']))
            weights.append(glb.accessor(p['attributes']['WEIGHTS_0']))
            tris.append(glb.accessor(p['indices']).reshape(-1, 3) + base)
            base += len(v)
        self.rig = rig
        self.verts = np.vstack(pos)
        self.joints = np.vstack(joints).astype(int)
        self.weights = np.vstack(weights).astype(float)
        self.tris = np.vstack(tris).astype(int)
        self.main = self.joints[np.arange(len(self.verts)), np.argmax(self.weights, axis=1)]

    def local(self, bone):
        """All vertices in the space of a bone, in game units and in the axes of the Fallout 4
        bone, and the mask of the vertices whose largest weight is of this bone."""
        ib = self.rig.inverse_bind[bone]
        loc = (self.verts @ ib[:3, :3].T + ib[:3, 3]) * SCALE
        return loc @ K_HAND[side_of(bone)], self.main == self.rig.skin_joints.index(bone)


def section(loc):
    """The extent of the skin across the bone (local Y and Z), from the middle part of the bone."""
    x0, x1 = loc[:, 0].min(), loc[:, 0].max()
    mid = loc[(loc[:, 0] > x0 + 0.25 * (x1 - x0)) & (loc[:, 0] < x0 + 0.75 * (x1 - x0))]
    if len(mid) < 4:
        mid = loc
    return {'y_min': float(mid[:, 1].min()), 'y_max': float(mid[:, 1].max()),
            'z_min': float(mid[:, 2].min()), 'z_max': float(mid[:, 2].max())}


def centers(loc):
    """The center of the skin about the bone axis (local Y and Z), in four parts along the bone:
    the mean of the two middle parts, and the value of the last part (the fingertip of a last bone)."""
    edges = np.linspace(0.0, loc[:, 0].max(), 5)
    parts = []
    for a, b in zip(edges[:-1], edges[1:]):
        s = loc[(loc[:, 0] >= a) & (loc[:, 0] <= b)]
        parts.append(None if len(s) < 3 else [(s[:, 1].min() + s[:, 1].max()) / 2, (s[:, 2].min() + s[:, 2].max()) / 2])
    whole = [(loc[:, 1].min() + loc[:, 1].max()) / 2, (loc[:, 2].min() + loc[:, 2].max()) / 2]
    middle = [m for m in parts[1:3] if m is not None] or [whole]
    last = parts[3] or middle[-1]
    return {'center': [round(float(np.mean([m[i] for m in middle])), 4) for i in (0, 1)],
            'tip_center': [round(float(last[i]), 4) for i in (0, 1)]}


def finger_values(hands):
    out = {}
    for side in ('l', 'r'):
        for finger in FINGERS:
            for k in (1, 2, 3):
                bone = f'b_{side}_{finger}_{k}'
                loc, sel = hands.local(bone)
                loc = loc[sel]
                v = {'x_max': float(loc[:, 0].max()), 'x_min': float(loc[:, 0].min()),
                     'radius': float(np.percentile(np.linalg.norm(loc[:, 1:], axis=1), 80)), 'verts': int(sel.sum())}
                v.update(section(loc))
                v.update(centers(loc))
                out[bone] = v
    return out


def surface_points(verts, tris, step=0.25):
    """Points on the triangles, about one for each `step` x `step` of area, in the order of the triangles."""
    out = []
    for a, b, c in verts[tris]:
        area = 0.5 * np.linalg.norm(np.cross(b - a, c - a))
        k = max(1, int(np.ceil(np.sqrt(2 * area) / step)))
        for i in range(k):
            for j in range(k - i):
                out.append(a + (b - a) * ((i + 1 / 3) / k) + (c - a) * ((j + 1 / 3) / k))
    return np.array(out)


def nearest(a, b):
    """For each point of a: the distance to the nearest point of b, and its index."""
    dist = np.empty(len(a))
    index = np.empty(len(a), int)
    for s in range(0, len(a), 400):
        d = np.linalg.norm(a[s:s + 400, None, :] - b[None, :, :], axis=2)
        i = d.argmin(1)
        index[s:s + 400] = i
        dist[s:s + 400] = d[np.arange(len(i)), i]
    return dist, index


def rotation_fit(src, dst, iterations=40, keep=0.9):
    """The rotation about the origin that puts the points `src` on the surface points `dst`
    (and `dst` on `src`): nearest points in the two directions, the worst tenth not used."""
    r = np.eye(3)
    for _ in range(iterations):
        cur = src @ r.T
        d1, i1 = nearest(cur, dst)
        d2, i2 = nearest(dst, cur)
        k1 = d1 <= np.quantile(d1, keep)
        k2 = d2 <= np.quantile(d2, keep)
        a = np.vstack([src[k1], src[i2[k2]]])
        b = np.vstack([dst[i1[k1]], dst[k2]])
        u, _, vt = np.linalg.svd(a.T @ b)
        r = vt.T @ np.diag([1.0, 1.0, np.sign(np.linalg.det(vt.T @ u.T))]) @ u.T
    cur = src @ r.T
    return r, float(np.sqrt((nearest(cur, dst)[0] ** 2).mean())), float(np.sqrt((nearest(dst, cur)[0] ** 2).mean()))


def palm_fit(hands, fo4):
    out = {}
    for side in ('L', 'R'):
        j = fo4.joint_names.index(f'{side}Arm_Hand')
        m = fo4.inv_bind[j]
        f = surface_points(fo4.verts @ m[:3, :3].T + m[:3, 3], fo4.tris[(fo4.main[fo4.tris] == j).all(1)])
        loc, sel = hands.local(f'b_{side.lower()}_hand')
        d = surface_points(loc, hands.tris[sel[hands.tris].all(1)])
        # the skin of the Fallout 4 hand bone starts here; the wrist is on a forearm bone
        d = d[d[:, 0] >= f[:, 0].min()]
        before = float(np.sqrt((nearest(f, d)[0] ** 2).mean()))
        r, e1, e2 = rotation_fit(f, d)
        angle = float(np.degrees(np.arccos(np.clip((np.trace(r) - 1) / 2, -1, 1))))
        out[side] = {'rotation': [[round(float(v), 8) for v in row] for row in r], 'angle_degrees': round(angle, 3),
                     'rms_before': round(before, 4), 'rms_fo4_to_source': round(e1, 4), 'rms_source_to_fo4': round(e2, 4)}
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('-o', '--output', default=paths.data('destiny', 'port', 'rig', 'd2_hands.json'),
                    help='default: data/destiny/port/rig/d2_hands.json (the tools read destiny/port/rig/d2_hands.json)')
    ap.add_argument('--fo4-hands', default=os.path.join(fo4clip.PORT_RIG, '1stpersonmalehands.glb'))
    a = ap.parse_args()
    glb = Glb(a.file)
    hands = SourceHands(glb, Rig(glb))
    data = {'format': 'd2_hands 1', 'units': 'Fallout 4 game units, axes of the Fallout 4 bone (+X along the bone, -Y to the palm side)',
            'scale': SCALE, 'palm_fit': palm_fit(hands, SkinnedMesh(a.fo4_hands)), 'source': finger_values(hands)}
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with open(a.output, 'w') as f:
        json.dump(data, f, indent=1)
    for side, v in data['palm_fit'].items():
        print('palm fit %s: %.2f degrees, rms %.3f -> %.3f / %.3f' % (side, v['angle_degrees'], v['rms_before'], v['rms_fo4_to_source'], v['rms_source_to_fo4']))
    tips = json.load(open(fo4clip.PORT_TIPS))['fo4']
    for (fo4_bones, src_bones) in [(['RArm_Finger%d%d' % (n, k) for k in (1, 2, 3)], ['b_r_%s_%d' % (fg, k) for k in (1, 2, 3)]) for n, fg in enumerate(FINGERS, 1)]:
        for fb, sb in zip(fo4_bones, src_bones):
            s, t = data['source'][sb], tips[fb]
            print('%-14s x_max %.2f radius %.2f center %s tip %s | %-14s x_max %.2f radius %.2f center %s tip %s' % (
                sb, s['x_max'], s['radius'], s['center'], s['tip_center'], fb, t['x_max'], t['radius'], t['center'], t['tip_center']))
