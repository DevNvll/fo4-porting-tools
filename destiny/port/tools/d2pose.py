#!/usr/bin/env python3
"""Clips of a Destiny 2 first-person rig with the hand pose of a pose clip of the gun.

    ./port destiny pose data/destiny/port/extract/NAME/manifest.json \
        --pose TAG --hold CLIP[:FRAME] --clip CLIP [--clip ...] [-o data/destiny/port/extract/NAME/posed]
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python \
        destiny/port/tools/d2pose.py ...          (the same program with no ./port)

Most clips of the hands are clips of the weapon class: the left hand has the pose for the
gun of the class, and it does not hold each gun of the class. The file of a gun has short
additive clips with one pose (2 frames, offsets only). One of them moves the left hand and
bends its fingers so that the hand is on this gun. The extraction does not say which state
uses such a clip, so the pose clip is a choice: `tools/d2pose.py --list` prints each short
additive clip with its offsets, and --measure prints the distance of the two hands to the
gun for a pose clip.

The program adds the offsets of the pose clip to each frame of a clip, at the level of the
rig controls (the rule of d2x/anim.py for an additive clip: rotation = base x offset,
translation = base + offset), and solves the rig again with the decoder of the extraction
(tiger-animation-parser). It reads the game packages with the modules of destiny/extract/d2x
and does not change them, so it runs with the Python environment of d2x.

    --pose TAG      the tag of the pose clip (8 hex digits), or the name of the clip in the file
    --bones left    the controls that get the offsets: `left` (the left hand and its fingers;
                    the default), `hands` (the two hands and their fingers) or `all`
    --hold CLIP[:FRAME]   the hold pose of the set file. A frame of a clip gets the offsets
                    with a weight: 1 while the left wrist is less than --near cm from its place
                    of the hold pose (in the space of the gun bone), 0 at more than --far cm.
                    So the hand has the pose only while it is on the gun.
    --gun-on-grip   the gun bone is on the grip bone of the right hand for the measurements
                    ([gun] rest = true of the set file)

Output, in the folder of -o: CLIP.npz for each clip, with the local tracks of each bone
(`t`, `r`, `s`: frames x bones x 3, 4, 3, as the file of the extraction has them), `names`,
and `weight` (the weight of each frame). tools/d2bake.py reads these tracks in place of the
clip of the file (the rule `tracks`; [hand_pose] of a set file).
"""
import argparse
import json
import os
import sys

import numpy as np

from d2x import anim, pkg

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import d2third  # noqa: E402
from glb import Glb  # noqa: E402
from d2bake import Rig  # noqa: E402

GUN_BONES = ('b_handle', 'bone_', 'b_magazine', 'b_pump', 'b_shell')
NOT_HAND = ('upperarm', 'clav', 'grip', 'foot', 'calf', 'thigh', 'toe')


def rows_multiply(a, b):
    """a (n x 4) x b (4), as (x, y, z, w)."""
    ax, ay, az, aw = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bx, by, bz, bw = b
    return np.stack([aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz], axis=-1)


def part(q, weight):
    """The part `weight` (n values from 0 to 1) of the rotation q, on the short way: n x 4."""
    q = np.asarray(q, float)
    q = -q if q[3] < 0 else q
    angle = np.arccos(np.clip(q[3], -1.0, 1.0))
    if angle < 1e-9:
        return np.tile(np.array([0.0, 0.0, 0.0, 1.0]), (len(weight), 1))
    axis = q[:3] / np.sin(angle)
    return np.concatenate([axis[None] * np.sin(angle * weight)[:, None], np.cos(angle * weight)[:, None]], axis=1)


