"""Put the gun meshes of a Destiny first-person file (.glb) into Fallout 4 weapon space.

    python3 destiny/port/tools/d2parts.py FILE.glb -o parts.json [--template revolver44] [--hold CLIP[:FRAME]] [--role BONE=KIND ...]
        [--bone BONE=FO4BONE ...] [--rest bind|hold] [--rules FILE.json]

The gun is rigid-skinned: each vertex has one weapon bone. The weapon root is `b_handle`, with
the muzzle along its +Z and up along its +Y, in meters. Fallout 4 weapon space has +Y to the
muzzle, +Z up and +X to the right, in game units. A point p of `b_handle` becomes

    p_fo4 = AXES @ p * SCALE + T

T puts the grip point of the gun at the grip point of the template weapon, so that the hands
of the vanilla clips hold the grip. The grip point is the middle of the first joints of the
index finger and the middle finger of the right hand, in the hold pose (--hold; default:
the first frame of the first clip of the file that is not additive).

Each moving part is on a Fallout 4 weapon bone (the roles of the template). Its rest
transform relative to its parent bone is that of the template weapon, so a vanilla clip
shows the part at its rest place. Each shape of the file has its vertices in the local space
of its Fallout 4 bone: a Fallout 4 model of the gun must have its shapes at these places.

The file also has, for each Fallout 4 weapon bone, the matrix C with
    Fallout 4 bone world = Destiny bone world @ C
where the Destiny bone world matrix is in Fallout 4 world space (tools/d2rig.py).
"""
import argparse
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from glb import Glb  # noqa: E402
from d2bake import Rig, load_rules  # noqa: E402
from d2rig import SCALE, AXES, WEAPON, WEAPON_ROLES  # noqa: E402
from d2template import Template  # noqa: E402


def units(m):
    """A matrix of the file (meters) with its translation in game units."""
    out = np.array(m, float, copy=True)
    out[:3, 3] *= SCALE
    return out


def hold_clip(rig, text=None):
    """(clip name, frame) of the hold pose."""
    if text:
        name, _, frame = text.partition(':')
        return name, int(frame or 0)
    for name in rig.clip_names():
        if not name.endswith('_add'):
            return name, 0
    raise SystemExit('the file has no clip')


def weapon_bones(rig):
    """The bones below the weapon root, in hierarchy order."""
    root = rig.index[WEAPON]
    out = []
    for k, p in enumerate(rig.parents):
        if p == root or (p >= 0 and rig.names[p] in out):
            out.append(rig.names[k])
    return out


