"""Move a New Vegas pose (the NVCS skeleton) to the Fallout 4 first-person skeleton.

The bones of the two skeletons have the same axes after a half turn about X (ARM_ROLL). The
arms are solved again for the Fallout 4 bone lengths with each wrist at the source wrist, and
each finger is solved on the line of the source finger. Each weapon bone follows its node of
the source through a constant matrix (see c_matrix in tools/port_config.py).
"""
import math
from mathutils import Matrix, Quaternion, Vector
from common import trs

ARM_ROLL = Quaternion((1, 0, 0), math.pi)
# The last thumb joint can bend this far to the back of the thumb. The vanilla clips of the
# 10mm pistol hold the left thumb at this value (17 degrees), and it is the largest value of
# the clips of the two templates but for some frames (23 degrees).
THUMB_BACK = math.radians(17.0)


def bone_map():
    result = {'COM': 'Bip01 Pelvis', 'Spine1': 'Bip01 Spine', 'Spine2': 'Bip01 Spine1',
              'Chest': 'Bip01 Spine2', 'Neck': 'Bip01 Neck', 'Head': 'Bip01 Head'}
    for side in ('L', 'R'):
        for target, source in [('Collarbone', 'Clavicle'), ('UpperArm', 'UpperArm'),
                               ('ForeArm1', 'Forearm'), ('Hand', 'Hand')]:
            result[f'{side}Arm_{target}'] = f'Bip01 {side} {source}'
        for target, source in [('Thigh', 'Thigh'), ('Calf', 'Calf'), ('Foot', 'Foot'), ('Toe1', 'Toe0')]:
            result[f'{side}Leg_{target}'] = f'Bip01 {side} {source}'
        for finger in range(1, 6):
            prefix = 'Thumb1' if finger == 1 else f'Finger{finger - 1}'
            for segment, suffix in [(1, ''), (2, '1'), (3, '2')]:
                result[f'{side}Arm_Finger{finger}{segment}'] = f'Bip01 {side} {prefix}{suffix}'
    return result


def aim_x(rotation, direction):
    return (rotation @ Vector((1, 0, 0))).rotation_difference(direction.normalized()) @ rotation


# FO4 finger -> the three FNV bones of the finger
def finger_chains():
    out = {}
    for side in ('L', 'R'):
        for finger in range(1, 6):
            prefix = 'Thumb1' if finger == 1 else f'Finger{finger - 1}'
            out[(side, finger)] = ([f'{side}Arm_Finger{finger}{k}' for k in (1, 2, 3)],
                                   [f'Bip01 {side} {prefix}{sfx}' for sfx in ('', '1', '2')])
    return out


def solve_finger(b0, m1, m2, m3, a1, a2, a3):
    """Joint positions of a FO4 finger whose tip is at the tip of the source finger.

    b0: FO4 knuckle. m1, m2, m3: FO4 segment lengths (m3 to the fingertip).
    a1, a2, a3: source positions of the second joint, the third joint and the fingertip.
    The last segment lies on the last segment of the source, so the pad of the finger
    touches the same place. The first joint bends to the side of the source joint.
    Returns (b1, b2, b3, reach error)."""
    u3 = (a3 - a2)
    if u3.length < 1e-6:
        u3 = (a2 - a1)
    u3.normalize()
    t2 = a3 - u3 * m3
    d = t2 - b0
    dist = d.length
    if dist < 1e-6:
        e = (a1 - b0).normalized()
        return b0 + e * m1, b0 + e * (m1 - m2), a3, 0.0
    e = d / dist
    if dist >= m1 + m2 - 1e-4:
        # out of reach: a straight finger to the target, and the last segment points to the tip
        b1 = b0 + e * m1
        b2 = b1 + e * m2
        v = a3 - b2
        if v.length < 1e-6:
            v = u3
        b3 = b2 + v.normalized() * m3
        return b1, b2, b3, (b3 - a3).length
    lo = abs(m1 - m2) + 1e-4
    dd = max(dist, lo)
    along = (m1 * m1 - m2 * m2 + dd * dd) / (2 * dd)
    h = math.sqrt(max(0.0, m1 * m1 - along * along))
    bend = (a1 - b0) - e * (a1 - b0).dot(e)
    if bend.length < 1e-5:
        bend = (a2 - b0) - e * (a2 - b0).dot(e)
    if bend.length < 1e-5:
        bend = e.orthogonal()
    bend.normalize()
    b1 = b0 + e * along + bend * h
    b2 = b1 + (t2 - b1).normalized() * m2
    b3 = b2 + (a3 - b2).normalized() * m3 if (a3 - b2).length > 1e-6 else b2 + u3 * m3
    return b1, b2, b3, (b3 - a3).length


