"""Retarget a third-person clip of Destiny (the body with the gun) to the Fallout 4 third-person skeleton.

blender --background --factory-startup --python destiny/port/tools/blender/d3retarget.py -- \
    --bake EXTRACT/third_person/reload.npz --name WPNReload --parts WORK/parts.json --out WORK/third

EXTRACT is the extraction of the weapon (data/destiny/port/extract/NAME) and WORK is its work
folder (data/destiny/port/work/NAME).

The bake file is that of tools/d2third.py: the world matrix of each bone of the body and of the
gun for each frame. The result is OUT/poses/NAME.npz (the world matrix of each Fallout 4 bone
for each frame) and OUT/report/NAME.json. tools/d2hkx.py makes the HKX file from the poses.

The two games have different bodies and different stances, and a Destiny third-person clip of
a weapon moves the upper body only (the pelvis and the legs do not move in it). So the clip
is the stance of Fallout 4 with the motion of Destiny on it:

* The stance (`base`): the first frame of the vanilla third-person clip `third_ready` of the
  template weapon. The pelvis, the legs and each bone that has no rule here keep that pose.
* The gun, `--gun stance` (the default). Its motion against its own first frame (a turn and a
  move in world space) goes on the place of the gun in the stance. So the gun starts and ends
  where the vanilla clips of Fallout 4 have it, and it tilts and moves as in Destiny. This is
  for a gun that Destiny has near the place of the stance (a rifle at the shoulder).
* The gun, `--gun source`. The gun has its place of Destiny against the right shoulder, and
  its rotation of Destiny. This is for a gun that Destiny has at another place than the
  stance: a machine gun is at the hip in its reload, 19 units below the shoulder, and with the
  rule above the left arm is too short for the hand places of the source. On the first and the
  last `--blend` frames the gun goes from the place of the stance to that place and back, so
  the clip starts and ends in the stance.
* The left hand and its fingers. Each frame of the source moves as one body so that its gun
  is on that gun: the hand has its place of Destiny against the gun. The rules of the fingers
  are those of the first-person retarget (tools/blender/d2solver.py).
* The right hand (`--grip`). While the right hand of the source is on the grip, it has its
  place against the gun and its fingers of the first-person hold pose (a pose file of the
  first-person retarget), as the vanilla third-person reload has a right hand that does not
  move on the grip. The third-person clips of Destiny move the right hand 1 to 3 units on the
  grip and open its fingers: in the game the fingers then do not hold the grip. "On the
  grip" is a move of less than `--grip-near` units against its place of the first frame (in
  the space of the gun). With a move of more than `--grip-far` units (the hand goes to the
  charging handle of a machine gun) the hand has the motion of the source: its move and its
  turn against the first frame, on the place of the grip, and the fingers of the source.
  Between the two values the two poses are mixed.
* The spine, the neck, the head and the collarbones. Each one has its rotation of the stance
  with the turn of the source bone against its first frame (in world space). Each bone keeps
  its length.
* The bone WeaponIKTargetL. The game puts the left hand on this bone with IK, in each
  third-person clip and pose of a weapon: each vanilla clip has it on the left hand (0.3 units
  or less away, on each frame). So it has the matrix of the left hand here. With this bone at
  its rest place (the origin of the gun) the game pulls the left hand to the grip.
* The arms. The shoulder is where the collarbone puts it. The elbow is on the circle that
  the two bone lengths give between the shoulder and the wrist, at the point nearest to the
  elbow of the source. When the wrist is farther from the shoulder than the arm is long, the
  collarbone moves to the wrist by the missing length (`max_shoulder_shift` of the report).
"""
import argparse
import json
import math
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
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
import fo4clip  # noqa: E402  (adds fnv/tools to the path)
sys.path.insert(0, os.path.join(fo4clip.PORT_TOOLS, 'blender'))
sys.path.insert(0, HERE)
from mathutils import Matrix, Quaternion, Vector  # noqa: E402
from common import load_target, trs  # noqa: E402
from solver import Collider, aim_x  # noqa: E402
from d2solver import D2Retargeter, to_matrix, twist_x, near, X_AXIS  # noqa: E402
from d2template import Template  # noqa: E402
import d2rig  # noqa: E402

# Fallout 4 bone -> the Destiny bone whose turn it takes
TORSO = (('Spine1', 'b_spine_1'), ('Spine2', 'b_spine_2'), ('Chest', 'b_spine_3'), ('Neck', 'b_neck_1'), ('Head', 'b_head'),
         ('LArm_Collarbone', 'b_l_clav'), ('RArm_Collarbone', 'b_r_clav'))
