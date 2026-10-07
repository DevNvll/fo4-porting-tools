"""The command ./port: one entry point for the tools of each area.

It finds the commands in the port.toml files of the source tree. It starts each one with the
folders and the local settings in the environment. `./port help` shows the usage, and
portkit/README.md describes port.toml.
"""
import difflib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tomllib
import warnings

from portkit import paths

USAGE = """\
./port: the tools that port weapons and animations to Fallout 4.

  ./port list [--json]               Each command of each area, with one line of help.
  ./port AREA [WORD]                 The commands of one area, or of one group (`destiny check`).
  ./port AREA COMMAND [ARGUMENTS]    Run a command. `--help` shows the help of the command.
  ./port doctor [--json]             Each setting, each tool and each necessary file: there or
                                     missing, and how to make it.
  ./port paths [--json]              The folders and the local settings.
  ./port mod list                    The mod projects.
  ./port mod status NAME             The source files that differ from their copies in data/.
  ./port mod sync NAME [--force]     Copy the files of mods/NAME/ into data/mods/NAME/.
  ./port mod build NAME [--update-lock] [ARGUMENTS OF esx build]
                                     Sync, run esx build, show the release files.
  ./port selftest                    The checks that need no game file.
  ./port help

Exit codes: a command gives the exit code of its program. 2: the command line or a port.toml
is wrong. 3: a thing that the command needs is missing, and the message tells you how to make
it. `doctor` and `selftest` give 1 when they find a fault.

Documents: README.md (start here), docs/ARCHITECTURE.md (the structure and port.toml),
AGENTS.md (the instructions for an AI agent), portkit/README.md (how to add a command).
"""

BUILTINS = ('list', 'doctor', 'paths', 'mod', 'selftest', 'help')
RUNNERS = ('python', 'python:d2x', 'sh', 'bash')
D2X_PYTHON = 'data/destiny/extract/venv/bin/python'
D2X_SETUP = './port destiny setup'
TOOLS = ('git', 'cargo', 'uv', 'ffmpeg')
SKIP = ('.git', '__pycache__', '.venv', 'target')   # folders that have no source
COMMAND_KEYS = ('name', 'help', 'run', 'env', 'needs')
CHECK_KEYS = ('path', 'setting', 'what', 'make')
WORD = re.compile(r'[a-z0-9][a-z0-9_-]*')


def say(text):
    print('port: ' + text, file=sys.stderr)


def options(arguments, *known):
    """The options of a command of ./port itself. Stops when one is not in `known`."""
    if set(arguments) - set(known):
        say('unknown argument: %s. `./port help` shows the usage.' % ' '.join(arguments))
        raise SystemExit(2)
    return set(arguments)


# --- the files of the source tree

def find(match, root=None):
    """Each file of the source tree whose name `match` accepts. It does not look below data/,
    .git/ or a folder that .gitignore names (__pycache__, .venv, target)."""
    root = root or paths.ROOT
    data = (os.path.join(root, 'data'), paths.DATA)
    for folder, names, files in os.walk(root):
        names[:] = sorted(n for n in names if n not in SKIP and os.path.join(folder, n) not in data)
        for name in sorted(files):
            if match(name):
                yield os.path.join(folder, name)


def resolve(path):
    """The absolute form of a path from the root. `data/...` is below the data folder."""
    if os.path.isabs(path):
        return path
    parts = os.path.normpath(path).split(os.sep)
    return paths.data(*parts[1:]) if parts[0] == 'data' else paths.repo(*parts)


def from_root(word):
    """`word` as an absolute path when it is a path from the root, else `word` as it is.
    A path from the root has a `/`, and its first part is `data` or a file or folder of the root."""
    first = word.split('/')[0]
    if '/' in word and first and not first.startswith('-') and (first == 'data' or os.path.exists(paths.repo(first))):
        return resolve(word)
    return word


# --- port.toml

def text(value):
    return isinstance(value, str) and bool(value.strip())


