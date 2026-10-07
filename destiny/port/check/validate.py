#!/usr/bin/env python3
"""Make the validation files of a clip set: videos of the source beside the result, and the numbers.

    ./port destiny check validate FILE.glb --set SET.toml --out data/destiny/port/validation/WEAPON
        [--clips FOLDER] [--work FOLDER] [--only NAME ...] [--left-hand] [--no-video]
    python3 destiny/port/check/validate.py ...          (the same program with no ./port)

The defaults, with WEAPON = the file name with no `_first_person`: --clips
data/destiny/port/out/WEAPON, --work data/destiny/port/work/WEAPON (the work folder of the
converter: it has the bake files and the parts file).

For each clip of the file in the set (one time for each clip, with the name of its first
Fallout 4 clip):

    NAME_first_person.mp4   the first-person camera, all frames: source at the left, result at the right
    NAME_gun.mp4            the grip from the left side and from the right side of the gun, at half speed
                            (a clip of more than 64 frames: each second frame, so at full speed)
    NAME_left_hand.mp4      with --left-hand (a gun for two hands): the left hand from the side of its
                            thumb and from its palm, at the same speed
    NAME.txt                the gun against the source gun, the hand vertices inside the gun and the
                            finger joints (check/gun.py, check/contact.py, check/fingers.py)

For each clip with vanilla weapon motion ([synth] and [static] of the set) there is no source:
NAME_first_person.mp4 has the result only. summary.txt has one line for each clip.
With --no-video the program makes NAME.txt and summary.txt only (the videos of a long clip
need many minutes).
Each picture comes from the HKX file. The work pictures are in WORK/validate.
"""
import argparse
import json
import os
import re
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
DATA = paths.data('destiny', 'port')
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import fo4clip  # noqa: E402


def run(args, quiet=True):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('failed: %s\n%s' % (' '.join(args[:6]), (r.stdout + r.stderr)[-2000:]))
    return r.stdout


def blender(script, *args):
    return ['sh', os.path.join(HERE, 'bl.sh'), os.path.join(HERE, script), '--', *args]


