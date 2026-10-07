"""Print a short table of a file of check/contact.py: for each hand bone, the largest depth in
the gun over the frames, for the source and for the result.

    python3 destiny/port/check/contact_table.py CONTACT.json
"""
import os
import sys

_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
import portkit  # noqa: E402,F401  (a file error is one line)
import json
import sys

FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky')


def worst(rows, bone):
    best = (0.0, -1, 0, '')
    count = 0
    for r in rows:
        v = r['bones'].get(bone)
        if v:
            count += 1
            if v[1] > best[0]:
                best = (v[1], r['frame'], v[0], v[2])
    return best, count


def main(path):
    d = json.load(open(path))
    n = len(d['frames'])
    print('%d frames. Vertices inside the gun, all frames: source %d of %d (%.1f %%), result %d of %d (%.1f %%)' % (
        n, sum(r['inside'] for r in d['source']), d['source_vertices'] * n,
        100.0 * sum(r['inside'] for r in d['source']) / (d['source_vertices'] * n),
        sum(r['inside'] for r in d['result']), d['result_vertices'] * n,
        100.0 * sum(r['inside'] for r in d['result']) / (d['result_vertices'] * n)))
    print('%-16s | %-34s | %s' % ('bone', 'source: depth, frame, frames, part', 'result: depth, frame, frames, part'))
    deeper = []
    for side in ('r', 'l'):
        pairs = [('b_%s_hand' % side, '%sArm_Hand' % side.upper())]
        for i, f in enumerate(FINGERS, 1):
            for k in (1, 2, 3):
                pairs.append(('b_%s_%s_%d' % (side, f, k), '%sArm_Finger%d%d' % (side.upper(), i, k)))
        for sb, fb in pairs:
            (sd, sf, sn, sp), sc = worst(d['source'], sb)
            (rd, rf, rn, rp), rc = worst(d['result'], fb)
            mark = ''
            if rd > sd + 0.15 and rd > 0.4:
                mark = '  <- deeper than the source'
                deeper.append(fb)
            print('%-16s | %.2f  f%-3d %3d  %-18s | %.2f  f%-3d %3d  %s%s' % (sb[2:], sd, sf, sc, sp.split('_', 2)[-1], rd, rf, rc, rp.split('_', 2)[-1], mark))
    print('bones of the result that go deeper than the source bone (0.15 units or more, and deeper than 0.4):', ', '.join(deeper) or 'none')


if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__.strip())
        raise SystemExit(0 if sys.argv[1:2] in (['-h'], ['--help']) else 2)
    main(sys.argv[1])
