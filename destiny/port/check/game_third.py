#!/usr/bin/env python3
"""Game test of the third-person clips of a weapon: pictures, and with --record a video.

    ./port destiny game third --session ID --weapon Khvostov --capacity 30 --out DIR [--record]
    python3 destiny/port/check/game_third.py ...          (the same program with no ./port)

The game is a session of `esx probe start` (a test copy of Fallout 4 in a headless gamescope;
the installed game does not change). The program sends no keyboard or mouse input: each step
is an op of the probe. The steps: give and equip the weapon, draw it, the third-person view,
then for each camera place (the right side, the front, the left side of the weapon): a
picture of the idle, a short burst, and a reload at one fifth of the game speed with a
picture at each step. With --record the program also records the game picture (as
check/game_record.py does), with one reload at the normal speed for each camera place.

Output in DIR: SIDE_idle.png, SIDE_NN.png, sheet_SIDE.jpg (the pictures of one side), steps.json,
trace.json (the clips that started), and with --record record.mp4.
The setting `esx` names the esx program (ESX_BIN, then data/config.toml, then esx in the PATH).

The probe has one session at a time for the whole computer. Look at `esx probe status` before
a start, and stop only the session ID that your start command printed
(destiny/port/check/third_session.sh keeps that ID).
"""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402
VIEWS = (('right', 75, 8), ('front', 20, 10), ('left', -70, 8))