def convert(glb, rig, template, hold=None, roles=None, direct=None, rest_pose='bind'):
    roles = dict(WEAPON_ROLES, **(roles or {}))
    direct = direct or {}
    clip, frame = hold_clip(rig, hold)
    world, _ = rig.bake(clip)
    w = world[frame]
    handle_inverse = np.linalg.inv(w[rig.index[WEAPON]])
    grip = np.mean([(handle_inverse @ w[rig.index[n]])[:3, 3] for n in ('b_r_index_1', 'b_r_middle_1')], axis=0)
    t = template.grip - AXES @ grip * SCALE
    t[0] = 0.0                                              # keep the gun on the center plane
    x = np.eye(4)                                           # b_handle (game units) -> Fallout 4 weapon space
    x[:3, :3] = AXES
    x[:3, 3] = t
    bind = {n: np.linalg.inv(rig.inverse_bind[n]) for n in rig.skin_joints}
    rest = {n: units(np.linalg.inv(bind[WEAPON]) @ bind[n]) for n in weapon_bones(rig)}       # in b_handle, at rest
    if rest_pose == 'hold':
        # The rest place of a part is its place in the hold pose, not in the bind pose of the file
        # (the belt of a machine gun is a straight line in the bind pose).
        rest = {n: units(handle_inverse @ w[rig.index[n]]) for n in weapon_bones(rig)}

    # the Fallout 4 bone of each weapon bone of the file
    bone_of = {WEAPON: 'Weapon'}
    for n in weapon_bones(rig):
        role = roles.get(n)
        if n in direct:
            if direct[n] not in template.pivots:
                raise SystemExit('the template has no bone %s (for %s)' % (direct[n], n))
            bone_of[n] = direct[n]
        elif role in template.roles:
            bone_of[n] = template.roles[role]
    if len(set(bone_of.values())) != len(bone_of):
        raise SystemExit('two bones of the file have the same Fallout 4 bone: %s' % sorted(bone_of.items()))
    for b in bone_of.values():
        p = template.parents.get(b)
        if b != 'Weapon' and p != 'Weapon' and p not in bone_of.values():
            raise SystemExit('the part bone %s needs its parent %s' % (b, p))

    def carrier(n):
        """The nearest bone, from `n` up, that has a Fallout 4 bone, and the rest matrix of `n` in it."""
        m = np.eye(4)
        while n not in bone_of:
            p = rig.names[rig.parents[rig.index[n]]]
            if rest_pose == 'hold':
                m = units(np.linalg.inv(w[rig.index[p]]) @ w[rig.index[n]]) @ m
            else:
                m = units(np.linalg.inv(bind[p]) @ bind[n]) @ m
            n = p
        return n, m

    def to_fo4_bone(n):
        """Matrix from the local space of the Destiny bone `n` (game units) to the local space of its Fallout 4 bone."""
        if n == WEAPON:
            return x
        return np.linalg.inv(template.rest_in_weapon(bone_of[n])) @ x @ rest[n]

    c = {'Weapon': np.linalg.inv(x)}
    for n, b in bone_of.items():
        if n != WEAPON:
            c[b] = np.linalg.inv(to_fo4_bone(n))

    shapes = []
    for node in glb.nodes:
        if 'mesh' not in node or not node.get('name', '').startswith('region'):
            continue
        mesh = glb.json['meshes'][node['mesh']]
        for pi, prim in enumerate(mesh['primitives']):
            pos = glb.accessor(prim['attributes']['POSITION'])
            joints = glb.accessor(prim['attributes']['JOINTS_0']).astype(int)
            weights = glb.accessor(prim['attributes']['WEIGHTS_0']).astype(float)
            if (weights > 1e-4).sum(1).max() > 1:
                raise SystemExit('%s: a vertex has more than one bone; the gun must be rigid-skinned' % node['name'])
            main = joints[np.arange(len(pos)), np.argmax(weights, axis=1)]
            tris = glb.accessor(prim['indices']).reshape(-1, 3).astype(int)
            uv = glb.accessor(prim['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in prim['attributes'] else None
            normal = glb.accessor(prim['attributes']['NORMAL']) if 'NORMAL' in prim['attributes'] else None
            material = glb.json['materials'][prim['material']].get('name') if 'material' in prim else None
            for j in np.unique(main):
                source = rig.skin_joints[j]
                if source != WEAPON and source not in rest:
                    raise SystemExit('%s: the bone %s is not a weapon bone' % (node['name'], source))
                tb = main[tris]
                if ((tb == j).any(1) & ~(tb == j).all(1)).any():
                    raise SystemExit('%s: a triangle has vertices on two bones' % node['name'])
                sel = main == j
                index = np.full(len(pos), -1)
                index[sel] = np.arange(sel.sum())
                ib = rig.inverse_bind[source]
                local = (pos[sel] @ ib[:3, :3].T + ib[:3, 3]) * SCALE          # in the Destiny bone, game units
                owner, extra = carrier(source)
                m = to_fo4_bone(owner) @ extra
                p = local @ m[:3, :3].T + m[:3, 3]
                shape = {'name': '%s_%d_%s' % (node['name'].split('_')[0], pi, source[2:] if source.startswith('b_') else source),
                         'source': node['name'],
                         'source_bone': source, 'bone': bone_of[owner], 'material': material,
                         'positions': np.round(p, 5).tolist(), 'triangles': index[tris[(tb == j).all(1)]].tolist()}
                if uv is not None:
                    shape['uvs'] = np.round(uv[sel], 6).tolist()
                if normal is not None:
                    n = normal[sel] @ ib[:3, :3].T @ m[:3, :3].T
                    shape['normals'] = np.round(n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12), 5).tolist()
                shapes.append(shape)

    bones = {}
    for n, b in bone_of.items():
        if n == WEAPON:
            continue
        bones[b] = {'source': n, 'parent': template.parents[b], 'local': template.pivots[b].tolist(),
                    'in_weapon': template.rest_in_weapon(b)[:3, 3].tolist()}
        if b in template.rotations:
            bones[b]['rotation'] = template.rotations[b].tolist()

    def in_weapon(s):
        p = np.array(s['positions'])
        if s['bone'] == 'Weapon':
            return p
        m = template.rest_in_weapon(s['bone'])
        return p @ m[:3, :3].T + m[:3, 3]
    allp = np.vstack([in_weapon(s) for s in shapes])
    return {'format': 'd2_parts 1', 'units': 'Fallout 4 game units, weapon space: +Y muzzle, +Z up, +X right',
            'template': template.name, 'hold': [clip, frame], 'rest': rest_pose, 'scale': SCALE, 'T': t.tolist(), 'axes': AXES.tolist(),
            'grip_source': (AXES @ grip * SCALE).tolist(), 'bones': bones,
            'c': {b: m.tolist() for b, m in c.items()}, 'sources': {b: n for n, b in bone_of.items()},
            'shapes': shapes, 'bbox_min': allp.min(0).tolist(), 'bbox_max': allp.max(0).tolist()}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('-o', '--output', required=True)
    ap.add_argument('--template', default='revolver44')
    ap.add_argument('--hold')
    ap.add_argument('--role', action='append', default=[], metavar='BONE=KIND',
                    help='the kind of a weapon bone of the file, for example bone_68719972=bolt')
    ap.add_argument('--bone', action='append', default=[], metavar='BONE=FO4BONE',
                    help='the Fallout 4 bone of a weapon bone of the file, for example bone_9EE2ED5C=WeaponOptics1')
    ap.add_argument('--rest', choices=('bind', 'hold'), default='bind',
                    help='the rest place of each part: its place in the bind pose of the file, or in the hold pose')
    ap.add_argument('--rules', help='a file with the clip rules of a set file (tools/d2bake.py), for the hold pose')
    a = ap.parse_args()
    glb = Glb(a.file)
    roles = dict(text.split('=', 1) for text in a.role)
    direct = dict(text.split('=', 1) for text in a.bone)
    data = convert(glb, Rig(glb, load_rules(a.rules)), Template(a.template), a.hold, roles, direct, a.rest)
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with open(a.output, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    print('[parts] hold pose %s frame %d, T %s, bbox %s %s' % (data['hold'][0], data['hold'][1], np.round(data['T'], 3),
                                                              np.round(data['bbox_min'], 2), np.round(data['bbox_max'], 2)))
    for s in data['shapes']:
        p = np.array(s['positions'])
        print('[parts] %-24s %-18s -> %-22s verts %5d tris %5d min %s max %s' % (
            s['name'], s['source_bone'], s['bone'], len(p), len(s['triangles']), np.round(p.min(0), 2), np.round(p.max(0), 2)))