KEEP = ('Camera', 'Camera Control', 'CamTarget')


def rotation_only(m):
    return m.to_quaternion().to_matrix().to_4x4()


class D3Retargeter(D2Retargeter):
    """The retarget of a third-person pose. `base` is the stance: Fallout 4 bone -> world matrix."""

    def __init__(self, target, parts, base, hands, part_local, first, grip=None):
        super().__init__(target, parts, base, hands, part_local)
        # grip: bone of the right hand -> its matrix against the bone Weapon, or None
        self.grip = grip
        self.place = None
        self.grip_near, self.grip_far = 4.0, 8.0
        self.grip_weight = 0.0
        self.max_grip_weight = 0.0
        self.grip_frames = 0
        self.stance = {n: m.copy() for n, m in base.items()}
        self.first = {n: m.copy() for n, m in first.items()}          # the first frame of the source
        self.gun_source, self.gun_c = parts['Weapon']
        self.gun_first = first[self.gun_source] @ self.gun_c
        self.stance_shoulder = (base['RArm_Collarbone'] @ self.base_local['RArm_UpperArm']).translation
        # the right hand of the source against its gun, in the first frame
        self.hand_first = self.gun_first.inverted() @ first['b_r_hand']
        self.gun_mode, self.blend = 'stance', 8
        self.frame, self.frames = 0, 1
        self.max_shoulder_shift = 0.0
        self.max_gun_move = 0.0
        self.max_gun_turn = 0.0
        self.torso_turn = {}
        self.last_pole = {}

    def gun(self, world, shoulder):
        """(the place of the gun for a source pose, the gun of the source). `shoulder` is the place
        of the right shoulder joint of the pose."""
        now = world[self.gun_source] @ self.gun_c
        turn = now.to_quaternion() @ self.gun_first.to_quaternion().inverted()
        move = now.translation - self.gun_first.translation
        stance = self.stance['Weapon']
        self.max_gun_move = max(self.max_gun_move, move.length)
        self.max_gun_turn = max(self.max_gun_turn, min(turn.angle, 2.0 * math.pi - turn.angle))
        if self.gun_mode == 'stance':
            # its motion against its first frame, on the stance
            return trs(stance.translation + move, turn @ stance.to_quaternion()), now
        # its place of the source against the right shoulder, and the stance at the two ends of the clip
        there = trs(shoulder + (now.translation - world['b_r_upperarm'].translation), now.to_quaternion())
        edge = min(self.frame, self.frames - 1 - self.frame)
        t = min(max(edge / float(self.blend), 0.0), 1.0) if self.blend > 0 else 1.0
        weight = t * t * (3.0 - 2.0 * t)
        if weight >= 1.0:
            return there, now
        here = shoulder + (stance.translation - self.stance_shoulder)
        return trs(here.lerp(there.translation, weight), stance.to_quaternion().slerp(there.to_quaternion(), weight)), now

    def convert(self, world):
        target = self.target
        # the stance with the turns of the upper body
        pose = {n: m.copy() for n, m in self.stance.items()}
        done = set()
        for name, source in TORSO:
            turn = world[source].to_quaternion() @ self.first[source].to_quaternion().inverted()
            self.torso_turn[name] = max(self.torso_turn.get(name, 0.0), min(turn.angle, 2.0 * math.pi - turn.angle))
            parent = target.parents[name]
            place_of = (pose[parent] @ self.base_local[name]).translation
            pose[name] = trs(place_of, turn @ self.stance[name].to_quaternion())
            done.add(name)
        for name in target.names:
            parent = target.parents[name]
            if name not in done and parent and name not in KEEP:
                pose[name] = pose[parent] @ self.base_local[name]
        place, now = self.gun(world, (pose['RArm_Collarbone'] @ self.base_local['RArm_UpperArm']).translation)
        self.place = place
        shift = place @ now.inverted()                                   # the source, as one body, with its gun on the gun
        moved = {n: shift @ m for n, m in world.items()}
        self.base, keep = pose, self.base                                # the solve of the first-person class starts from `base`
        try:
            out = super().convert(moved)
        finally:
            self.base = keep
        for name in KEEP:
            if name in self.stance:
                out[name] = self.stance[name].copy()
        out['WeaponIKTargetL'] = out['LArm_Hand'].copy()                   # the game puts the left hand here with IK
        if self.grip:
            # The fingers of the right hand. On the grip: those of the grip, with no collision step
            # and no time filter. Away from the grip: those of the source. Between: a mix, in the
            # space of the hand.
            weight = self.grip_weight
            if weight < 1.0:
                hand = out['RArm_Hand']
                for name, m in self.grip.items():
                    if 'Finger' not in name:
                        continue
                    held = self.grip['RArm_Hand'].inverted() @ m             # the finger bone against the hand, in the grip
                    if weight > 0.0:
                        solved = hand.inverted() @ out[name]
                        held = trs(held.translation.lerp(solved.translation, weight),
                                   held.to_quaternion().slerp(solved.to_quaternion(), weight))
                    out[name] = hand @ held
                for log in (self.finger_log[-1], self.finger_normals[-1]):
                    for key in [k for k in log if k[0] == 'R']:
                        del log[key]
            for name in target.names:
                if target.parents[name] == 'RArm_Hand' and name.startswith('AnimObject'):
                    out[name] = out['RArm_Hand'] @ self.base_local[name]
        return out

    def solve_arm(self, side, world, pose):
        target = self.target
        s = side.lower()
        collar, upper, fore1, fore2, fore3, hand = [f'{side}Arm_{n}' for n in (
            'Collarbone', 'UpperArm', 'ForeArm1', 'ForeArm2', 'ForeArm3', 'Hand')]
        su, sf, sh = f'b_{s}_upperarm', f'b_{s}_forearm', f'b_{s}_hand'
        hand_rotation = self.rotation(world, sh)
        wrist = world[sh].translation + hand_rotation @ self.hand_shift[side]
        if side == 'R' and self.grip:
            # the motion of the hand of the source against its place of the first frame, in the space of the gun
            now = self.place.inverted() @ world[sh]
            move = now.translation - self.hand_first.translation
            turn = now.to_quaternion() @ self.hand_first.to_quaternion().inverted()
            t = min(max((move.length - self.grip_near) / (self.grip_far - self.grip_near), 0.0), 1.0)
            weight = t * t * (3.0 - 2.0 * t)
            self.grip_weight = weight
            self.max_grip_weight = max(self.max_grip_weight, weight)
            self.grip_frames += 1 if weight == 0.0 else 0
            held = self.grip[hand]
            if weight > 0.0:
                held = trs(held.translation + move * weight, Quaternion().slerp(turn, weight) @ held.to_quaternion())
            held = self.place @ held
            hand_rotation, wrist = held.to_quaternion(), held.translation
        lengths = [target.local[n].translation.length for n in (fore1, fore2, fore3, hand)]
        a, b = lengths[0], sum(lengths[1:])
        shoulder = (pose[collar] @ self.base_local[upper]).translation
        line = wrist - shoulder
        distance = line.length
        reach = (a + b) * 0.999
        if distance > reach:
            # the arm is too short: the collarbone moves to the wrist by the missing length
            step = line.normalized() * (distance - reach)
            self.max_shoulder_shift = max(self.max_shoulder_shift, step.length)
            pose[collar] = Matrix.Translation(step) @ pose[collar]
            shoulder = shoulder + step
            line = wrist - shoulder
            distance = line.length
        axis = line.normalized()
        along = (a * a - b * b + distance * distance) / (2.0 * distance)
        radius = math.sqrt(max(a * a - along * along, 0.0))
        pole = world[sf].translation - shoulder
        pole -= axis * pole.dot(axis)
        if pole.length < 1e-4:
            pole = self.last_pole.get(side, Vector((0.0, 0.0, -1.0)))
            pole -= axis * pole.dot(axis)
        pole.normalize()
        self.last_pole[side] = pole.copy()
        elbow = shoulder + axis * along + pole * radius
        upper_line = (elbow - shoulder).normalized()
        fore_line = (wrist - elbow).normalized()
        qu = aim_x(self.rotation(world, su), upper_line)
        qf = aim_x(self.rotation(world, sf), fore_line)
        twist = near(twist_x(qf.inverted() @ hand_rotation @ self.hand_ref[side].inverted()), self.last_twist.get(('fore', side)))
        self.last_twist[('fore', side)] = twist
        self.max_forearm_twist = max(self.max_forearm_twist, abs(twist))
        pose[upper] = trs(shoulder, qu)
        pose[fore1] = trs(elbow, qf)
        pose[fore2] = trs(elbow + fore_line * lengths[1], qf @ Quaternion(X_AXIS, twist / 3.0))
        pose[fore3] = trs(elbow + fore_line * (lengths[1] + lengths[2]), qf @ Quaternion(X_AXIS, 2.0 * twist / 3.0))
        pose[hand] = trs(wrist, hand_rotation)
        qc = pose[collar].to_quaternion()
        turn = near(twist_x((qc @ self.upper_ref[side]).inverted() @ qu), self.last_twist.get(('upper', side)))
        self.last_twist[('upper', side)] = turn
        self.max_upper_twist = max(self.max_upper_twist, abs(turn))
        tw1, tw2 = f'{side}Arm_UpperTwist1', f'{side}Arm_UpperTwist2'
        pose[tw1] = trs((pose[upper] @ target.local[tw1]).translation, qu @ Quaternion(X_AXIS, -2.0 * turn / 3.0))
        pose[tw2] = trs((pose[tw1] @ target.local[tw2]).translation, qu @ Quaternion(X_AXIS, -turn / 3.0))