def _march(points, start_seg, start_point, length):
    """The first point on the polyline, at or after `start_point` on the segment `start_seg`,
    that is `length` away from `start_point` (straight distance). The last segment goes on as
    a ray. Returns (point, segment index)."""
    n = len(points) - 1
    for i in range(start_seg, n):
        p, q = points[i], points[i + 1]
        d = q - p
        seg_len = d.length
        if seg_len < 1e-8:
            continue
        u = d / seg_len
        last = i == n - 1
        # |p + u t - c| = length
        c = start_point
        w = p - c
        b = w.dot(u)
        cc = w.dot(w) - length * length
        disc = b * b - cc
        if disc < 0:
            continue
        t = -b + math.sqrt(disc)
        t0 = (start_point - p).dot(u) if i == start_seg else 0.0
        if t < t0 - 1e-6:
            continue
        if t <= seg_len or last:
            return p + u * t, i
    # no intersection: straight on along the last segment
    u = (points[-1] - points[-2]).normalized()
    return start_point + u * length, n - 1


def solve_finger_path(b0, m1, m2, m3, a0, a1, a2, a3, lift=0.0):
    """Joint positions of a FO4 finger whose joints are on the centerline of the source finger.

    The centerline is the line through the source joints a0, a1, a2 and the fingertip a3.
    The FO4 knuckle b0 is not on it (the hands have other proportions), so the first bone
    goes from b0 to the point of the centerline at its length, and the next joints are on the
    centerline too. The finger then lies where the source finger lies on the gun. A shorter
    finger ends before the source fingertip.

    A FO4 bone is shorter than the source bone, so it is a chord that cuts the corner at a
    source joint, and its middle is nearer to the gun than the source finger. `lift` moves the
    two ends of such a bone toward the corner, by that part of the distance between the bone
    and the corner (0: no change; 1: the bone goes through the corner).
    Returns (b1, b2, b3, distance of the tip to a3)."""
    pts = [a0, a1, a2, a3]
    b1, i1 = _march(pts, 0, b0, m1)
    b2, i2 = _march(pts, i1, b1, m2)
    b3, i3 = _march(pts, i2, b2, m3)
    if lift > 0.0:
        joints = [b0, b1, b2, b3]
        seg = [0, i1, i2, i3]
        move = [Vector((0, 0, 0)) for _ in range(4)]
        for j in (1, 2):
            p, q = joints[j], joints[j + 1]
            d = q - p
            l2 = d.dot(d)
            if l2 < 1e-10:
                continue
            for i in range(seg[j] + 1, seg[j + 1] + 1):
                t = max(0.0, min(1.0, (pts[i] - p).dot(d) / l2))
                h = (pts[i] - (p + d * t)) * lift
                move[j] += h
                move[j + 1] += h
        lengths = (m1, m2, m3)
        out = [b0]
        for j in range(1, 4):
            v = joints[j] + move[j] - out[j - 1]
            out.append(out[j - 1] + v.normalized() * lengths[j - 1] if v.length > 1e-8 else joints[j])
        b1, b2, b3 = out[1:]
    return b1, b2, b3, (b3 - a3).length


_DIRS = (Vector((0.577, 0.577, 0.577)), Vector((-0.8, 0.27, 0.53)), Vector((0.2, -0.9, 0.38)))


def _inside(tree, p):
    votes = 0
    for d in _DIRS:
        n = 0
        o = p.copy()
        for _ in range(48):
            loc, nrm, idx, dist = tree.ray_cast(o, d)
            if loc is None:
                break
            n += 1
            o = loc + d * 1e-4
        votes += n & 1
    return votes >= 2


def hinge_axes(rotations, points, local_axes):
    """The hinge of the two joints of a finger in world space: the hinge of the reference pose
    (`local_axes`, in the frame of the bone before the joint) in the frame that the bone has
    when it points along the finger line. The direction of an axis bends the finger to the palm."""
    return [None if local_axes[k] is None else aim_x(rotations[k], points[k + 1] - points[k]) @ local_axes[k]
            for k in range(2)]


