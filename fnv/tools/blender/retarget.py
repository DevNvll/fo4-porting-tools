"""Retarget baked FNV poses to the Fallout 4 first-person skeleton.

blender --background --factory-startup --python retarget.py -- \
    --bake out/anim/A.json [--bake ...] [--out out/fo4] [--fo4-skeleton FILE] [--nvcs FILE]

For each bake file: out/fo4/poses/NAME.npz (the world matrix of each FO4 bone for each
frame, 4x4, column vectors) and out/fo4/report/NAME.json (the checks).
The HKX file is made by tools/port_hkx.py from the poses.
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
from solver import Retargeter, Collider, ARM_ROLL  # noqa: E402
import port_config as cfg  # noqa: E402


def np_to_matrix(m):
    return Matrix([list(r) for r in m])


def parts():
    out = {}
    for bone, (node, _) in cfg.PARTS.items():
        out[bone] = (node, np_to_matrix(cfg.c_matrix(bone)))
    return out


class Setup:
    """The options of the solver, read one time."""

    def __init__(self, a, source, target):
        self.a, self.source, self.target = a, source, target
        if not os.path.exists(a.tips):
            raise SystemExit('the file %s is not there (measurements of the two hand meshes, rig/finger_tips.json of the repository)' % a.tips)
        self.tips = json.load(open(a.tips))
        self.collider_parts = None
        if not a.no_collision and a.fingers != 'rotation':
            if not os.path.exists(a.parts):
                raise SystemExit('the file %s is not there: run the step `parts` first' % a.parts)
            self.collider_parts = json.load(open(a.parts))

    def retargeter(self):
        a = self.a
        rt = Retargeter(self.source.rest, self.target, parts())
        rt.tips = self.tips
        if self.collider_parts is not None and not a.no_collision and a.fingers != 'rotation':
            rt.collider = Collider(self.collider_parts, tuple(cfg.D.get('collision', {}).get('skip', ())))
        if a.hand_shift > 0:
            rt.align_knuckles(a.hand_shift)
        rt.finger_mode = 'rotation' if a.fingers == 'rotation' else 'tip'
        rt.finger_solver = 'tip' if a.fingers == 'tip' else 'path'
        rt.corner_lift = a.corner_lift
        rt.thumb_mode = a.thumb
        rt.finger_depth = a.finger_depth
        rt.finger_max_push = a.finger_max_push
        rt.finger_min_bend = a.finger_min_bend
        rt.skin_center = a.skin_center == 'on'
        return rt


def add_solver_arguments(ap):
    ap.add_argument('--tips', default=os.path.join(cfg.RIG, 'finger_tips.json'))
    ap.add_argument('--parts', default=os.path.join(cfg.OUT, 'fo4mesh', 'parts.json'), help='the gun meshes, for the finger collision step')
    ap.add_argument('--no-collision', action='store_true')
    ap.add_argument('--hand-shift', type=float, default=0.0,
                    help='0: the wrist at the source wrist, so the palm is where the source palm is (the two palms have the same outline to 0.5 units); '
                         '1: move each wrist so that the FO4 knuckles are at the source knuckles (mean of four). With 1 the palm is 0.6 units to the side, '
                         'and a part that the palm holds comes through it')
    ap.add_argument('--corner-lift', type=float, default=0.5,
                    help='how much a finger bone that cuts a corner of the source finger line moves toward the corner (0 to 1)')
    ap.add_argument('--finger-depth', type=float, default=0.65,
                    help='the least distance of a finger centerline to the gun, in finger radii')
    ap.add_argument('--finger-max-push', type=float, default=1.15, help='the largest joint move of the collision step')
    ap.add_argument('--finger-min-bend', type=float, default=float(cfg.D.get('fingers', {}).get('min_bend', 0.0)),
                    help='the least flexion of each finger joint, as a part of its bend in the Fallout 4 reference pose '
                         '(0: no rule, a joint can be straight or bend back). Default: min_bend of [fingers] in the configuration file')
    ap.add_argument('--skin-center', choices=('on', 'off'), default='on' if cfg.D.get('fingers', {}).get('skin_center', False) else 'off',
                    help='on: the center of the skin of each finger goes to the center of the skin of the source finger; '
                         'off: the bones go to the bones. Default: skin_center of [fingers] in the configuration file')
    ap.add_argument('--thumb', default='path', choices=('path', 'rotation'),
                    help='rotation: the thumb copies the source rotations; path: its joints are on the source thumb line')
    ap.add_argument('--fingers', default='path', choices=('path', 'tip', 'rotation'),
                    help='path: each finger joint on the path of the source finger; tip: the fingertip at the source fingertip; rotation: copy the source rotations')


def run(a):
    skel, target = load_target(a.fo4_skeleton)
    source = load_source_rest(a.nvcs)
    os.makedirs(os.path.join(a.out, 'poses'), exist_ok=True)
    os.makedirs(os.path.join(a.out, 'report'), exist_ok=True)
    names = list(skel.bones)
    setup = Setup(a, source, target)
    for path in a.bake:
        bake = Bake(path)
        tag = os.path.splitext(os.path.basename(path))[0]
        rt = setup.retargeter()
        poses = []
        missing = set()
        rest_camera = source.rest['Camera1st']
        for f in range(bake.count):
            world = bake.world(f)
            if 'Camera1st' not in world:
                world['Camera1st'] = rest_camera
                missing.add('Camera1st')
            for need in ('Bip01 L Hand', 'Bip01 R Hand', 'Weapon'):
                if need not in world:
                    raise SystemExit('%s: no %s at frame %d' % (tag, need, f))
            poses.append(rt.convert(world))
        smoothed = rt.smooth_fingers(poses)
        arr = np.zeros((len(poses), len(names), 4, 4), np.float64)
        for i, pose in enumerate(poses):
            for j, n in enumerate(names):
                arr[i, j] = np.array(pose[n])
        if not np.all(np.isfinite(arr)):
            raise SystemExit(tag + ': non-finite pose')
        # checks: the hand and the weapon keep their source relation
        hand_err = 0.0
        weap_err = 0.0
        cw = np_to_matrix(cfg.c_matrix('Weapon'))
        for f in (0, bake.count // 2, bake.count - 1):
            world = bake.world(f)
            for side in ('L', 'R'):
                src = world['Bip01 %s Hand' % side].translation + rt.offset
                src = src + (world['Bip01 %s Hand' % side].to_quaternion() @ ARM_ROLL) @ rt.hand_shift[side]
                hand_err = max(hand_err, (poses[f]['%sArm_Hand' % side].translation - src).length)
            src_w = rt.shifted(world['Weapon']) @ cw
            weap_err = max(weap_err, (poses[f]['Weapon'].translation - src_w.translation).length)
        report = {'scene': tag, 'frames': bake.count, 'fps': bake.fps,
                  'offset': list(rt.offset),
                  'max_wrist_error': rt.max_wrist_error, 'max_arm_length_error': rt.max_length_error,
                  'max_shoulder_adjustment': rt.max_shoulder_adjustment,
                  'hand_position_error': hand_err, 'weapon_position_error': weap_err,
                  'hand_shift': {k: list(v) for k, v in rt.hand_shift.items()},
                  'fingers': a.fingers, 'max_fingertip_error': rt.max_tip_error,
                  'finger_collision': rt.collider is not None, 'fingers_moved_by_collision_step': rt.push_count,
                  'max_joint_move_of_collision_step': rt.max_push_turn,
                  'max_joint_move_after_time_filter': smoothed,
                  'corner_lift': rt.corner_lift, 'finger_depth': rt.finger_depth,
                  'finger_min_bend': rt.finger_min_bend, 'skin_center': rt.skin_center,
                  'mean_fingertip_error': rt.tip_error_sum / rt.tip_count if rt.tip_count else None,
                  'missing_sources': sorted(missing)}
        np.savez_compressed(os.path.join(a.out, 'poses', tag + '.npz'), poses=arr, names=np.array(names),
                            parents=np.array(skel.parents), fps=bake.fps)
        with open(os.path.join(a.out, 'report', tag + '.json'), 'w') as f:
            json.dump(report, f, indent=1)
        print('[retarget] %-32s frames %4d wrist %.4f length %.5f shoulder %.3f tip max %.3f mean %.4f moved %d max move %.2f filtered %.2f missing %s' % (
            tag, bake.count, rt.max_wrist_error, rt.max_length_error, rt.max_shoulder_adjustment, rt.max_tip_error,
            rt.tip_error_sum / rt.tip_count if rt.tip_count else 0.0, rt.push_count, rt.max_push_turn, smoothed, sorted(missing)), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--bake', action='append', required=True)
    ap.add_argument('--out', default=os.path.join(cfg.OUT, 'fo4'))
    ap.add_argument('--fo4-skeleton', default=os.path.join(cfg.RIG, '1st_skeleton.hkx'))
    ap.add_argument('--nvcs', default=os.path.join(cfg.RIG, 'nvcs_1st.json'))
    add_solver_arguments(ap)
    run(ap.parse_args(sys.argv[sys.argv.index('--') + 1:]))
