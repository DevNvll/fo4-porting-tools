"""Put the gun meshes of a New Vegas model (.nif) into Fallout 4 weapon space.

    python3 tools/gun_parts.py [-o out/fo4mesh/parts.json]

The model is `model` of the configuration file. Each shape has its vertices in the local
space of the Fallout 4 weapon bone that carries it: a shape below a node of [parts] is on the
bone of that node, and each other shape is on the bone Weapon.

The retarget uses the file to keep the fingers out of the gun. It is also the place of the
gun that the clips are for: a Fallout 4 model of the gun must have each shape at these
coordinates on these bones.
"""
import argparse
import json
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import port_config as cfg
from port_defaults import shape_name


def convert():
    nif = cfg.MODEL
    node_bone = {node: bone for bone, (node, _) in cfg.PARTS.items() if bone != 'Weapon'}
    parent_of = {}
    shapes = []
    for b, parent, wr, wt, ws in nif.walk():
        parent_of[b['name']] = parent['name'] if parent is not None else None
        if 'data' not in b:
            continue
        name = b['name']
        bone = None
        n = parent_of[name]
        while bone is None and n is not None:
            bone = node_bone.get(n)
            n = parent_of[n]
        bone = bone or 'Weapon'
        g = nif.blocks[b['data']]
        if g['vertices'] is None:
            raise SystemExit('the shape %s has no vertices' % name)
        q = g['vertices'] @ wr.T * ws + wt                      # FNV weapon space, at rest
        pos = cfg.to_bone(bone, cfg.fnv_to_fo4(q))
        shapes.append({'name': shape_name(name), 'source': name, 'bone': bone,
                       'positions': np.round(pos, 5).tolist(), 'triangles': g['triangles'].tolist()})
    bones = {}
    for bone in cfg.PARTS:
        if bone == 'Weapon':
            continue
        bones[bone] = {'parent': cfg.FO4_PARENT[bone], 'local': cfg.PARTS[bone][1].tolist(),
                       'in_weapon': cfg.pivot_in_weapon(bone).tolist()}
        if bone in cfg.PART_ROTATION:
            bones[bone]['rotation'] = cfg.PART_ROTATION[bone].tolist()

    def in_weapon(s):
        p = np.array(s['positions'])
        if s['bone'] == 'Weapon' or not cfg.turned(s['bone']):
            return p + cfg.pivot_in_weapon(s['bone'])
        m = cfg.rest_in_weapon(s['bone'])
        return p @ m[:3, :3].T + m[:3, 3]
    allp = np.vstack([in_weapon(s) for s in shapes])
    return {'format': 'port_parts 2', 'units': 'Fallout 4 game units, weapon space: +Y muzzle, +Z up, +X right',
            'T': cfg.T.tolist(), 'R': cfg.R.tolist(), 'bones': bones, 'shapes': shapes,
            'bbox_min': allp.min(0).tolist(), 'bbox_max': allp.max(0).tolist()}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('-o', '--output', default=os.path.join(cfg.OUT, 'fo4mesh', 'parts.json'))
    a = ap.parse_args()
    data = convert()
    os.makedirs(os.path.dirname(os.path.abspath(a.output)), exist_ok=True)
    json.dump(data, open(a.output, 'w'), separators=(',', ':'))
    print('T', np.round(cfg.T, 3), 'bbox', np.round(data['bbox_min'], 2), np.round(data['bbox_max'], 2))
    for s in data['shapes']:
        p = np.array(s['positions'])
        print('%-22s bone=%-22s verts=%5d tris=%5d min=%s max=%s' % (
            s['name'], s['bone'], len(p), len(s['triangles']), np.round(p.min(0), 2), np.round(p.max(0), 2)))