def flexion(d0, d1, axis):
    """The bend of a joint about its hinge (radians): the turn from the bone before the joint
    (direction d0) to the bone after it (d1). Positive to the palm, negative to the back of the
    finger. A bend to the side is not in the value."""
    a = axis - d0 * axis.dot(d0)                       # a hinge is at a right angle to the bone
    if a.length < 1e-6:
        return None, None
    a.normalize()
    side = d1 - a * d1.dot(a)
    return math.atan2(d0.cross(side).dot(a), d0.dot(side)), a


def bend_least(points, rotations, local_axes, least):
    """Give each joint of a finger at least the flexion `least[k]` (radians), with the fingertip on its line.

    The Fallout 4 hand mesh is modelled with bent fingers (about 45 and 30 degrees at the two
    joints), and the vanilla clips keep each joint in a small range: no finger joint bends to
    the back of the finger, and only the last thumb joint does (17 degrees). A joint outside
    that range has lumps, and a thumb that bends back at its first joint is not at its place on
    the gun. A New Vegas clip can have such joints: its hand mesh is flat in the rest pose.

    The flexion is the bend about the hinge of the bone (see hinge_axes and flexion), so a
    source joint that bends back does not count as a bent joint. `least[k]` can be negative
    (the joint can bend back that far) or None (no rule).

    A joint with less flexion turns the part of the finger after it to the palm. The complete
    finger then turns about the knuckle until the fingertip is again on the line from the
    knuckle to the old fingertip. The finger is an arch over that line, so the fingertip does
    not go into the part that it touches. A joint with sufficient flexion does not change.
    Returns the new points."""
    pts = [p.copy() for p in points]
    changed = False
    for k in range(2):
        if local_axes[k] is None or least[k] is None:
            continue
        d0 = (pts[k + 1] - pts[k]).normalized()
        d1 = (pts[k + 2] - pts[k + 1]).normalized()
        bend, a = flexion(d0, d1, hinge_axes(rotations, pts, local_axes)[k])
        if a is None:
            continue
        if bend < least[k] - 1e-6:
            q = Quaternion(a, least[k] - bend)
            for j in range(k + 2, 4):
                pts[j] = pts[k + 1] + q @ (pts[j] - pts[k + 1])
            changed = True
    if not changed:
        return points
    old_line, new_line = points[3] - points[0], pts[3] - pts[0]
    if old_line.length > 1e-6 and new_line.length > 1e-6:
        q = new_line.rotation_difference(old_line)
        for j in range(1, 4):
            pts[j] = pts[0] + q @ (pts[j] - pts[0])
    return pts


