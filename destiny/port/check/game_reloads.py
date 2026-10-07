#!/usr/bin/env python3
"""Game test of the reload clips of a weapon that has one clip for each count of rounds.

    ./port destiny game reloads --session ID --weapon TheChaperone --capacity 6 --out DIR
    python3 destiny/port/check/game_reloads.py ...          (the same program with no ./port)

The game is a session of `esx probe start` (check/game_record.py says more). For each view
(first person, third person) and each count of rounds in the gun from 0 to the capacity less
one, the program sets the count, starts a reload and waits for its end. It writes the clip
that the game started (from the trace of the probe), the time from the start to the event
reloadEnd, the count of rounds after the reload and the sounds that the clips started (the
events SoundPlay). Output in DIR: reloads.json.
The setting `esx` names the esx program (ESX_BIN, then data/config.toml, then esx in the PATH).

The probe has one session at a time for the whole computer. Look at `esx probe status` before
a start, and stop only the session ID that your start command printed
(destiny/port/check/third_session.sh keeps that ID).
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


def call(session, op, args=None, timeout=20):
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
    return answer.get('data') if answer.get('ok') else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--weapon', required=True)
    ap.add_argument('--capacity', type=int, required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    s = a.session
    call(s, 'camera.set', {'view': 'first'})
    time.sleep(1.0)
    call(s, 'item.give', {'form': a.weapon, 'equip': True}, 30)
    call(s, 'weapon.draw', {'drawn': True}, 30)
    time.sleep(3.0)
    rows, failed = [], 0
    for view, owner in (('first', 'player_1st'), ('third', 'player_3rd')):
        call(s, 'camera.set', {'view': view})
        time.sleep(2.0)
        for loaded in range(a.capacity):
            call(s, 'ammo.set', {'loaded': loaded, 'reserve': 100})
            time.sleep(0.5)
            seq = (call(s, 'game.state') or {}).get('seq', 0)
            start = time.time()
            ok = call(s, 'action.run', {'action': 'ActionReload'})
            end = call(s, 'anim.wait', {'event': 'reloadEnd'}, 40)
            seconds = round(time.time() - start, 2)
            time.sleep(1.0)
            after = call(s, 'ammo.get') or {}
            trace = call(s, 'anim.trace', {'since': seq, 'limit': 2048}) or {}
            clips = [e.get('node') for e in trace.get('events', []) if e.get('kind') == 'clip_start' and e.get('owner') == owner
                     and str(e.get('node', '')).lower().startswith('wpnreload')]
            sounds = [e.get('payload') for e in trace.get('events', []) if e.get('kind') == 'event' and e.get('tag') == 'SoundPlay']
            row = {'view': view, 'rounds_before': loaded, 'reload_accepted': bool(ok and ok.get('accepted')), 'reload_end': end is not None,
                   'seconds': seconds, 'rounds_after': after.get('loaded'), 'clips': clips, 'sounds': sounds}
            rows.append(row)
            good = row['reload_accepted'] and row['reload_end'] and row['rounds_after'] == a.capacity
            failed += 0 if good else 1
            count = {}
            for name in sounds:
                count[name] = count.get(name, 0) + 1
            print('%-5s person, %d rounds: clip %-22s %5.2f s to reloadEnd, %s rounds after, sounds: %s%s' % (
                view, loaded, ', '.join(clips) or '-', seconds, after.get('loaded'),
                ', '.join('%d x %s' % (n, name) for name, n in count.items()) or 'none', '' if good else '   FAILED'), flush=True)
    call(s, 'camera.set', {'view': 'first'})
    with open(os.path.join(a.out, 'reloads.json'), 'w') as f:
        json.dump(rows, f, indent=1)
    print('reloads %d failed %d' % (len(rows), failed))


if __name__ == '__main__':
    main()
