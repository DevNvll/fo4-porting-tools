"""The paths and the local settings of this repository. Standard library only.

Each program of the repository gets its folders and its external programs from this module,
so that no program has a path of one computer in it.

    from portkit import paths
    paths.repo('fnv', 'tools')                    # a path in the source tree
    paths.data('destiny', 'port', 'work', name)   # a path below the data folder (not in git)
    paths.program('blender')                      # an external program, or None
    paths.require('fo4_data')                     # a setting that must be there

A setting comes from, in this order: its environment variable, the file data/config.toml,
its default (for a program: the PATH). config.example.toml lists the settings.

    python3 -m portkit.paths                # each setting with its value and where it comes from
    python3 -m portkit.paths --json
    python3 -m portkit.paths get blender    # one value, for a shell script (exit 1: not set)

A program that ./port does not start (a program in Blender, for example) finds this package
with these lines at its top:

    import os, sys
    _r = os.path.dirname(os.path.abspath(__file__))
    while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
        _r = os.path.dirname(_r)
    sys.path.insert(0, _r)
    from portkit import paths
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.abspath(os.environ.get('FO4PORTS_DATA') or os.path.join(ROOT, 'data'))
CONFIG = os.path.join(DATA, 'config.toml')

# name: (environment variable, kind, name in the PATH or None, meaning)
SETTINGS = {
    'blender': ('BLENDER', 'program', 'blender', 'Blender 4.5. It runs with no window.'),
    'esx': ('ESX_BIN', 'program', 'esx', 'The esx command: it builds a mod project and runs the game test.'),
    'fo4_data': ('FO4_DATA', 'folder', None, 'The Data folder of Fallout 4.'),
    'proton': ('PROTON_DIR', 'folder', None, 'The Proton folder for the game test.'),
    'destiny_game': ('D2X_GAME', 'folder', None, 'The game folder of Destiny 2 (it has packages/ and bin/x64/).'),
    'marathon_game': ('MARATHON_GAME', 'folder', None, 'The game folder of Marathon (it has packages/ and bin/x64/).'),
    'nvcs_skeleton': ('NVCS_SKELETON', 'file', None, 'The first-person skeleton of the New Vegas compatibility skeleton mod (NVCS), for `fnv make-rig`.'),
}

_config = None


def repo(*parts):
    """A path in the source tree."""
    return os.path.join(ROOT, *parts)


def data(*parts, make=False):
    """A path below the data folder. make=True makes the folder."""
    path = os.path.join(DATA, *parts)
    if make:
        os.makedirs(path, exist_ok=True)
    return path


def short(path):
    """A path for a message: from the root when it is in the repository, else as it is."""
    inside = os.path.abspath(path).startswith(ROOT + os.sep)
    return os.path.relpath(path, ROOT) if inside else path


def config():
    """The values of data/config.toml (an empty table when the file is not there)."""
    global _config
    if _config is None:
        _config = {}
        if os.path.isfile(CONFIG):
            import tomllib
            with open(CONFIG, 'rb') as f:
                _config = tomllib.load(f)
    return _config


def lookup(name, env=None, default=None):
    """(value, source) of a setting. source: 'environment', 'config', 'path', 'default' or None."""
    known = SETTINGS.get(name)
    env = env or (known[0] if known else None)
    if env and os.environ.get(env):
        return os.path.expanduser(os.environ[env]), 'environment'
    value = config().get(name)
    if value:
        return os.path.expanduser(str(value)), 'config'
    if known and known[2]:
        found = shutil.which(known[2])
        if found:
            return found, 'path'
    if default is not None:
        return default, 'default'
    return None, None


def setting(name, env=None, default=None):
    """The value of a setting, or None. `env` names the environment variable of a setting that
    is not in SETTINGS."""
    return lookup(name, env, default)[0]


def program(name):
    """An external program ('blender', 'esx'), or None."""
    return setting(name)


def advice(name, env=None):
    """One sentence that tells the user where to give the value of a setting."""
    known = SETTINGS.get(name)
    variable = env or (known[0] if known else None)
    return 'Give it in %s (%s = "...")%s.' % (
        short(CONFIG), name, (' or in the environment variable %s' % variable) if variable else '')


def require(name, env=None):
    """The value of a setting. Stops with advice when the setting has no value."""
    value = setting(name, env)
    if not value:
        known = SETTINGS.get(name)
        raise SystemExit('The setting `%s` has no value.%s %s `./port doctor` shows each setting.' % (
            name, (' ' + known[3]) if known else '', advice(name, env)))
    return value


def report():
    """Each setting of SETTINGS: name, value, source, environment variable, kind, meaning, ok."""
    rows = []
    for name, (env, kind, _, meaning) in SETTINGS.items():
        value, source = lookup(name)
        ok = bool(value) and (os.path.isdir(value) if kind == 'folder' else os.path.isfile(value))
        rows.append({'name': name, 'value': value, 'source': source, 'env': env, 'kind': kind, 'meaning': meaning, 'ok': ok})
    return rows


def main(argv):
    if argv[:1] == ['get'] and len(argv) == 2:
        value = setting(argv[1])
        if not value:
            return 1
        print(value)
        return 0
    rows = report()
    if '--json' in argv:
        print(json.dumps({'root': ROOT, 'data': DATA, 'config': CONFIG, 'settings': rows}, indent=1))
        return 0
    print('root    %s\ndata    %s\nconfig  %s%s' % (ROOT, DATA, CONFIG, '' if os.path.isfile(CONFIG) else '  (not there)'))
    for r in rows:
        print('%-14s %-8s %s%s' % (r['name'], 'ok' if r['ok'] else ('MISSING' if r['value'] else 'not set'),
                                   r['value'] or '', ('  [%s]' % r['source']) if r['source'] else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