class Game:
    def __init__(self, session):
        self.session, self.steps, self.start = session, [], time.time()

    def call(self, op, args=None, timeout=20, note=''):
        cmd = [paths.require('esx'), 'probe', 'call', op, '--session', self.session, '--timeout', str(timeout), '--format', 'json']
        if args is not None:
            cmd += ['--args', json.dumps(args)]
        at = round(time.time() - self.start, 2)
        for attempt in range(8):
            r = subprocess.run(cmd, capture_output=True, text=True)
            try:
                answer = json.loads(r.stdout)
            except Exception:
                answer = {'ok': False, 'raw': (r.stdout + r.stderr)[-500:]}
            # the probe has one connection: an op that comes while the op before still has it can be sent again
            if answer.get('ok') or not (answer.get('error') or {}).get('details', {}).get('retryable'):
                break
            time.sleep(0.5)
        ok = bool(answer.get('ok'))
        data = answer.get('data') if ok else answer.get('error')
        self.steps.append({'seconds': at, 'op': op, 'args': args, 'ok': ok, 'note': note, 'answer': data})
        return data if ok else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--weapon', required=True)
    ap.add_argument('--capacity', type=int, default=30)
    ap.add_argument('--distance', type=float, default=150.0, help='the distance of the camera from the weapon')
    ap.add_argument('--pictures', type=int, default=11, help='the count of pictures of a slow reload')
    ap.add_argument('--speed', type=float, default=0.2, help='the game speed in the reload with pictures')
    ap.add_argument('--record', action='store_true')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    g = Game(a.session)
    state = g.call('game.state')
    if not state or state.get('state') != 'in_game':
        raise SystemExit('the game of the session %s is not ready' % a.session)
    seq = state.get('seq', 0)
    recorder = None
    if a.record:
        raw = os.path.join(a.out, 'record.mkv')
        recorder = subprocess.Popen(
            ['gst-launch-1.0', '-e', 'pipewiresrc', 'target-object=gamescope', 'do-timestamp=true', '!', 'videoconvert', '!',
             'video/x-raw,format=I420', '!', 'videorate', '!', 'video/x-raw,framerate=60/1', '!',
             'x264enc', 'speed-preset=veryfast', 'bitrate=12000', 'key-int-max=60', '!', 'matroskamux', '!', 'filesink', 'location=' + raw],
            stdout=open(os.path.join(a.out, 'recorder.log'), 'w'), stderr=subprocess.STDOUT)
        time.sleep(2.0)
        g.start = time.time()
    paths = {}
    try:
        g.call('console.run', {'command': 'setini "fAutoVanityModeDelay:Camera" 100000'})
        g.call('camera.set', {'view': 'first'})
        time.sleep(1.0)
        g.call('item.give', {'form': a.weapon, 'equip': True}, timeout=30, note='give and equip')
        g.call('ammo.set', {'loaded': a.capacity, 'reserve': 300})
        g.call('weapon.draw', {'drawn': True}, timeout=30, note='draw')
        time.sleep(3.0)
        g.call('camera.set', {'view': 'third'}, note='third person')
        time.sleep(2.0)
        for side, yaw, pitch in VIEWS:
            g.call('camera.orbit', {'target': 'weapon', 'yaw': yaw, 'pitch': pitch, 'distance': a.distance}, note='camera: ' + side)
            time.sleep(1.5)
            shot = g.call('screenshot.take', {'name': '%s_idle' % side, 'hud': False, 'wait_ms': 200})
            paths[(side, 'idle')] = shot and shot.get('path')
            g.call('action.run', {'action': 'ActionFireAuto'}, note='burst')
            time.sleep(0.3)
            g.call('action.run', {'action': 'ActionRightRelease'})
            time.sleep(1.5)
            shot = g.call('screenshot.take', {'name': '%s_ready' % side, 'hud': False, 'wait_ms': 100})
            paths[(side, 'ready')] = shot and shot.get('path')
            if a.record:
                g.call('action.run', {'action': 'ActionReload'}, note='reload, %s' % side)
                g.call('anim.wait', {'event': 'reloadEnd'}, timeout=20)
                time.sleep(1.5)
                g.call('action.run', {'action': 'ActionFireAuto'})
                time.sleep(0.3)
                g.call('action.run', {'action': 'ActionRightRelease'})
                time.sleep(1.5)
            before = g.call('ammo.get')
            g.call('console.run', {'command': 'sgtm %g' % a.speed}, note='slow motion')
            g.call('action.run', {'action': 'ActionReload'}, note='reload, slow, %s' % side)
            for i in range(1, a.pictures + 1):
                shot = g.call('screenshot.take', {'name': '%s_%02d' % (side, i), 'hud': False, 'wait_ms': 20})
                paths[(side, '%02d' % i)] = shot and shot.get('path')
            g.call('console.run', {'command': 'sgtm 1'}, note='normal speed')
            time.sleep(2.5)
            after = g.call('ammo.get')
            g.steps.append({'note': 'ammunition in the reload, %s' % side, 'before': before and before.get('loaded'), 'after': after and after.get('loaded')})
        g.call('camera.orbit', {'reset': True})
        g.call('camera.set', {'view': 'first'})
        time.sleep(1.0)
    finally:
        if recorder is not None:
            recorder.send_signal(signal.SIGINT)
            try:
                recorder.wait(timeout=30)
            except subprocess.TimeoutExpired:
                recorder.kill()
    trace = g.call('anim.trace', {'since': seq, 'limit': 4096}, timeout=20)
    with open(os.path.join(a.out, 'steps.json'), 'w') as f:
        json.dump(g.steps, f, indent=1)
    with open(os.path.join(a.out, 'trace.json'), 'w') as f:
        json.dump(trace, f, indent=1)
    from PIL import Image
    for (side, tag), path in paths.items():
        if path and os.path.exists(path):
            shutil.copyfile(path, os.path.join(a.out, '%s_%s.png' % (side, tag)))
    for side, _, _ in VIEWS:
        tags = ['idle', 'ready'] + ['%02d' % i for i in range(1, a.pictures + 1)]
        tiles = [Image.open(os.path.join(a.out, '%s_%s.png' % (side, t))).convert('RGB').crop((340, 40, 940, 640)).resize((400, 400), Image.LANCZOS)
                 for t in tags if os.path.exists(os.path.join(a.out, '%s_%s.png' % (side, t)))]
        cols = 7
        sheet = Image.new('RGB', (400 * cols, 400 * ((len(tiles) + cols - 1) // cols)))
        for i, t in enumerate(tiles):
            sheet.paste(t, ((i % cols) * 400, (i // cols) * 400))
        sheet.save(os.path.join(a.out, 'sheet_%s.jpg' % side), quality=88)
    if a.record:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(a.out, 'record.mkv'), '-c:v', 'libx264', '-crf', '20',
                        '-pix_fmt', 'yuv420p', '-r', '60', os.path.join(a.out, 'record.mp4')], check=True)
        os.remove(os.path.join(a.out, 'record.mkv'))
    failed = [s for s in g.steps if s.get('ok') is False]
    print('ops', len([s for s in g.steps if 'op' in s]), 'failed', [(s['op'], s['args']) for s in failed])
    for s in g.steps:
        if 'before' in s:
            print(s['note'], s['before'], '->', s['after'])


if __name__ == '__main__':
    main()
