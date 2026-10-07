"""The Destiny first-person rig against the Fallout 4 first-person rig: axes, scale and bone names.

A Destiny file (.glb of d2x or m2x) has +Y up, +Z forward and +X to the left of the
player, in meters. Fallout 4 has +Z up, +Y forward and +X to the right, in game units.

The bones of the two rigs have different local axes:

    bone                    Destiny                              Fallout 4
    along the bone          +Z (right side), -Z (left side)      +X
    hinge of a finger       +Y bends the finger to the palm      -Z bends it to the palm
    hinge of the elbow      +Y bends the arm                     +Z bends the arm
    palm side of the hand   +X (right side), -X (left side)      -Y

So the rotation of a Fallout 4 bone is the rotation of the Destiny bone times a constant
matrix K (its columns are the Fallout 4 axes in the axes of the Destiny bone). The hand bone
has one more constant rotation, from a fit of the palm skin of the two hand meshes
(tools/d2hands.py, rig/d2_hands.json).
"""
import numpy as np

# One meter in game units (the value that esx uses for a model file).
SCALE = 69.99125

# rows: Fallout 4 x, y, z from glTF (x, y, z). It is a rotation.
AXES = np.array([[-1.0, 0.0, 0.0],
                 [0.0, 0.0, 1.0],
                 [0.0, 1.0, 0.0]])

# hand and finger bones
K_HAND = {'R': np.array([[0.0, -1.0, 0.0], [0.0, 0.0, -1.0], [1.0, 0.0, 0.0]]),
          'L': np.array([[0.0, 1.0, 0.0], [0.0, 0.0, -1.0], [-1.0, 0.0, 0.0]])}
# upper arm and forearm
K_ARM = {'R': np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]]),
         'L': np.array([[0.0, -1.0, 0.0], [0.0, 0.0, 1.0], [-1.0, 0.0, 0.0]])}
# The camera bone b_utility looks along its +Z with +Y up; a Fallout 4 camera bone looks
# along its -Z with +Y up.
K_CAMERA = np.diag([-1.0, 1.0, -1.0])

# The camera bone: its place is the first-person eye point and its axes are the view axes.
CAMERA = 'b_utility'
# The place of the camera bone when a clip does not move the camera (meters, axes of the file).
# This point of the file is at the place of the Fallout 4 camera bone.
EYE = (0.0, 1.66, 0.0)
WEAPON = 'b_handle'
FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky')

# The kind of each weapon bone of a Destiny gun. The template says which Fallout 4 bone each
# kind gets ([roles]). A bone with a hash in place of a name (`bone_68719972`, the charging
# handle of the Khvostov) gets its kind in the set file of the weapon ([roles]).
WEAPON_ROLES = {'b_release_1': 'crane', 'b_release_2': 'yoke', 'b_chamber': 'cylinder', 'b_ammo': 'rounds',
                'b_hammer': 'hammer', 'b_trigger': 'trigger', 'b_release_button': 'latch',
                'b_magazine': 'magazine', 'b_bolt': 'bolt', 'b_safety': 'safety', 'b_charging_handle': 'bolt'}


def side_of(name):
    """'L' or 'R' for a bone b_l_... or b_r_..., else None."""
    return {'b_l_': 'L', 'b_r_': 'R'}.get(name[:4])


def finger_chains():
    """(side, finger number) -> (the three Fallout 4 bones, the three Destiny bones)."""
    out = {}
    for side in ('L', 'R'):
        for number, finger in enumerate(FINGERS, 1):
            out[(side, number)] = ([f'{side}Arm_Finger{number}{k}' for k in (1, 2, 3)],
                                   [f'b_{side.lower()}_{finger}_{k}' for k in (1, 2, 3)])
    return out


def bone_axes(name):
    """The matrix K of a Destiny bone (with no palm fit), or None for a bone that the retarget does not read."""
    side = side_of(name)
    if side is None:
        return K_CAMERA if name == CAMERA else None
    part = name[4:]
    if part in ('upperarm', 'forearm'):
        return K_ARM[side]
    if part == 'hand' or part.rsplit('_', 1)[0] in FINGERS:
        return K_HAND[side]
    return None


def to_fo4_world(world, origin, camera):
    """World matrices of a Destiny pose (... x 4 x 4, glTF axes, meters) in Fallout 4 world
    space: the point `origin` of the file (the rest place of the camera bone) is at `camera`
    (the place of the Fallout 4 camera bone). The local axes of a bone do not change, and a
    local point is in game units."""
    out = np.array(world, float, copy=True)
    out[..., :3, :3] = AXES @ world[..., :3, :3]
    out[..., :3, 3] = (world[..., :3, 3] - np.asarray(origin, float)) @ AXES.T * SCALE + np.asarray(camera, float)
    return out


def quat_matrix(q):
    """(x, y, z, w) -> 3 x 3 rotation matrix (column vectors)."""
    x, y, z, w = np.asarray(q, float) / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