def relax_out(points, radii, collider, floor=0.3, max_push=0.6, iterations=8, source_points=None, guard_axes=None, guard_back=None):
    """Move a finger that is deep in a gun part out, until its skin is on the surface.

    The source hands are partly inside the gun: at some poses the centerline of a source
    finger is 0.5 units below the surface. The centerline of each FO4 finger bone must be
    `floor * radius` away from a surface. A joint that is nearer (or inside) moves along the
    direction that leads out of the part, `max_push` at most in total, and each bone keeps its
    length. A point that is more than 1.2 units inside is not a grip (the hand goes through a
    part on its way), and it does not move.

    With `source_points` (the four points of the source finger line) a joint does not bend
    against the bend of the source finger: a bone that would point to the back of the finger
    is put in line with the bone before it. `guard_axes` gives the two hinges for this rule
    in place of the hinges of the source line (see bend_least), and `guard_back` the bend to
    the back that each joint can have (radians; the last thumb joint has one).
    Returns (points, largest joint move)."""
    orig = [p.copy() for p in points]
    pts = [p.copy() for p in points]
    lengths = [(points[k + 1] - points[k]).length for k in range(3)]
    axes = None
    if source_points is not None:
        sd_ = [(source_points[k + 1] - source_points[k]) for k in range(3)]
        axes = []
        for k in range(2):
            n = sd_[k].cross(sd_[k + 1])
            axes.append(n.normalized() if n.length > 1e-4 else None)
        # a finger that is straight in the source: one bend axis for the two joints
        if axes[0] is None:
            axes[0] = axes[1]
        if axes[1] is None:
            axes[1] = axes[0]
    if guard_axes is not None:
        axes = list(guard_axes)
    for _ in range(iterations):
        want = [Vector((0, 0, 0)) for _ in range(4)]
        count = [0, 0, 0, 0]
        for k in range(3):
            wanted = floor * radii[k]
            for t in (0.25, 0.5, 0.75, 1.0):
                p = pts[k].lerp(pts[k + 1], t)
                sd, n = collider.sdist(p)
                if sd is None or sd >= wanted - 0.02:
                    continue
                d = n * ((wanted - sd) * max(0.0, min(1.0, (sd + 1.2) / 0.6)))
                # the least move of the two joints that moves the sample by d; the knuckle does not move
                if k == 0:
                    want[1] += d * min(1.0 / t, 2.0)
                    count[1] += 1
                else:
                    w = (1.0 - t) ** 2 + t ** 2
                    if t < 1.0:
                        want[k] += d * ((1.0 - t) / w)
                        count[k] += 1
                    want[k + 1] += d * (t / w)
                    count[k + 1] += 1
        if not any(count):
            break
        for j in range(1, 4):
            if not count[j]:
                continue
            np_ = pts[j] + want[j] * (0.8 / count[j])
            off = np_ - orig[j]
            if off.length > max_push:
                np_ = orig[j] + off.normalized() * max_push
            pts[j] = np_
        # keep the bone lengths, from the knuckle to the tip
        for k in range(3):
            v = pts[k + 1] - pts[k]
            if v.length > 1e-6:
                pts[k + 1] = pts[k] + v.normalized() * lengths[k]
        # no bend against the bend of the source finger
        if axes is not None:
            for k in range(2):
                if axes[k] is None:
                    continue
                d0 = (pts[k + 1] - pts[k]).normalized()
                d1 = (pts[k + 2] - pts[k + 1]).normalized()
                if guard_back is not None and guard_back[k] > 0.0:
                    # this joint can bend back: only a larger bend goes to the limit
                    bend, a = flexion(d0, d1, axes[k])
                    if a is not None and bend < -guard_back[k]:
                        pts[k + 2] = pts[k + 1] + (Quaternion(a, -guard_back[k] - bend) @ d1) * lengths[k + 1]
                        if k == 0:
                            pts[3] = pts[2] + (pts[3] - (pts[1] + d1 * lengths[1])).normalized() * lengths[2]
                    continue
                if d0.cross(d1).dot(axes[k]) < 0.0:
                    # the part of d1 in the bend plane goes back in line with d0
                    side = d1 - axes[k] * d1.dot(axes[k])
                    out_of_plane = axes[k] * d1.dot(axes[k])
                    fixed = d0 * side.length + out_of_plane
                    if fixed.length > 1e-6:
                        pts[k + 2] = pts[k + 1] + fixed.normalized() * lengths[k + 1]
                        if k == 0:
                            pts[3] = pts[2] + d1 * lengths[2] if False else pts[2] + (pts[3] - (pts[1] + d1 * lengths[1])).normalized() * lengths[2] if (pts[3] - (pts[1] + d1 * lengths[1])).length > 1e-6 else pts[3]
    worst = max((pts[j] - orig[j]).length for j in range(1, 4))
    return pts, worst


class Collider:
    """The gun parts as BVH trees, each in the local space of its FO4 weapon bone."""

    def __init__(self, parts, skip=()):
        from mathutils.bvhtree import BVHTree
        self.items = []
        for s in parts['shapes']:
            if s['name'] in skip:
                continue                            # for example a cartridge inside the magazine, or an open plane
            tree = BVHTree.FromPolygons([tuple(v) for v in s['positions']], [tuple(t) for t in s['triangles']], epsilon=0.0)
            self.items.append((s['name'], s['bone'], tree))
        self.frames = []

    def set_pose(self, pose):
        """Give the world matrix of each weapon bone for the current frame."""
        self.frames = []
        for name, bone, tree in self.items:
            m = pose[bone]
            # a part with a scale near 0 is a hidden part
            if m.to_scale().x < 0.5:
                continue
            self.frames.append((name, tree, m, m.inverted(), m.to_3x3()))

    def sdist(self, p):
        """Signed distance of a world point to the nearest part (negative inside) and the unit
        direction that leads out of (or away from) that part. (None, None) with no part near."""
        best = None
        for name, tree, m, mi, m3 in self.frames:
            q = mi @ p
            near = tree.find_nearest(q, 3.0)
            if near[0] is None:
                continue
            loc, nrm, idx, dist = near
            ins = _inside(tree, q)
            sd = -dist if ins else dist
            if best is None or sd < best[0]:
                v = (loc - q) if ins else (q - loc)
                if v.length < 1e-5:
                    v = nrm
                best = (sd, (m3 @ v).normalized())
        return best if best is not None else (None, None)

    def ray(self, origin, direction, distance):
        """First hit of a ray in world space: (distance, hit point, normal, part name) or None."""
        best = None
        for name, tree, m, mi, m3 in self.frames:
            o = mi @ origin
            d = (mi.to_3x3() @ direction).normalized()
            loc, nrm, idx, dist = tree.ray_cast(o, d, distance)
            if loc is None:
                continue
            if best is None or dist < best[0]:
                best = (dist, m @ loc, (m3 @ nrm).normalized(), name)
        return best