class Poser:
    def __init__(self, manifest_path):
        self.manifest = json.load(open(manifest_path))
        self.first = self.manifest['first_person'][0]
        folder = os.path.dirname(os.path.abspath(manifest_path))
        raw = os.path.join(folder, 'raw')
        os.makedirs(raw, exist_ok=True)
        self.pm = pkg.PackageManager()
        self.body = d2third.Body(self.pm, int(self.first['entity'], 16), raw)
        self.names = self.body.names
        self.index = {n: i for i, n in enumerate(self.names)}
        self.controls = list(self.body.rig.rig.control_to_bone)
        self.glb = Glb(os.path.join(folder, self.first['file']))
        self.rig = Rig(self.glb)
        self.tags = {r['name']: int(r['tag'], 16) for r in self.first['clips']}

    def tag(self, text):
        """The tag of a clip: 8 hex digits, or a clip name of the file (with or with no `_add`)."""
        for name in (text, text[:-4] if text.endswith('_add') else text + '_add'):
            if name in self.tags:
                return self.tags[name]
        return int(text, 16)

    def selected(self, control, which):
        if control >= len(self.controls):
            return False
        bone = self.names[self.controls[control]]
        if which == 'all':
            return True
        hand = bone[:4] in ('b_l_', 'b_r_') and bone[4:] not in NOT_HAND
        return hand and (which == 'hands' or bone.startswith('b_l_'))

    def tracks(self, clip_tag, pose_tag=None, which='left', weight=None):
        """The local tracks (t, r, s) of a clip, with the offsets of a pose clip."""
        data, tracks = self.body.rig.controls(self.body.dump(clip_tag))
        if pose_tag is not None:
            _, offsets = self.body.rig.controls(self.body.dump(pose_tag))
            frames = data.animation_header.frame_count
            w = np.ones(frames) if weight is None else np.asarray(weight, float)
            for i, (track, offset) in enumerate(zip(tracks, offsets)):
                if not self.selected(i, which):
                    continue
                if offset.rotations is not None and track.rotations is not None:
                    q = np.asarray(offset.rotations, float).reshape(-1, 4)[-1]
                    base = np.asarray(track.rotations, float).reshape(-1, 4)
                    if len(base) == 1 and frames > 1:
                        base = np.repeat(base, frames, axis=0)
                    turned = np.stack([rows_multiply(base[f:f + 1], p)[0] for f, p in enumerate(part(q, w[:len(base)]))])
                    track.rotations = turned.astype(np.float32)
                if offset.translations is not None and track.translations is not None:
                    move = np.asarray(offset.translations, float)
                    move = move.reshape(-1, move.shape[-1])[-1, :3]
                    base = np.asarray(track.translations, float)
                    base = base.reshape(-1, base.shape[-1]).copy()
                    if len(base) == 1 and frames > 1:
                        base = np.repeat(base, frames, axis=0)
                    base[:, :3] += move[None] * w[:len(base), None]
                    track.translations = base.astype(np.float32)
        solved = anim.convert_obj_to_local(data, anim.rig_retarget(data, tracks, self.body.rig.skeleton, self.body.rig.rig),
                                           self.body.rig.skeleton)
        r = np.moveaxis(np.stack([np.asarray(t.rotations, float) for t in solved]), 0, 1)
        t = np.moveaxis(np.stack([np.asarray(t.translations, float) for t in solved]), 0, 1)[..., :3]
        s = np.moveaxis(np.stack([np.asarray(t.scales, float) for t in solved]), 0, 1)
        if s.ndim == 2:
            s = np.repeat(s[..., None], 3, axis=-1)
        return t, r, s

    def world(self, t, r, s, gun_on_grip=False):
        local = np.zeros(t.shape[:2] + (4, 4))
        local[..., :3, :3] = d2third.quat_matrix(r) * s[..., None, :]
        local[..., :3, 3] = t
        local[..., 3, 3] = 1.0
        world = d2third.world_of(local, self.body.parents)
        if gun_on_grip:
            t0, r0, s0 = self.rig.rest_local()
            rest = self.rig.world(t0[None], r0[None], s0[None])[0]
            handle = np.linalg.inv(rest[self.rig.index['b_handle']])
            for n in self.names:
                if n.startswith(GUN_BONES) and n in self.rig.index:
                    world[:, self.index[n]] = world[:, self.index['b_r_grip']] @ (handle @ rest[self.rig.index[n]])
        return world

    def wrist(self, world):
        """The left wrist in the space of the gun bone, for each frame (meters)."""
        return (np.linalg.inv(world[:, self.index['b_handle']]) @ world[:, self.index['b_l_hand']])[:, :3, 3]

    # the meshes of the file, for --measure
    def meshes(self, test):
        out = []
        for node in self.glb.nodes:
            if 'mesh' not in node or not test(node.get('name', '')):
                continue
            for prim in self.glb.json['meshes'][node['mesh']]['primitives']:
                a = prim['attributes']
                out.append((self.glb.accessor(a['POSITION']), self.glb.accessor(a['JOINTS_0']).astype(int),
                            self.glb.accessor(a['WEIGHTS_0']).astype(float), self.glb.accessor(prim['indices']).reshape(-1, 3).astype(int)))
        return out

    def skinned(self, parts, world):
        joints_of = self.rig.skin_joints
        out = []
        for pos, joints, weights, tris in parts:
            p = np.zeros_like(pos)
            for k in range(joints.shape[1]):
                for j in np.unique(joints[:, k]):
                    sel = (joints[:, k] == j) & (weights[:, k] > 0)
                    if sel.any():
                        m = world[self.index[joints_of[j]]] @ self.rig.inverse_bind[joints_of[j]]
                        p[sel] += weights[sel, k, None] * (pos[sel] @ m[:3, :3].T + m[:3, 3])
            out.append((p, joints, weights, tris))
        return out

    def measure(self, world):
        """For each hand: (nearest vertex to the gun in cm, vertices nearer than 0.5 cm, than 1.5 cm, vertices)."""
        rng = np.random.default_rng(1)
        gun = self.skinned(self.meshes(lambda n: n.startswith('region')), world)
        tri = np.vstack([p[t] for p, _, _, t in gun])
        area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
        pick = rng.choice(len(tri), 120000, p=area / area.sum())
        u, v = rng.random(len(pick)), rng.random(len(pick))
        flip = u + v > 1
        u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
        surface = (tri[pick, 0] + u[:, None] * (tri[pick, 1] - tri[pick, 0]) + v[:, None] * (tri[pick, 2] - tri[pick, 0])).astype(np.float32)
        out = {}
        hands = self.skinned(self.meshes(lambda n: n == 'body_hands'), world)
        pos = np.vstack([h[0] for h in hands])
        main = np.concatenate([h[1][np.arange(len(h[0])), np.argmax(h[2], axis=1)] for h in hands])
        names = [self.rig.skin_joints[j] for j in main]
        for side in ('l', 'r'):
            sel = np.array([n.startswith('b_%s_' % side) and 'forearm' not in n and 'upperarm' not in n for n in names])
            p = pos[sel].astype(np.float32)
            d = np.concatenate([np.sqrt(((p[i:i + 400, None] - surface[None]) ** 2).sum(-1)).min(1) for i in range(0, len(p), 400)]) * 100
            out[side] = (float(d.min()), int((d < 0.5).sum()), int((d < 1.5).sum()), len(d))
        return out


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest')
    ap.add_argument('--pose', help='the pose clip: a tag or a clip name')
    ap.add_argument('--bones', choices=('left', 'hands', 'all'), default='left')
    ap.add_argument('--hold', help='CLIP[:FRAME], the hold pose')
    ap.add_argument('--near', type=float, default=3.0, help='cm')
    ap.add_argument('--far', type=float, default=8.0, help='cm')
    ap.add_argument('--clip', action='append', default=[])
    ap.add_argument('--gun-on-grip', action='store_true')
    ap.add_argument('--list', action='store_true', help='print each additive clip of 2 or 3 frames with its offsets')
    ap.add_argument('--measure', action='store_true', help='print the distance of the hands to the gun in the hold pose, with and with no pose clip')
    ap.add_argument('-o', '--output')
    a = ap.parse_args()
    p = Poser(a.manifest)
    if a.list:
        for record in p.first['clips']:
            if not record.get('additive') or record['frames'] > 3:
                continue
            _, tracks = p.body.rig.controls(p.body.dump(int(record['tag'], 16)))
            found = []
            for i, track in enumerate(tracks):
                if i >= len(p.controls):
                    continue
                move = 0.0 if track.translations is None else float(np.abs(np.asarray(track.translations, float)[..., :3]).max())
                turn = 0.0 if track.rotations is None else float(np.degrees(2 * np.arccos(np.clip(np.abs(np.asarray(track.rotations, float).reshape(-1, 4)[:, 3]), 0, 1))).max())
                if move > 0.002 or turn > 1.0:
                    found.append('%s %.1f cm %.0f deg' % (p.names[p.controls[i]], move * 100, turn))
            print('%-22s %s, %d frames, %d nodes: %s' % (record['name'], record['tag'], record['frames'], record['nodes'], '; '.join(found) or 'no offset'))
        return
    if not a.hold:
        raise SystemExit('give --hold CLIP[:FRAME]')
    hold_clip, _, hold_frame = a.hold.partition(':')
    hold_frame = int(hold_frame or 0)
    hold = p.wrist(p.world(*p.tracks(p.tag(hold_clip)), a.gun_on_grip))[hold_frame]
    pose = p.tag(a.pose) if a.pose else None
    if a.measure:
        for label, tag in (('no pose clip', None), ('the pose clip %08X, %s' % (pose or 0, a.bones), pose)):
            if label != 'no pose clip' and tag is None:
                continue
            world = p.world(*p.tracks(p.tag(hold_clip), tag, a.bones), a.gun_on_grip)
            m = p.measure(world[hold_frame])
            print('%-36s the left wrist in the gun bone (cm) %s' % (label, (p.wrist(world)[hold_frame] * 100).round(1).tolist()))
            for side, text in (('l', 'left'), ('r', 'right')):
                print('    %-5s hand: the nearest vertex is %.2f cm from the gun; %d of %d vertices are nearer than 0.5 cm, %d nearer than 1.5 cm' % (
                    text, m[side][0], m[side][1], m[side][3], m[side][2]))
        return
    if pose is None:
        raise SystemExit('give --pose TAG')
    out = a.output or os.path.join(os.path.dirname(os.path.abspath(a.manifest)), 'posed')
    os.makedirs(out, exist_ok=True)
    order = [p.index[n] for n in p.rig.names]                 # the bones in the order of tools/d2bake.py
    for clip in a.clip:
        tag = p.tag(clip)
        base = p.world(*p.tracks(tag), a.gun_on_grip)
        distance = np.linalg.norm(p.wrist(base) - hold, axis=1) * 100
        weight = 1.0 - smooth((distance - a.near) / (a.far - a.near))
        t, r, s = p.tracks(tag, pose, a.bones, weight)
        moved = np.linalg.norm(p.wrist(p.world(t, r, s, a.gun_on_grip)) - p.wrist(base), axis=1) * 100
        np.savez_compressed(os.path.join(out, clip + '.npz'), t=t[:, order], r=r[:, order], s=s[:, order], names=np.array(p.rig.names), weight=weight)
        print('[pose] %-20s %3d frames; the weight of the pose is 1 on %d frames and 0 on %d frames; the left wrist moves %.1f cm at most' % (
            clip, len(weight), int((weight > 0.999).sum()), int((weight < 0.001).sum()), moved.max()))


if __name__ == '__main__':
    main()
