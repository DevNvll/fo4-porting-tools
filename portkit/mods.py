"""The mod projects, for `./port mod`.

mods/NAME/ has the files that a person writes (esx.toml, items/, behavior/, README.md) and
the lock files that esx keeps (ids.lock, behavior/WEAPON/WEAPON.lock). data/mods/NAME/ is the
complete esx project: a copy of those files, the meshes, the textures, the clips and build/.
esx builds there, and a release is build/release/.
"""
import filecmp
import hashlib
import os
import shutil
import subprocess
import sys
import tomllib

from portkit import paths

LOCK = 'ids.lock'

USAGE = """\
./port mod list                    Each mod of mods/, its plugin, and if it has a release.
./port mod status NAME             The source files that differ from their copies in data/mods/NAME/.
./port mod sync NAME [--force]     Copy the files of mods/NAME/ into data/mods/NAME/. It deletes
                                   nothing. It keeps a lock file of data/ that is different and
                                   newer; --force replaces that file too.
./port mod build NAME [--update-lock] [ARGUMENTS OF esx build]
                                   Sync, run `esx build` on data/mods/NAME/, copy each new or
                                   changed lock file back to mods/NAME/, show the release files.
The lock files are ids.lock and behavior/WEAPON/WEAPON.lock.
"""


def names():
    """Each mod of mods/."""
    folder = paths.repo('mods')
    return sorted(n for n in os.listdir(folder) if os.path.isdir(os.path.join(folder, n))) if os.path.isdir(folder) else []


def source(name, *parts):
    """A path in mods/NAME/."""
    return paths.repo('mods', name, *parts)


def project(name, *parts):
    """A path in data/mods/NAME/."""
    return paths.data('mods', name, *parts)


def plugin(name):
    """The plugin of a mod: `plugin` of esx.toml, or the name of the folder with .esp."""
    try:
        with open(source(name, 'esx.toml'), 'rb') as f:
            return tomllib.load(f).get('plugin') or name + '.esp'
    except (OSError, tomllib.TOMLDecodeError):
        return name + '.esp'


def is_lock(file):
    """A lock file that esx keeps: ids.lock, or behavior/WEAPON/WEAPON.lock."""
    parts = file.split(os.sep)
    return file == LOCK or (len(parts) == 3 and parts[0] == 'behavior' and parts[2].endswith('.lock'))


def data_locks(name):
    """Each lock file of data/mods/NAME/, as a path from that folder."""
    found = [LOCK] if os.path.isfile(project(name, LOCK)) else []
    behavior = project(name, 'behavior')
    for weapon in sorted(os.listdir(behavior)) if os.path.isdir(behavior) else []:
        folder = os.path.join(behavior, weapon)
        if os.path.isdir(folder):
            found += [os.path.join('behavior', weapon, n) for n in sorted(os.listdir(folder)) if n.endswith('.lock')]
    return found


def files(name):
    """Each file of mods/NAME/, as a path from that folder."""
    found = []
    for folder, folders, here in os.walk(source(name)):
        folders[:] = [f for f in folders if f != '__pycache__']
        found += [os.path.relpath(os.path.join(folder, n), source(name)) for n in here]
    return sorted(found)


def state(name, file):
    """The copy of a source file in data/mods/NAME/: 'same', 'different' or 'missing'."""
    copy = project(name, file)
    if not os.path.isfile(copy):
        return 'missing'
    return 'same' if filecmp.cmp(source(name, file), copy, shallow=False) else 'different'


def newer_in_data(name, file):
    return os.stat(project(name, file)).st_mtime_ns > os.stat(source(name, file)).st_mtime_ns


def release(name):
    """The files of the release of a mod, the plugin first. Empty when no release is there."""
    folder = project(name, 'build', 'release')
    return sorted(os.listdir(folder), key=lambda n: (n != plugin(name), n)) if os.path.isdir(folder) else []