def command_faults(c):
    """Each fault of a [[command]] table."""
    faults = ['unknown key `%s`' % k for k in c if k not in COMMAND_KEYS]
    name, run, env, needs = c.get('name'), c.get('run'), c.get('env', {}), c.get('needs', [])
    words = name.split(' ') if isinstance(name, str) else []
    if len(words) not in (2, 3) or not all(WORD.fullmatch(w) for w in words):
        faults.append('`name` must have two or three words of small letters, digits, `-` and `_`')
    elif words[0] in BUILTINS:
        faults.append('`%s` is a command of ./port, thus it cannot be an area' % words[0])
    if not text(c.get('help')) or '\n' in c['help']:
        faults.append('`help` must be one line of text')
    if not (isinstance(run, list) and run and all(text(w) for w in run)):
        faults.append('`run` must be a list of words')
    elif run[0] in RUNNERS and (len(run) < 2 or run[1].startswith('-')):
        faults.append('`run` must have a program file after `%s` (a path from the root, not an option)' % run[0])
    if not (isinstance(env, dict) and all(isinstance(v, str) for v in env.values())):
        faults.append('`env` must be a table of text values')
    if not (isinstance(needs, list) and all(text(n) for n in needs)):
        faults.append('`needs` must be a list of settings and paths')
    else:
        faults += ['`needs`: `%s` is not a setting (%s) and is not a path (a path has a `/`)' % (n, ', '.join(paths.SETTINGS))
                   for n in needs if n not in paths.SETTINGS and '/' not in n]
    return faults


def check_faults(c):
    """Each fault of a [[check]] table."""
    faults = ['unknown key `%s`' % k for k in c if k not in CHECK_KEYS]
    faults += ['`%s` must be text' % k for k in CHECK_KEYS if k in c and not text(c[k])]
    if ('path' in c) == ('setting' in c):
        faults.append('give `path` or `setting`, and not the two')
    elif text(c.get('setting')) and c['setting'] not in paths.SETTINGS:
        faults.append('`%s` is not a setting (%s)' % (c['setting'], ', '.join(paths.SETTINGS)))
    if 'what' not in c:
        faults.append('`what` is necessary')
    return faults


def load(root=None):
    """(commands, checks, problems) of the port.toml files of the source tree. `commands` is
    name -> table. A table with a fault is not in the result: `problems` has a line for it."""
    root = root or paths.ROOT
    commands, checks, problems = {}, [], []
    for file in find(lambda name: name == 'port.toml', root):
        source = os.path.relpath(file, root)
        try:
            with open(file, 'rb') as f:
                table = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError) as e:
            problems.append('%s: %s' % (source, e))
            continue
        problems += ['%s: unknown key `%s`' % (source, k) for k in table if k not in ('command', 'check')]
        for kind, faults_of in (('command', command_faults), ('check', check_faults)):
            entries = table.get(kind, [])
            if not (isinstance(entries, list) and all(isinstance(e, dict) for e in entries)):
                problems.append('%s: write each %s as a [[%s]] table' % (source, kind, kind))
                continue
            for number, entry in enumerate(entries, 1):
                label = next((entry[k] for k in ('name', 'path', 'setting') if text(entry.get(k))), 'number %d' % number)
                faults = faults_of(entry)
                if kind == 'command' and not faults and entry['name'] in commands:
                    faults = ['the name is also in %s' % commands[entry['name']]['source']]
                problems += ['%s: %s `%s`: %s' % (source, kind, label, fault) for fault in faults]
                if faults:
                    continue
                if kind == 'command':
                    commands[entry['name']] = dict({'env': {}, 'needs': []}, **entry, source=source)
                else:
                    checks.append(dict(entry, source=source))
    return commands, checks, problems


def program(command):
    """The program file of a command: the word of `run` after the runner, as an absolute path."""
    run = command['run']
    return resolve(run[1] if run[0] in RUNNERS else run[0])


def program_faults(commands):
    """A line for each command whose program file is not there or cannot start."""
    faults = []
    for name, command in sorted(commands.items()):
        file, direct = program(command), command['run'][0] not in RUNNERS
        if not os.path.isfile(file) or direct and not os.access(file, os.X_OK):
            state = 'not executable' if os.path.isfile(file) else 'not there'
            faults.append('%s: command `%s`: the program %s is %s' % (command['source'], name, paths.short(file), state))
    return faults


def table(commands):
    """One line for each command: name, help, the file that defines it."""
    width = max((len(c['name']) for c in commands), default=0)
    return ['%-*s  %s  [%s]' % (width, c['name'], c['help'], c['source']) for c in commands]


