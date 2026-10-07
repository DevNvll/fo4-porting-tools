#!/usr/bin/env python3
"""The distance of each hand to the gun, for each clip of a set file (check/touch.py).

    ./port destiny check touch-table FILE.glb --set SET.toml --clips DIR [--out FILE.txt]
    python3 destiny/port/check/touch_table.py ...          (the same program with no ./port)

DIR is the folder with the HKX clips. The work folder of the weapon (--work; default:
data/destiny/port/work/NAME) has the bake files and the parts file of the converter.

For each Fallout 4 clip that comes from a clip of the file: the percent of the vertices of
each hand that are nearer than 0.5 cm to the gun, as the mean of the frames and as the least
value of a frame, for the Destiny hand of the source and for the Fallout 4 hand of the
result. A frame in which a hand is away from the gun (a reload) has 0 percent, so the least
value of such a clip is 0.
"""
import argparse
import json
import os
import subprocess
import sys
import tomllib

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import fo4clip  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--set', required=True)
    ap.add_argument('--clips', required=True, help='the folder with the HKX clips')
    ap.add_argument('--work', help='the work folder of the weapon (default: data/destiny/port/work/NAME)')
    ap.add_argument('--only', action='append', default=[])
    ap.add_argument('--out')
    a = ap.parse_args()
    with open(a.set, 'rb') as f:
        data = tomllib.load(f)
    name = os.path.splitext(os.path.basename(a.file))[0].replace('_first_person', '')
    work = os.path.abspath(a.work or paths.data('destiny', 'port', 'work', name))
    os.environ['D2FO4_WORK'] = work
    first = {}
    for target, clip in data.get('clips', {}).items():
        first.setdefault(clip, target)
    lines = ['The percent of the vertices of each hand that are nearer than 0.5 cm to the gun (check/touch.py): the mean of',
             'the frames, and the least value of a frame. Source: the Destiny hand. Result: the Fallout 4 hand.', '',
             '%-22s %-17s %6s | %-27s | %-27s | %-27s | %-27s' % ('clip', 'from', 'frames', 'left hand, source', 'left hand, result',
                                                                  'right hand, source', 'right hand, result')]
    for clip, target in first.items():
        if a.only and target not in a.only:
            continue
        hkx = os.path.join(a.clips, target + '.hkx')
        count = fo4clip.load_poses(hkx)[0].shape[0]
        frames = range(0, count, 1 if count <= 64 else 2)
        out = os.path.join(work, 'validate', target + '_touch.json')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        r = subprocess.run(['sh', os.path.join(HERE, 'bl.sh'), os.path.join(HERE, 'touch.py'), '--', '--glb', a.file,
                            '--bake', os.path.join(work, 'bake', clip + '.npz'), '--poses', hkx, '--parts', os.path.join(work, 'parts.json'),
                            '--frames', ','.join(str(f) for f in frames), '--quiet', '--out', out], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(r.stdout[-2000:] + r.stderr[-2000:])
        d = json.load(open(out))
        cells = []
        for side in ('left', 'right'):
            for kind in ('source', 'result'):
                part = [100.0 * row[side]['near'][0] / row[side]['vertices'] for row in d[kind]]
                cells.append('%5.1f %% mean, %5.1f %% least' % (sum(part) / len(part), min(part)))
        lines.append('%-22s %-17s %6d | %s' % (target, clip, count, ' | '.join(cells)))
        print(lines[-1], flush=True)
    if a.out:
        with open(a.out, 'w') as f:
            f.write('\n'.join(lines) + '\n')


if __name__ == '__main__':
    main()
