"""Make first-person clips from the weapon motion of the vanilla clips of the template weapon.

A source set has no walk, run, sprint or gun-down animation, and some sets have only a
reload. A vanilla clip of the template weapon has the hands of another gun, so the pose
would change at each step. This script takes from a vanilla clip only the rigid motion of
the weapon bone against the vanilla ready pose, and applies that motion to a pose of the
ported gun (weapon, hands, fingers, elbow direction). The arms are solved again by the
retarget solver. The camera bone and the annotations are those of the vanilla clip.

[synth] of the configuration file of the weapon:

    ready = { bake = "SCENE" }              the pose at the ready: a bake file, frame 0
    ready = { bake = "SCENE", frame = 0 }   the same, and a static clip has copies of this one frame
    sighted = { bake = "SCENE" }            the pose in the sights from a bake file, or
    sighted = { sight = [x, y, z], back = 2.0 }   the ready pose, moved so that the eye point of the gun
                                            (FNV weapon space) is on the view axis, `back` units in front of the camera
    sighted = { bake = "SCENE", frame = 0, sight_node = "##SightingNode", distance = 17.6 }
                                            a pose of the source, moved so that this node of the gun is on the view
                                            axis. New Vegas moves the camera to the node; Fallout 4 has the sights
                                            in the clip. `distance`: the weapon bone is this far in front of the camera.
                                            `align = true`: the gun also turns until its barrel axis is the view axis
    moving = ["NODE", ...]                  more nodes of the bake that move with the gun
    [synth.clips]    NAME = "ready" or "sighted"          the vanilla clip NAME on that pose
    [synth.static]   NAME = { base = "ready", vanilla = "CLIP", frame = 0, frames = 60 }
                     one weapon place of a vanilla clip (or the pose as it is) on each frame of the pose
                     NAME = { base = "sighted", bake = "SCENE", events = [[0, "weaponFire"]] }
                     each frame of a source clip with the move of that pose, and its annotations

blender --background --factory-startup --python synth.py -- [--vanilla rig/smg] [--out out/fo4]
"""
import argparse
import json
import math
import os
import sys
import numpy as np
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from common import Bake, load_target, load_source_rest  # noqa: E402
from solver import Retargeter  # noqa: E402
from retarget import parts, Setup, add_solver_arguments, np_to_matrix  # noqa: E402
import anim_fo4  # noqa: E402
from port_hkx import world_from_local  # noqa: E402
import port_config as cfg  # noqa: E402

SY = cfg.D.get('synth', {})
# kind of pose -> the vanilla clip whose first frame has the weapon in that pose
REF = dict(cfg.TEMPLATE['synth'])
EXTRA_MOVING = tuple(SY.get('moving', ()))


def decode(path, skel):
    an = anim_fo4.load_fo4_animation(path)
    nb = len(skel.bones)
    n = an.num_frames
    tr = np.zeros((n, nb, 3))
    ro = np.zeros((n, nb, 4))
    sc = np.ones((n, nb, 3))
    for j in range(nb):
        rp = skel.reference_pose[j]
        tr[:, j] = rp.translation
        ro[:, j] = rp.rotation
        sc[:, j] = rp.scale
    t2b = an.track_to_bone_indices or list(range(an.num_tracks))
    for ti, bi in enumerate(t2b):
        t = an.tracks[ti]
        tr[:, bi] = np.array(t.translations)
        ro[:, bi] = np.array(t.rotations)
        sc[:, bi] = np.array(t.scales)
    return an, world_from_local(tr, ro, sc, skel.parents)


def moving(name):
    if name == 'Weapon' or name in EXTRA_MOVING or name.startswith('##'):
        return True
    for side in ('L', 'R'):
        if name.startswith('Bip01 %s ' % side) or name.startswith('Bip01 %sUpArm' % side):
            rest = name[len('Bip01 %s' % side):].strip()
            if rest.split(' ')[0] in ('Clavicle', 'Thigh', 'Calf', 'Foot', 'Toe0'):
                return False
            return True
    return False


def to_matrix(m):
    return Matrix([list(r) for r in m])


