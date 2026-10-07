#!/usr/bin/env python3
"""Run each game test of the weapons of a mod in one session.

    ./port destiny game all --weapon TheChaperone:6:reloads --weapon TheHuckleberry:30:auto \
        --weapon TheLastWord:8 --out DIR [--session ID] [--mod NAME --tested FILE.sha] [--dry-run]
    python3 destiny/port/check/game_all.py ...          (the same program with no ./port)

--weapon is EDITORID:CAPACITY with the options `auto` (an automatic weapon: bursts) and
`reloads` (one reload clip for each count of rounds: also game_reloads.py). The tests, in
this order, with their results below DIR/EDITORID:

    record/    game_record.py for each weapon (the first-person test with a video)
    third/     game_third.py --record for each weapon (the third-person reload from three sides)
    reloads/   game_reloads.py for each weapon with `reloads`
    sight/     game_sight.py for each weapon (pictures at the hip and in the sights)

The session is that of --session, or the session that destiny/port/check/third_session.sh
started (the ID in data/destiny/port/work/probe_session.txt). The program does not start
and does not stop a session. It waits --wait seconds first (default 100): about two minutes
after the start of a session the game turns the camera about the player, and a recording
must not have that turn.

With --mod NAME the program prints the sha256 of each file of data/mods/NAME/build/release
after the tests. With --tested FILE (lines of `sha256sum`) it compares them with the file:
do the tests on the last build, and compare the hashes of the release before and after.
With --dry-run the program prints each command and runs nothing.
destiny/port/check/game_results.py copies the results into the validation folder.
"""
import argparse
import hashlib
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

HERE = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = paths.data('destiny', 'port', 'work', 'probe_session.txt')


def weapon(text):
    """(editor ID, capacity, the set of options) of EDITORID:CAPACITY[:auto][:reloads]."""
    parts = text.split(':')
    if len(parts) < 2 or not parts[1].isdigit() or set(parts[2:]) - {'auto', 'reloads'}:
        raise argparse.ArgumentTypeError('%s: give EDITORID:CAPACITY[:auto][:reloads]' % text)
    return parts[0], int(parts[1]), set(parts[2:])


def release_hashes(mod):
    folder = paths.data('mods', mod, 'build', 'release')
    out = {}
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        with open(os.path.join(folder, name), 'rb') as f:
            out[name] = hashlib.file_digest(f, 'sha256').hexdigest()
    return out


def main():
    ap = argparse.ArgumentParser(description='Run each game test of the weapons of a mod in one session.')
    ap.add_argument('--weapon', action='append', type=weapon, required=True, metavar='EDITORID:CAPACITY[:auto][:reloads]')
    ap.add_argument('--out', required=True, help='the folder for the results: one folder for each weapon')
    ap.add_argument('--session', help='the session ID (default: the ID in data/destiny/port/work/probe_session.txt)')
    ap.add_argument('--wait', type=float, default=100.0, help='seconds to wait before the first test (default 100)')
    ap.add_argument('--pictures', type=int, default=11, help='the pictures of a slow third-person reload (default 11)')
    ap.add_argument('--mod', help='the name of the mod: print the hashes of data/mods/NAME/build/release after the tests')
    ap.add_argument('--tested', help='a file with the hashes of the tested release (lines of sha256sum), to compare with --mod')
    ap.add_argument('--dry-run', action='store_true', help='print each command and run nothing')
    a = ap.parse_args()
    session = a.session
    if not session and os.path.isfile(SESSION_FILE):
        session = open(SESSION_FILE).read().strip()
    if not session:
        if not a.dry_run:
            raise SystemExit('give --session ID (no session file %s; destiny/port/check/third_session.sh makes it)' % SESSION_FILE)
        session = 'ID'
    commands = []
    for name, capacity, options in a.weapon:
        commands.append(['game_record.py', '--session', session, '--weapon', name, '--capacity', str(capacity),
                         *(['--auto'] if 'auto' in options else []), '--out', os.path.join(a.out, name, 'record')])
    for name, capacity, options in a.weapon:
        commands.append(['game_third.py', '--session', session, '--weapon', name, '--capacity', str(capacity),
                         '--pictures', str(a.pictures), '--record', '--out', os.path.join(a.out, name, 'third')])
    for name, capacity, options in a.weapon:
        if 'reloads' in options:
            commands.append(['game_reloads.py', '--session', session, '--weapon', name, '--capacity', str(capacity),
                             '--out', os.path.join(a.out, name, 'reloads')])
    for name, capacity, options in a.weapon:
        commands.append(['game_sight.py', '--session', session, '--weapon', name, '--capacity', str(capacity),
                         '--out', os.path.join(a.out, name, 'sight')])
    if a.dry_run:
        print('session %s; wait %g s' % (session, a.wait))
        for args in commands:
            print('python3 ' + ' '.join([os.path.join('destiny', 'port', 'check', args[0])] + args[1:]))
        return 0
    print('session %s' % session, flush=True)
    time.sleep(a.wait)
    failed = 0
    for args in commands:
        print('== ' + ' '.join(args), flush=True)
        r = subprocess.run([sys.executable, os.path.join(HERE, args[0])] + args[1:], capture_output=True, text=True)
        lines = (r.stdout.strip().splitlines() or ['(no output)'])[-(14 if args[0] == 'game_reloads.py' else 4):]
        print('\n'.join(lines), flush=True)
        if r.returncode != 0:
            failed += 1
            print('FAILED (exit code %d): %s' % (r.returncode, r.stderr.strip()[-600:]), flush=True)
    if a.mod:
        now = release_hashes(a.mod)
        for name, value in now.items():
            print('%s  %s' % (value, name))
        if a.tested:
            tested = dict(reversed(line.split(None, 1)) for line in open(a.tested).read().splitlines() if line.strip())
            tested = {name.strip().lstrip('*'): value for name, value in tested.items()}
            same = tested == now
            failed += 0 if same else 1
            print('the release is the tested one' if same else 'THE RELEASE IS NOT THE TESTED ONE (%s)' % a.tested)
    print('all tests done: %d commands, %d failed' % (len(commands), failed))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
