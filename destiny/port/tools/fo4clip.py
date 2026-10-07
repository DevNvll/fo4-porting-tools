"""Read a Fallout 4 first-person clip (HKX) as world matrices of the skeleton bones.

The reader of the clips is `fnv/tools/anim_fo4.py` of this repository (the Fallout 4 library).
Its rig folder is `data/fnv/rig` (`./port fnv make-rig` makes it: the skeleton, and with
`--arm-meshes` the arm meshes that the checks read); the environment variable PORT_RIG names
another folder. `fnv/rig/finger_tips.json` is in the source tree.
"""
import os
import sys
import numpy as np

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

PORT = paths.repo('fnv')
PORT_TOOLS = os.path.join(PORT, 'tools')
PORT_RIG = os.environ.get('PORT_RIG') or paths.data('fnv', 'rig')
# measurements of the two hand meshes: a file of the source tree
PORT_TIPS = paths.repo('fnv', 'rig', 'finger_tips.json')
if PORT_TOOLS not in sys.path:
    sys.path.insert(0, PORT_TOOLS)
import anim_fo4  # noqa: E402
from port_hkx import world_from_local, compose  # noqa: E402


def skeleton(path=None):
    return anim_fo4.load_fo4_skeleton(path or os.path.join(PORT_RIG, '1st_skeleton.hkx'))


def rest_world(skel):
    """World matrix of each bone in the reference pose: bones x 4 x 4."""
    out = np.zeros((len(skel.bones), 4, 4))
    for i in range(len(skel.bones)):
        p = skel.reference_pose[i]
        m = compose(np.array(p.translation[:3]), np.array(p.rotation), np.array(p.scale[:3]))
        out[i] = m if skel.parents[i] < 0 else out[skel.parents[i]] @ m
    return out


def decode(path, skel):
    """(the clip data, world matrices frames x bones x 4 x 4, the set of bones with a track)."""
    an = anim_fo4.load_fo4_animation(path)
    nb = len(skel.bones)
    n = an.num_frames
    tr = np.zeros((n, nb, 3))
    ro = np.zeros((n, nb, 4))
    sc = np.ones((n, nb, 3))
    for j in range(nb):
        rp = skel.reference_pose[j]
        tr[:, j] = rp.translation[:3]
        ro[:, j] = rp.rotation
        sc[:, j] = rp.scale[:3]
    t2b = an.track_to_bone_indices or list(range(an.num_tracks))
    for ti, bi in enumerate(t2b):
        t = an.tracks[ti]
        tr[:, bi] = np.array(t.translations)[:, :3]
        ro[:, bi] = np.array(t.rotations)
        sc[:, bi] = np.array(t.scales)[:, :3]
    return an, world_from_local(tr, ro, sc, skel.parents), set(t2b), (tr, ro, sc)


def load_poses(path, skel=None):
    """(world matrices frames x bones x 4 x 4, bone names) of a pose file (.npz of the retarget)
    or of a clip (.hkx)."""
    if path.lower().endswith('.hkx'):
        skel = skel or skeleton()
        _, world, _, _ = decode(path, skel)
        return world, list(skel.bones)
    d = np.load(path, allow_pickle=False)
    return d['poses'], [str(x) for x in d['names']]
