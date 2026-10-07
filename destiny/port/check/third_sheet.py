#!/usr/bin/env python3
"""Draw a third-person clip as lines: the source of Destiny above the result for Fallout 4.

    python3 destiny/port/check/third_sheet.py SOURCE.npz RESULT.npz OUT.png [--frames 8]

SOURCE is a file of tools/d2third.py and RESULT is a pose file of tools/blender/d3retarget.py
(or a clip .hkx of the third-person skeleton). Each column is one frame: the view from the
right side of the body, and the view from the front. The yellow line is the axis of the gun.
"""
import argparse
import os
import sys
import numpy as np
from PIL import Image, ImageDraw

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'tools'))
import d2rig  # noqa: E402

SKIP_SOURCE = ('index', 'middle', 'ring', 'pinky', 'thumb', 'brow', 'eye', 'lip', 'jaw', 'fixup', 'utility')
SKIP_RESULT = ('Finger', 'AnimObject', 'IKTarget', 'Camera', 'CamTarget', 'Rib', 'Pipboy', 'WeaponLeft')


def load(path):
    if path.lower().endswith('.hkx'):
        import fo4clip
        skel = fo4clip.skeleton(paths.data('destiny', 'port', 'rig', 'third', 'skeleton.hkx'))
        _, world, _, _ = fo4clip.decode(path, skel)
        return world, list(skel.bones), list(skel.parents), 'result'
    d = np.load(path)
    names = [str(n) for n in d['names']]
    if 'world' in d:
        return d2rig.to_fo4_world(d['world'], (0, 0, 0), (0, 0, 0)), names, d['parents'].tolist(), 'source'
    return d['poses'], names, d['parents'].tolist(), 'result'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+')
    ap.add_argument('--frames', type=int, default=8)
    ap.add_argument('--size', type=int, default=300)
    a = ap.parse_args()
    out = a.files[-1]
    rows = [load(p) for p in a.files[:-1]]
    s, scale = a.size, a.size / 150.0
    sheet = Image.new('RGB', (s * a.frames, s * 2 * len(rows)), (20, 20, 24))
    dr = ImageDraw.Draw(sheet)
    for r, (world, names, parents, kind) in enumerate(rows):
        skip = SKIP_SOURCE if kind == 'source' else SKIP_RESULT
        keep = [i for i, n in enumerate(names) if not any(x in n for x in skip)]
        gun = 'b_handle' if kind == 'source' else 'Weapon'
        count = world.shape[0]
        for k in range(a.frames):
            f = int(round(k * (count - 1) / (a.frames - 1)))
            for view, axis in enumerate((1, 0)):
                x0, y0 = k * s + s / 2, (r * 2 + view) * s + s - 15

                def at(p):
                    return (x0 + p[axis] * scale * (1 if axis == 1 else 1), y0 - p[2] * scale)
                for i in keep:
                    p = parents[i]
                    if p < 0 or p not in keep:
                        continue
                    n = names[i]
                    is_gun = n.startswith('Weapon') or (kind == 'source' and i >= 72)
                    left = n.startswith(('b_l_', 'LArm', 'LLeg'))
                    right = n.startswith(('b_r_', 'RArm', 'RLeg'))
                    color = (255, 120, 60) if is_gun else (120, 200, 255) if left else (160, 255, 160) if right else (230, 230, 230)
                    dr.line([at(world[f, p, :3, 3]), at(world[f, i, :3, 3])], fill=color, width=3 if is_gun else 2)
                g = world[f, names.index(gun)]
                forward = g[:3, 2] if kind == 'source' else g[:3, 1]
                dr.line([at(g[:3, 3]), at(g[:3, 3] + forward * 42)], fill=(255, 200, 0), width=2)
                dr.text((k * s + 6, (r * 2 + view) * s + 4), '%s frame %d %s' % (os.path.basename(a.files[r])[:24], f, 'side' if view == 0 else 'front'), fill=(255, 255, 255))
    sheet.save(out)


if __name__ == '__main__':
    main()