def sync(name, force=False, build=False):
    """Copy each file of mods/NAME/ that is new or different to data/mods/NAME/. Delete
    nothing. False when a lock file of data/ that is different and newer stays as it is."""
    copied, kept, all_files = 0, False, files(name)
    for file in all_files:
        what = state(name, file)
        if what == 'same':
            continue
        if is_lock(file) and what == 'different' and not force and newer_in_data(name, file):
            kept = True
            print('kept     %s: the copy in %s is different and newer. %s' % (file, paths.short(project(name)), (
                'The build uses it.' if build else
                'Run `./port mod build %s --update-lock` to keep it, or `./port mod sync %s --force` to replace it.' % (name, name))))
            continue
        os.makedirs(os.path.dirname(project(name, file)), exist_ok=True)
        shutil.copy2(source(name, file), project(name, file))
        copied += 1
        print('%-8s %s' % ('new' if what == 'missing' else 'changed', file))
    print('sync %s: %d of %d files copied to %s.' % (name, copied, len(all_files), paths.short(project(name))))
    return not kept


def build(name, arguments):
    """Sync, run esx build on data/mods/NAME/, copy each new or changed lock file back, show
    the release files with their sha256. The exit code of esx."""
    try:
        esx, game = paths.require('esx'), paths.require('fo4_data')
    except SystemExit as stop:
        print('port: %s' % stop, file=sys.stderr)
        return 3
    sync(name, build=True)
    sys.stdout.flush()
    try:
        code = subprocess.call([esx, '--data', game, 'build', project(name)] + arguments)
    except OSError as e:
        print('port: esx did not start: %s. `./port doctor` shows each setting.' % e, file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        return 130
    for file in data_locks(name):
        lock, mine = project(name, file), source(name, file)
        if os.path.isfile(mine) and filecmp.cmp(lock, mine, shallow=False):
            continue
        if code == 0:
            os.makedirs(os.path.dirname(mine), exist_ok=True)
            shutil.copy2(lock, mine)
            print('%s changed: copied to %s.' % (file, paths.short(mine)))
        else:
            print('%s of %s is different. The build failed, thus %s stays as it is.' % (file, paths.short(project(name)), paths.short(mine)))
    if code == 0:
        there = release(name)
        print('release %s:%s' % (paths.short(project(name, 'build', 'release')), '' if there else ' not there'))
        for file in there:
            with open(project(name, 'build', 'release', file), 'rb') as f:
                print('%s  %s' % (hashlib.file_digest(f, 'sha256').hexdigest(), file))
    return code if code >= 0 else 128 - code


def status(name):
    """Show the source files that differ from their copies in data/mods/NAME/, and the release."""
    states = [(file, state(name, file)) for file in files(name)]
    for file, what in states:
        if what == 'different':
            newer = project(name) if newer_in_data(name, file) else source(name)
            print('different  %s  (the newer file is in %s)' % (file, paths.short(newer)))
        elif what == 'missing':
            print('missing    %s  (not in %s)' % (file, paths.short(project(name))))
    count = sum(what != 'same' for _, what in states)
    print('%s (%s): %d of %d source files differ from %s.%s' % (
        name, plugin(name), count, len(states), paths.short(project(name)), ' `./port mod sync %s` copies them.' % name if count else ''))
    there = release(name)
    print('release: %s' % ('%s (%s)' % (paths.short(project(name, 'build', 'release')), ', '.join(there)) if there
                           else 'not there. `./port mod build %s` makes it.' % name))
    return 0


def main(argv):
    if not argv or argv[0] in ('help', '--help', '-h'):
        print(USAGE, end='')
        return 0
    action, rest = argv[0], argv[1:]
    if action == 'list' and not rest:
        rows = [(name, plugin(name), 'yes' if release(name) else 'no') for name in names()]
        widths = [max(len(row[column]) for row in rows) for column in (0, 1)] if rows else []
        for name, file, there in rows:
            print('%-*s  %-*s  release: %s' % (widths[0], name, widths[1], file, there))
        return 0
    if action in ('status', 'sync', 'build') and rest and not rest[0].startswith('-'):
        name, options = os.path.basename(rest[0].rstrip('/')), rest[1:]
        if name not in names():
            print('port: no mod has the name `%s`. The mods: %s.' % (name, ', '.join(names())), file=sys.stderr)
            return 2
        if action == 'build':
            return build(name, options)
        if action == 'sync' and set(options) <= {'--force'}:
            return 0 if sync(name, force='--force' in options) else 1
        if action == 'status' and not options:
            return status(name)
    print('port: wrong arguments for `./port mod`.\n' + USAGE, end='', file=sys.stderr)
    return 2
