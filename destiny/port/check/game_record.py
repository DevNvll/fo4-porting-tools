#!/usr/bin/env python3
"""Record a game test of a weapon: a video of the game picture while the probe of esx runs the weapon.

    ./port destiny game record --session ID --weapon TheLastWord --capacity 8 --out DIR
    ./port destiny game record --session ID --weapon Khvostov --capacity 30 --auto --out DIR
    python3 destiny/port/check/game_record.py ...          (the same program with no ./port)

The game is a session of `esx probe start` (a test copy of Fallout 4 in a headless gamescope;
the installed game does not change). gamescope gives its picture as the PipeWire video node
`gamescope`, and GStreamer records that node (1280 x 720, 60 frames for each second). The
program sends no keyboard or mouse input: each step is an op of the probe (`esx probe call`).

The steps: first-person view, give and equip the weapon, draw, idle, three shots, reload,
aim, two shots in the sights, leave the sights, gun down and ready, the sprint events, put
away, draw, a reload and a shot at one quarter of the game speed, then the third-person view
with a shot and a reload. With --auto (an automatic weapon) each group of shots is a burst:
the trigger stays down for a time.

Output in DIR: record.mp4 (the video), steps.json (each op with its answer and its time in
the video) and trace.json (each clip and event that started, from the trace of the probe).
The setting `esx` names the esx program (ESX_BIN, then data/config.toml, then esx in the PATH).

The probe has one session at a time for the whole computer. Look at `esx probe status` before
a start, and stop only the session ID that your start command printed
(destiny/port/check/third_session.sh keeps that ID).
"""
import argparse
import json
import os
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


