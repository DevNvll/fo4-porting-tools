#!/usr/bin/env python3
"""Make the clips of each ported weapon again and compare the bytes with the clips that the data folder has.

    ./port destiny regress [--only NAME ...] [--jobs N]
    python3 destiny/port/check/regress.py ...          (the same program with no ./port)

The table destiny/port/regress.toml has one part [[weapon]] for each weapon:

    name           the name of the weapon in this table (--only NAME)
    file           the first-person file (.glb), a path below the data folder
    set            the set file, a path from the root of the repository
    first_person   the folders with the baseline clips of the first-person view: one path below
                   the data folder, or a list of such paths
    third_person   the same for the third-person view. With this key the program also runs the
                   step `third` of the converter.
    power_armor    the same for the clips of the body in power armor ([third.power_armor])

For each weapon the program runs the converter (destiny/port/d2fo4.py) with a new work
folder and new output folders below the scratch folder (data/destiny/port/work/_regress/NAME:
`work`, `first_person`, `third_person`, `power_armor_third_person`, `convert.log`). Then it
compares each HKX file of each output folder with the file of the same name in each baseline
folder, byte for byte. It prints one line for each weapon, each view and each baseline
folder: the count of clips and the count of clips that differ. A clip that only one of the
two folders has is a difference too.

The exit code is 1 when a clip differs or a run of the converter fails, else 0.

    --only NAME      one weapon of the table (give it again for more)
    --jobs N         the count of weapons that run at the same time (default 1)
    --list           print the weapons of the table and stop
    --table FILE     another table
    --scratch DIR    another scratch folder
    --converter FILE another converter (a d2fo4.py), to compare two versions of the tools
    --against DIR    compare with the results of an earlier run of this program (its scratch
                     folder) in place of the baseline folders of the table
    --no-run         do not run the converter: compare the results that the scratch folder has

A run of one weapon needs about 1 minute, and the third-person step about 30 seconds.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

VIEWS = (('first_person', 'first person', 'first_person'),
         ('third_person', 'third person', 'third_person'),
         ('power_armor', 'power armor', 'power_armor_third_person'))


def folders(value):
    """The baseline folders of a key of the table: a list of paths below the data folder."""
    if not value:
        return []
    return [value] if isinstance(value, str) else list(value)


def clips(folder):
    return sorted(n for n in os.listdir(folder) if n.lower().endswith('.hkx')) if os.path.isdir(folder) else []


def compare(new, old):
    """(the clips of `new`, the clips that differ, the clips that `old` does not have, the
    clips that only `old` has)."""
    mine, theirs = clips(new), clips(old)
    missing = [n for n in mine if n not in theirs]
    more = [n for n in theirs if n not in mine]
    differ = [n for n in mine if n in theirs and not filecmp.cmp(os.path.join(new, n), os.path.join(old, n), shallow=False)]
    return mine, differ, missing, more


def convert(weapon, scratch, converter):
    """Run the converter for one weapon. Returns None, or the text of the failure."""
    name = weapon['name']
    source = paths.data(*weapon['file'].split('/'))
    set_file = paths.repo(*weapon['set'].split('/'))
    for path in (source, set_file):
        if not os.path.isfile(path):
            return 'the file %s is not there' % path
    folder = os.path.join(scratch, name)
    if os.path.isdir(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    base = [sys.executable, converter, source, '--set', set_file, '--name', name, '--work', os.path.join(folder, 'work')]
    runs = [base + ['-o', os.path.join(folder, 'first_person')]]
    if weapon.get('third_person'):
        runs.append(base + ['-o', os.path.join(folder, 'first_person'), 'third', '--third-output', os.path.join(folder, 'third_person')])
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    with open(os.path.join(folder, 'convert.log'), 'w') as log:
        for args in runs:
            log.write('$ ' + ' '.join(args) + '\n')
            log.flush()
            if subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, env=env).returncode != 0:
                tail = open(os.path.join(folder, 'convert.log')).read().strip().splitlines()[-6:]
                return 'the converter failed (%s):\n    %s' % (os.path.join(folder, 'convert.log'), '\n    '.join(tail))
    return None


def main():
    ap = argparse.ArgumentParser(description='Make the clips of each ported weapon again and compare the bytes with the baseline clips of the data folder.')
    ap.add_argument('--only', action='append', default=[], metavar='NAME', help='one weapon of the table (give it again for more)')
    ap.add_argument('--jobs', type=int, default=1, help='the count of weapons that run at the same time (default 1)')
    ap.add_argument('--list', action='store_true', help='print the weapons of the table and stop')
    ap.add_argument('--table', default=paths.repo('destiny', 'port', 'regress.toml'), help='the table (default: destiny/port/regress.toml)')
    ap.add_argument('--scratch', default=paths.data('destiny', 'port', 'work', '_regress'),
                    help='the scratch folder (default: data/destiny/port/work/_regress)')
    ap.add_argument('--converter', default=paths.repo('destiny', 'port', 'd2fo4.py'), help='the converter (default: destiny/port/d2fo4.py)')
    ap.add_argument('--against', metavar='DIR', help='the scratch folder of an earlier run: compare with its results, not with the baseline folders')
    ap.add_argument('--no-run', action='store_true', help='do not run the converter: compare the results that the scratch folder has')
    a = ap.parse_args()
    with open(a.table, 'rb') as f:
        weapons = tomllib.load(f).get('weapon', [])
    names = [w['name'] for w in weapons]
    for name in a.only:
        if name not in names:
            raise SystemExit('%s has no weapon %s; the weapons are: %s' % (os.path.relpath(a.table, paths.ROOT), name, ' '.join(names)))
    if a.only:
        weapons = [w for w in weapons if w['name'] in a.only]
    if a.list:
        for w in weapons:
            print('%-18s %s  (%s)' % (w['name'], w['set'], w['file']))
        return 0
    scratch = os.path.abspath(a.scratch)
    if os.path.commonpath([scratch, paths.DATA]) != paths.DATA or scratch == paths.DATA:
        raise SystemExit('the scratch folder %s is not below the data folder %s' % (scratch, paths.DATA))
    width = max(len(n) for n in names)

    def one(weapon):
        """The lines of one weapon, and True when each clip is the same."""
        failure = None if a.no_run else convert(weapon, scratch, a.converter)
        if failure:
            return ['%-*s FAILED: %s' % (width, weapon['name'], failure)], False
        lines, good = [], True
        for key, label, sub in VIEWS:
            new = os.path.join(scratch, weapon['name'], sub)
            if a.against:
                old = [os.path.join(os.path.abspath(a.against), weapon['name'], sub)] if weapon.get(key) else []
            else:
                old = [paths.data(*p.split('/')) for p in folders(weapon.get(key))]
            for folder in old:
                mine, differ, missing, more = compare(new, folder)
                ok = bool(mine) and not differ and not missing and not more
                good = good and ok
                text = '%-*s %-12s %3d clips, %d differ' % (width, weapon['name'], label, len(mine), len(differ))
                if missing:
                    text += ', %d not in the baseline' % len(missing)
                if more:
                    text += ', %d only in the baseline' % len(more)
                where = os.path.relpath(folder, paths.DATA)
                lines.append('%s   %s   %s' % (text, 'ok  ' if ok else 'DIFF', where if not where.startswith('..') else folder))
                for kind, items in (('differ', differ), ('not in the baseline', missing), ('only in the baseline', more)):
                    if items:
                        lines.append('%-*s     %s: %s' % (width, '', kind, ' '.join(n[:-4] for n in items)))
        if not lines:
            return ['%-*s has no baseline folder in the table' % (width, weapon['name'])], False
        return lines, good

    passed = True
    with ThreadPoolExecutor(max_workers=max(1, a.jobs)) as pool:
        for lines, good in pool.map(one, weapons):
            passed = passed and good
            print('\n'.join(lines), flush=True)
    print('regress: %d weapons, %s' % (len(weapons), 'each clip has the bytes of its baseline' if passed else 'DIFFERENT'))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
