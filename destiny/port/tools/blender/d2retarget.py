"""Retarget baked Destiny poses to the Fallout 4 first-person skeleton.

blender --background --factory-startup --python destiny/port/tools/blender/d2retarget.py -- \
    --bake WORK/bake/CLIP.npz [--bake ...] --parts WORK/parts.json --out WORK/fo4

WORK is the work folder of the weapon (data/destiny/port/work/NAME).

For each bake file: OUT/poses/CLIP.npz (the world matrix of each Fallout 4 bone for each frame,
4 x 4, column vectors) and OUT/report/CLIP.json (the checks). tools/d2hkx.py makes the HKX
file from the poses. With --synth FILE: OUT/poses/synth_NAME.npz and .json for each clip that
takes the weapon motion of a vanilla clip of the template (see synth).
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
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
import fo4clip  # noqa: E402  (adds fnv/tools to the path)
sys.path.insert(0, os.path.join(fo4clip.PORT_TOOLS, 'blender'))
sys.path.insert(0, HERE)
from common import load_target  # noqa: E402
from solver import Collider  # noqa: E402
from d2solver import D2Retargeter, to_matrix  # noqa: E402
from d2template import Template  # noqa: E402
import d2rig  # noqa: E402


class Setup:
    """The data of the solver, read one time."""

    def __init__(self, a):
        self.a = a
        self.skel, self.target = load_target(a.fo4_skeleton)
        self.names = list(self.skel.bones)
        self.template = Template(a.template)
        hands = json.load(open(a.hands))
        tips = json.load(open(a.tips))
        self.hands = hands
        self.tips = {'fnv': hands['source'], 'fo4': tips['fo4']}
        self.parts_data = json.load(open(a.parts))
        self.parts = {bone: (self.parts_data['sources'][bone], to_matrix(c)) for bone, c in self.parts_data['c'].items()}
        _, world, _, _ = fo4clip.decode(os.path.join(self.template.clip_folder(a.rig), self.template.data['ready'] + '.hkx'), self.skel)
        self.base = {n: to_matrix(world[0, i]) for i, n in enumerate(self.names)}
        self.part_local = {b: to_matrix(self.template.local(b)) for b in self.template.pivots}

    def retargeter(self):
        a = self.a
        rt = D2Retargeter(self.target, self.parts, self.base, self.hands, self.part_local)
        rt.tips = self.tips
        if not a.no_collision:
            rt.collider = Collider(self.parts_data, tuple(a.skip))
        rt.corner_lift = a.corner_lift
        rt.finger_depth = a.finger_depth
        rt.finger_max_push = a.finger_max_push
        rt.finger_min_bend = a.finger_min_bend
        rt.skin_center = a.skin_center == 'on'
        rt.planar = a.planar == 'on'
        rt.knuckles = a.knuckles == 'align'
        rt.closed_fingers = a.closed_fingers == 'on'
        rt.plane_fit = a.plane_fit == 'on'
        rt.collision_iterations = a.collision_iterations
        return rt


def sight_move(setup, a, tag, world, source):
    """The move of a clip in the sights (--sight-clip) that puts the aim point of the sight
    (--sight, Fallout 4 weapon space) on the view axis in the first frame, or None.

    A Destiny clip in the sights can be the clip of a weapon class (each rifle has the same
    one), and the game aligns the sight of each weapon when it runs. The move is at a right
    angle to the view axis, and each bone but the camera bone gets it on each frame: the arms,
    the hands and the gun move as one body."""
    if not a.sight or tag not in a.sight_clip:
        return None
    sidx = {n: i for i, n in enumerate(source)}
    weapon = np.array(world[0, sidx[d2rig.WEAPON]]) @ np.array(setup.parts['Weapon'][1])
    point = weapon[:3, :3] @ np.array([float(x) for x in a.sight.split(',')]) + weapon[:3, 3]
    camera = np.array(world[0, sidx[d2rig.CAMERA]])
    view = camera[:3, 2] / np.linalg.norm(camera[:3, 2])        # the camera bone of the file looks along its +Z
    offset = camera[:3, 3] - point
    return offset - view * float(offset @ view)


def moved(world, source, move):
    out = np.array(world, copy=True)
    for i, n in enumerate(source):
        if n != d2rig.CAMERA:
            out[..., i, :3, 3] += move
    return out


def run(a):
    setup = Setup(a)
    names = setup.names
    os.makedirs(os.path.join(a.out, 'poses'), exist_ok=True)
    os.makedirs(os.path.join(a.out, 'report'), exist_ok=True)
    moves = {}
    for path in a.bake:
        bake = np.load(path)
        tag = os.path.splitext(os.path.basename(path))[0]
        source = [str(n) for n in bake['names']]
        world = bake['world']
        move = sight_move(setup, a, tag, world, source)
        if move is not None:
            world = moved(world, source, move)
            moves[tag] = [float(x) for x in move]
            print('[retarget] %-20s the sight goes to the view axis: each bone but the camera moves %s (%.3f units)' % (
                tag, np.round(move, 3), np.linalg.norm(move)), flush=True)
        rt = setup.retargeter()
        poses = []
        for f in range(world.shape[0]):
            poses.append(rt.convert({n: to_matrix(world[f, i]) for i, n in enumerate(source)}))
        smoothed = rt.smooth_fingers(poses)
        arr = np.zeros((len(poses), len(names), 4, 4), np.float64)
        for i, pose in enumerate(poses):
            for j, n in enumerate(names):
                arr[i, j] = np.array(pose[n])
        if not np.all(np.isfinite(arr)):
            raise SystemExit(tag + ': non-finite pose')
        idx = {n: i for i, n in enumerate(names)}
        sidx = {n: i for i, n in enumerate(source)}
        wrist = max(float(np.abs(arr[:, idx[f'{s}Arm_Hand'], :3, 3] - world[:, sidx[f'b_{s.lower()}_hand'], :3, 3]).max()) for s in 'LR')
        # with `--knuckles align` the wrist has the move of the knuckles: the error is against that place
        wrist = max(0.0, wrist - rt.max_knuckle_shift) if rt.knuckles else wrist
        weapon = float(np.abs(arr[:, idx['Weapon']] - world[:, sidx[d2rig.WEAPON]] @ np.array(setup.parts['Weapon'][1])).max())
        report = {'clip': tag, 'frames': int(world.shape[0]), 'fps': float(bake['fps']),
                  'wrist_position_error': wrist, 'weapon_matrix_error': weapon,
                  'max_shoulder_move': rt.max_shoulder_move,
                  'max_forearm_twist_degrees': float(np.degrees(rt.max_forearm_twist)),
                  'max_upper_arm_twist_degrees': float(np.degrees(rt.max_upper_twist)),
                  'max_fingertip_error': rt.max_tip_error,
                  'mean_fingertip_error': rt.tip_error_sum / rt.tip_count if rt.tip_count else None,
                  'fingers_with_the_rule_for_a_closed_finger': rt.hook_count,
                  'knuckles': 'align' if rt.knuckles else 'wrist', 'max_wrist_move_for_the_knuckles': rt.max_knuckle_shift,
                  'finger_collision': rt.collider is not None, 'fingers_moved_by_collision_step': rt.push_count,
                  'max_joint_move_of_collision_step': rt.max_push_turn, 'max_joint_move_after_time_filter': smoothed,
                  'corner_lift': rt.corner_lift, 'finger_depth': rt.finger_depth, 'finger_max_push': rt.finger_max_push,
                  'finger_min_bend': rt.finger_min_bend, 'skin_center': rt.skin_center, 'planar': rt.planar, 'collision_skip': list(a.skip)}
        np.savez_compressed(os.path.join(a.out, 'poses', tag + '.npz'), poses=arr, names=np.array(names),
                            parents=np.array(setup.skel.parents), fps=float(bake['fps']))
        with open(os.path.join(a.out, 'report', tag + '.json'), 'w') as f:
            json.dump(report, f, indent=1)
        print('[retarget] %-20s frames %4d wrist %.4f weapon %.5f shoulder %.2f twist fore %.0f upper %.0f tip max %.3f mean %.4f moved %d max move %.2f filtered %.2f closed %d' % (
            tag, world.shape[0], wrist, weapon, rt.max_shoulder_move, report['max_forearm_twist_degrees'],
            report['max_upper_arm_twist_degrees'], rt.max_tip_error, report['mean_fingertip_error'] or 0.0,
            rt.push_count, rt.max_push_turn, smoothed, rt.hook_count), flush=True)
    # the check programs give the same move to the source (check/gun.py, check/contact.py)
    with open(os.path.join(a.out, 'moves.json'), 'w') as f:
        json.dump(moves, f, indent=1)


def synth(a):
    """The clips that the source does not have (the file of --synth: a list of
    {"name", "bake", "frame", "kind", "vanilla", "static", "frames", "reference"}).

    A vanilla clip of the template weapon has the hands of another gun, so the pose would
    change at each step. Such a clip gives only the rigid motion of its weapon bone against
    the vanilla ready pose (kind "ready") or the vanilla pose in the sights (kind "sighted"),
    or against the first frame of the vanilla clip `reference` (the sprint: the motion of the
    vanilla sprint against its own first frame, on the sprint pose of the source).
    That motion moves a pose of the source as one body: the arms, the hands and the gun. The
    camera bone, the bone Camera Control and the events are those of the vanilla clip. Each
    bone of `synth_bones` of the template (the bolt) has its motion of the vanilla clip on the
    gun. With `static`, one weapon place of the vanilla clip (that frame) is on each of
    `frames` frames, and the camera is that of the pose."""
    setup = Setup(a)
    names = setup.names
    idx = {n: i for i, n in enumerate(names)}
    folder = setup.template.clip_folder(a.rig)
    cache = {}

    def vanilla(name):
        if name not in cache:
            an, world, _, _ = fo4clip.decode(os.path.join(folder, name.lower() + '.hkx'), setup.skel)
            cache[name] = (an, world)
        return cache[name]
    os.makedirs(os.path.join(a.out, 'poses'), exist_ok=True)
    for spec in json.load(open(a.synth)):
        bake = np.load(spec['bake'])
        source = [str(n) for n in bake['names']]
        world_source = bake['world']
        move = sight_move(setup, a, os.path.splitext(os.path.basename(spec['bake']))[0], world_source, source)
        if move is not None:
            world_source = moved(world_source, source, move)
        base = {n: to_matrix(world_source[spec['frame'], i]) for i, n in enumerate(source)}
        # the vanilla pose of the gun that the pose of the source is: the ready pose or the pose in
        # the sights of the template, or the first frame of the clip `reference`
        _, ref = vanilla(spec.get('reference') or setup.template.data[spec['kind']])
        an, world = vanilla(spec['vanilla'])
        ref_inverse = to_matrix(ref[0, idx['Weapon']]).inverted()
        if spec.get('static') is not None:
            moves = [(to_matrix(world[spec['static'], idx['Weapon']]) @ ref_inverse, None, None)] * int(spec.get('frames', 30))
            annotations = []
        else:
            moves = [(to_matrix(world[f, idx['Weapon']]) @ ref_inverse, to_matrix(world[f, idx['Camera']]),
                      to_matrix(world[f, idx['Camera Control']])) for f in range(world.shape[0])]
            annotations = [[round(x.time, 4), x.text] for x in an.annotations]
        rt = setup.retargeter()
        poses = []
        # A part that the vanilla clip moves on the gun (`synth_bones` of the template: the bolt in
        # a shot). The bone of the ported gun has the rest place of the vanilla bone, so the
        # place of the vanilla bone in the vanilla weapon is the place of the part in the gun.
        parts = [b for b in setup.template.data.get('synth_bones', []) if b in idx] if spec.get('static') is None else []
        for f, (move, camera, control) in enumerate(moves):
            pose = rt.convert({n: (m if n == d2rig.CAMERA else move @ m) for n, m in base.items()})
            if camera is not None:
                pose['Camera'] = camera
                pose['Camera Control'] = control
            for b in parts:
                pose[b] = pose['Weapon'] @ (to_matrix(world[f, idx['Weapon']]).inverted() @ to_matrix(world[f, idx[b]]))
            poses.append(pose)
        rt.smooth_fingers(poses)
        arr = np.zeros((len(poses), len(names), 4, 4), np.float64)
        for i, pose in enumerate(poses):
            for j, n in enumerate(names):
                arr[i, j] = np.array(pose[n])
        if not np.all(np.isfinite(arr)):
            raise SystemExit(spec['name'] + ': non-finite pose')
        tag = 'synth_' + spec['name']
        np.savez_compressed(os.path.join(a.out, 'poses', tag + '.npz'), poses=arr, names=np.array(names),
                            parents=np.array(setup.skel.parents), fps=30.0)
        with open(os.path.join(a.out, 'poses', tag + '.json'), 'w') as f:
            json.dump({'annotations': annotations, 'vanilla': spec['vanilla'], 'kind': spec['kind'],
                       'max_shoulder_move': rt.max_shoulder_move}, f, indent=1)
        print('[synth] %-24s frames %3d  weapon motion of %-22s on the pose %-8s events %d' % (
            spec['name'], len(poses), spec['vanilla'], spec['kind'], len(annotations)), flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--bake', action='append', default=[])
    ap.add_argument('--synth', help='a file with the clips that take the weapon motion of a vanilla clip (see synth)')
    ap.add_argument('--parts', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--sight', help='X,Y,Z: the aim point of the sight in Fallout 4 weapon space (see sight_move)')
    ap.add_argument('--sight-clip', action='append', default=[], help='a clip of the file in the sights: it gets the move of --sight')
    ap.add_argument('--template', default='revolver44')
    ap.add_argument('--rig', default=paths.data('destiny', 'port', 'rig'),
                    help='the folder with the clips of the template weapon (default: data/destiny/port/rig)')
    ap.add_argument('--hands', default=paths.repo('destiny', 'port', 'rig', 'd2_hands.json'))
    ap.add_argument('--tips', default=fo4clip.PORT_TIPS)
    ap.add_argument('--fo4-skeleton', default=os.path.join(fo4clip.PORT_RIG, '1st_skeleton.hkx'))
    ap.add_argument('--no-collision', action='store_true')
    ap.add_argument('--skip', action='append', default=[], help='a shape of the parts file that is not a collider for the fingers')
    ap.add_argument('--corner-lift', type=float, default=0.5)
    ap.add_argument('--finger-depth', type=float, default=0.65)
    ap.add_argument('--finger-max-push', type=float, default=1.15)
    ap.add_argument('--finger-min-bend', type=float, default=0.3)
    ap.add_argument('--skin-center', choices=('on', 'off'), default='on')
    ap.add_argument('--plane-fit', choices=('on', 'off'), default='on',
                    help='on: after the collision step, the plane of a finger is fitted to its joints; off: the plane through the knuckle and the fingertip')
    ap.add_argument('--collision-iterations', type=int, default=8, help='the count of passes of the collision step for each finger')
    ap.add_argument('--closed-fingers', choices=('on', 'off'), default='off',
                    help='on: a closed finger (a hook, a fist) keeps the bends of its last two bones (see finger_path of d2solver.py)')
    ap.add_argument('--knuckles', choices=('wrist', 'align'), default='wrist',
                    help='wrist: each wrist at the source wrist; align: the wrist moves so that the mean of the four knuckles is at the mean of the source knuckles (see knuckle_shift)')
    ap.add_argument('--planar', choices=('on', 'off'), default='on',
                    help='on: each finger in one plane, so the joints after the knuckle are hinges; off: the joints on the source line')
    args = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if args.bake:
        run(args)
    if args.synth:
        synth(args)
