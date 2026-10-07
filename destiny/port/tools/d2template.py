"""A template weapon (templates/NAME.toml): the rest matrix of each weapon bone."""
import os
import tomllib
import numpy as np

from d2rig import quat_matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Template:
    def __init__(self, name):
        path = name if os.path.exists(name) else os.path.join(ROOT, 'templates', name + '.toml')
        with open(path, 'rb') as f:
            self.data = tomllib.load(f)
        if 'base' in self.data:
            # a template that is a second template with more values: each table gets the keys of the two
            base = Template(self.data['base']).data
            merged = dict(base)
            for key, value in self.data.items():
                merged[key] = dict(base.get(key, {}), **value) if isinstance(value, dict) else value
            self.data = merged
        self.name = os.path.splitext(os.path.basename(path))[0]
        self.sound = self.data['sound']
        self.pivots = {b: np.array(v, float) for b, v in self.data['pivots'].items()}
        self.rotations = {b: np.array(q, float) / np.linalg.norm(q) for b, q in self.data.get('rotations', {}).items()}
        self.parents = dict(self.data['parents'])
        self.roles = dict(self.data['roles'])
        self.grip = np.array(self.data['grip'], float)

    def clip_folder(self, rig):
        return os.path.join(rig, self.data['clips'])

    def local(self, bone):
        """Rest matrix (4 x 4, column vectors) of a weapon bone relative to its parent bone."""
        m = np.eye(4)
        if bone in self.rotations:
            m[:3, :3] = quat_matrix(self.rotations[bone])
        m[:3, 3] = self.pivots[bone]
        return m

    def rest_in_weapon(self, bone):
        """Rest matrix of a weapon bone in Fallout 4 weapon space."""
        m = np.eye(4)
        while bone != 'Weapon':
            m = self.local(bone) @ m
            bone = self.parents[bone]
        return m
