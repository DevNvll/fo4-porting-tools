#!/usr/bin/env python3
"""Game pictures of a weapon at the hip and in the sights.

    ./port destiny game sight --session ID --weapon TheChaperone --capacity 6 --out DIR
    python3 destiny/port/check/game_sight.py ...          (the same program with no ./port)

The steps: first-person view, give and equip the weapon, draw, a picture at the hip
(hip.png), the action ActionSighted, a picture in the sights 4 s later (sighted.png), leave
the sights. The pictures have no HUD. Use them to examine the sight glass, the reticle and
the two hands in the hold pose: `esx render` does not draw an effect material.

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


def call(session, op, args=None, timeout=20):
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
    ap = argparse.ArgumentParser(description='Game pictures of a weapon at the hip and in the sights.')
    ap.add_argument('--session', required=True)
    ap.add_argument('--weapon', required=True, help='the editor ID of the weapon')
    ap.add_argument('--capacity', type=int, required=True, help='the rounds in the gun')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    s = a.session
    call(s, 'camera.set', {'view': 'first'})
    time.sleep(1)
    call(s, 'item.give', {'form': a.weapon, 'equip': True}, 30)
    call(s, 'ammo.set', {'loaded': a.capacity, 'reserve': 200})
    call(s, 'weapon.draw', {'drawn': True}, 30)
    time.sleep(4)
    shot = call(s, 'screenshot.take', {'name': a.weapon + '_hip', 'hud': False, 'wait_ms': 200})
    if not shot:
        raise SystemExit('the probe made no picture at the hip')
    shutil.copyfile(shot['path'], os.path.join(a.out, 'hip.png'))
    call(s, 'action.run', {'action': 'ActionSighted'})
    time.sleep(4)
    shot = call(s, 'screenshot.take', {'name': a.weapon + '_sighted', 'hud': False, 'wait_ms': 200})
    if not shot:
        raise SystemExit('the probe made no picture in the sights')
    shutil.copyfile(shot['path'], os.path.join(a.out, 'sighted.png'))
    call(s, 'anim.send_event', {'event': 'rifleSightedEnd', 'target': 'player'})
    time.sleep(1.5)
    print('done', a.out)


if __name__ == '__main__':
    sys.exit(main())