def run(a):
    skel, target = load_target(a.fo4_skeleton)
    source = load_source_rest(a.nvcs)
    idx = {n: i for i, n in enumerate(skel.bones)}
    names = list(skel.bones)
    os.makedirs(os.path.join(a.out, 'poses'), exist_ok=True)
    cache = {}
    setup = Setup(a, source, target)

    def vanilla(name):
        if name not in cache:
            cache[name] = decode(os.path.join(a.vanilla, name.lower() + '.hkx'), skel)
        return cache[name]
    bakes = {}

    def bake(scene):
        if scene not in bakes:
            bakes[scene] = Bake(os.path.join(a.anim, scene + '.json'))
        return bakes[scene]
    rx = Quaternion((1, 0, 0), -math.pi / 2).to_matrix().to_4x4()

    def make(name, frames, annotations):
        """frames: list of (delta matrix in FO4 world space, base world dict, FO4 camera matrix or None,
        FO4 matrix of the Camera Control bone or None)."""
        rt = setup.retargeter()
        off = Matrix.Translation(rt.offset)
        offi = Matrix.Translation(-rt.offset)
        arr = np.zeros((len(frames), len(names), 4, 4))
        poses = []
        for i, (d, base, cam, control) in enumerate(frames):
            dfnv = offi @ d @ off
            world = {}
            for n, m in base.items():
                world[n] = dfnv @ m if moving(n) else m
            if 'Camera1st' not in world:
                world['Camera1st'] = source.rest['Camera1st']
            if cam is not None:
                world['Camera1st'] = offi @ cam @ rx
            pose = rt.convert(world)
            if control is not None:
                # the vanilla clip moves this bone in the sprint (0, 0, 9.518); keep its values
                pose['Camera Control'] = control
            poses.append(pose)
        rt.smooth_fingers(poses)
        for i, pose in enumerate(poses):
            for j, n in enumerate(names):
                arr[i, j] = np.array(pose[n])
        tag = 'synth_' + name
        np.savez_compressed(os.path.join(a.out, 'poses', tag + '.npz'), poses=arr, names=np.array(names),
                            parents=np.array(skel.parents), fps=30)
        with open(os.path.join(a.out, 'poses', tag + '.json'), 'w') as f:
            json.dump({'annotations': annotations, 'max_shoulder_adjustment': rt.max_shoulder_adjustment,
                       'max_arm_length_error': rt.max_length_error}, f, indent=1)
        print('[synth] %-24s frames %3d shoulder adjustment %.3f arm length error %.5f annotations %d' % (
            name, len(frames), rt.max_shoulder_adjustment, rt.max_length_error, len(annotations)), flush=True)

    wi = idx['Weapon']
    ci = idx['Camera']
    cci = idx['Camera Control']

    def spec(kind):
        sp = SY[kind]
        return SY['ready'] if 'sight' in sp else sp

    def fixed_view(kind):
        """True when the pose of this kind has the sights on the view axis of the vanilla camera."""
        return 'sight' in SY[kind] or 'sight_node' in SY[kind]

    def base_world(kind, frame=None):
        sp = spec(kind)
        return bake(sp['bake']).world(sp.get('frame', 0) if frame is None else frame)

    def pre(kind):
        """The move of the gun from the base pose to the pose of this kind, in FO4 world space."""
        sp = SY[kind]
        if 'sight_node' in sp:
            rt = setup.retargeter()
            base = base_world(kind)
            hold = rt.shifted(base['Weapon']) @ np_to_matrix(cfg.c_matrix('Weapon'))
            eye = base[sp['sight_node']].translation + rt.offset
            _, wr = vanilla(REF[kind])
            camera = to_matrix(wr[0, ci]).translation
            turn = Matrix.Identity(4)
            if sp.get('align'):
                # turn the gun about the eye point until its barrel axis is the view axis (+Y)
                forward = hold.to_3x3() @ Vector((0.0, 1.0, 0.0))
                q = forward.rotation_difference(Vector((0.0, 1.0, 0.0)))
                turn = Matrix.Translation(eye) @ q.to_matrix().to_4x4() @ Matrix.Translation(-eye)
                hold = turn @ hold
            move = camera - eye
            # the view axis is +Y: the place along it is that of the source, or `distance` from the camera
            move.y = (camera.y + float(sp['distance']) - hold.translation.y) if 'distance' in sp else 0.0
            return Matrix.Translation(move) @ turn
        if 'sight' not in sp:
            return Matrix.Identity(4)
        rt = setup.retargeter()
        hold = rt.shifted(base_world(kind)['Weapon']) @ np_to_matrix(cfg.c_matrix('Weapon'))
        _, wr = vanilla(REF[kind])
        eye = Vector(cfg.fnv_to_fo4(np.array(sp['sight'], float)))
        # the vanilla weapon bone has no rotation in the sights, and the view axis is +Y through the camera
        target = Matrix.Translation(to_matrix(wr[0, ci]).translation - eye + Vector((0.0, float(sp.get('back', 0.0)), 0.0)))
        return target @ hold.inverted()

    for name, kind in SY.get('clips', {}).items():
        an, w = vanilla(name)
        _, wr = vanilla(REF[kind])
        w0i = to_matrix(wr[0, wi]).inverted() @ pre(kind)
        base = base_world(kind)
        frames = [(to_matrix(w[f, wi]) @ w0i, base, to_matrix(w[f, ci]), to_matrix(w[f, cci])) for f in range(w.shape[0])]
        make(name, frames, [(round(x.time, 4), x.text) for x in an.annotations])
    for name, st in SY.get('static', {}).items():
        kind = st['base']
        _, wr = vanilla(REF[kind])
        d = pre(kind)
        if 'vanilla' in st:
            _, w = vanilla(st['vanilla'])
            d = to_matrix(w[st.get('frame', 0), wi]) @ to_matrix(wr[0, wi]).inverted() @ d
        sp = spec(kind)
        if 'bake' in st:
            bk = bake(st['bake'])
            worlds = [bk.world(f) for f in range(bk.count)]
        elif 'frame' in sp:
            count = int(st.get('frames', 2))
            worlds = [base_world(kind)] * count
        else:
            bk = bake(sp['bake'])
            worlds = [bk.world(f) for f in range(bk.count)]
        cam = control = None
        if fixed_view(kind):
            cam, control = to_matrix(wr[0, ci]), to_matrix(wr[0, cci])
        frames = [(d, world, cam, control) for world in worlds]
        make(name, frames, [(round(frame / 30.0, 4), text.replace('{sound}', cfg.SOUND)) for frame, text in st.get('events', [])])


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--vanilla', default=os.path.join(cfg.RIG, cfg.TEMPLATE['clips']))
    ap.add_argument('--anim', default=os.path.join(cfg.OUT, 'anim'))
    ap.add_argument('--out', default=os.path.join(cfg.OUT, 'fo4'))
    ap.add_argument('--fo4-skeleton', default=os.path.join(cfg.RIG, '1st_skeleton.hkx'))
    ap.add_argument('--nvcs', default=os.path.join(cfg.RIG, 'nvcs_1st.json'))
    add_solver_arguments(ap)
    run(ap.parse_args(sys.argv[sys.argv.index('--') + 1:]))
