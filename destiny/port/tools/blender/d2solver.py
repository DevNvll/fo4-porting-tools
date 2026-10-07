"""Move a Destiny first-person pose to the Fallout 4 first-person skeleton.

This is the Retargeter of fnv/tools/blender/solver.py for the Destiny rig. The
finger rules are the functions of that file, with no change: each finger joint on the line of
the source finger (solve_finger_path), the center of the skin of each finger on the center of
the skin of the source finger (skin_shift), the least bend of each joint (bend_least), the
collision with the gun parts (relax_out) and the time filter (smooth_fingers).

What is different for the Destiny rig:

* A source pose is in Fallout 4 world space before it comes here (tools/d2rig.py), and each
  source bone has a constant matrix K that gives the axes of the Fallout 4 bone. The hand has
  the palm fit of rig/d2_hands.json in its K.
* The arms need no solve. The two rigs have the same arm lengths to 6 percent, and a
  first-person view shows the forearm and the hand, not the shoulder. So the wrist is at the
  source wrist, the forearm lies on the source forearm, and the upper arm is parallel to the
  source upper arm. The shoulder is then at most 1.8 units away from the source shoulder.
* The source has no twist bones with data (the game moves them at run time). The twist bones
  of the forearm and of the upper arm follow the rule of the vanilla clips: ForeArm2 and
  ForeArm3 have 1/3 and 2/3 of the twist of the hand against the forearm; UpperTwist1 and
  UpperTwist2 have -2/3 and -1/3 of the twist of the upper arm against the collarbone.
* A Destiny first-person clip has useful poses of the arms and the weapon only. Each other
  bone has its pose of the first frame of the ready clip of the template weapon.
* The camera bone follows the source camera bone (b_utility).
* Each finger stays in one plane (`planar`). The two hands have their knuckles at different
  places (the Fallout 4 palm is 0.8 units wider), and the collision step moves a joint in any
  direction. With the joints on the source line, the joint after the knuckle then turns to
  the side by 20 to 38 degrees, which a finger cannot do, and no vanilla clip has. So the
  finger lies in the plane through its knuckle and the source fingertip that is nearest to
  the plane of the source finger: the knuckle takes the turn to the side, the two other
  joints are hinges about the axis of the plane, and the fingertip is at its place.
  After the collision step the plane is fitted to the joints that the step moved
  (`fitted_normal`), so a move of the complete finger to the side stays: with the plane
  through the knuckle and the fingertip only, the middle finger of the right hand went back
  into the grip below the trigger guard (0.93 units deep in the hold pose; 0.66 with the fit,
  and the source finger is 0.69 deep there).
"""
import math
from mathutils import Matrix, Quaternion, Vector
from common import trs
from solver import Retargeter, aim_x, solve_finger_path, bend_least, hinge_axes, relax_out, THUMB_BACK

import d2rig

X_AXIS = Vector((1.0, 0.0, 0.0))


def to_matrix(m):
    return Matrix([list(r) for r in m])


def twist_x(q):
    """The turn of a rotation about its own X axis (radians, -pi to pi): the twist part of the
    rotation as a swing and a twist."""
    angle = 2.0 * math.atan2(q.x, q.w)
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def near(angle, last):
    """The same angle, a full turn more or less, that is nearest to the angle of the frame before."""
    if last is None:
        return angle
    return angle + 2.0 * math.pi * round((last - angle) / (2.0 * math.pi))


def plane_normal(knuckle, tip, hinge):
    """The normal of the plane through the knuckle and the fingertip that is nearest to `hinge`
    (the hinge of the source finger, or the normal of the frame before)."""
    e = tip - knuckle
    if e.length > 1e-6:
        e.normalize()
        n = hinge - e * hinge.dot(e)
        if n.length > 1e-4:
            return n.normalized()
    return hinge.normalized()


def fitted_normal(points, normal, weight=0.05):
    """The normal of the plane through the knuckle that is nearest to the joints after it, and,
    where the joints do not say (a straight finger is a line), nearest to `normal`. It is the
    least squares answer for sum(((p - knuckle) . n) ** 2) + weight * |n - normal| ** 2. A move
    of the complete finger to the side (a turn about the knuckle) stays in the result."""
    m = Matrix(((weight, 0.0, 0.0), (0.0, weight, 0.0), (0.0, 0.0, weight)))
    for p in points[1:]:
        v = p - points[0]
        for i in range(3):
            for j in range(3):
                m[i][j] += v[i] * v[j]
    n = m.inverted() @ normal
    return n.normalized() if n.length > 1e-12 else normal.normalized()


