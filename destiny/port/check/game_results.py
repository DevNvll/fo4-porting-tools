#!/usr/bin/env python3
"""Copy the results of the game tests of a weapon into its validation folder, and print the numbers.

    ./port destiny game results --out data/destiny/port/validation/NAME [--record DIR] [--third DIR]
        [--sight DIR] [--reloads DIR --title "The Chaperone"]
    python3 destiny/port/check/game_results.py ...          (the same program with no ./port)

Each DIR is the output folder of one game test program (destiny/port/check/game_all.py makes
the four folders of a weapon). The files that the program writes into the folder of --out:

    --record DIR    of game_record.py: game_test.mp4, game_test.log, game_test_steps.json. It prints
                    the count of ops and of failed ops, the rounds in the gun at each `ammo.get`,
                    the first-person clips that started (from trace.json) and the time of each step.
    --third DIR     of game_third.py: game_test_third_person.mp4 (when the test has a recording),
                    game_test_third_person_steps.json, and third_person_reload_game.jpg (the
                    pictures of the three sides, at half size). It prints the count of ops and of
                    failed ops, and the rounds before and after each reload.
    --sight DIR     of game_sight.py: red_dot_game.jpg (the picture in the sights, its center
                    2.4 times larger, and the picture at the hip). It prints the place of the
                    reddest pixel near the center of the picture (the dot of a red dot sight;
                    the center of a picture of 1280 x 720 is 640, 360).
    --reloads DIR   of game_reloads.py: game_test_reloads.json and game_test_reloads.txt (a
                    table: the clip, the time to reloadEnd, the rounds, the shell sounds and
                    the lever sounds of each reload). --title is the name of the weapon in
                    the first line of the table.

This program does not start the game: it reads the result folders.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys


def seconds(video):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', video], capture_output=True, text=True)
    return float(r.stdout) if r.returncode == 0 and r.stdout.strip() else float('nan')


def record(folder, out):
    shutil.copyfile(os.path.join(folder, 'record.mp4'), os.path.join(out, 'game_test.mp4'))
    shutil.copyfile(os.path.join(folder, 'record.log'), os.path.join(out, 'game_test.log'))
    shutil.copyfile(os.path.join(folder, 'steps.json'), os.path.join(out, 'game_test_steps.json'))
    steps = json.load(open(os.path.join(folder, 'steps.json')))
    ammo = [(s['video_seconds'], s['answer'].get('loaded')) for s in steps if s['op'] == 'ammo.get' and s['ok']]
    # steps.json does not have the last op (the read of the trace)
    print('first person: ops', len(steps) + 1, 'failed', sum(1 for s in steps if not s['ok']), 'ammo', ammo,
          '| video %.1f s' % seconds(os.path.join(out, 'game_test.mp4')))
    trace = json.load(open(os.path.join(folder, 'trace.json')))
    names = []
    for e in trace['events']:
        if e.get('kind') == 'clip_start' and e.get('owner') == 'player_1st':
            name = e.get('node', '')
            if name.startswith('WPN') and 'Add' not in name:
                base = name.rstrip('0123456789') if not name.startswith('WPNReload') else name
                for end in ('SlowWalk', 'Fast'):
                    if base.endswith(end) and base != 'WPNEquipFast':
                        base = base[:-len(end)]
                if base not in names:
                    names.append(base)
    print('   clips', len(names), sorted(names))
    print('   steps:', [(s['video_seconds'], (s['args'] or {}).get('action') or (s['args'] or {}).get('event') or (s['args'] or {}).get('view')
                         or (s['args'] or {}).get('drawn')) for s in steps
                        if s['op'] in ('action.run', 'anim.send_event', 'weapon.draw', 'camera.set') and (s['args'] or {}).get('action') != 'ActionRightRelease'])


def third(folder, out):
    from PIL import Image
    video = os.path.join(folder, 'record.mp4')
    if os.path.isfile(video):
        shutil.copyfile(video, os.path.join(out, 'game_test_third_person.mp4'))
    shutil.copyfile(os.path.join(folder, 'steps.json'), os.path.join(out, 'game_test_third_person_steps.json'))
    sheets = [Image.open(os.path.join(folder, 'sheet_%s.jpg' % side)).convert('RGB') for side in ('right', 'front', 'left')]
    w, h = max(s.size[0] for s in sheets), sum(s.size[1] for s in sheets)
    sheet, y = Image.new('RGB', (w, h)), 0
    for s in sheets:
        sheet.paste(s, (0, y))
        y += s.size[1]
    sheet.resize((w // 2, h // 2), Image.LANCZOS).save(os.path.join(out, 'third_person_reload_game.jpg'), quality=86)
    steps = json.load(open(os.path.join(folder, 'steps.json')))
    print('third person: ops', sum(1 for s in steps if 'op' in s), 'failed', sum(1 for s in steps if s.get('ok') is False),
          'rounds before and after each reload', [(s['before'], s['after']) for s in steps if 'before' in s],
          ('| video %.1f s' % seconds(video)) if os.path.isfile(video) else '| no video')


def sight(folder, out):
    import numpy as np
    from PIL import Image
    a = Image.open(os.path.join(folder, 'sighted.png')).convert('RGB')
    b = Image.open(os.path.join(folder, 'hip.png')).convert('RGB')
    sheet = Image.new('RGB', (1280 + 720, 720 + 405))
    sheet.paste(a, (0, 0))
    sheet.paste(a.crop((490, 210, 790, 510)).resize((720, 720), Image.LANCZOS), (1280, 0))
    sheet.paste(b.resize((720, 405), Image.LANCZOS), (0, 720))
    sheet.save(os.path.join(out, 'red_dot_game.jpg'), quality=90)
    x = np.asarray(a).astype(float)
    part = x[348:372, 628:652]
    red = part[..., 0] - np.maximum(part[..., 1], part[..., 2])
    yy, xx = np.unravel_index(np.argmax(red), red.shape)
    print('sight: the reddest pixel near the center is at (%d, %d)' % (xx + 628, yy + 348))


def reloads(folder, out, title):
    rows = json.load(open(os.path.join(folder, 'reloads.json')))
    shutil.copyfile(os.path.join(folder, 'reloads.json'), os.path.join(out, 'game_test_reloads.json'))
    lines = ['The reload clips of %s in the game (check/game_reloads.py): one reload for each count of rounds, in each view.' % title, '',
             'view    rounds before  clip        seconds to reloadEnd  rounds after  shell sounds  lever sounds']
    for r in rows:
        body = [c for c in r['clips'] if c != 'WPNReload'] or r['clips']
        lines.append('%-7s %-14d %-11s %-21.2f %-13s %-13d %d' % (
            r['view'], r['rounds_before'], body[0] if body else '-', r['seconds'], r['rounds_after'],
            sum(1 for s in r['sounds'] if s.endswith('ReloadMagIn')), sum(1 for s in r['sounds'] if 'ReloadBolt' in s)))
    with open(os.path.join(out, 'game_test_reloads.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines[2:]))


def main():
    ap = argparse.ArgumentParser(description='Copy the results of the game tests of a weapon into its validation folder, and print the numbers.')
    ap.add_argument('--out', required=True, help='the validation folder of the weapon (data/destiny/port/validation/NAME)')
    ap.add_argument('--record', metavar='DIR', help='the output folder of game_record.py')
    ap.add_argument('--third', metavar='DIR', help='the output folder of game_third.py')
    ap.add_argument('--sight', metavar='DIR', help='the output folder of game_sight.py')
    ap.add_argument('--reloads', metavar='DIR', help='the output folder of game_reloads.py')
    ap.add_argument('--title', default='the weapon', help='the name of the weapon in the first line of game_test_reloads.txt')
    a = ap.parse_args()
    if not (a.record or a.third or a.sight or a.reloads):
        raise SystemExit('give one or more of --record, --third, --sight, --reloads')
    os.makedirs(a.out, exist_ok=True)
    if a.record:
        record(a.record, a.out)
    if a.third:
        third(a.third, a.out)
    if a.sight:
        sight(a.sight, a.out)
    if a.reloads:
        reloads(a.reloads, a.out, a.title)


if __name__ == '__main__':
    sys.exit(main())
