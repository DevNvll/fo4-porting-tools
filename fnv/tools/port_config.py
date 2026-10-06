"""The data of one conversion, read from its configuration file.

The environment variable PORT_CONFIG names the file. PORT_WORK replaces the work folder of
the file, and PORT_RIG replaces the rig folder. The file gives only what the tools cannot
find; tools/port_defaults.py has the defaults. tools/port.py writes the file for a source
folder.

FNV weapon bone space: +X to the muzzle, +Y up, +Z to the right.
FO4 weapon space: +Y to the muzzle, +Z up, +X to the right.
A point p_fnv becomes p_fo4 = R @ p_fnv + T.

T puts the trigger of the gun at the trigger pivot of the template weapon, so that the
hands of the vanilla clips (third person, and the clips that the mod does not replace) hold
the grip.

Each moving part is on a FO4 weapon bone. Its rest transform relative to its parent bone is
the pivot of the template weapon. A vanilla clip then shows the part at its rest place.
"""
import os
import tomllib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CONFIG = os.environ.get('PORT_CONFIG')
if not CONFIG:
    raise SystemExit('Set PORT_CONFIG to the configuration file of the conversion.')
CONFIG = os.path.abspath(CONFIG)
PROJECT = os.path.dirname(CONFIG)
with open(CONFIG, 'rb') as _f:
    D = tomllib.load(_f)


NAME = D['name']
WORK = os.environ.get('PORT_WORK') or os.path.expanduser(D.get('work') or '/tmp/%s-port' % NAME.lower())
RIG = os.environ.get('PORT_RIG') or os.path.join(ROOT, 'rig')
OUT = os.path.join(WORK, 'out')


def path(p):
    """A path of the configuration file: relative to the folder of the file. {work} is the work folder."""
    p = os.path.expanduser(p.replace('{work}', WORK))
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(PROJECT, p))


with open(os.path.join(ROOT, 'templates', D['template'] + '.toml'), 'rb') as _f:
    TEMPLATE = tomllib.load(_f)
SOUND = TEMPLATE['sound']
FPS = 30

# A file gives only what the tools cannot find: port_defaults adds each other value.
import port_defaults  # noqa: E402
MODEL = port_defaults.resolve(D, PROJECT, TEMPLATE, OUT, RIG)
SOURCE = D['source']

# rows: FO4 x, y, z from FNV (x, y, z)
R = np.array([[0.0, 0.0, 1.0],
              [1.0, 0.0, 0.0],
              [0.0, 1.0, 0.0]])
TRIGGER_FNV = np.array(D['weapon']['trigger'], float)         # center of the trigger mesh in weapon bone space
TEMPLATE_TRIGGER = np.array(TEMPLATE['trigger_pivot'], float)
T = TEMPLATE_TRIGGER - R @ TRIGGER_FNV
T[0] = 0.0                                                    # keep the gun on the center plane

# FO4 bone -> (FNV node, pivot relative to the FO4 parent bone at rest)
PARTS = {'Weapon': ('Weapon', None)}
for _bone, _node in D.get('parts', {}).items():
    PARTS[_bone] = (_node, np.array(TEMPLATE['pivots'][_bone], float))
# FO4 bone -> rest rotation relative to its parent bone (x, y, z, w), for a template whose
# clips keep a bone turned at rest (the magazine of the 10mm pistol). Most bones have none.
PART_ROTATION = {b: np.array(q, float) / np.linalg.norm(q) for b, q in TEMPLATE.get('rotations', {}).items() if b in PARTS}
FO4_PARENT = {b: TEMPLATE['parents'][b] for b in PARTS if b != 'Weapon'}
for _bone, _parent in FO4_PARENT.items():
    if _parent not in PARTS:
        raise SystemExit('%s: the part %s needs its parent %s in [parts]' % (CONFIG, _bone, _parent))

# FO4 bone -> rest matrix of its FNV node in FNV weapon space (4x4, column vectors).
# A part node has its own place in the model.
NODE_REST = {}
_world = {}
for _b, _parent, _wr, _wt, _ws in MODEL.walk():
    _m = np.eye(4)
    _m[:3, :3] = _wr * _ws
    _m[:3, 3] = _wt
    _world[_b['name']] = _m
for _bone, (_node, _) in PARTS.items():
    if _bone != 'Weapon':
        if _node not in _world:
            raise SystemExit('%s: the model has no node %s' % (CONFIG, _node))
        NODE_REST[_bone] = _world[_node]


def pivot_in_weapon(bone):
    """Rest position of a FO4 weapon bone in FO4 weapon space."""
    if turned(bone):
        return rest_in_weapon(bone)[:3, 3].copy()
    p = np.zeros(3)
    b = bone
    while b != 'Weapon':
        p = p + PARTS[b][1]
        b = FO4_PARENT[b]
    return p


def turned(bone):
    """True when the bone or a bone above it has a rest rotation."""
    b = bone
    while b != 'Weapon':
        if b in PART_ROTATION:
            return True
        b = FO4_PARENT[b]
    return False


def quat_matrix(q):
    """(x, y, z, w) -> 3x3 rotation matrix (column vectors)."""
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def rest_in_weapon(bone):
    """Rest matrix (4x4, column vectors) of a FO4 weapon bone in FO4 weapon space."""
    chain = []
    b = bone
    while b != 'Weapon':
        chain.append(b)
        b = FO4_PARENT[b]
    m = np.eye(4)
    for b in reversed(chain):
        local = np.eye(4)
        if b in PART_ROTATION:
            local[:3, :3] = quat_matrix(PART_ROTATION[b])
        local[:3, 3] = PARTS[b][1]
        m = m @ local
    return m


def to_bone(bone, points):
    """Points in FO4 weapon space -> the rest space of a FO4 weapon bone."""
    points = np.asarray(points, float)
    if not turned(bone):
        return points - pivot_in_weapon(bone)
    m = np.linalg.inv(rest_in_weapon(bone))
    return points @ m[:3, :3].T + m[:3, 3]


def fnv_to_fo4(p):
    """Points in FNV weapon bone space -> FO4 weapon space."""
    return np.asarray(p, float) @ R.T + T


def c_matrix(bone):
    """4x4 matrix C (column vectors) with: FO4 bone world = FNV node world @ C.
    C maps a point in the local space of the FO4 bone to the local space of the FNV node."""
    m = np.eye(4)
    ri = R.T                      # inverse of R
    piv = pivot_in_weapon(bone)
    m[:3, :3] = ri
    m[:3, 3] = ri @ (piv - T)
    if bone != 'Weapon' and turned(bone):
        # FO4 weapon space -> FNV weapon space, after the rest matrix of the bone
        back = np.eye(4)
        back[:3, :3] = ri
        back[:3, 3] = -(ri @ T)
        m = back @ rest_in_weapon(bone)
    if bone in NODE_REST:
        m = np.linalg.inv(NODE_REST[bone]) @ m
    return m
