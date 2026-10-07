"""Compare the gun of the result with the gun of the source, vertex by vertex.

    ./port destiny check gun FILE.glb CLIP WORK/parts.json OUT/WPNReload.hkx
    python3 destiny/port/check/gun.py ...          (the same program with no ./port)

WORK is the work folder of the weapon (data/destiny/port/work/NAME) and OUT is the folder
of its clips (data/destiny/port/out/NAME, or the animation folder of the mod project).

Source: each gun vertex with the skin of the file and the clip of the file, in Fallout 4 world
space. Result: the same vertex of the parts file on its Fallout 4 weapon bone, with the poses
of the clip (an HKX file or a pose file). The program prints the largest distance for each
shape. It also compares the wrist places and the camera.
"""
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
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))
import fo4clip  # noqa: E402
from glb import Glb  # noqa: E402
from d2bake import Rig, camera_place, load_rules  # noqa: E402
import d2rig  # noqa: E402


def main(path, clip, parts_path, poses_path):
    glb = Glb(path)
    # the clip rules of the set file (tools/d2bake.py), which d2fo4.py writes beside the parts file
    rig = Rig(glb, load_rules(os.path.join(os.path.dirname(os.path.abspath(parts_path)), 'clips.json')))
    parts = json.load(open(parts_path))
    poses, names = fo4clip.load_poses(poses_path)
    idx = {n: i for i, n in enumerate(names)}
    world, _ = rig.bake(clip)
    world = d2rig.to_fo4_world(world, d2rig.EYE, camera_place(parts['template'], paths.data('destiny', 'port', 'rig')))
    # A clip in the sights can have a move that puts the sight on the view axis (the retarget
    # step writes it): the source gets the same move, on each bone but the camera bone.
    moves = os.path.join(os.path.dirname(os.path.abspath(parts_path)), 'fo4', 'moves.json')
    move = np.array(json.load(open(moves)).get(clip, [0.0, 0.0, 0.0])) if os.path.exists(moves) else np.zeros(3)
    if np.abs(move).max() > 0.0:
        camera = np.array(world[:, rig.index[d2rig.CAMERA]], copy=True)
        world = np.array(world, copy=True)
        world[:, :, :3, 3] += move
        world[:, rig.index[d2rig.CAMERA]] = camera
        print('the source has the move of the sight: %s units' % np.round(move, 3).tolist())
    # A clip with frames of its last pose at its end (hold_end of the set): the source has its last pose there.
    if poses.shape[0] > world.shape[0]:
        world = np.concatenate([world, np.repeat(world[-1:], poses.shape[0] - world.shape[0], axis=0)], axis=0)
    worst = 0.0
    for s in parts['shapes']:
        node = glb.nodes[glb.node_index(s['source'])]
        prim = glb.json['meshes'][node['mesh']]['primitives'][int(s['name'].split('_')[1])]
        pos = glb.accessor(prim['attributes']['POSITION'])
        joints = glb.accessor(prim['attributes']['JOINTS_0']).astype(int)[:, 0]
        j = rig.skin_joints.index(s['source_bone'])
        ib = rig.inverse_bind[s['source_bone']]
        local = (pos[joints == j] @ ib[:3, :3].T + ib[:3, 3]) * d2rig.SCALE
        m = world[:, rig.index[s['source_bone']]]
        src = np.einsum('fij,vj->fvi', m[:, :3, :3], local) + m[:, None, :3, 3]
        b = poses[:, idx[s['bone']]]
        res = np.einsum('fij,vj->fvi', b[:, :3, :3], np.array(s['positions'])) + b[:, None, :3, 3]
        d = np.linalg.norm(src - res, axis=2)
        worst = max(worst, float(d.max()))
        print('%-24s on %-22s %5d vertices  largest distance %.4f units (frame %d)' % (
            s['name'], s['bone'], len(local), d.max(), int(np.argmax(d.max(1)))))
    for side in 'LR':
        d = np.linalg.norm(poses[:, idx[side + 'Arm_Hand'], :3, 3] - world[:, rig.index['b_%s_hand' % side.lower()], :3, 3], axis=1)
        print('wrist %s: largest distance to the source wrist %.4f units' % (side, d.max()))
    d = np.linalg.norm(poses[:, idx['Camera'], :3, 3] - world[:, rig.index[d2rig.CAMERA], :3, 3], axis=1)
    print('camera: largest distance to the source camera %.4f units; the camera moves %.2f units in the clip' % (
        d.max(), np.linalg.norm(poses[:, idx['Camera'], :3, 3] - poses[0, idx['Camera'], :3, 3], axis=1).max()))
    print('gun: largest distance of a vertex to its place in the source %.4f units (%d frames)' % (worst, poses.shape[0]))


if __name__ == '__main__':
    if len(sys.argv) != 5 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        raise SystemExit(0 if sys.argv[1:2] in (['-h'], ['--help']) else 2)
    main(*sys.argv[1:5])