def into_plane(points, normal, lengths=None):
    """The joints after the knuckle, moved into the plane through the knuckle. With `lengths`
    each bone keeps its length, from the knuckle to the tip."""
    out = [points[0].copy()]
    for j in range(1, len(points)):
        p = points[j] - normal * (points[j] - points[0]).dot(normal)
        if lengths is not None:
            v = p - out[j - 1]
            v -= normal * v.dot(normal)
            if v.length > 1e-8:
                p = out[j - 1] + v.normalized() * lengths[j - 1]
        out.append(p)
    return out


def hinge_rotation(direction, normal):
    """The rotation of a finger bone that points along `direction` with its hinge (local Z) along `normal`."""
    x = direction.normalized()
    z = normal - x * normal.dot(x)
    z.normalize()
    y = z.cross(x)
    return Matrix(((x[0], y[0], z[0]), (x[1], y[1], z[1]), (x[2], y[2], z[2]))).to_quaternion()


FINGER_HINGE = Vector((0.0, 0.0, -1.0))      # a Fallout 4 finger joint bends to the palm about -Z


HOOK_MARGIN = 0.6                            # game units: see finger_path


def finger_path(b0, m1, m2, m3, a0, a1, a2, a3, lift=0.0):
    """The joints of a Fallout 4 finger on the line of the source finger: solve_finger_path of
    fnv/tools/blender/solver.py, with one more rule for a finger that is closed.

    That function puts the end of each bone at the first point of the source line (the joints
    a0, a1, a2 and the fingertip a3) that is the length of the bone away from the start of the
    bone, and the line goes on behind the fingertip as a straight line. The first bone starts at
    the Fallout 4 knuckle b0, which is not on the line (the two hands have other proportions).
    When the finger is closed (a hook on a small handle, or a fist), each point of the line
    can be nearer to that knuckle than the length of the first bone. The only point at that
    distance is then behind the fingertip. The first bone points there: to the wrist when the
    fingertip points to the palm (the finger turns 170 degrees in one frame), or along the last
    bone, with the two other bones in line behind it (the fingertip is 4 units from its place).
    The reload of the M77 of Marathon showed the two cases (the left index finger on the bolt
    handle, frames 74 to 83, and on the magazine, frames 28 to 46).

    The rule for a closed finger keeps the part of the finger that holds the gun: the last bone
    and the bone before it are parallel to those of the source, with the fingertip at the
    source fingertip. The first bone points from the knuckle to the start of that part, and the
    part moves along that bone by the difference of the lengths (the knuckle is the joint that
    can turn to each side). The two rules mix with a weight: 0 when the farthest joint of the
    line is more than the length of the first bone and HOOK_MARGIN away from the knuckle, 1
    when it is nearer than that length (the rule of the line has no good result there).
    `closed_fingers = true` of a set file gives this rule. The ports of Destiny do not have it:
    it changes 4 of their 5 clip sets (1.4 units at most), and those are tested in the game.
    Returns (b1, b2, b3, distance of the tip to a3, the weight of the rule for a closed finger)."""
    reach = max((p - b0).length for p in (a1, a2, a3))
    x = min(1.0, max(0.0, (m1 + HOOK_MARGIN - reach) / HOOK_MARGIN))
    weight = x * x * (3.0 - 2.0 * x)
    if weight < 1.0:
        b1, b2, b3, _ = solve_finger_path(b0, m1, m2, m3, a0, a1, a2, a3, lift)
        if weight <= 0.0:
            return b1, b2, b3, (b3 - a3).length, 0.0
    u = [(q - p).normalized() if (q - p).length > 1e-8 else None for p, q in ((a0, a1), (a1, a2), (a2, a3))]
    if u[0] is None or u[1] is None or u[2] is None:
        # a source bone with no length: the rule of the line
        b1, b2, b3, error = solve_finger_path(b0, m1, m2, m3, a0, a1, a2, a3, lift)
        return b1, b2, b3, error, 0.0
    start = a3 - u[2] * m3 - u[1] * m2 - b0                # from the knuckle to the start of the part that holds
    first = start.normalized() if start.length > 1e-6 else u[0]
    closed = [first, u[1], u[2]]
    if weight < 1.0:
        line = [(b1 - b0).normalized(), (b2 - b1).normalized(), (b3 - b2).normalized()]
        closed = [(line[k] * (1.0 - weight) + closed[k] * weight) for k in range(3)]
        closed = [closed[k].normalized() if closed[k].length > 1e-6 else line[k] for k in range(3)]
    b1 = b0 + closed[0] * m1
    b2 = b1 + closed[1] * m2
    b3 = b2 + closed[2] * m3
    return b1, b2, b3, (b3 - a3).length, weight


