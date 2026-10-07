#!/usr/bin/env python3
"""Print the clips and the events of one reload in the game, from the trace of the probe.

    ./port destiny game trace --session ID --weapon TheChaperone --loaded 3 --view third
    python3 destiny/port/check/game_trace.py ...          (the same program with no ./port)

The steps: give and equip the weapon, draw, set the view, set the rounds in the gun, start a
reload, wait for the event reloadEnd, then read the trace. The program prints each start and
end of a clip whose data has the text Reload, and each event after the first of them, with
the time from that first line (in frames of 30 for each second), the owner (player_1st or
player_3rd), and the name. Use it to find a reload that ends early or a sound of another
clip: a game test that passes does not show these faults.

The game is a session of `esx probe start` (destiny/port/check/game_record.py says more;
destiny/port/check/third_session.sh starts one). The probe has one session at a time for the
whole computer. Look at `esx probe status` before a start, and stop only the session ID that
your start command printed. The setting `esx` names the esx program (ESX_BIN, then
data/config.toml, then esx in the PATH).
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402


def call(session, op, args=None, timeout=40):
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
    ap = argparse.ArgumentParser(description='Print the clips and the events of one reload in the game.')
    ap.add_argument('--session', required=True)
    ap.add_argument('--weapon', required=True, help='the editor ID of the weapon')
    ap.add_argument('--loaded', type=int, required=True, help='the rounds in the gun before the reload')
    ap.add_argument('--view', choices=('first', 'third'), default='first')
    a = ap.parse_args()
    s = a.session
    call(s, 'camera.set', {'view': 'first'})
    time.sleep(1)
    call(s, 'item.give', {'form': a.weapon, 'equip': True})
    call(s, 'weapon.draw', {'drawn': True})
    time.sleep(3)
    call(s, 'camera.set', {'view': a.view})
    time.sleep(2)
    call(s, 'ammo.set', {'loaded': a.loaded, 'reserve': 100})
    time.sleep(0.5)
    state = call(s, 'game.state')
    if not state:
        raise SystemExit('the game of the session %s gives no state' % s)
    call(s, 'action.run', {'action': 'ActionReload'})
    call(s, 'anim.wait', {'event': 'reloadEnd'}, 40)
    time.sleep(2.0)
    trace = call(s, 'anim.trace', {'since': state['seq'], 'limit': 4096}) or {'events': []}
    first = None
    for e in trace['events']:
        if e.get('kind') in ('clip_start', 'clip_end') and 'Reload' in json.dumps(e):
            first = first or e['frame']
            print('%6.2f frames' % ((e['frame'] - first) / 4.0), e['kind'], e.get('owner'), e.get('node'))
        elif e.get('kind') == 'event' and first and e.get('tag') not in ('00NextClip',):
            print('%6.2f frames' % ((e['frame'] - first) / 4.0), 'event', e.get('owner'), e.get('tag'), e.get('payload'))
    call(s, 'camera.set', {'view': 'first'})


if __name__ == '__main__':
    sys.exit(main())
