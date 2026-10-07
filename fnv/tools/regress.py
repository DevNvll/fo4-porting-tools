"""Convert each fixture again and compare the clips with the results that the data folder has.

    ./port fnv regress [NAME ...]
    python3 fnv/tools/regress.py [NAME ...]       the same command with no ./port

A fixture is a folder data/fnv/fixtures/NAME: the extracted New Vegas mod of a weapon that is
ported (the gun model and the first-person animations). Its results are the HKX clips in
data/fnv/out/NAME (the name in lower case).

For each fixture the program runs the conversion (fnv/tools/port.py FIXTURE) into the scratch
folder data/fnv/work/_regress/NAME, and compares each HKX clip with the clip of the same name
in data/fnv/out/NAME. It prints one line for each fixture:

    ppk     same       27 clips
    famas   DIFFERENT  2 of 26 clips: WPNReload.hkx WPNSprint.hkx
    mygun   NO RESULT  data/fnv/out/mygun has no clip: `./port fnv convert data/fnv/fixtures/mygun --name mygun` makes them
    other   FAILED     the conversion stopped: see data/fnv/work/_regress/other/log.txt

The exit code is 1 when a line is not `same`. With no fixture the program says so, and the
exit code is 0. The program does not change data/fnv/out. The scratch folder of a fixture
stays after the run (the log, the work files and the new clips) and the next run makes it
again.

To add a fixture: copy the extracted mod to data/fnv/fixtures/NAME, run
`./port fnv convert data/fnv/fixtures/NAME --name NAME`, and check the clips. They are then
the results that this program compares with.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True                # no cache file in the source tree
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def short(path):
    """A path from the root of the repository, for a message."""
    rel = os.path.relpath(path, paths.ROOT)
    return path if rel.startswith('..') else rel


def clips(folder):
    return sorted(f for f in os.listdir(folder) if f.lower().endswith('.hkx')) if os.path.isdir(folder) else []


def check(name, fixture):
    """Convert one fixture and compare. Returns (state, text of the line)."""
    result = paths.data('fnv', 'out', name.lower())
    have = clips(result)
    if not have:
        return 'NO RESULT', '%s has no clip: `./port fnv convert %s --name %s` makes them' % (short(result), short(fixture), name)
    scratch = paths.data('fnv', 'work', '_regress', name)
    if os.path.isdir(scratch):
        shutil.rmtree(scratch)
    os.makedirs(scratch)
    new = os.path.join(scratch, 'clips')
    log = os.path.join(scratch, 'log.txt')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    for key in ('PORT_CONFIG', 'PORT_WORK', 'PORT_CHILD'):
        env.pop(key, None)                      # values of a conversion that started this program
    with open(log, 'w') as f:
        r = subprocess.run([sys.executable, os.path.join(HERE, 'port.py'), fixture, '--name', name, '-o', new,
                            '--work', os.path.join(scratch, 'work')], stdout=f, stderr=subprocess.STDOUT, env=env)
    if r.returncode != 0:
        return 'FAILED', 'the conversion stopped: see %s' % short(log)
    made = clips(new)
    different = [f for f in sorted(set(have) | set(made))
                 if f not in have or f not in made or not filecmp.cmp(os.path.join(result, f), os.path.join(new, f), shallow=False)]
    if different:
        notes = []
        for f in different:
            notes.append(f + (' (not in the results)' if f not in have else ' (not made)' if f not in made else ''))
        return 'DIFFERENT', '%d of %d clips: %s' % (len(different), len(set(have) | set(made)), ' '.join(notes))
    return 'same', '%d clips' % len(have)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('names', nargs='*', metavar='NAME', help='only these fixtures (default: each folder of data/fnv/fixtures)')
    ap.add_argument('--list', action='store_true', help='print the name of each fixture and stop')
    a = ap.parse_args()
    root = paths.data('fnv', 'fixtures')
    found = sorted(n for n in os.listdir(root) if os.path.isdir(os.path.join(root, n)) and not n.startswith(('.', '_'))) if os.path.isdir(root) else []
    if a.list:
        for n in found:
            print(n)
        return 0
    unknown = [n for n in a.names if n not in found]
    if unknown:
        raise SystemExit('no fixture %s in %s (the fixtures: %s)' % (', '.join(unknown), short(root), ' '.join(found) or 'none'))
    names = a.names or found
    if not names:
        print('no fixture in %s: nothing to compare' % short(root))
        return 0
    width = max(len(n) for n in names)
    bad = 0
    for n in names:
        state, text = check(n, os.path.join(root, n))
        bad += state != 'same'
        print('%-*s  %-9s  %s' % (width, n, state, text), flush=True)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