class Retargeter:
    """parts: FO4 weapon bone -> (FNV node, constant matrix C). The FO4 bone world matrix is
    the FNV node world matrix @ C."""

    def __init__(self, source_rest, target, parts, camera_source='Camera1st'):
        self.source_rest, self.target = source_rest, target
        self.parts = parts
        self.mapping = bone_map()
        self.camera_source = camera_source
        self.offset = target.rest['Camera'].translation - source_rest[camera_source].translation
        self.max_wrist_error = 0.0
        self.max_shoulder_adjustment = 0.0
        self.max_length_error = 0.0
        # Finger tips: `tips` has the tip length of each last finger bone of the two hand
        # meshes ({'fnv': {bone: {'x_max': ..}}, 'fo4': {...}}). With no data the fingers
        # copy the source rotations.
        self.tips = None
        self.finger_mode = 'tip'
        self.finger_solver = 'path'
        self.collider = None
        self.max_push_turn = 0.0        # the largest joint move of the collision step
        self.push_count = 0
        self.finger_depth = 0.65         # the least distance of a finger centerline to the gun, in finger radii
        self.finger_max_push = 1.15
        self.corner_lift = 0.5
        # The least flexion of each finger joint, as a part of the bend of that joint in the FO4
        # reference pose (0: no rule, a joint can be straight or bend back; see bend_least).
        self.finger_min_bend = 0.0
        self.rest_flex_cache = {}
        # True: the center of the skin of each Fallout 4 finger goes to the center of the skin
        # of the source finger. False: the bones go to the bones (see skin_shift).
        self.skin_center = False
        self.skin_shift_cache = {}
        self.thumb_mode = 'path'        # 'rotation': the thumb copies the source rotations
        self.finger_log = []            # for each frame: finger -> (bones, rotations, joints before and after the collision step)
        self.max_tip_error = 0.0
        self.tip_error_sum = 0.0
        self.tip_count = 0
        # The FO4 hand has a longer palm and shorter fingers than the FNV hand. With the two
        # wrists at one place, the FO4 knuckles are about 0.7 units away from the source
        # knuckles, and each finger is then at a wrong place on the gun. `hand_shift` moves
        # the FO4 wrist (a constant vector in the space of the hand bone) so that the mean of
        # the four knuckles is at the mean of the source knuckles.
        self.hand_shift = {'L': Vector((0, 0, 0)), 'R': Vector((0, 0, 0))}

    def rest_world(self, name):
        m = Matrix.Identity(4)
        chain = []
        while name:
            chain.append(name)
            name = self.target.parents[name]
        for n in reversed(chain):
            m = m @ self.target.local[n]
        return m

    def align_knuckles(self, weight=1.0):
        """Set `hand_shift` from the rest poses of the two rigs. Returns the two vectors."""
        roll = ARM_ROLL.to_matrix().to_4x4()
        for side in ('L', 'R'):
            hs = (self.source_rest[f'Bip01 {side} Hand'] @ roll).inverted()
            ht = self.rest_world(f'{side}Arm_Hand').inverted()
            total = Vector((0, 0, 0))
            for finger in range(2, 6):
                a = (hs @ self.source_rest[f'Bip01 {side} Finger{finger - 1}']).translation
                b = (ht @ self.rest_world(f'{side}Arm_Finger{finger}1')).translation
                total += a - b
            self.hand_shift[side] = total * (weight / 4.0)
        return self.hand_shift

    @property
    def arm_bones(self):
        return {f'{s}Arm_{p}' for s in ('L', 'R') for p in ('UpperArm', 'ForeArm1', 'ForeArm2', 'ForeArm3', 'Hand')}

    def shifted(self, m):
        r = m.copy()
        r.translation = m.translation + self.offset
        return r

    def convert(self, world):
        target = self.target
        pose = {}

        def position(name):
            return world[name].translation + self.offset
        for name in target.names:
            parent = target.parents[name]
            base = (pose[parent] if parent else Matrix.Identity(4)) @ target.local[name]
            source = self.mapping.get(name)
            if source and source in world:
                rotation = world[source].to_quaternion()
                if name.startswith(('LArm_', 'RArm_')):
                    rotation = rotation @ ARM_ROLL
                p = base.translation
                if name == 'COM' or name.endswith('Collarbone'):
                    p = position(source)
                pose[name] = trs(p, rotation)
            else:
                pose[name] = base
        for side in ('L', 'R'):
            self.solve_arm(side, world, pose)
        self.place_weapon(world, pose)
        if self.collider is not None:
            self.collider.set_pose(pose)
        solved = set()
        log = {}
        self.finger_log.append(log)
        if self.tips is not None and self.finger_mode == 'tip':
            for (side, finger), (fo4, fnv) in finger_chains().items():
                if any(n not in world for n in fnv) or fo4[2] not in self.tips['fo4'] or fnv[2] not in self.tips['fnv']:
                    continue
                if finger == 1 and self.thumb_mode == 'rotation':
                    continue
                hand = pose[f'{side}Arm_Hand']
                b0 = (hand @ target.local[fo4[0]]).translation
                m1 = target.local[fo4[1]].translation.length
                m2 = target.local[fo4[2]].translation.length
                m3 = self.tips['fo4'][fo4[2]]['x_max']
                a1 = world[fnv[1]].translation + self.offset
                a2 = world[fnv[2]].translation + self.offset
                a3 = (world[fnv[2]] @ Vector((self.tips['fnv'][fnv[2]]['x_max'], 0.0, 0.0))) + self.offset
                a0 = world[fnv[0]].translation + self.offset
                rotations = [world[n].to_quaternion() @ ARM_ROLL for n in fnv]
                if self.skin_center:
                    # the source line becomes the line of the skin centers; its first point
                    # moves with the second one
                    shift = self.skin_shift(fo4, fnv)
                    a1, a2, a3 = a1 + rotations[1] @ shift[0], a2 + rotations[2] @ shift[1], a3 + rotations[2] @ shift[2]
                    a0 = a0 + rotations[1] @ shift[0]
                if self.finger_solver == 'path':
                    b1, b2, b3, err = solve_finger_path(b0, m1, m2, m3, a0, a1, a2, a3, self.corner_lift)
                else:
                    b1, b2, b3, err = solve_finger(b0, m1, m2, m3, a1, a2, a3)
                self.max_tip_error = max(self.max_tip_error, err)
                self.tip_error_sum += err
                self.tip_count += 1
                pts = [b0, b1, b2, b3]
                flex = back = None
                if self.finger_min_bend > 0.0:
                    axes_local, rest_bend = self.rest_flex(fo4)
                    least = [rest_bend[k] * self.finger_min_bend for k in range(2)]
                    if finger == 1:
                        least[1] = -THUMB_BACK
                    pts = bend_least(pts, rotations, axes_local, least)
                    flex = hinge_axes(rotations, pts, axes_local)
                    back = [max(0.0, -v) for v in least]
                if self.collider is not None:
                    radii = [self.tips['fo4'][n]['radius'] for n in fo4]
                    clear = pts
                    pts, moved = relax_out(pts, radii, self.collider, self.finger_depth, self.finger_max_push, source_points=(a0, a1, a2, a3),
                                           guard_axes=flex, guard_back=back)
                    self.max_push_turn = max(self.max_push_turn, moved)
                    if moved > 1e-4:
                        self.push_count += 1
                    log[(side, finger)] = (fo4, rotations, clear, pts)
                for k in range(3):
                    pose[fo4[k]] = trs(pts[k], aim_x(rotations[k], pts[k + 1] - pts[k]))
                    solved.add(fo4[k])
        for name in target.names:
            parent = target.parents[name]
            if name in solved:
                continue
            if 'Finger' in name:
                source = self.mapping[name]
                p = (pose[parent] @ target.local[name]).translation
                pose[name] = trs(p, world[source].to_quaternion() @ ARM_ROLL)
            elif 'UpperTwist' in name:
                side = name[0]
                upper = pose[f'{side}Arm_UpperArm']
                twist = world[f'Bip01 {side}UpArmTwistBone'].to_quaternion() @ ARM_ROLL
                twist = aim_x(twist, upper.to_3x3().col[0])
                weight = 0.5 if name.endswith('1') else 1.0
                pose[name] = trs((pose[parent] @ target.local[name]).translation,
                                 upper.to_quaternion().slerp(twist, weight))
            elif name not in self.mapping and name not in ('Root', 'Pelvis') and name not in self.arm_bones:
                pose[name] = (pose[parent] if parent else Matrix.Identity(4)) @ target.local[name]
        self.place_weapon(world, pose)
        # The four WeaponIKTarget bones keep the local transform of the reference pose (zero
        # under the Weapon bone), as in each vanilla first-person clip. place_weapon does that.
        camera = world[self.camera_source]
        pose['Camera'] = trs(camera.translation + self.offset,
                             camera.to_quaternion() @ Quaternion((1, 0, 0), math.pi / 2))
        return pose

    def rest_flex(self, fo4):
        """For the two joints of a FO4 finger: the hinge axis in the frame of the bone before the
        joint, and the bend, in the reference pose."""
        key = fo4[0]
        if key not in self.rest_flex_cache:
            rest = self.target.rest
            p = [rest[n].translation for n in fo4]
            p.append(rest[fo4[2]] @ Vector((self.tips['fo4'][fo4[2]]['x_max'], 0.0, 0.0)))
            axes, bends = [], []
            for k in range(2):
                d0, d1 = (p[k + 1] - p[k]).normalized(), (p[k + 2] - p[k + 1]).normalized()
                n = d0.cross(d1)
                axes.append(rest[fo4[k]].to_3x3().inverted() @ n.normalized() if n.length > 1e-5 else None)
                bends.append(d0.angle(d1))
            self.rest_flex_cache[key] = (axes, bends)
        return self.rest_flex_cache[key]

    def skin_shift(self, fo4, fnv):
        """The move of the source finger line that puts the skin of the Fallout 4 finger on the
        skin of the source finger: for the second joint, the third joint and the fingertip, a
        vector in the frame of the bone (the second bone, the third bone and the third bone).

        The skin of a finger is not a tube about its bone. The thumb of the Fallout 4 hand has
        the center of its skin 0.4 units to the pad side of the bone, and the New Vegas thumb
        has it 0.13 units to the nail side. With the bones at one place the Fallout 4 thumb is
        0.5 units to the pad side of the source thumb (the difference of the other fingers is
        0.1 units). The values are in rig/finger_tips.json (tools/blender/finger_tips.py).
        The first joint is the knuckle: the hand bone gives its place."""
        key = fo4[0]
        if key not in self.skin_shift_cache:
            s, t = self.tips['fnv'], self.tips['fo4']
            out = []
            for a, b, field in ((fnv[1], fo4[1], 'center'), (fnv[2], fo4[2], 'center'), (fnv[2], fo4[2], 'tip_center')):
                if field not in s.get(a, {}) or field not in t.get(b, {}):
                    out.append(Vector((0.0, 0.0, 0.0)))
                    continue
                out.append(Vector((0.0, s[a][field][0] - t[b][field][0], s[a][field][1] - t[b][field][1])))
            self.skin_shift_cache[key] = out
        return self.skin_shift_cache[key]

    def smooth_fingers(self, poses, sigma=1.5):
        """Filter the moves of the collision step over time (a Gaussian window, `sigma` frames).

        The collision step works on one frame, so its result can change fast from one frame to
        the next. The move of each joint, in the space of the hand bone, is filtered, and the
        finger bones of `poses` (the list of the poses of convert, in frame order) are written
        again. Returns the largest joint move after the filter."""
        count = len(poses)
        if self.collider is None or len(self.finger_log) != count or count < 2:
            return 0.0
        radius = max(1, int(round(3 * sigma)))
        kernel = [math.exp(-0.5 * (i / sigma) ** 2) for i in range(-radius, radius + 1)]
        worst = 0.0
        for key in self.finger_log[0]:
            if any(key not in log for log in self.finger_log):
                continue
            side = key[0]
            hands = [pose[f'{side}Arm_Hand'].to_quaternion() for pose in poses]
            local = []
            for f in range(count):
                fo4, rotations, clear, pts = self.finger_log[f][key]
                inverse = hands[f].inverted()
                local.append([inverse @ (pts[j] - clear[j]) for j in range(4)])
            if max(v.length for row in local for v in row) < 1e-5:
                continue
            for f in range(count):
                fo4, rotations, clear, pts = self.finger_log[f][key]
                out = [clear[0]]
                for j in range(1, 4):
                    total = Vector((0, 0, 0))
                    weight = 0.0
                    for i, k in enumerate(kernel):
                        g = f + i - radius
                        if 0 <= g < count:
                            total += local[g][j] * k
                            weight += k
                    move = hands[f] @ (total / weight)
                    worst = max(worst, move.length)
                    v = clear[j] + move - out[j - 1]
                    length = (clear[j] - clear[j - 1]).length
                    out.append(out[j - 1] + v.normalized() * length)
                for k in range(3):
                    poses[f][fo4[k]] = trs(out[k], aim_x(rotations[k], out[k + 1] - out[k]))
        return worst

    def place_weapon(self, world, pose):
        target = self.target
        # Weapon bones in hierarchy order: a part with no source keeps its local rest
        # transform under its animated parent.
        for name in target.names:
            if not name.startswith('Weapon') or name.startswith('WeaponIK') or name == 'WeaponLeft':
                continue
            if name in self.parts and self.parts[name][0] in world:
                node, c = self.parts[name]
                pose[name] = self.shifted(world[node]) @ c
            else:
                parent = target.parents[name]
                local = self.part_local.get(name, target.local[name]) if hasattr(self, 'part_local') else target.local[name]
                pose[name] = pose[parent] @ local

    def solve_arm(self, side, source, pose):
        target = self.target
        names = [f'{side}Arm_{n}' for n in ('Collarbone', 'UpperArm', 'ForeArm1', 'ForeArm2', 'ForeArm3', 'Hand')]
        collar, upper, fore1, fore2, fore3, hand = names
        shoulder = (pose[collar] @ target.local[upper]).translation
        hand_rotation = source[f'Bip01 {side} Hand'].to_quaternion() @ ARM_ROLL
        wrist = source[f'Bip01 {side} Hand'].translation + self.offset + hand_rotation @ self.hand_shift[side]
        pole = source[f'Bip01 {side} Forearm'].translation + self.offset
        lengths = [target.local[n].translation.length for n in (fore1, fore2, fore3, hand)]
        a, b = lengths[0], sum(lengths[1:])
        direction = wrist - shoulder
        distance = max(direction.length, 1e-8)
        direction /= distance
        maximum = a + b - 1e-4
        minimum = abs(a - b) + 1e-4
        corrected = min(max(distance, minimum), maximum)
        adjustment = (distance - corrected) * direction
        if abs(distance - corrected) > 1e-6:
            shoulder += adjustment
            pose[collar].translation += adjustment
            self.max_shoulder_adjustment = max(self.max_shoulder_adjustment, adjustment.length)
        distance = corrected
        bend = pole - shoulder
        bend -= direction * bend.dot(direction)
        if bend.length < 1e-6:
            bend = source[f'Bip01 {side} UpperArm'].to_3x3().col[1]
            bend -= direction * bend.dot(direction)
        bend.normalize()
        along = (a * a - b * b + distance * distance) / (2 * distance)
        elbow = shoulder + direction * along + bend * math.sqrt(max(0, a * a - along * along))
        qu = aim_x(source[f'Bip01 {side} UpperArm'].to_quaternion() @ ARM_ROLL, elbow - shoulder)
        qf = aim_x(source[f'Bip01 {side} Forearm'].to_quaternion() @ ARM_ROLL, wrist - elbow)
        qt = aim_x(source[f'Bip01 {side} ForeTwist'].to_quaternion() @ ARM_ROLL, wrist - elbow)
        pose[upper] = trs(shoulder, qu)
        pose[fore1] = trs(elbow, qf)
        line = (wrist - elbow).normalized()
        pose[fore2] = trs(elbow + line * lengths[1], qf.slerp(qt, 0.5))
        pose[fore3] = trs(elbow + line * (lengths[1] + lengths[2]), qt)
        pose[hand] = trs(wrist, hand_rotation)
        self.max_wrist_error = max(self.max_wrist_error, (pose[hand].translation - wrist).length)
        for parent, child, length in zip((upper, fore1, fore2, fore3), (fore1, fore2, fore3, hand), lengths):
            error = abs((pose[child].translation - pose[parent].translation).length - length)
            self.max_length_error = max(self.max_length_error, error)