def run(a):
    skel, target = load_target(a.fo4_skeleton)
    names = list(skel.bones)
    template = Template(a.template)
    hands = json.load(open(a.hands))
    tips = json.load(open(a.tips))
    parts_data = json.load(open(a.parts))
    parts = {bone: (parts_data['sources'][bone], to_matrix(c)) for bone, c in parts_data['c'].items()}
    base_clip = a.base or os.path.join(a.rig, template.data['third_clips'], template.data['third_ready'] + '.hkx')
    _, world, _, _ = fo4clip.decode(base_clip, skel)
    base = {n: to_matrix(world[a.base_frame, i]) for i, n in enumerate(names)}
    part_local = {b: to_matrix(template.local(b)) for b in template.pivots}
    os.makedirs(os.path.join(a.out, 'poses'), exist_ok=True)
    os.makedirs(os.path.join(a.out, 'report'), exist_ok=True)
    grip = None
    if a.grip:
        # the right hand of the first-person hold pose, against the gun
        d = np.load(a.grip)
        held = d['poses'][a.grip_frame]
        index = {str(n): i for i, n in enumerate(d['names'])}
        inverse = to_matrix(held[index['Weapon']]).inverted()
        grip = {n: inverse @ to_matrix(held[index[n]]) for n in index if n == 'RArm_Hand' or n.startswith('RArm_Finger')}
    for path, name in zip(a.bake, a.name):
        bake = np.load(path)
        source = [str(n) for n in bake['names']]
        # the feet of the source are at the origin, as the bone Root of the stance
        src = d2rig.to_fo4_world(bake['world'], (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        first = {n: to_matrix(src[0, i]) for i, n in enumerate(source)}
        rt = D3Retargeter(target, parts, base, hands, part_local, first, grip)
        rt.grip_near, rt.grip_far = a.grip_near, a.grip_far
        rt.gun_mode, rt.blend, rt.frames = a.gun, a.blend, int(src.shape[0])
        rt.tips = {'fnv': hands['source'], 'fo4': tips['fo4']}
        if not a.no_collision:
            rt.collider = Collider(parts_data, tuple(a.skip))
        rt.corner_lift, rt.finger_depth, rt.finger_max_push, rt.finger_min_bend = 0.5, 0.65, 1.15, 0.3
        rt.skin_center = rt.planar = rt.plane_fit = True
        poses = []
        for f in range(src.shape[0]):
            rt.frame = f
            poses.append(rt.convert({n: to_matrix(src[f, i]) for i, n in enumerate(source)}))
        smoothed = rt.smooth_fingers(poses)
        arr = np.zeros((len(poses), len(names), 4, 4), np.float64)
        for i, pose in enumerate(poses):
            for j, n in enumerate(names):
                arr[i, j] = np.array(pose[n])
        if not np.all(np.isfinite(arr)):
            raise SystemExit(name + ': non-finite pose')
        idx = {n: i for i, n in enumerate(names)}
        sidx = {n: i for i, n in enumerate(source)}
        # the hands against the gun: the result against the source
        gun_r = arr[:, idx['Weapon']]
        gun_s = src[:, sidx[d2rig.WEAPON]] @ np.array(parts['Weapon'][1])
        hand_error = 0.0
        for s in ('L' if grip else 'LR'):
            ar = np.linalg.inv(gun_r) @ arr[:, idx[f'{s}Arm_Hand']]
            as_ = np.linalg.inv(gun_s) @ src[:, sidx[f'b_{s.lower()}_hand']]
            hand_error = max(hand_error, float(np.abs(ar[:, :3, 3] - as_[:, :3, 3]).max()))
        # each bone of the body keeps its length
        local = np.linalg.inv(arr[:, [max(skel.parents[i], 0) for i in range(len(names))]]) @ arr
        stretch = 0.0
        for n in names:
            i = idx[n]
            if skel.parents[i] < 0 or n.startswith(('Weapon', 'Camera', 'CamTarget', 'AnimObject')) or 'Finger' in n:
                continue
            length = np.linalg.norm(local[:, i, :3, 3], axis=1)
            stretch = max(stretch, float(np.abs(length - np.linalg.norm(np.array(rt.base_local[n].translation))).max()))
        report = {'clip': name, 'source': os.path.basename(path), 'frames': int(src.shape[0]), 'fps': float(bake['fps']),
                  'base': os.path.relpath(base_clip, a.rig), 'base_frame': a.base_frame, 'gun': a.gun,
                  'blend_frames': a.blend if a.gun == 'source' else 0,
                  'hand_to_gun_position_error': hand_error, 'max_bone_length_change': stretch,
                  'right_hand': 'the grip of %s, frame %d' % (os.path.basename(a.grip), a.grip_frame) if grip else 'the source',
                  'right_hand_frames_on_the_grip': rt.grip_frames if grip else 0,
                  'right_hand_largest_part_of_the_source_motion': rt.max_grip_weight if grip else 1.0,
                  'max_shoulder_shift': rt.max_shoulder_shift, 'max_gun_move': rt.max_gun_move,
                  'max_gun_turn_degrees': math.degrees(rt.max_gun_turn),
                  'max_turn_degrees': {n: round(math.degrees(v), 2) for n, v in rt.torso_turn.items()},
                  'max_forearm_twist_degrees': math.degrees(rt.max_forearm_twist),
                  'max_upper_arm_twist_degrees': math.degrees(rt.max_upper_twist),
                  'max_fingertip_error': rt.max_tip_error, 'fingers_moved_by_collision_step': rt.push_count,
                  'max_joint_move_after_time_filter': smoothed}
        np.savez_compressed(os.path.join(a.out, 'poses', name + '.npz'), poses=arr, names=np.array(names),
                            parents=np.array(skel.parents), fps=float(bake['fps']))
        with open(os.path.join(a.out, 'report', name + '.json'), 'w') as f:
            json.dump(report, f, indent=1)
        print('[third] %-12s frames %4d  left hand to gun %.4f  bone length %.4f  shoulder shift %.2f  gun move %.1f turn %.0f  right hand on the grip %d frames  torso turns %s' % (
            name, src.shape[0], hand_error, stretch, rt.max_shoulder_shift, rt.max_gun_move, report['max_gun_turn_degrees'], rt.grip_frames,
            ' '.join('%s %.0f' % (n.replace('Arm_Collarbone', ' collar'), v) for n, v in report['max_turn_degrees'].items())), flush=True)


if __name__ == '__main__':
    rig_folder = paths.data('destiny', 'port', 'rig')
    ap = argparse.ArgumentParser()
    ap.add_argument('--bake', action='append', required=True, help='a file of tools/d2third.py')
    ap.add_argument('--name', action='append', required=True, help='the name of the Fallout 4 clip of each --bake')
    ap.add_argument('--parts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--template', default='combatrifle')
    ap.add_argument('--rig', default=rig_folder, help='default: data/destiny/port/rig')
    ap.add_argument('--base', help='a vanilla third-person clip (.hkx) with the stance, in place of that of the template')
    ap.add_argument('--base-frame', type=int, default=0)
    ap.add_argument('--hands', default=paths.repo('destiny', 'port', 'rig', 'd2_hands.json'))
    ap.add_argument('--tips', default=fo4clip.PORT_TIPS)
    ap.add_argument('--fo4-skeleton', default=os.path.join(rig_folder, 'third', 'skeleton.hkx'))
    ap.add_argument('--gun', choices=('stance', 'source'), default='stance',
                    help='stance: the motion of the gun on its place of the stance; source: its place of the source against the right shoulder')
    ap.add_argument('--blend', type=int, default=8, help='with --gun source: the frames at each end of the clip for the way from and to the stance')
    ap.add_argument('--grip', help='a pose file of the first-person retarget: the right hand has its place against the gun and its fingers of this pose')
    ap.add_argument('--grip-frame', type=int, default=0)
    ap.add_argument('--grip-near', type=float, default=4.0, help='the right hand is on the grip with a move of less than this (units)')
    ap.add_argument('--grip-far', type=float, default=8.0, help='the right hand has the motion of the source with a move of more than this')
    ap.add_argument('--no-collision', action='store_true')
    ap.add_argument('--skip', action='append', default=[])
    args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if len(args.bake) != len(args.name):
        raise SystemExit('give one --name for each --bake')
    run(args)