# --- run a command

def match(commands, argv):
    """(command, arguments): the command with the longest name at the start of argv, then
    the words after the name. (None, argv) when no name is there."""
    for count in (3, 2):
        name = ' '.join(argv[:count])
        if len(argv) >= count and name in commands:
            return commands[name], argv[count:]
    return None, argv


def command_line(command, arguments):
    """The runner, the program file and the other words of `run`, then the arguments of the user."""
    run = list(command['run'])
    kind = run.pop(0) if run[0] in RUNNERS else None
    runner = {'python': [sys.executable], 'python:d2x': [resolve(D2X_PYTHON)], 'sh': ['sh'], 'bash': ['bash'], None: []}[kind]
    return runner + [resolve(run[0])] + [from_root(word) for word in run[1:]] + list(arguments)


def environment(command):
    """The environment of the caller, the two folders, one variable for each setting that has
    a value, the variables of `env`, and the root in front of PYTHONPATH."""
    env = dict(os.environ, FO4PORTS_ROOT=paths.ROOT, FO4PORTS_DATA=paths.DATA, PYTHONDONTWRITEBYTECODE='1')
    env.update((row['env'], row['value']) for row in paths.report() if row['value'])
    python_path = [paths.ROOT]
    for key, value in command['env'].items():
        parts = [part for part in value.split(os.pathsep) if part]
        if key == 'PYTHONPATH':
            python_path += [resolve(part) for part in parts]
        else:
            env[key] = os.pathsep.join(from_root(part) for part in parts)
    python_path += [part for part in os.environ.get('PYTHONPATH', '').split(os.pathsep) if part]
    env['PYTHONPATH'] = os.pathsep.join(python_path)
    return env


def check_for(need, checks, source=None):
    """The [[check]] of a setting, or of a path or of a folder above it. The best one: a check
    with `make`, then the longest path, then a check of the port.toml `source`."""
    best, best_rank, need = None, (), os.path.normpath(need)
    for check in checks:
        path = os.path.normpath(check.get('path', ''))
        if check.get('setting') == need or (need + os.sep).startswith(path + os.sep):
            rank = ('make' in check, len(path), check['source'] == source)
            if rank > best_rank:
                best, best_rank = check, rank
    return best


def missing(command, checks, only_runner=False):
    """A text for each thing that the command needs and that is not there, with the way to
    make it. only_runner: look only at the Python of `python:d2x`."""
    settings = {row['name']: row for row in paths.report()}
    needs = [D2X_PYTHON] if command['run'][0] == 'python:d2x' else []
    found = []
    for need in dict.fromkeys(needs + ([] if only_runner else command['needs'])):
        row, check = settings.get(need), check_for(need, checks, command['source']) or {}
        if row['ok'] if row else os.path.exists(resolve(need)):
            continue
        if row:
            state = ('is %s, and that is not there' % row['value']) if row['value'] else 'has no value'
            what, make = 'The setting `%s` %s. %s' % (need, state, row['meaning']), check.get('make') or paths.advice(need)
        else:
            what = '%s is not there.%s' % (need, ' ' + check['what'] if check else '')
            make = check.get('make') or (D2X_SETUP if need == D2X_PYTHON else 'no port.toml tells how')
        found.append('%s\n      make: %s' % (what, make))
    return found


def group(commands, words):
    """The commands whose name starts with `words` and has more words."""
    return [commands[name] for name in sorted(commands) if name.startswith(' '.join(words) + ' ')]


def unknown(commands, problems, argv):
    """The answer to words that are not a command. One or two words that start names (an
    area, or `destiny check`): those commands. Other words: the nearest names, exit code 2."""
    asked = argv[:-1] if argv[-1] in ('--help', '-h') else argv
    area = group(commands, argv[:1])
    if 1 <= len(asked) <= 2 and group(commands, asked):
        print('\n'.join(table(group(commands, asked))))
        return 0
    if not area:
        near = difflib.get_close_matches(argv[0], sorted({name.split()[0] for name in commands}) + list(BUILTINS), 3, 0.5)
        say('`%s` is not a command and not an area.%s' % (argv[0], ' The nearest names: %s.' % ', '.join(near) if near else ''))
    else:
        rests = {command['name'].split(' ', 1)[1]: command for command in area}
        typed = [' '.join(argv[1:count]) for count in (3, 2) if len(argv) >= count]
        near = {rest: rests[rest] for words in typed for rest in difflib.get_close_matches(words, rests, 3, 0.6)}
        start = argv[:2] if group(commands, argv[:2]) else argv[:1]
        say('`%s` does not start with the name of a command. %s' % (
            ' '.join(argv[:3]), 'The nearest names:' if near else 'The commands of `%s`:' % ' '.join(start)))
        print('\n'.join('  ' + line for line in table(list(near.values()) or group(commands, start))), file=sys.stderr)
    if problems:
        say('these entries of port.toml files have a fault, thus they are not commands:')
        print('\n'.join('  ' + line for line in problems), file=sys.stderr)
    say('`./port list` shows each command.')
    return 2