class Game:
    def __init__(self, session, log):
        self.session, self.log, self.start = session, log, None
        self.steps = []

    def call(self, op, args=None, timeout=10, note=''):
        cmd = [paths.require('esx'), 'probe', 'call', op, '--session', self.session, '--timeout', str(timeout), '--format', 'json']
        if args is not None:
            cmd += ['--args', json.dumps(args)]
        at = None if self.start is None else round(time.time() - self.start, 2)
        r = subprocess.run(cmd, capture_output=True, text=True)
        try:
            answer = json.loads(r.stdout)
        except Exception:
            answer = {'ok': False, 'raw': (r.stdout + r.stderr)[-500:]}
        ok = bool(answer.get('ok'))
        data = answer.get('data') if ok else answer.get('error')
        self.steps.append({'video_seconds': at, 'op': op, 'args': args, 'ok': ok, 'note': note, 'answer': data})
        short = json.dumps(data)[:150] if data is not None else ''
        print('[game] %6s s  %-18s %-44s %s %s' % ('-' if at is None else '%.1f' % at, op, json.dumps(args) if args else '',
                                                 'ok' if ok else 'FAILED', short), file=self.log, flush=True)
        return data if ok else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    ap.add_argument('--weapon', required=True, help='the editor ID of the weapon')
    ap.add_argument('--capacity', type=int, default=6)
    ap.add_argument('--reload', default='WPNReload', help='the name of the reload clip')
    ap.add_argument('--auto', action='store_true', help='an automatic weapon: bursts in place of single shots')
    ap.add_argument('--fire-action', help='the action of a shot (default: ActionFireSingle, or ActionFireAuto with --auto)')
    ap.add_argument('--orbit-distance', type=float, default=90.0, help='the distance of the camera in the third-person side views')
    ap.add_argument('--out', required=True)
    ap.add_argument('--node', default='gamescope', help='the PipeWire node of the game picture')
    a = ap.parse_args()
    a.fire_action = a.fire_action or ('ActionFireAuto' if a.auto else 'ActionFireSingle')
    os.makedirs(a.out, exist_ok=True)
    log = open(os.path.join(a.out, 'record.log'), 'w')
    g = Game(a.session, log)
    state = g.call('game.state')
    if not state or state.get('state') != 'in_game':
        raise SystemExit('the game of the session %s is not ready' % a.session)
    seq = state.get('seq', 0)
    raw = os.path.join(a.out, 'record.mkv')
    recorder = subprocess.Popen(
        ['gst-launch-1.0', '-e', 'pipewiresrc', 'target-object=' + a.node, 'do-timestamp=true', '!', 'videoconvert', '!',
         'video/x-raw,format=I420', '!', 'videorate', '!', 'video/x-raw,framerate=60/1', '!',
         'x264enc', 'speed-preset=veryfast', 'bitrate=12000', 'key-int-max=60', '!', 'matroskamux', '!', 'filesink', 'location=' + raw],
        stdout=open(os.path.join(a.out, 'recorder.log'), 'w'), stderr=subprocess.STDOUT)
    time.sleep(2.0)
    g.start = time.time()
    try:
        # The clip of a reload does not end in the graph (the state ends at reloadEnd), so the
        # wait is for that event.
        reload_wait = {'event': 'reloadEnd'}
        # no idle camera (the game turns the camera about the player after 120 s with no input)
        g.call('console.run', {'command': 'setini "fAutoVanityModeDelay:Camera" 100000'})
        g.call('camera.set', {'view': 'first'}, timeout=20, note='first person')
        time.sleep(1.0)
        g.call('item.give', {'form': a.weapon, 'equip': True}, timeout=30, note='give and equip')
        g.call('ammo.set', {'loaded': a.capacity, 'reserve': 100})
        g.call('weapon.draw', {'drawn': True}, timeout=30, note='draw: WPNEquip')
        time.sleep(4.0)                                           # the idle

        def fire(note, hold=0.25, after=1.1):
            """One shot, or with --auto a burst: the trigger stays down for `hold` seconds."""
            g.call('action.run', {'action': a.fire_action}, note=note)
            time.sleep(hold)
            g.call('action.run', {'action': 'ActionRightRelease'})
            time.sleep(after)
        if a.auto:
            fire('burst', hold=1.2, after=1.5)
            fire('short burst', hold=0.45, after=1.5)
        else:
            for _ in range(3):
                fire('shot')
        g.call('ammo.get')
        g.call('action.run', {'action': 'ActionReload'}, note='reload')
        g.call('anim.wait', reload_wait, timeout=15)
        g.call('ammo.get')
        time.sleep(2.0)
        g.call('action.run', {'action': 'ActionSighted'}, note='aim')
        time.sleep(2.5)
        if a.auto:
            fire('burst in the sights', hold=1.0, after=1.5)
        else:
            for _ in range(2):
                fire('shot in the sights', after=1.2)
        g.call('anim.send_event', {'event': 'rifleSightedEnd', 'target': 'player'}, note='leave the sights')
        time.sleep(2.0)
        g.call('action.run', {'action': 'ActionGunDown'}, note='gun down')
        time.sleep(2.5)
        # ActionGunReady gets no answer from the graph with no enemy near; the event of the graph does
        g.call('anim.send_event', {'event': 'GunUp', 'target': 'player'}, note='gun ready')
        time.sleep(2.0)
        g.call('anim.send_event', {'event': 'SprintStart', 'target': 'player'}, note='sprint start (the probe sends no move input)')
        time.sleep(2.5)
        g.call('anim.send_event', {'event': 'SprintStop', 'target': 'player'}, note='sprint stop')
        time.sleep(2.0)
        g.call('weapon.draw', {'drawn': False}, timeout=30, note='put away: WPNUnEquip')
        time.sleep(2.0)
        g.call('weapon.draw', {'drawn': True}, timeout=30, note='draw again')
        time.sleep(2.5)
        # one quarter of the game speed: the reload and one shot
        g.call('ammo.set', {'loaded': 3, 'reserve': 90})
        g.call('console.run', {'command': 'sgtm 0.25'}, note='slow motion')
        g.call('action.run', {'action': 'ActionReload'}, note='reload, slow')
        g.call('anim.wait', reload_wait, timeout=45)
        time.sleep(4.0)
        fire('burst, slow' if a.auto else 'shot, slow', hold=2.0 if a.auto else 0.5, after=4.5)
        g.call('console.run', {'command': 'sgtm 1'}, note='normal speed')
        time.sleep(1.0)
        # third person
        g.call('camera.set', {'view': 'third'}, timeout=20, note='third person')
        time.sleep(2.0)
        fire('burst, third person' if a.auto else 'shot, third person', hold=0.8 if a.auto else 0.25, after=1.3)
        g.call('action.run', {'action': 'ActionReload'}, note='reload, third person')
        time.sleep(4.5)
        g.call('camera.orbit', {'target': 'weapon', 'yaw': 90, 'pitch': 5, 'distance': a.orbit_distance}, timeout=20, note='camera at the right side')
        time.sleep(2.5)
        g.call('camera.orbit', {'target': 'weapon', 'yaw': 45, 'pitch': 10, 'distance': a.orbit_distance - 10.0}, timeout=20)
        time.sleep(2.5)
        g.call('camera.orbit', {'reset': True}, timeout=20)
        g.call('camera.set', {'view': 'first'}, timeout=20, note='first person')
        time.sleep(2.0)
    finally:
        recorder.send_signal(signal.SIGINT)                      # end of stream: the file gets its index
        try:
            recorder.wait(timeout=30)
        except subprocess.TimeoutExpired:
            recorder.kill()
    g.start = None
    trace = g.call('anim.trace', {'since': seq, 'limit': 4096}, timeout=20)
    with open(os.path.join(a.out, 'steps.json'), 'w') as f:
        json.dump(g.steps[:-1], f, indent=1)
    with open(os.path.join(a.out, 'trace.json'), 'w') as f:
        json.dump(trace, f, indent=1)
    out = os.path.join(a.out, 'record.mp4')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', raw, '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', '60', out], check=True)
    failed = [s for s in g.steps if not s['ok']]
    print('[game] video %s; %d ops, %d failed' % (out, len(g.steps), len(failed)), file=log, flush=True)
    print('video', out, 'ops', len(g.steps), 'failed', [(s['op'], s['args']) for s in failed])


if __name__ == '__main__':
    main()
