"""The vanilla first-person arm meshes of Fallout 4 (glTF files of the rig folder data/fnv/rig).

The meshes are in game units after the change of axes: glTF point (x, y, z) -> game point
(x, -z, y). Each vertex is sum(weight * bone world * skin-to-bone * vertex), as in the game.
The class and the rules for the skin bones that the skeleton does not have are those of
fnv-fo4-port-checks/blender/render_fo4.py.
"""
import json
import os
import numpy as np

from glb import Glb

A = np.array([[1.0, 0, 0, 0], [0, 0, -1.0, 0], [0, 1.0, 0, 0], [0, 0, 0, 1.0]])
AI = np.linalg.inv(A)
GUESS = {'Chest_Rear_Skin': 'Chest', 'LArm_ShoulderFat_skin': 'LArm_Collarbone', 'RArm_ShoulderFat_skin': 'RArm_Collarbone'}


class SkinnedMesh:
    def __init__(self, path):
        glb = Glb(path)
        js = glb.json
        node = [n for n in js['nodes'] if 'mesh' in n and 'skin' in n][0]
        prim = js['meshes'][node['mesh']]['primitives'][0]
        skin = js['skins'][node['skin']]
        self.name = node['name']
        self.verts = glb.accessor(prim['attributes']['POSITION']) @ A[:3, :3].T
        self.tris = glb.accessor(prim['indices']).reshape(-1, 3).astype(int)
        self.joints = glb.accessor(prim['attributes']['JOINTS_0']).astype(int)
        self.weights = glb.accessor(prim['attributes']['WEIGHTS_0']).astype(float)
        self.joint_names = [js['nodes'][i]['name'] for i in skin['joints']]
        ibm = glb.accessor(skin['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1)
        self.inv_bind = np.array([A @ m @ AI for m in ibm])
        self.bind_world = {n: np.linalg.inv(self.inv_bind[i]) for i, n in enumerate(self.joint_names)}
        self.main = self.joints[np.arange(len(self.verts)), np.argmax(self.weights, axis=1)]

    def local(self, joint):
        """The vertices whose largest weight is of this joint, in the space of the joint."""
        j = self.joint_names.index(joint)
        sel = self.main == j
        m = self.inv_bind[j]
        return self.verts[sel] @ m[:3, :3].T + m[:3, 3]

    def rules(self, names, helpers):
        """For each joint: (index of the animated bone that carries it, matrix of the joint relative to that bone)."""
        idx = {n: i for i, n in enumerate(names)}
        out = []
        for jn in self.joint_names:
            if jn in idx:
                out.append((idx[jn], np.eye(4)))
                continue
            ch = helpers.chain(jn)
            if ch is None:
                base = GUESS.get(jn) or jn.replace('_skin', '')
                if base not in idx:
                    raise SystemExit('no rule for the skin bone ' + jn)
                wb = self.bind_world.get(base)
                if wb is None:
                    wb = helpers.rest_world(base)
                if wb is None:
                    raise SystemExit('no bind matrix for %s (skin bone %s)' % (base, jn))
                out.append((idx[base], np.linalg.inv(wb) @ self.bind_world[jn]))
            else:
                out.append((idx[ch[0]], ch[1]))
        return out

    def skinned(self, pose, rules):
        """The vertices for one pose (bones x 4 x 4 world matrices)."""
        out = np.zeros_like(self.verts)
        mats = [pose[bi] @ extra @ self.inv_bind[j] for j, (bi, extra) in enumerate(rules)]
        for k in range(self.joints.shape[1]):
            jj = self.joints[:, k]
            ww = self.weights[:, k]
            for j in np.unique(jj):
                sel = (jj == j) & (ww > 0)
                if sel.any():
                    m = mats[j]
                    out[sel] += ww[sel, None] * (self.verts[sel] @ m[:3, :3].T + m[:3, 3])
        return out


class Helpers:
    """Bones of the skeleton NIF that the animation does not have: fixed under an animated bone."""

    def __init__(self, rig, names):
        d = json.load(open(os.path.join(rig, '1st_skeleton_nodes.json')))['data']
        nodes = d['nodes']
        self.local = {}
        self.parent = {}
        byblock = {n['block']: n for n in nodes}
        for n in nodes:
            m = np.eye(4)
            m[:3, :3] = np.array(n['rotation'], float).reshape(3, 3)
            m[:3, 3] = n['translation']
            p = byblock.get(n['parent']) if n.get('parent') is not None else None
            if p is n:
                p = None
            self.local[n['name']] = m
            self.parent[n['name']] = p['name'] if p is not None else None
        self.animated = set(names)

    def rest_world(self, name):
        m = np.eye(4)
        cur = name
        while cur is not None:
            if cur not in self.local:
                return None
            m = self.local[cur] @ m
            cur = self.parent.get(cur)
        return m

    def chain(self, name):
        m = np.eye(4)
        cur = name
        seen = 0
        while cur is not None and cur not in self.animated and seen < 50:
            if cur not in self.local:
                return None
            m = self.local[cur] @ m
            cur = self.parent.get(cur)
            seen += 1
        if cur is None or cur not in self.animated:
            return None
        return cur, m