def run(argv):
    """Run the command that argv names. The exit code of its program."""
    commands, checks, problems = load()
    command, arguments = match(commands, argv)
    if not command:
        return unknown(commands, problems, argv)
    name = command['name']
    lacking = missing(command, checks, only_runner=bool({'--help', '-h'} & set(arguments)))
    if lacking:
        say('`%s` cannot start (%s).' % (name, command['source']))
        print('\n'.join('  ' + line for line in lacking), file=sys.stderr)
        return 3
    if not os.path.isfile(program(command)):
        say('`%s`: the program %s is not there (%s).' % (name, paths.short(program(command)), command['source']))
        return 2
    sys.stdout.flush()
    try:
        code = subprocess.call(command_line(command, arguments), env=environment(command))
    except OSError as e:
        say('`%s` did not start: %s' % (name, e))
        return 2
    except KeyboardInterrupt:
        return 130
    return code if code >= 0 else 128 - code


# --- the commands of ./port itself

def list_commands(arguments):
    as_json = '--json' in options(arguments, '--json')
    commands, _, problems = load()
    rows = [commands[name] for name in sorted(commands)]
    if as_json:
        print(json.dumps([{key: row[key] for key in COMMAND_KEYS + ('source',)} for row in rows], indent=1))
    else:
        print('\n'.join(table(rows)) if rows else 'No port.toml has a command.')
    for line in problems:
        say('fault: ' + line)
    return 0


def doctor(arguments):
    """Show what is there and what is missing. 1 when a check is not ok, or a setting that a
    command or a check uses. With an area (`./port doctor fnv`): only the port.toml files below
    that folder, so a person who uses one area gets a result for that area."""
    area = next((a for a in arguments if not a.startswith('-')), None)
    as_json = '--json' in options([a for a in arguments if a != area], '--json')
    commands, checks, problems = load()
    if area:
        commands = {name: c for name, c in commands.items() if c['source'].split(os.sep)[0] == area}
        checks = [c for c in checks if c['source'].split(os.sep)[0] == area]
        if not commands and not checks:
            say('no port.toml is below the folder `%s`.' % area)
            return 2
    used = {need for c in commands.values() for need in c['needs'] if need in paths.SETTINGS} | {c['setting'] for c in checks if 'setting' in c}
    settings = [dict(row, used=row['name'] in used) for row in paths.report()]
    ok = {row['name']: row['ok'] for row in settings}
    checks = [dict(c, ok=ok[c['setting']] if 'setting' in c else os.path.exists(resolve(c['path']))) for c in checks]
    numpy = subprocess.run([sys.executable, '-c', 'import numpy; print(numpy.__version__)'], capture_output=True, text=True)
    facts = {
        'ok': all(row['ok'] for row in checks) and all(row['ok'] for row in settings if row['used']),
        'area': area,
        'python': {'version': platform.python_version(), 'executable': sys.executable, 'ok': True},
        'numpy': {'version': numpy.stdout.strip() or None, 'ok': numpy.returncode == 0},
        'root': paths.ROOT, 'data': paths.DATA, 'config': paths.CONFIG,
        'settings': settings,
        'checks': checks,
        'tools': [{'name': tool, 'path': shutil.which(tool), 'ok': bool(shutil.which(tool))} for tool in TOOLS],
        'problems': problems,
    }
    if as_json:
        print(json.dumps(facts, indent=1))
        return 0 if facts['ok'] else 1

    print('python   ok       %s  %s' % (facts['python']['version'], sys.executable))
    print('numpy    %-8s %s' % ('ok' if facts['numpy']['ok'] else 'no',
                                facts['numpy']['version'] or 'This Python cannot import numpy. fnv/ and destiny/port/ need it.'))
    print('root     %s\ndata     %s' % (paths.ROOT, paths.DATA))
    print('config   %s%s' % (paths.CONFIG, '' if os.path.isfile(paths.CONFIG) else '  (not there)'))
    print('\nSettings' + (' (a setting that no command of `%s` uses is `unused`)' % area if area else ''))
    for row in settings:
        state = 'ok' if row['ok'] else ('MISSING' if row['value'] else ('not set' if row['used'] else 'unused'))
        print('  %-8s %-14s %s' % (state, row['name'], '%s  [%s]' % (row['value'], row['source']) if row['value'] else row['meaning']))
        if not row['ok'] and (row['used'] or row['value']):
            print('  %8s %s' % ('', 'That file or folder is not there.' if row['value'] else paths.advice(row['name'])))
    print('\nChecks of the port.toml files' + ('' if checks else '\n  (none)'))
    for check in checks:
        subject = check.get('path') or 'setting ' + check['setting']
        print('  %-8s %s  %s  [%s]' % ('ok' if check['ok'] else 'MISSING', subject, check['what'], check['source']))
        if not check['ok']:
            print('  %8s make: %s' % ('', check.get('make') or 'no port.toml tells how'))
    print('\nPrograms in the PATH (only some commands use them)')
    for tool in facts['tools']:
        print('  %-8s %-14s %s' % ('ok' if tool['ok'] else 'no', tool['name'], tool['path'] or ''))
    for line in problems:
        say('fault: ' + line)
    count = sum(not row['ok'] for row in checks) + sum(not row['ok'] for row in settings if row['used'])
    print('\nResult: %s' % ('each setting and each check is ok.' if facts['ok'] else '%d of the settings and checks are not ok.' % count))
    return 0 if facts['ok'] else 1


