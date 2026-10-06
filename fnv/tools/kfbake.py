"""Evaluate a New Vegas animation file (.kf) and write the matrix of each node for each frame.

    python3 tools/kfbake.py FILE.kf --model GUN.nif -o out/anim/NAME.json [--skeleton rig/nvcs_1st.json] [--fps 30]

The output is a bake file: for each node, its parent and its world matrix for each sample
time. A matrix is 12 numbers: the three axis rows and the translation row.
The nodes are the bones of the first-person skeleton and the nodes and shapes of the gun
model, which hang on the bone Weapon. A node with no track keeps its rest transform.
"""
import argparse
import json
import math
import os
import sys
from bisect import bisect_right
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fnvnif

TICKS_PER_SEC = 4800


def quat_matrix(q):
    """(w, x, y, z) -> 3x3 rotation matrix (column vectors)."""
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def matrix_quat(r):
    """3x3 rotation matrix -> (w, x, y, z)."""
    t = r[0, 0] + r[1, 1] + r[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = [0.25 * s, (r[2, 1] - r[1, 2]) / s, (r[0, 2] - r[2, 0]) / s, (r[1, 0] - r[0, 1]) / s]
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = math.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2
        q = [(r[2, 1] - r[1, 2]) / s, 0.25 * s, (r[0, 1] + r[1, 0]) / s, (r[0, 2] + r[2, 0]) / s]
    elif r[1, 1] > r[2, 2]:
        s = math.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2
        q = [(r[0, 2] - r[2, 0]) / s, (r[0, 1] + r[1, 0]) / s, 0.25 * s, (r[1, 2] + r[2, 1]) / s]
    else:
        s = math.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1]) * 2
        q = [(r[1, 0] - r[0, 1]) / s, (r[0, 2] + r[2, 0]) / s, (r[1, 2] + r[2, 1]) / s, 0.25 * s]
    q = np.array(q)
    return q / np.linalg.norm(q)


def slerp(a, b, u):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    d = float(np.dot(a, b))
    if d < 0:
        b, d = -b, -d
    if d > 0.9995:
        q = a + (b - a) * u
        return q / np.linalg.norm(q)
    th = math.acos(min(1.0, d))
    return (math.sin((1 - u) * th) * a + math.sin(u * th) * b) / math.sin(th)


def euler_matrix(x, y, z):
    """Rotation about X, then Y, then Z."""
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def sample(group, time, default, quaternion=False):
    """The value of a key group at a time. Before the first key and after the last key the value is constant."""
    keys = group['keys']
    if not keys:
        return default
    kind = group['type']
    if kind not in (1, 2, 5):
        raise ValueError('key interpolation %d is not supported' % kind)
    i = bisect_right([k['time'] for k in keys], time) - 1
    if i < 0:
        return keys[0]['value']
    if i >= len(keys) - 1 or kind == 5:
        return keys[i]['value']
    a, b = keys[i], keys[i + 1]
    u = (time - a['time']) / (b['time'] - a['time'])
    if quaternion:
        # Quaternion keys have no tangents. The game uses the spherical interpolation.
        return slerp(a['value'], b['value'], u)
    if kind == 1:
        return a['value'] * (1 - u) + b['value'] * u
    return ((2 * u**3 - 3 * u**2 + 1) * a['value'] + (u**3 - 2 * u**2 + u) * a['forward']
            + (-2 * u**3 + 3 * u**2) * b['value'] + (u**3 - u**2) * b['backward'])


def valid(v):
    return bool(np.all(np.isfinite(v)) and np.all(np.abs(v) < fnvnif.FLT_LIMIT))


def compose(t, r, s):
    m = np.eye(4)
    m[:3, :3] = r * s
    m[:3, 3] = t
    return m


class Rig:
    """The skeleton and the gun nodes: name -> parent and rest local matrix (column vectors)."""

    def __init__(self, skeleton, model=None, weapon_bone='Weapon'):
        self.parent, self.local, self.order = {}, {}, []
        for n in json.load(open(skeleton))['nodes']:
            self.add(n['name'], n['parent'] or None, np.array(n['matrix'], float).reshape(4, 4).T)
        if model:
            nif = fnvnif.Nif(model)
            root = nif.root()
            for b, parent, _, _, _ in nif.walk():
                if b is root:
                    continue
                self.add(b['name'], weapon_bone if parent is root else parent['name'],
                         compose(b['translation'], b['rotation'], b['scale']))

    def add(self, name, parent, local):
        if name in self.local:
            raise SystemExit('two nodes have the name ' + name)
        self.parent[name], self.local[name] = parent, local

    def sorted(self):
        done, out = set(), []

        def visit(n):
            if n in done:
                return
            p = self.parent[n]
            if p is not None:
                visit(p)
            done.add(n)
            out.append(n)
        for n in self.local:
            visit(n)
        return out