class D2Retargeter(Retargeter):
    """parts: Fallout 4 weapon bone -> (Destiny bone, constant matrix C). The Fallout 4 bone
    world matrix is the Destiny bone world matrix @ C.
    base: Fallout 4 bone -> world matrix of the ready pose of the template.
    hands: the data of rig/d2_hands.json."""

    def __init__(self, target, parts, base, hands, part_local=None):
        super().__init__({'Camera1st': Matrix.Translation(target.rest['Camera'].translation)}, target, parts)
        self.offset = Vector((0.0, 0.0, 0.0))            # a source pose is in Fallout 4 world space
        self.base = base
        self.base_local = {n: (base[target.parents[n]].inverted() @ base[n] if target.parents[n] else base[n].copy())
                           for n in target.names}
        # a weapon bone with no part keeps its local transform of the ready pose
        self.part_local = dict(part_local or {})
        for n in target.names:
            if n.startswith('Weapon') and n not in self.part_local:
                self.part_local[n] = self.base_local[n]
        self.chains = d2rig.finger_chains()
        self.k = {}
        for side in ('L', 'R'):
            s = side.lower()
            fit = to_matrix(hands['palm_fit'][side]['rotation'])
            self.k[f'b_{s}_hand'] = (to_matrix(d2rig.K_HAND[side]) @ fit).to_quaternion()
            for part in ('upperarm', 'forearm'):
                self.k[f'b_{s}_{part}'] = to_matrix(d2rig.K_ARM[side]).to_quaternion()
            for finger in d2rig.FINGERS:
                for k in (1, 2, 3):
                    self.k[f'b_{s}_{finger}_{k}'] = to_matrix(d2rig.K_HAND[side]).to_quaternion()
        self.k[d2rig.CAMERA] = to_matrix(d2rig.K_CAMERA).to_quaternion()
        rest = target.rest
        # the rotation of the hand against the last forearm bone, and of the upper arm against
        # the collarbone, in the reference pose: the twist is measured from these
        self.hand_ref = {s: (rest[f'{s}Arm_ForeArm3'].to_quaternion().inverted() @ rest[f'{s}Arm_Hand'].to_quaternion())
                         for s in ('L', 'R')}
        self.upper_ref = {s: (rest[f'{s}Arm_Collarbone'].to_quaternion().inverted() @ rest[f'{s}Arm_UpperArm'].to_quaternion())
                          for s in ('L', 'R')}
        self.last_twist = {}
        self.planar = True
        self.plane_fit = True            # the plane of a finger after the collision step: fitted to its joints
        self.collision_iterations = 8
        self.finger_normals = []         # for each frame: finger -> the normal of its plane (local +Z of its bones)
        self.hook_count = 0              # fingers, in all frames, with the rule for a closed finger (finger_path)
        self.knuckles = False            # True: the wrist moves so that the knuckles are at the source knuckles (knuckle_shift)
        self.closed_fingers = False      # True: the rule for a closed finger (finger_path)
        self.max_knuckle_shift = 0.0
        self.max_shoulder_move = 0.0
        self.max_forearm_twist = 0.0
        self.max_upper_twist = 0.0

    def rotation(self, world, name):
        """The rotation of a source bone in the axes of its Fallout 4 bone."""
        return (world[name].to_quaternion() @ self.k[name]).normalized()

    def knuckle_shift(self, side, world):
        """The move of the Fallout 4 wrist, in the frame of its hand bone, that puts the Fallout 4
        hand on the joints of the source hand: the middle of two vectors, (a) the mean of the
        four source knuckles against the mean of the four Fallout 4 knuckles, and (b) the root
        of the source thumb against the root of the Fallout 4 thumb. The fingers and the thumb
        hold a part from two sides, so the two have the same weight.

        With the two wrists at one place the knuckles of the Destiny hand are 0.50 units from
        those of the Fallout 4 hand and the thumb root is 0.35 units away, and the ports of
        Destiny have no such move. The rig of Marathon has the same bone names and bone axes,
        but its hand bone is at another place in the hand (the forearm is 1.2 cm longer and
        the palm 0.7 cm shorter, and the knuckles are 0.9 cm more to the thumb): its knuckles
        are 1.42 units from those of the Fallout 4 hand, and its thumb root 0.64 units. Each
        finger then starts 2 cm from the finger that it follows, the tip of a bent finger is
        nearer to that knuckle than the length of the first bone, and the finger has no good
        place on the source line. With this move the two distances are 0.41 units.
        `knuckles = "align"` of a set file gives this move. (The move for the four knuckles
        only puts the thumb root 0.82 units to the side of the gun: the right thumb of the M77
        then was in the gun, and the collision step moved it from frame to frame.)"""
        s = side.lower()
        inverse = self.rotation(world, f'b_{s}_hand').inverted()
        origin = world[f'b_{s}_hand'].translation

        def difference(number, finger):
            return (inverse @ (world[f'b_{s}_{finger}_1'].translation - origin)
                    - self.target.local[f'{side}Arm_Finger{number}1'].translation)
        knuckles = Vector((0.0, 0.0, 0.0))
        for number, finger in enumerate(d2rig.FINGERS[1:], 2):
            knuckles += difference(number, finger) / 4.0
        return (knuckles + difference(1, d2rig.FINGERS[0])) / 2.0

    def convert(self, world):
        target = self.target
        pose = {n: m.copy() for n, m in self.base.items()}
        for side in ('L', 'R'):
            if self.knuckles:
                self.hand_shift[side] = self.knuckle_shift(side, world)
                self.max_knuckle_shift = max(self.max_knuckle_shift, self.hand_shift[side].length)
            self.solve_arm(side, world, pose)
        self.place_weapon(world, pose)
        if self.collider is not None:
            self.collider.set_pose(pose)
        log = {}
        self.finger_log.append(log)
        normals = {}
        self.finger_normals.append(normals)
        for (side, finger), (fo4, src) in self.chains.items():
            hand = pose[f'{side}Arm_Hand']
            b0 = (hand @ target.local[fo4[0]]).translation
            m1 = target.local[fo4[1]].translation.length
            m2 = target.local[fo4[2]].translation.length
            m3 = self.tips['fo4'][fo4[2]]['x_max']
            rotations = [self.rotation(world, n) for n in src]
            a0 = world[src[0]].translation.copy()
            a1 = world[src[1]].translation.copy()
            a2 = world[src[2]].translation.copy()
            a3 = a2 + rotations[2] @ Vector((self.tips['fnv'][src[2]]['x_max'], 0.0, 0.0))
            if self.skin_center:
                # the source line becomes the line of the skin centers; its first point moves with the second one
                shift = self.skin_shift(fo4, src)
                a1, a2, a3 = a1 + rotations[1] @ shift[0], a2 + rotations[2] @ shift[1], a3 + rotations[2] @ shift[2]
                a0 = a0 + rotations[1] @ shift[0]
            normal = None
            if self.planar:
                # the plane of the finger: through the knuckle and the source fingertip, nearest to the
                # plane of the source finger (its normal is the hinge of the source bones, local Z)
                normal = plane_normal(b0, a3, rotations[1] @ Vector((0.0, 0.0, 1.0)))
                a0, a1, a2, a3 = into_plane([b0, a0, a1, a2, a3], normal)[1:]
                rotations = [hinge_rotation(rotations[k] @ X_AXIS, normal) for k in range(3)]
            if self.closed_fingers:
                b1, b2, b3, err, closed = finger_path(b0, m1, m2, m3, a0, a1, a2, a3, self.corner_lift)
                self.hook_count += 1 if closed > 0.0 else 0
            else:
                b1, b2, b3, err = solve_finger_path(b0, m1, m2, m3, a0, a1, a2, a3, self.corner_lift)
            self.max_tip_error = max(self.max_tip_error, err)
            self.tip_error_sum += err
            self.tip_count += 1
            pts = [b0, b1, b2, b3]
            flex = back = None
            if self.finger_min_bend > 0.0:
                axes_local, rest_bend = self.rest_flex(fo4)
                if self.planar:
                    axes_local = [FINGER_HINGE, FINGER_HINGE]
                least = [rest_bend[k] * self.finger_min_bend for k in range(2)]
                if finger == 1:
                    least[1] = -THUMB_BACK
                pts = bend_least(pts, rotations, axes_local, least)
                flex = hinge_axes(rotations, pts, axes_local)
                back = [max(0.0, -v) for v in least]
            clear = pts
            if self.collider is not None:
                radii = [self.tips['fo4'][n]['radius'] for n in fo4]
                pts, moved = relax_out(pts, radii, self.collider, self.finger_depth, self.finger_max_push,
                                       iterations=self.collision_iterations,
                                       source_points=(a0, a1, a2, a3), guard_axes=flex, guard_back=back)
                self.max_push_turn = max(self.max_push_turn, moved)
                if moved > 1e-4:
                    self.push_count += 1
                log[(side, finger)] = (fo4, rotations, clear, pts)
            normals[(side, finger)] = normal
            self.write_finger(pose, fo4, rotations, pts, normal)
        # a bone below a hand or a forearm that has no source keeps its local transform of the ready pose
        for name in target.names:
            parent = target.parents[name]
            if name.startswith('WeaponIK'):
                pose[name] = pose[parent] @ target.local[name]
            elif name in ('PipboyBone', 'WeaponLeft') or name.startswith(('AnimObjectL', 'AnimObjectR')):
                pose[name] = pose[parent] @ self.base_local[name]
        camera = world[d2rig.CAMERA]
        pose['Camera'] = trs(camera.translation, self.rotation(world, d2rig.CAMERA))
        return pose

    def write_finger(self, pose, fo4, rotations, points, normal):
        """Write the three bones of a finger. With a plane (`normal`), the joints go into the plane
        through the knuckle and the fingertip that is nearest to it, and each bone has its hinge
        along the normal of that plane, so the two joints after the knuckle are hinges."""
        if normal is None:
            for k in range(3):
                pose[fo4[k]] = trs(points[k], aim_x(rotations[k], points[k + 1] - points[k]))
            return
        lengths = [(points[k + 1] - points[k]).length for k in range(3)]
        n = fitted_normal(points, normal) if self.plane_fit else plane_normal(points[0], points[3], normal)
        points = into_plane(points, n, lengths)
        for k in range(3):
            pose[fo4[k]] = trs(points[k], hinge_rotation(points[k + 1] - points[k], n))

    def smooth_fingers(self, poses, sigma=1.5):
        """The time filter of the collision step (see Retargeter.smooth_fingers: the move of each
        joint, in the space of the hand bone, with a Gaussian window of `sigma` frames), with the
        plane rule for the bones that it writes again. Returns the largest joint move after the filter."""
        if not self.planar:
            return super().smooth_fingers(poses, sigma)
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
                self.write_finger(poses[f], fo4, rotations, out, self.finger_normals[f][key])
        return worst

    def solve_arm(self, side, world, pose):
        target = self.target
        s = side.lower()
        collar, upper, fore1, fore2, fore3, hand = [f'{side}Arm_{n}' for n in (
            'Collarbone', 'UpperArm', 'ForeArm1', 'ForeArm2', 'ForeArm3', 'Hand')]
        su, sf, sh = f'b_{s}_upperarm', f'b_{s}_forearm', f'b_{s}_hand'
        hand_rotation = self.rotation(world, sh)
        wrist = world[sh].translation + hand_rotation @ self.hand_shift[side]
        lengths = [target.local[n].translation.length for n in (fore1, fore2, fore3, hand)]
        a, b = target.local[fore1].translation.length, sum(lengths[1:])
        fore_line = (world[sh].translation - world[sf].translation).normalized()
        upper_line = (world[sf].translation - world[su].translation).normalized()
        elbow = wrist - fore_line * b
        shoulder = elbow - upper_line * a
        self.max_shoulder_move = max(self.max_shoulder_move, (shoulder - world[su].translation).length)
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
        # the collarbone keeps its rotation of the ready pose; its place puts the shoulder joint at the shoulder
        qc = self.base[collar].to_quaternion()
        pose[collar] = trs(shoulder - qc @ target.local[upper].translation, qc)
        turn = near(twist_x((qc @ self.upper_ref[side]).inverted() @ qu), self.last_twist.get(('upper', side)))
        self.last_twist[('upper', side)] = turn
        self.max_upper_twist = max(self.max_upper_twist, abs(turn))
        tw1, tw2 = f'{side}Arm_UpperTwist1', f'{side}Arm_UpperTwist2'
        pose[tw1] = trs((pose[upper] @ target.local[tw1]).translation, qu @ Quaternion(X_AXIS, -2.0 * turn / 3.0))
        pose[tw2] = trs((pose[tw1] @ target.local[tw2]).translation, qu @ Quaternion(X_AXIS, -turn / 3.0))