def selftest():
    """The checks that need no game file. One line for each part. 1 when a part fails."""
    faults, count = [], 0
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for file in find(lambda name: name.endswith('.py')):
            count += 1
            try:
                with open(file, 'rb') as f:
                    compile(f.read(), paths.short(file), 'exec', dont_inherit=True)
            except (SyntaxError, ValueError) as e:
                faults.append('%s: %s' % (paths.short(file), e))
    notes = ['warning: %s:%s: %s' % (w.filename, w.lineno, w.message) for w in caught]
    results = [('python', not faults, '%d files, %d do not compile' % (count, len(faults)), faults + notes)]

    commands, checks, problems = load()
    faults = problems + program_faults(commands)
    files = sum(1 for _ in find(lambda name: name == 'port.toml'))
    summary = '%d files, %d commands, %d checks, %d faults' % (files, len(commands), len(checks), len(faults))
    results.append(('port.toml', not faults, summary, faults))

    if os.path.isdir(paths.repo('tests')):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=paths.ROOT)
        done = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests'],
                              cwd=paths.ROOT, env=env, capture_output=True, text=True)
        ran = re.search(r'^Ran (\d+ tests?)', done.stderr, re.M)
        summary = '%s, unittest exit code %d' % (ran.group(1) if ran else 'no test ran', done.returncode)
        results.append(('tests', done.returncode == 0, summary, [] if done.returncode == 0 else (done.stderr + done.stdout).splitlines()))
    else:
        results.append(('tests', True, 'no tests/ folder', []))

    for part, ok, summary, lines in results:
        print('%-5s %-10s %s' % ('ok' if ok else 'FAIL', part, summary))
        print(''.join('      %s\n' % line for line in lines), end='')
    return 0 if all(ok for _, ok, _, _ in results) else 1


def main(argv):
    if not argv or argv[0] in ('help', '--help', '-h'):
        print(USAGE, end='')
        return 0
    word, rest = argv[0], argv[1:]
    if word == 'list':
        return list_commands(rest)
    if word == 'doctor':
        return doctor(rest)
    if word == 'paths':
        return paths.main(rest)
    if word == 'mod':
        from portkit import mods
        return mods.main(rest)
    if word == 'selftest':
        options(rest)
        return selftest()
    return run(argv)
