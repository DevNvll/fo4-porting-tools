"""Measure the finger joints of a clip against the vanilla clips of the template weapon.

    python3 destiny/port/check/fingers.py OUT/WPNReload.hkx [--bake WORK/bake/CLIP.npz]
        [--vanilla data/destiny/port/rig/revolver44]

WORK is the work folder of the weapon (data/destiny/port/work/NAME) and OUT is the folder
of its clips (data/destiny/port/out/NAME, or the animation folder of the mod project).

For each joint between two finger bones: the bend about the hinge of the bone (degrees,
positive to the palm), the turn to the side and the twist about the bone, over the frames of
the clip. A vanilla clip has no twist and no turn to the side at these joints, and no joint
bends to the back of the finger, but for the last joint of the thumb. The table has the same
values for all vanilla clips of the template that the reader can read.

With --bake the program also compares how fast each finger bone turns from one frame to the
next with the same bone of the source (a fast turn that the source does not have is a jump).
"""
import argparse
import glob
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
import d2rig  # noqa: E402


def log_vectors(r):
    """Rotation vectors (degrees) of rotation matrices (n x 3 x 3)."""
    cos = np.clip((np.trace(r, axis1=1, axis2=2) - 1.0) / 2.0, -1.0, 1.0)
    angle = np.arccos(cos)
    axis = np.stack([r[:, 2, 1] - r[:, 1, 2], r[:, 0, 2] - r[:, 2, 0], r[:, 1, 0] - r[:, 0, 1]], axis=1)
    norm = np.linalg.norm(axis, axis=1, keepdims=True)
    return np.degrees(np.where(norm > 1e-9, axis / np.where(norm > 1e-9, norm, 1.0) * angle[:, None], 0.0))


def unit_rotations(m):
    r = m[..., :3, :3]
    return r / np.linalg.norm(r, axis=-2, keepdims=True)


def joint_values(world, idx):
    """joint -> array frames x 3: twist about the bone, turn to the side, bend to the palm."""
    out = {}
    for side in 'LR':
        for finger in range(1, 6):
            for k in (1, 2):
                a, b = '%sArm_Finger%d%d' % (side, finger, k), '%sArm_Finger%d%d' % (side, finger, k + 1)
                rel = np.einsum('fji,fjk->fik', unit_rotations(world[:, idx[a]]), unit_rotations(world[:, idx[b]]))
                v = log_vectors(rel)
                out[(side, finger, k)] = np.stack([v[:, 0], v[:, 1], -v[:, 2]], axis=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--bake')
    ap.add_argument('--vanilla', default=paths.data('destiny', 'port', 'rig', 'revolver44'),
                    help='the folder with the vanilla clips of the template (default: data/destiny/port/rig/revolver44)')
    a = ap.parse_args()
    skel = fo4clip.skeleton()
    world, names = fo4clip.load_poses(a.clip, skel)
    idx = {n: i for i, n in enumerate(names)}
    values = joint_values(world, idx)
    vanilla = {}
    count = 0
    for path in sorted(glob.glob(os.path.join(a.vanilla, '*.hkx'))):
        try:
            w, _ = fo4clip.load_poses(path, skel)
        except Exception:
            continue
        count += 1
        for key, v in joint_values(w, idx).items():
            vanilla.setdefault(key, []).append(v)
    vanilla = {k: np.vstack(v) for k, v in vanilla.items()}
    print('%d frames; vanilla: %d clips of %s' % (world.shape[0], count, a.vanilla))
    print('joint            | clip: bend min..max   side max  twist max | vanilla: bend min..max   side max  twist max')
    back = []
    for key in sorted(values):
        side, finger, k = key
        v, w = values[key], vanilla[key]
        name = '%sArm_Finger%d%d-%d' % (side, finger, k, k + 1)
        print('%-16s | %7.1f .. %6.1f   %7.1f   %7.1f   | %7.1f .. %6.1f   %7.1f   %7.1f' % (
            name, v[:, 2].min(), v[:, 2].max(), np.abs(v[:, 1]).max(), np.abs(v[:, 0]).max(),
            w[:, 2].min(), w[:, 2].max(), np.abs(w[:, 1]).max(), np.abs(w[:, 0]).max()))
        if v[:, 2].min() < -0.5 and not (finger == 1 and k == 2):
            back.append('%s %.1f' % (name, v[:, 2].min()))
    print('joints that bend to the back of the finger (not the last thumb joint):', ', '.join(back) or 'none')
    if a.bake:
        bake = np.load(a.bake)
        bw = bake['world']
        # a clip with frames of its last pose at its end (hold_end of the set): the source has its last pose there
        if world.shape[0] > bw.shape[0]:
            bw = np.concatenate([bw, np.repeat(bw[-1:], world.shape[0] - bw.shape[0], axis=0)], axis=0)
        bidx = {str(n): i for i, n in enumerate(bake['names'])}
        print('the largest turn of a finger bone in one frame (degrees), in the space of its hand bone: source | result')
        worst = (0.0, '')
        for (side, finger), (fo4, src) in d2rig.finger_chains().items():
            for fb, sb in zip(fo4, src):
                def speed(w, i, hand):
                    rel = np.einsum('fji,fjk->fik', unit_rotations(w[:, hand]), unit_rotations(w[:, i]))
                    step = np.einsum('fji,fjk->fik', rel[:-1], rel[1:])
                    return np.linalg.norm(log_vectors(step), axis=1)
                s = speed(bw, bidx[sb], bidx['b_%s_hand' % side.lower()])
                r = speed(world, idx[fb], idx[side + 'Arm_Hand'])
                extra = float((r - s).max())
                if extra > worst[0]:
                    worst = (extra, '%s frame %d: source %.1f, result %.1f' % (fb, int(np.argmax(r - s)), s[np.argmax(r - s)], r[np.argmax(r - s)]))
                print('  %-16s %6.1f | %6.1f   (largest difference in one frame %.1f at frame %d)' % (fb, s.max(), r.max(), extra, int(np.argmax(r - s))))
        print('largest turn in one frame that the source does not have: %.1f degrees (%s)' % worst)


if __name__ == '__main__':
    main()
