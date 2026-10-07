#!/usr/bin/env python3
"""Print the points of a gun that a set file needs: the muzzle, the eye point and a map of the sight.

    ./port destiny points WORK/parts.json [--poses WORK/fo4/poses/CLIP.npz] [--sight TEXT]
    python3 destiny/port/tools/d2points.py ...          (the same program with no ./port)

WORK is the work folder of the weapon (data/destiny/port/work/NAME).

All values are in Fallout 4 weapon space (+Y to the muzzle, +Z up, +X to the right, units).

* The muzzle (`muzzle` of [model]): the vertices at the front of the gun, with the center and
  the size of that group. Look at the model: the front can be a flash hider, and the bore
  can be a different shape.
* With --poses (a clip in the sights): the eye point in the first frame, which is the place of
  the camera bone in weapon space, and the direction of the view.
* A map of the shapes whose name has TEXT (default: the shapes of `region03`, the sight of a
  Destiny gun), seen along the barrel: `#` is a place with a triangle. The window of the
  sight is the hole in the map. Its center, with the Y of the sight, is `point` of [sight].
"""
import os
import sys

_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import portkit  # noqa: E402,F401  (a file error is one line)
import argparse
import json
import numpy as np


def in_weapon(parts, shape):
    """The vertices of a shape in weapon space at rest."""
    p = np.array(shape['positions'], float)
    bone = shape['bone']
    while bone != 'Weapon':
        b = parts['bones'][bone]
        if 'rotation' in b:
            x, y, z, w = b['rotation']
            r = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                          [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                          [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
            p = p @ r.T
        p = p + np.array(b['local'], float)
        bone = b['parent']
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('parts')
    ap.add_argument('--poses', help='the poses of a clip in the sights (WORK/fo4/poses/CLIP.npz), for the eye point')
    ap.add_argument('--sight', default='region03', help='text in the name of each shape of the sight')
    ap.add_argument('--cell', type=float, default=0.1, help='the size of a cell of the map, in units')
    a = ap.parse_args()
    parts = json.load(open(a.parts))
    shapes = [(s, in_weapon(parts, s)) for s in parts['shapes']]
    allp = np.vstack([p for _, p in shapes])
    front = allp[:, 1].max()
    print('the gun: x %.2f..%.2f, y %.2f..%.2f, z %.2f..%.2f (%.1f units long)' % (
        allp[:, 0].min(), allp[:, 0].max(), allp[:, 1].min(), front, allp[:, 2].min(), allp[:, 2].max(), front - allp[:, 1].min()))
    for depth in (0.05, 0.5, 2.0):
        q = allp[allp[:, 1] > front - depth]
        print('the front %.2f units: %4d vertices, x %.2f..%.2f (center %.2f), z %.2f..%.2f (center %.2f)' % (
            depth, len(q), q[:, 0].min(), q[:, 0].max(), (q[:, 0].min() + q[:, 0].max()) / 2,
            q[:, 2].min(), q[:, 2].max(), (q[:, 2].min() + q[:, 2].max()) / 2))
    if a.poses:
        d = np.load(a.poses, allow_pickle=True)
        names = [str(n) for n in d['names']]
        m = np.linalg.inv(d['poses'][0, names.index('Weapon')]) @ d['poses'][0, names.index('Camera')]
        print('the eye point in the first frame: %s; the view direction: %s' % (
            np.round(m[:3, 3], 3).tolist(), np.round(m[:3, :3] @ np.array([0.0, 0.0, -1.0]), 4).tolist()))
    sight = [(s, p) for s, p in shapes if a.sight in s['name']]
    if not sight:
        print('no shape has `%s` in its name' % a.sight)
        return
    tris = np.vstack([p[np.array(s['triangles'])] for s, p in sight])
    lo, hi = tris.reshape(-1, 3).min(0), tris.reshape(-1, 3).max(0)
    print('the sight (%s): x %.2f..%.2f, y %.2f..%.2f, z %.2f..%.2f' % (
        ', '.join(s['name'] for s, _ in sight), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    nx, nz = int((hi[0] - lo[0]) / a.cell) + 3, int((hi[2] - lo[2]) / a.cell) + 3
    grid = np.zeros((nz, nx), bool)
    for t in tris:
        size = np.linalg.norm(t.max(0) - t.min(0))
        n = max(3, int(size / a.cell * 2))
        for u in np.linspace(0, 1, n):
            for v in np.linspace(0, 1 - u, max(2, int(n * (1 - u)))):
                q = t[0] + (t[1] - t[0]) * u + (t[2] - t[0]) * v
                grid[int(round((q[2] - lo[2]) / a.cell)) + 1, int(round((q[0] - lo[0]) / a.cell)) + 1] = True
    for i in range(nz - 1, -1, -1):
        print('%7.2f  %s' % (lo[2] + (i - 1) * a.cell, ''.join('#' if c else '.' for c in grid[i])))
    print('         x from %.2f, %.2f units for each cell' % (lo[0] - a.cell, a.cell))


if __name__ == '__main__':
    main()
