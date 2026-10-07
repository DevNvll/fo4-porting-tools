#!/usr/bin/env python3
"""Game pictures of the gun in a third-person reload at a slow game speed.

    ./port destiny game shots --session ID --weapon TheChaperone --loaded 3 --from 0.5 --to 2.5 --count 12 --out DIR
    python3 destiny/port/check/game_shots.py ...          (the same program with no ./port)

The weapon must be in the hand of the player (destiny/port/check/game_record.py or
game_sight.py gives and draws it). The steps: the third-person view, the camera at one side
of the weapon, set the rounds in the gun, the game speed of --speed, start a reload, then
COUNT pictures at equal steps from T0 to T1 (seconds of the reload at the normal speed). A
picture is DIR/rLOADED_NN_TIMEs.png. Use it to examine a part of the gun in a reload (the
lever of The Chaperone), which the pictures of game_third.py show too small.

The game is a session of `esx probe start` (destiny/port/check/game_record.py says more;
destiny/port/check/third_session.sh starts one). The probe has one session at a time for the
whole computer. Look at `esx probe status` before a start, and stop only the session ID that
your start command printed. The setting `esx` names the esx program (ESX_BIN, then
data/config.toml, then esx in the PATH).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402


def call(session, op, args=None, timeout=60):
    """Send one op to the probe. Returns its data, or None when it fails."""
    cmd = [paths.require('esx'), 'probe', 'call', op, '--session', session, '--timeout', str(timeout), '--format', 'json']
    if args is not None:
        cmd += ['--args', json.dumps(args)]
    for _ in range(8):
        r = subprocess.run(cmd, capture_output=True, text=True)
        try:
            answer = json.loads(r.stdout)
        except Exception:
            answer = {'ok': False, 'error': {'raw': (r.stdout + r.stderr)[-300:]}}
        # the probe has one connection: an op that comes while the op before still has it can be sent again
        if answer.get('ok') or not (answer.get('error') or {}).get('details', {}).get('retryable'):
            break
        time.sleep(0.5)
    if not answer.get('ok'):
        print('FAILED', op, args, json.dumps(answer.get('error'))[:300], file=sys.stderr)
    return answer.get('data') if answer.get('ok') else None


def main():
    ap = argparse.ArgumentParser(description='Game pictures of the gun in a third-person reload at a slow game speed.')
    ap.add_argument('--session', required=True)
    ap.add_argument('--weapon', help='the editor ID of the weapon: the program gives and draws it (default: the weapon in the hand)')
    ap.add_argument('--loaded', type=int, required=True, help='the rounds in the gun before the reload')
    ap.add_argument('--from', dest='start', type=float, required=True, metavar='T0', help='the time of the first picture (s of the reload)')
    ap.add_argument('--to', dest='end', type=float, required=True, metavar='T1', help='the time of the last picture')
    ap.add_argument('--count', type=int, required=True, help='the count of pictures')
    ap.add_argument('--out', required=True)
    ap.add_argument('--speed', type=float, default=0.1, help='the game speed in the reload (default 0.1)')
    ap.add_argument('--yaw', type=float, default=-80.0, help='the camera about the weapon, degrees (default -80: the left side)')
    ap.add_argument('--pitch', type=float, default=0.0)
    ap.add_argument('--distance', type=float, default=70.0, help='the distance of the camera from the weapon (default 70)')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    s = a.session
    if a.weapon:
        call(s, 'camera.set', {'view': 'first'})
        time.sleep(1)
        call(s, 'item.give', {'form': a.weapon, 'equip': True})
        call(s, 'weapon.draw', {'drawn': True})
        time.sleep(3)
    call(s, 'camera.set', {'view': 'third'})
    time.sleep(2)
    call(s, 'camera.orbit', {'target': 'weapon', 'yaw': a.yaw, 'pitch': a.pitch, 'distance': a.distance})
    time.sleep(1)
    call(s, 'ammo.set', {'loaded': a.loaded, 'reserve': 100})
    time.sleep(0.5)
    call(s, 'console.run', {'command': 'sgtm %g' % a.speed})
    start = time.time()
    call(s, 'action.run', {'action': 'ActionReload'})
    try:
        for i in range(a.count):
            t = a.start + (a.end - a.start) * i / max(a.count - 1, 1)
            wait = start + t / a.speed - time.time()
            if wait > 0:
                time.sleep(wait)
            shot = call(s, 'screenshot.take', {'name': 'shots_%d_%02d' % (a.loaded, i), 'hud': False, 'wait_ms': 0})
            now = (time.time() - start) * a.speed
            if shot:
                shutil.copyfile(shot['path'], os.path.join(a.out, 'r%d_%02d_%.2fs.png' % (a.loaded, i, now)))
    finally:
        call(s, 'console.run', {'command': 'sgtm 1'})
        time.sleep(3)
        call(s, 'camera.orbit', {'reset': True})
        call(s, 'camera.set', {'view': 'first'})
    print('done', a.out)


if __name__ == '__main__':
    sys.exit(main())