def video(out, rate, *rows):
    """rows: lists of picture patterns; each row is one line of pictures."""
    inputs = []
    for row in rows:
        for pattern in row:
            inputs += ['-framerate', str(rate), '-pattern_type', 'glob', '-i', pattern]
    n = [len(row) for row in rows]
    if len(rows) == 1:
        graph = ''.join('[%d:v]' % i for i in range(n[0])) + ('hstack=inputs=%d,' % n[0] if n[0] > 1 else 'null,') + 'format=yuv420p'
    else:
        layout = '|'.join('%s_%s' % ('+'.join('w%d' % k for k in range(c)) or '0', '+'.join('h%d' % (k * n[0]) for k in range(r)) or '0')
                          for r in range(len(rows)) for c in range(n[r]))
        graph = ''.join('[%d:v]' % i for i in range(sum(n))) + 'xstack=inputs=%d:layout=%s,format=yuv420p' % (sum(n), layout)
    run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', graph, '-c:v', 'libx264', '-crf', '18', '-r', '30', out])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file')
    ap.add_argument('--set', required=True)
    ap.add_argument('--out', required=True, help='the folder for the results (data/destiny/port/validation/WEAPON)')
    ap.add_argument('--clips', help='the folder with the HKX clips (default: data/destiny/port/out/WEAPON)')
    ap.add_argument('--work', help='the work folder of the converter (default: data/destiny/port/work/WEAPON)')
    ap.add_argument('--only', action='append', default=[])
    ap.add_argument('--resume', action='store_true',
                    help='a clip of the file that has its NAME.txt keeps its files: only its line of summary.txt is made again')
    ap.add_argument('--no-video', action='store_true', help='the numbers only: NAME.txt and summary.txt')
    ap.add_argument('--left-hand', action='store_true',
                    help='a gun for two hands: also NAME_left_hand.mp4, the left hand from the side of its thumb and from its palm')
    a = ap.parse_args()
    with open(a.set, 'rb') as f:
        data = tomllib.load(f)
    name = os.path.splitext(os.path.basename(a.file))[0].replace('_first_person', '')
    work = os.path.abspath(a.work or os.path.join(DATA, 'work', name))
    clips = os.path.abspath(a.clips or os.path.join(DATA, 'out', name))
    parts = os.path.join(work, 'parts.json')
    template = data.get('template', 'revolver44')
    from d2template import Template
    vanilla = Template(template).clip_folder(os.path.join(DATA, 'rig'))        # the vanilla clips of the template
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(os.path.join(work, 'validate'), exist_ok=True)      # the folder of the contact files (with --no-video no picture makes it)
    os.environ['D2FO4_WORK'] = work
    first = {}
    for target, clip in data.get('clips', {}).items():
        first.setdefault(clip, target)
    others = {clip: [t for t, c in data['clips'].items() if c == clip and t != target] for clip, target in first.items()}
    # an automatic fire clip is made from the clip of one shot ([auto]): it has no source of its own
    made = list(data.get('synth', {})) + list(data.get('static', {})) + list(data.get('auto', {}))
    summary = []
    for clip, target in first.items():
        if a.only and target not in a.only:
            continue
        hkx = os.path.join(clips, target + '.hkx')
        pictures = os.path.join(work, 'validate', target)
        print('[validate] %s (%s)' % (target, clip), flush=True)
        count = fo4clip.load_poses(hkx)[0].shape[0]
        contact = os.path.join(work, 'validate', target + '_contact.json')
        text = os.path.join(a.out, target + '.txt')
        if a.resume and os.path.exists(text) and os.path.exists(contact):
            gun = table = fingers = open(text).read()
        else:
            # the views of the grip: each frame of a short clip, each second frame of a longer one
            step = 1 if count <= 64 else 2
            p = os.path.join(pictures, target + '_f*_')
            if not a.no_video:
                run(blender('render.py', '--glb', a.file, '--clip', clip, '--poses', hkx, '--parts', parts, '--out', pictures, '--tag', target, '--template', template,
                            '--frames', 'all', '--views', 'fp', '--kinds', 'src,fo4', '--size', '960x540'))
                run(blender('render.py', '--glb', a.file, '--clip', clip, '--poses', hkx, '--parts', parts, '--out', pictures, '--tag', target, '--template', template,
                            '--frames', ','.join(str(f) for f in range(0, count, step)), '--views', 'gun_left,gun_right', '--kinds', 'src,fo4',
                            '--close-size', '540x540'))
                video(os.path.join(a.out, target + '_first_person.mp4'), 30, [p + 'fp_src.png', p + 'fp_fo4.png'])
                video(os.path.join(a.out, target + '_gun.mp4'), 15, [p + 'gun_left_src.png', p + 'gun_left_fo4.png'],
                      [p + 'gun_right_src.png', p + 'gun_right_fo4.png'])
            if a.left_hand and not a.no_video:
                run(blender('render.py', '--glb', a.file, '--clip', clip, '--poses', hkx, '--parts', parts, '--out', pictures, '--tag', target, '--template', template,
                            '--frames', ','.join(str(f) for f in range(0, count, step)), '--views', 'l_thumb,l_palm', '--kinds', 'src,fo4',
                            '--close-size', '540x540'))
                video(os.path.join(a.out, target + '_left_hand.mp4'), 15, [p + 'l_thumb_src.png', p + 'l_thumb_fo4.png'],
                      [p + 'l_palm_src.png', p + 'l_palm_fo4.png'])
            gun = run([sys.executable, os.path.join(HERE, 'gun.py'), a.file, clip, parts, hkx])
            contact = os.path.join(work, 'validate', target + '_contact.json')
            run(blender('contact.py', '--glb', a.file, '--bake', os.path.join(work, 'bake', clip + '.npz'), '--poses', hkx,
                        '--parts', parts, '--frames', 'all', '--quiet', '--out', contact))
            table = run([sys.executable, os.path.join(HERE, 'contact_table.py'), contact])
            fingers = run([sys.executable, os.path.join(HERE, 'fingers.py'), hkx, '--bake', os.path.join(work, 'bake', clip + '.npz'),
                           '--vanilla', vanilla])
            with open(os.path.join(a.out, target + '.txt'), 'w') as f:
                f.write('%s from the clip %s%s\n\n== The gun and the wrists against the source (check/gun.py)\n%s\n== Hand vertices inside the gun (check/contact.py)\n%s\n'
                        '== Finger joints (check/fingers.py)\n%s' % (target, clip, (' (also ' + ', '.join(others[clip]) + ')') if others[clip] else '', gun, table, fingers))
        c = json.load(open(contact))
        frames = len(c['frames'])
        src = 100.0 * sum(r['inside'] for r in c['source']) / (c['source_vertices'] * frames)
        res = 100.0 * sum(r['inside'] for r in c['result']) / (c['result_vertices'] * frames)
        g = re.search(r'gun: largest distance .*? ([0-9.]+) units', gun)
        back = re.search(r'joints that bend to the back.*: (.*)', fingers).group(1)
        jump = re.search(r'largest turn in one frame that the source does not have: ([0-9.]+)', fingers)
        deeper = re.search(r'bones of the result that go deeper.*: (.*)', table).group(1)
        summary.append('%-22s %-17s %4d frames | gun %s units | vertices in the gun: source %4.1f %%, result %4.1f %% | deeper than the source: %s | '
                       'joints bent back: %s | largest finger turn in one frame that the source does not have: %s degrees' % (
                           target, clip, frames, g.group(1) if g else '?', src, res, deeper, back, jump.group(1) if jump else '?'))
    reference = next(iter(first), None)
    for target in made:
        if a.only and target not in a.only:
            continue
        hkx = os.path.join(clips, target + '.hkx')
        pictures = os.path.join(work, 'validate', target)
        kind = 'automatic fire from the clip of one shot' if target in data.get('auto', {}) else 'vanilla weapon motion'
        print('[validate] %s (%s)' % (target, kind), flush=True)
        if not a.no_video:
            run(blender('render.py', '--glb', a.file, '--clip', reference, '--poses', hkx, '--parts', parts, '--out', pictures, '--tag', target, '--template', template,
                        '--frames', 'all', '--views', 'fp', '--kinds', 'fo4', '--size', '960x540'))
            p = os.path.join(pictures, target + '_f*_')
            video(os.path.join(a.out, target + '_first_person.mp4'), 30, [p + 'fp_fo4.png'])
        summary.append('%-22s %s: the result only' % (target, kind))
    # With --only, the lines of the other clips stay as they are.
    path = os.path.join(a.out, 'summary.txt')
    lines = {}
    if a.only and os.path.exists(path):
        for line in open(path).read().splitlines():
            if line.strip():
                lines[line.split()[0]] = line
    for line in summary:
        lines[line.split()[0]] = line
    order = list(first.values()) + made
    with open(path, 'w') as f:
        f.write('\n'.join(lines[t] for t in order if t in lines) + '\n')
    print('\n'.join(summary))


if __name__ == '__main__':
    main()
