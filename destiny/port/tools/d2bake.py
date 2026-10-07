"""Evaluate a clip of a Destiny first-person rig (.glb of d2x or m2x) on its skeleton.

    python3 destiny/port/tools/d2bake.py FILE.glb --clip CLIP [--clip ...] -o FOLDER [--fo4] [--rules FILE.json]

The file has one skin (the 80 bones) and one animation for each clip. A clip keys the local
translation, rotation and scale of each bone, with linear interpolation, at 30 frames for each
second. The result has the world matrix of each bone for each frame (4x4, column vectors), in
the axes and the units of the file: +Y up, +Z forward, +X to the left of the player, meters.
With --fo4 the matrices are in Fallout 4 world space and game units (tools/d2rig.py).

`--rules` names a file with the clip rules of a set file (d2fo4.py writes it from the tables
[gun] and [compose]):

    {"tracks": {"CLIP": "FILE.npz"},
     "gun": {"rest": true, "parts": {"CLIP": "CLIP2"}},
     "compose": {"NAME": {"clips": ["CLIP", ...], "blend": 3, "cut": ["b_shell"]}}}

    tracks       The local tracks of CLIP are those of FILE.npz (`t`, `r`, `s` and `names`), not
                 those of the file of the extraction. tools/d2pose.py writes such a file: the
                 clip with the hand pose of a pose clip of the gun.

    gun.rest     In each clip, the gun bone (b_handle) and each bone below it have their rest
                 place: the gun is on the grip bone of the right hand. This is for a weapon
                 whose clips of the hands are clips of a rig with one more gun bone (the
                 Huckleberry: the clips have 77 nodes, the rig has 76 bones), where the file has
                 the gun bones at wrong places.
    gun.parts    The gun parts of CLIP move as they do in CLIP2 (an additive clip of the gun
                 parts): each bone below the gun bone gets its motion in CLIP2 against the
                 first frame of CLIP2, on its rest place. Frame n of CLIP has frame n of CLIP2.
    compose      A new clip NAME: the clips of the list, one after the other. The first frame of
                 a clip is on the last frame of the clip before it. When the two poses are not
                 the same, the difference goes to zero in the first `blend` frames. A bone of
                 `cut` has no such blend (a shell that the game hides between two clips).
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glb import Glb  # noqa: E402

FPS = 30.0


def quat_matrix(q):
    """(x, y, z, w) arrays (n x 4) -> rotation matrices (n x 3 x 3, column vectors)."""
    q = q / np.linalg.norm(q, axis=-1, keepdims=True)
    x, y, z, w = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    m = np.empty(q.shape[:-1] + (3, 3))
    m[..., 0, 0] = 1 - 2 * (y * y + z * z)
    m[..., 0, 1] = 2 * (x * y - z * w)
    m[..., 0, 2] = 2 * (x * z + y * w)
    m[..., 1, 0] = 2 * (x * y + z * w)
    m[..., 1, 1] = 1 - 2 * (x * x + z * z)
    m[..., 1, 2] = 2 * (y * z - x * w)
    m[..., 2, 0] = 2 * (x * z - y * w)
    m[..., 2, 1] = 2 * (y * z + x * w)
    m[..., 2, 2] = 1 - 2 * (x * x + y * y)
    return m


def sample(times, values, at, rotation=False):
    """Linear interpolation of the keys at the times `at` (a rotation: normalized lerp on the short way)."""
    if len(times) == 1:
        return np.repeat(values[:1], len(at), axis=0)
    hi = np.clip(np.searchsorted(times, at, side='right'), 1, len(times) - 1)
    lo = hi - 1
    span = times[hi] - times[lo]
    t = np.clip(np.where(span > 0, (at - times[lo]) / np.where(span > 0, span, 1.0), 0.0), 0.0, 1.0)[:, None]
    a, b = values[lo], values[hi]
    if rotation:
        b = np.where(np.sum(a * b, axis=1, keepdims=True) < 0, -b, b)
        out = a + (b - a) * t
        return out / np.linalg.norm(out, axis=1, keepdims=True)
    return a + (b - a) * t


def matrix_quat(m):
    """Rotation matrices (n x 3 x 3) -> (x, y, z, w) arrays (n x 4)."""
    m = np.asarray(m, float)
    out = np.empty(m.shape[:-2] + (4,))
    trace = m[..., 0, 0] + m[..., 1, 1] + m[..., 2, 2]
    out[..., 3] = np.sqrt(np.maximum(1.0 + trace, 0.0)) / 2.0
    out[..., 0] = np.sqrt(np.maximum(1.0 + m[..., 0, 0] - m[..., 1, 1] - m[..., 2, 2], 0.0)) / 2.0
    out[..., 1] = np.sqrt(np.maximum(1.0 - m[..., 0, 0] + m[..., 1, 1] - m[..., 2, 2], 0.0)) / 2.0
    out[..., 2] = np.sqrt(np.maximum(1.0 - m[..., 0, 0] - m[..., 1, 1] + m[..., 2, 2], 0.0)) / 2.0
    out[..., 0] = np.copysign(out[..., 0], m[..., 2, 1] - m[..., 1, 2])
    out[..., 1] = np.copysign(out[..., 1], m[..., 0, 2] - m[..., 2, 0])
    out[..., 2] = np.copysign(out[..., 2], m[..., 1, 0] - m[..., 0, 1])
    return out / np.linalg.norm(out, axis=-1, keepdims=True)


def quat_multiply(a, b):
    """The product a * b of (x, y, z, w) arrays."""
    ax, ay, az, aw = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bx, by, bz, bw = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz], axis=-1)


def quat_inverse(q):
    return q * np.array([-1.0, -1.0, -1.0, 1.0])


def quat_power(q, weight):
    """The part `weight` (0 to 1) of the rotations q, on the short way."""
    q = np.where(q[..., 3:] < 0, -q, q)
    angle = np.arccos(np.clip(q[..., 3], -1.0, 1.0))
    sine = np.sin(angle)
    scale = np.where(sine > 1e-9, np.sin(angle * weight) / np.where(sine > 1e-9, sine, 1.0), weight)
    out = np.concatenate([q[..., :3] * scale[..., None], np.cos(angle * weight)[..., None]], axis=-1)
    return out / np.linalg.norm(out, axis=-1, keepdims=True)


def join(pieces, blend=0, cut=()):
    """Local tracks (t, r, s: frames x bones x 3, 4, 3) of clips, one after the other. The first
    frame of a clip is on the last frame of the clip before it. The difference of the two poses
    goes to zero in the first `blend` frames of the later clip, but not for the bones `cut`."""
    t, r, s = (np.array(x, float, copy=True) for x in pieces[0])
    for nt, nr, ns in pieces[1:]:
        nt, nr, ns = (np.array(x, float, copy=True) for x in (nt, nr, ns))
        dt, ds = t[-1] - nt[0], s[-1] - ns[0]
        dr = quat_multiply(r[-1], quat_inverse(nr[0]))
        for bone in cut:
            dt[bone], ds[bone], dr[bone] = 0.0, 0.0, (0.0, 0.0, 0.0, 1.0)
        for frame in range(1, min(blend, len(nt) - 1) + 1):
            weight = 1.0 - frame / (blend + 1.0)
            nt[frame] += dt * weight
            ns[frame] += ds * weight
            nr[frame] = quat_multiply(quat_power(dr, weight), nr[frame])
        t, r, s = (np.concatenate([a, b[1:]], axis=0) for a, b in ((t, nt), (r, nr), (s, ns)))
    return t, r, s


def join_world(worlds, parents, blend=0, cut=()):
    """As `join`, for clips that are world matrices (frames x bones x 4 x 4) of one skeleton."""
    pieces = []
    for world in worlds:
        local = np.array(world, float, copy=True)
        for k, p in enumerate(parents):
            if p >= 0:
                local[:, k] = np.linalg.inv(world[:, p]) @ world[:, k]
        s = np.linalg.norm(local[..., :3, :3], axis=-2)
        pieces.append((local[..., :3, 3], matrix_quat(local[..., :3, :3] / s[..., None, :]), s))
    t, r, s = join(pieces, blend, cut)
    local = np.zeros(t.shape[:2] + (4, 4))
    local[..., :3, :3] = quat_matrix(r) * s[..., None, :]
    local[..., :3, 3] = t
    local[..., 3, 3] = 1.0
    out = np.zeros_like(local)

    def depth(k):
        return 0 if parents[k] < 0 else 1 + depth(parents[k])
    for k in sorted(range(len(parents)), key=depth):                # a parent before its children
        out[:, k] = local[:, k] if parents[k] < 0 else out[:, parents[k]] @ local[:, k]
    return out


def load_rules(path):
    """The clip rules of a set file, from the file that d2fo4.py writes (None: no rules)."""
    if not path or not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


class Rig:
    """The joints of the skin of a file, in hierarchy order. `rules`: the clip rules of a set file."""

    def __init__(self, glb, rules=None):
        self.glb = glb
        self.rules = rules or {}
        skin = glb.json['skins'][0]
        order = []

        def visit(i):
            if i in joints:
                order.append(i)
            for c in glb.nodes[i].get('children', ()):
                visit(c)
        joints = set(skin['joints'])
        for root in glb.json['scenes'][glb.json.get('scene', 0)]['nodes']:
            visit(root)
        self.node_ids = order
        self.names = [glb.nodes[i]['name'] for i in order]
        self.index = {n: k for k, n in enumerate(self.names)}
        slot = {i: k for k, i in enumerate(order)}
        self.parents = [slot.get(glb.parent.get(i), -1) for i in order]
        self.slot = slot
        ibm = glb.accessor(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        self.inverse_bind = {glb.nodes[j]['name']: ibm[k] for k, j in enumerate(skin['joints'])}
        self.skin_joints = [glb.nodes[j]['name'] for j in skin['joints']]

    def rest_local(self):
        t = np.zeros((len(self.names), 3))
        r = np.zeros((len(self.names), 4))
        s = np.ones((len(self.names), 3))
        r[:, 3] = 1.0
        for k, i in enumerate(self.node_ids):
            n = self.glb.nodes[i]
            t[k] = n.get('translation', (0, 0, 0))
            r[k] = n.get('rotation', (0, 0, 0, 1))
            s[k] = n.get('scale', (1, 1, 1))
        return t, r, s

    def clip_names(self):
        return [a['name'] for a in self.glb.json['animations']] + list(self.rules.get('compose', {}))

    def gun_bones(self, root='b_handle'):
        """The slots of the bones below the gun bone, in hierarchy order."""
        out = []
        for k, p in enumerate(self.parents):
            if p >= 0 and (self.names[p] == root or p in out):
                out.append(k)
        return out

    def keys(self, clip):
        """The local tracks of a clip as the file has them (t, r, s: frames x bones x 3, 4, 3), or
        those of the file that the rule `tracks` names for the clip."""
        other = self.rules.get('tracks', {}).get(clip)
        if other:
            d = np.load(other)
            order = [list(d['names']).index(n) for n in self.names]
            return tuple(np.array(d[k][:, order], float) for k in ('t', 'r', 's'))
        glb = self.glb
        anim = [a for a in glb.json['animations'] if a['name'] == clip]
        if not anim:
            raise SystemExit('%s has no clip %s' % (glb.path, clip))
        anim = anim[0]
        last = max(float(glb.json['accessors'][s['input']]['max'][0]) if 'max' in glb.json['accessors'][s['input']]
                   else float(glb.accessor(s['input']).max()) for s in anim['samplers'])
        count = int(round(last * FPS)) + 1
        at = np.arange(count) / FPS
        t0, r0, s0 = self.rest_local()
        t = np.repeat(t0[None], count, axis=0)
        r = np.repeat(r0[None], count, axis=0)
        s = np.repeat(s0[None], count, axis=0)
        for ch in anim['channels']:
            k = self.slot.get(ch['target']['node'])
            if k is None:
                continue
            smp = anim['samplers'][ch['sampler']]
            if smp.get('interpolation', 'LINEAR') != 'LINEAR':
                raise SystemExit('%s: the clip %s has %s keys, which this reader does not read' % (glb.path, clip, smp['interpolation']))
            times = glb.accessor(smp['input']).reshape(-1)
            values = glb.accessor(smp['output'])
            path = ch['target']['path']
            if path == 'translation':
                t[:, k] = sample(times, values, at)
            elif path == 'rotation':
                r[:, k] = sample(times, values, at, rotation=True)
            elif path == 'scale':
                s[:, k] = sample(times, values, at)
        return t, r, s

    def local(self, clip):
        """The local tracks of a clip, with the rules of [gun] and [compose] of the set file."""
        compose = self.rules.get('compose', {})
        if clip in compose:
            spec = compose[clip]
            return join([self.local(c) for c in spec['clips']], int(spec.get('blend', 0)),
                        [self.index[b] for b in spec.get('cut', [])])
        t, r, s = self.keys(clip)
        gun = self.rules.get('gun', {})
        if gun.get('rest'):
            # the gun bone on its parent (the grip bone of the hand) and each part on the gun, at rest
            t0, r0, s0 = self.rest_local()
            for k in [self.index['b_handle']] + self.gun_bones():
                t[:, k], r[:, k], s[:, k] = t0[k], r0[k], s0[k]
        source = gun.get('parts', {}).get(clip)
        if source:
            # the motion of each part in the second clip, against the first frame of that clip, on the rest place
            t0, r0, s0 = self.rest_local()
            pt, pr, ps = self.keys(source)
            frames = np.minimum(np.arange(len(t)), len(pt) - 1)
            for k in self.gun_bones():
                t[:, k] = t0[k] + pt[frames, k] - pt[0, k]
                r[:, k] = quat_multiply(r0[k], quat_multiply(quat_inverse(pr[0, k]), pr[frames, k]))
                s[:, k] = s0[k] * ps[frames, k] / ps[0, k]
        return t, r, s

    def world(self, t, r, s):
        """The world matrix of each bone for each frame, from local tracks."""
        local = np.zeros(t.shape[:2] + (4, 4))
        local[..., :3, :3] = quat_matrix(r) * s[..., None, :]
        local[..., :3, 3] = t
        local[..., 3, 3] = 1.0
        world = np.zeros_like(local)
        for k, p in enumerate(self.parents):
            world[:, k] = local[:, k] if p < 0 else world[:, p] @ local[:, k]
        return world

    def bake(self, clip):
        """World matrices of a clip: (frames x bones x 4 x 4, local scale frames x bones x 3)."""
        t, r, s = self.local(clip)
        return self.world(t, r, s), s

    def pieces(self, clip):
        """(the clips of a clip of [compose], the first frame of each one), else two empty lists."""
        spec = self.rules.get('compose', {}).get(clip)
        if not spec:
            return [], []
        starts, at = [], 0
        for c in spec['clips']:
            starts.append(at)
            at += len(self.local(c)[0]) - 1
        return list(spec['clips']), starts


def camera_place(template, rig_folder):
    """The place of the camera bone in the first frame of the ready clip of the template weapon."""
    import fo4clip
    from d2template import Template
    t = Template(template)
    skel = fo4clip.skeleton()
    _, world, _, _ = fo4clip.decode(os.path.join(t.clip_folder(rig_folder), t.data['ready'] + '.hkx'), skel)
    return world[0, list(skel.bones).index('Camera'), :3, 3]


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Evaluate clips of a Destiny first-person file.')
    ap.add_argument('file')
    ap.add_argument('--clip', action='append', required=True)
    ap.add_argument('-o', '--output', required=True, help='the folder for CLIP.npz')
    ap.add_argument('--fo4', action='store_true',
                    help='the matrices in Fallout 4 world space (tools/d2rig.py): the eye point of the rig at the '
                         'place of the camera bone of the template weapon')
    ap.add_argument('--template', default='revolver44')
    ap.add_argument('--rig', default=paths.data('destiny', 'port', 'rig'),
                    help='the folder with the clips of the template weapon (default: data/destiny/port/rig)')
    ap.add_argument('--rules', help='a file with the clip rules of a set file (the tables [gun] and [compose])')
    a = ap.parse_args()
    rig = Rig(Glb(a.file), load_rules(a.rules))
    os.makedirs(a.output, exist_ok=True)
    place = camera_place(a.template, a.rig) if a.fo4 else None
    for clip in a.clip:
        world, scale = rig.bake(clip)
        note = ''
        if a.fo4:
            import d2rig
            eye = world[0, rig.index[d2rig.CAMERA], :3, 3]
            if np.abs(eye - np.array(d2rig.EYE)).max() > 1e-3:
                note = ' (the camera bone is at %s in the first frame, not at the eye point)' % np.round(eye, 4)
            world = d2rig.to_fo4_world(world, d2rig.EYE, place)
        pieces, starts = rig.pieces(clip)
        np.savez_compressed(os.path.join(a.output, clip + '.npz'), world=world, names=np.array(rig.names),
                            parents=np.array(rig.parents), fps=FPS, pieces=np.array(pieces), starts=np.array(starts, int))
        if pieces:
            note += ' (%s)' % ', '.join('%s from frame %d' % x for x in zip(pieces, starts))
        elif rig.rules.get('gun', {}).get('parts', {}).get(clip):
            note += ' (the gun parts of %s)' % rig.rules['gun']['parts'][clip]
        print('[bake] %-20s %d frames, %d bones%s' % (clip, world.shape[0], world.shape[1], note))
