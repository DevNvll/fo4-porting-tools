"""Write Fallout 4 HKX clips from the retargeted poses (out/fo4/poses/*.npz).

    python3 tools/port_hkx.py --poses out/fo4/poses --out out/fo4/hkx [--only NAME]

A pose file has the world matrix of each FO4 bone for each frame. A clip is a list of
(source scene, first frame, last frame) parts with annotations. The clip table is in the
configuration file of the weapon (see port_clips.py).
"""
import argparse
import json
import math
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_fo4


def mat_to_quat(r):
    """3x3 rotation matrix (column vectors) -> (x, y, z, w)."""
    t = r[0, 0] + r[1, 1] + r[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        w = 0.25 * s
        x = (r[2, 1] - r[1, 2]) / s
        y = (r[0, 2] - r[2, 0]) / s
        z = (r[1, 0] - r[0, 1]) / s
    elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
        s = math.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2
        w = (r[2, 1] - r[1, 2]) / s
        x = 0.25 * s
        y = (r[0, 1] + r[1, 0]) / s
        z = (r[0, 2] + r[2, 0]) / s
    elif r[1, 1] > r[2, 2]:
        s = math.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2
        w = (r[0, 2] - r[2, 0]) / s
        x = (r[0, 1] + r[1, 0]) / s
        y = 0.25 * s
        z = (r[1, 2] + r[2, 1]) / s
    else:
        s = math.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1]) * 2
        w = (r[1, 0] - r[0, 1]) / s
        x = (r[0, 2] + r[2, 0]) / s
        y = (r[1, 2] + r[2, 1]) / s
        z = 0.25 * s
    q = np.array([x, y, z, w])
    return q / np.linalg.norm(q)


def quat_to_mat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def decompose(m):
    t = m[:3, 3].copy()
    s = np.linalg.norm(m[:3, :3], axis=0)
    r = m[:3, :3] / np.where(s > 0, s, 1)
    if np.linalg.det(r) < 0:
        s[0] = -s[0]
        r[:, 0] = -r[:, 0]
    return t, mat_to_quat(r), s


def compose(t, q, s):
    m = np.eye(4)
    m[:3, :3] = quat_to_mat(q) * np.asarray(s)[None, :]
    m[:3, 3] = t
    return m


def local_tracks(poses, parents):
    """poses: frames x bones x 4 x 4 world matrices. Returns t, q, s arrays (frames x bones x n)."""
    f, b = poses.shape[:2]
    tr = np.zeros((f, b, 3))
    ro = np.zeros((f, b, 4))
    sc = np.ones((f, b, 3))
    for j in range(b):
        p = parents[j]
        prev = None
        for i in range(f):
            local = np.linalg.inv(poses[i, p]) @ poses[i, j] if p >= 0 else poses[i, j]
            t, q, s = decompose(local)
            if prev is not None and float(np.dot(q, prev)) < 0:
                q = -q
            prev = q
            tr[i, j], ro[i, j], sc[i, j] = t, q, s
    return tr, ro, sc


def world_from_local(tr, ro, sc, parents):
    f, b = tr.shape[:2]
    out = np.zeros((f, b, 4, 4))
    for i in range(f):
        for j in range(b):
            m = compose(tr[i, j], ro[i, j], sc[i, j])
            p = parents[j]
            out[i, j] = out[i, p] @ m if p >= 0 else m
    return out


def write_clip(path, names, tr, ro, sc, fps, annotations=()):
    n = tr.shape[0]
    sc = np.where(np.abs(sc - 1.0) < 2e-4, 1.0, sc)
    anim = anim_fo4.AnimationData()
    anim.num_frames = n
    anim.frame_duration = 1.0 / fps
    anim.duration = (n - 1) / fps
    anim.num_tracks = len(names)
    anim.bone_names = [''] * len(names)
    anim.track_to_bone_indices = list(range(len(names)))
    anim.original_skeleton_name = 'Root'
    anim.max_frames_per_block = 256
    anim.num_blocks = max(1, (n + 255) // 256)
    anim.block_duration = 255.0 / fps
    anim.tracks = [anim_fo4.TrackData(translations=tr[:, j].tolist(), rotations=ro[:, j].tolist(), scales=sc[:, j].tolist())
                   for j in range(len(names))]
    anim.annotations = [anim_fo4.Annotation(time=float(t), text=text) for t, text in sorted(annotations)]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    anim_fo4.write_fo4_animation(path, anim)
    return anim


def check_clip(path, tr, ro, sc, parents):
    """Read the file again and compare the world poses."""
    a = anim_fo4.load_fo4_animation(path)
    n = tr.shape[0]
    if a.num_frames != n:
        return {'frames_written': n, 'frames_read': a.num_frames}
    t2 = np.array([t.translations for t in a.tracks]).transpose(1, 0, 2)
    r2 = np.array([t.rotations for t in a.tracks]).transpose(1, 0, 2)
    s2 = np.array([t.scales for t in a.tracks]).transpose(1, 0, 2)
    w1 = world_from_local(tr, ro, sc, parents)
    w2 = world_from_local(t2, r2, s2, parents)
    pos = float(np.abs(w1[:, :, :3, 3] - w2[:, :, :3, 3]).max())
    d = np.abs(np.sum(ro * r2, axis=2)).clip(0, 1)
    rot = float(np.degrees(2 * np.arccos(d)).max())
    return {'frames': n, 'max_world_position_error': pos, 'max_local_rotation_error_deg': rot,
            'annotations': [(round(x.time, 4), x.text) for x in a.annotations], 'duration': a.duration}


class Poses:
    def __init__(self, folder):
        self.folder = folder
        self.cache = {}

    def get(self, scene):
        if scene not in self.cache:
            d = np.load(os.path.join(self.folder, scene + '.npz'))
            self.cache[scene] = (d['poses'], [str(x) for x in d['names']], [int(x) for x in d['parents']], int(d['fps']))
        return self.cache[scene]


def main():
    import port_clips
    ap = argparse.ArgumentParser()
    ap.add_argument('--poses', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--only')
    a = ap.parse_args()
    src = Poses(a.poses)
    report = {}
    for name, clip in port_clips.clips().items():
        if a.only and name != a.only:
            continue
        poses, names, parents, fps, ann = port_clips.build(clip, src)
        tr, ro, sc = local_tracks(poses, parents)
        path = os.path.join(a.out, name + '.hkx')
        write_clip(path, names, tr, ro, sc, fps, ann)
        np.savez_compressed(os.path.join(a.out, name + '.npz'), poses=poses, names=np.array(names), parents=np.array(parents), fps=fps)
        r = check_clip(path, tr, ro, sc, parents)
        r['source'] = clip.get('note') or clip['parts']
        report[name] = r
        print('%-28s frames %4d  %.3fs  pos err %.4f  rot err %.3f deg  ann %d' % (
            name, tr.shape[0], (tr.shape[0] - 1) / fps, r.get('max_world_position_error', -1),
            r.get('max_local_rotation_error_deg', -1), len(ann)))
    with open(os.path.join(a.out, 'report.json'), 'w') as f:
        json.dump(report, f, indent=1)


if __name__ == '__main__':
    main()
