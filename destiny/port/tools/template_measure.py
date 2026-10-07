"""Measure the weapon bones of the vanilla clips of a template folder, for a new template file.

    python3 destiny/port/tools/template_measure.py data/destiny/port/rig/combatrifle wpnreload wpnfiresingleready wpnfireautosighted

The folder has the first-person clips of a vanilla weapon (tools/make_rig.py makes it from
`clips` and `game_clips` of the template file). The program prints

* the rest place of each weapon bone against its parent bone, from the first frame of the
  walk clip (`[pivots]` and `[rotations]` of the template),
* for each clip of the command line, the weapon bones that move and how far (to find the
  part of each bone: the magazine, the bolt),
* the grip point (`grip` of the template), the place of the left hand and the bone
  Camera Control in the first frame of the ready clip and of the clip in the sights.
"""
import sys

sys.dont_write_bytecode = True
if '-h' in sys.argv[1:] or '--help' in sys.argv[1:]:
    print(__doc__.strip())
    sys.exit(0)
import sys, os, math
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fo4clip
folder = sys.argv[1]
skel = fo4clip.skeleton()
names = list(skel.bones); idx = {n: i for i, n in enumerate(names)}


def world(name):
    return fo4clip.decode(os.path.join(folder, name + '.hkx'), skel)[1]


def ang(R):
    return math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))


def quat(R):
    w = math.sqrt(max(0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = math.copysign(math.sqrt(max(0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
    y = math.copysign(math.sqrt(max(0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
    z = math.copysign(math.sqrt(max(0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
    return [x, y, z, w]


wb = [n for n in names if n.startswith('Weapon') and n not in ('Weapon', 'WeaponLeft') and 'IKTarget' not in n]


def local(W, f, b):
    p = names[skel.parents[idx[b]]]
    return np.linalg.inv(W[f, idx[p]]) @ W[f, idx[b]]


W = world('wpnwalkforwardready')
rest = {}
print('rest locals (walk clip, frame 0):')
for b in wb:
    m = local(W, 0, b); rest[b] = m
    print('  %-22s parent %-16s T [%.6f, %.6f, %.6f]  rot %.2f deg  q %s' % (
        b, names[skel.parents[idx[b]]], m[0, 3], m[1, 3], m[2, 3], ang(m[:3, :3]), np.round(quat(m[:3, :3]), 5).tolist()))
for clip in sys.argv[2:]:
    Wc = world(clip)
    print('motion in %s (%d frames): max distance and angle from the rest local' % (clip, Wc.shape[0]))
    for b in wb:
        d = [np.linalg.norm(local(Wc, f, b)[:3, 3] - rest[b][:3, 3]) for f in range(Wc.shape[0])]
        a = [ang(rest[b][:3, :3].T @ local(Wc, f, b)[:3, :3]) for f in range(Wc.shape[0])]
        if max(d) > 0.01 or max(a) > 0.1:
            moving = [f for f in range(Wc.shape[0]) if d[f] > 0.05 or a[f] > 0.5]
            f = int(np.argmax(d))
            delta = local(Wc, f, b)[:3, 3] - rest[b][:3, 3]
            print('  %-22s max %.3f units (frame %d, delta %s), %.1f deg; away in frames %s..%s' % (
                b, max(d), f, np.round(delta, 2).tolist(), max(a), moving[0] if moving else '-', moving[-1] if moving else '-'))
# the grip point: the middle of the first joints of the index and middle fingers of the right hand, weapon space
for clip in ('wpnfiresingleready', 'wpnfiresinglesighted'):
    Wc = world(clip)
    wi = np.linalg.inv(Wc[0, idx['Weapon']])
    g = np.mean([(wi @ Wc[0, idx[n]])[:3, 3] for n in ('RArm_Finger21', 'RArm_Finger31')], axis=0)
    cam = (np.linalg.inv(Wc[0, idx['Camera']]) @ Wc[0, idx['Weapon']])
    cc = Wc[0, idx['Camera Control']]
    lh = (wi @ Wc[0, idx['LArm_Hand']])[:3, 3]
    print('%s frame 0: grip point in weapon space %s; left hand in weapon space %s; Camera Control local %s' % (
        clip, np.round(g, 4).tolist(), np.round(lh, 2).tolist(),
        np.round((np.linalg.inv(Wc[0, idx[names[skel.parents[idx['Camera Control']]]]]) @ cc)[:3, 3], 3).tolist()))