def bake(kf, skeleton, model=None, fps=30):
    rig = Rig(skeleton, model)
    nif = fnvnif.Nif(kf)
    seq = nif.sequence()
    tracks, unknown = {}, []
    for t in seq['tracks']:
        if t['controller_type'] != 'NiTransformController':
            continue
        if t['node'] not in rig.local:
            unknown.append(t['node'])
            continue
        ip = nif.blocks[t['interpolator']]
        tracks[t['node']] = (ip, nif.blocks[ip['data']] if ip['data'] >= 0 else None)
    count = int(round((seq['stop'] - seq['start']) * fps)) + 1
    seconds = [seq['start'] + i / fps for i in range(count)]
    order = rig.sorted()
    out = {n: {'parent': rig.parent[n], 'world': []} for n in order}
    for time in seconds:
        world = {}
        for n in order:
            local = rig.local[n]
            if n in tracks:
                ip, d = tracks[n]
                rest = local
                rs = float(np.linalg.norm(rest[:3, 0]))
                p0 = ip['translation'] if valid(ip['translation']) else rest[:3, 3]
                q0 = ip['rotation'] if valid(ip['rotation']) and float(ip['rotation'] @ ip['rotation']) > 1e-8 else matrix_quat(rest[:3, :3] / rs)
                s0 = ip['scale'] if valid(np.array([ip['scale']])) else rs
                if d is None:
                    p, r, s = p0, quat_matrix(q0), s0
                else:
                    p = sample(d['translations'], time, p0)
                    if d['euler'] is not None:
                        r = euler_matrix(*[sample(g, time, 0.0) for g in d['euler']])
                    else:
                        r = quat_matrix(sample(d['rotations'], time, q0, quaternion=True))
                    s = sample(d['scales'], time, s0)
                local = compose(p, r, s)
            p = rig.parent[n]
            world[n] = world[p] @ local if p is not None else local
            m = world[n]
            out[n]['world'].append([round(float(v), 6) for v in (
                m[0, 0], m[1, 0], m[2, 0], m[0, 1], m[1, 1], m[2, 1], m[0, 2], m[1, 2], m[2, 2], m[0, 3], m[1, 3], m[2, 3])])
    tk = nif.blocks[seq['text_keys']] if seq['text_keys'] >= 0 else None
    return {'scene': os.path.basename(kf), 'sequence': seq['name'], 'fps': fps, 'ticks_per_second': TICKS_PER_SEC,
            'start': int(round(seq['start'] * TICKS_PER_SEC)), 'end': int(round(seq['stop'] * TICKS_PER_SEC)),
            'times': [int(round(t * TICKS_PER_SEC)) for t in seconds],
            'text_keys': [[round(float(t), 4), s] for t, s in tk['keys']] if tk else [],
            'tracks': sorted(tracks), 'tracks_with_no_node': unknown, 'nodes': out, 'errors': {}}


if __name__ == '__main__':
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument('kf')
    ap.add_argument('-o', '--output', required=True)
    ap.add_argument('--model', help='the gun model (.nif); its nodes hang on the bone Weapon')
    ap.add_argument('--skeleton', default=os.path.join(os.environ.get('PORT_RIG') or os.path.join(os.path.dirname(here), 'rig'), 'nvcs_1st.json'))
    ap.add_argument('--fps', type=int, default=30)
    a = ap.parse_args()
    data = bake(a.kf, a.skeleton, a.model, a.fps)
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    with open(a.output, 'w') as f:
        json.dump(data, f, separators=(',', ':'))
    print('sequence', data['sequence'], 'frames', len(data['times']), 'nodes', len(data['nodes']), 'tracks', len(data['tracks']),
          'tracks with no node', data['tracks_with_no_node'])
    for t, s in data['text_keys']:
        print('  text key %.4f (frame %.1f) %s' % (t, t * a.fps, s))
