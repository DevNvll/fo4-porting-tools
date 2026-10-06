"""Shared helpers of the Blender programs: matrices, the two skeletons and the bake files."""
import json
import os
import sys
from mathutils import Matrix, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import anim_fo4  # noqa: E402


def matrix(values):
    """16 numbers, the translation last -> Matrix."""
    return Matrix([values[i:i + 4] for i in range(0, 16, 4)]).transposed()


def bake_to_matrix(v):
    """12 numbers of a bake file (three axis rows, then the translation row) -> Matrix."""
    return Matrix(((v[0], v[3], v[6], v[9]),
                   (v[1], v[4], v[7], v[10]),
                   (v[2], v[5], v[8], v[11]),
                   (0.0, 0.0, 0.0, 1.0)))


def trs(position, rotation, scale=1.0):
    if isinstance(scale, (int, float)):
        scale = (scale,) * 3
    return Matrix.LocRotScale(Vector(position), Quaternion(rotation).normalized(), Vector(scale))


class Skeleton:
    """The nodes of a skeleton in hierarchy order, each with its parent, its local matrix and
    its world matrix at rest."""

    def __init__(self, nodes):
        self.parents = {n['name']: n['parent'] for n in nodes}
        self.local = {n['name']: matrix(n['matrix']) for n in nodes}
        self.names = []
        active = set()

        def visit(name):
            if name in self.names:
                return
            if name in active:
                raise ValueError(f'Cyclic source hierarchy at {name}')
            active.add(name)
            parent = self.parents[name]
            if parent:
                visit(parent)
            active.remove(name)
            self.names.append(name)
        for name in self.parents:
            visit(name)
        self.rest = self.worlds(self.local)

    def worlds(self, local):
        world = {}
        for name in self.names:
            parent = self.parents[name]
            world[name] = (world[parent] if parent else Matrix.Identity(4)) @ local[name]
        return world


def load_target(path):
    """The Fallout 4 skeleton of an HKX file: (the data of the file, Skeleton)."""
    skel = anim_fo4.load_fo4_skeleton(path)
    nodes = []
    for i, name in enumerate(skel.bones):
        p = skel.reference_pose[i]
        rotation = (p.rotation[3], *p.rotation[:3])
        mat = trs(p.translation, rotation, p.scale)
        parent = skel.bones[skel.parents[i]] if skel.parents[i] >= 0 else ''
        nodes.append({'name': name, 'parent': parent, 'matrix': [v for row in mat.transposed() for v in row]})
    return skel, Skeleton(nodes)


def load_source_rest(path):
    """The New Vegas skeleton of rig/nvcs_1st.json."""
    data = json.loads(open(path).read())
    return Skeleton(data['nodes'])


class Bake:
    """World matrices of the nodes of a bake file (tools/kfbake.py), relative to the node Bip01."""

    def __init__(self, path, root='Bip01'):
        d = json.loads(open(path).read())
        self.data = d
        self.fps = d['fps']
        self.times = d['times']
        self.tps = d['ticks_per_second']
        self.nodes = d['nodes']
        self.root = root
        self.count = len(self.times)
        self.seconds = [(t - self.times[0]) / self.tps for t in self.times]

    def world(self, frame, names=None):
        nodes = self.nodes
        rootinv = bake_to_matrix(nodes[self.root]['world'][frame]).inverted()
        out = {}
        for name, n in nodes.items():
            if names is not None and name not in names:
                continue
            w = n['world'][frame]
            if w is None:
                continue
            out[name] = rootinv @ bake_to_matrix(w)
        return out
