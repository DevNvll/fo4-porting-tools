"""The tests of portkit and of ./port. They need no game file and no network.

    ./port selftest                             # the usual way
    python3 -B -m unittest discover -s tests    # the tests only

Most tests make a temporary copy of the layout (`port`, `portkit/`, their own port.toml
files and mods), and run `./port` there with FO4PORTS_DATA and a PATH that has only a shell.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True
sys.path.insert(0, ROOT)

from portkit import cli, paths  # noqa: E402

SETTING_VARIABLES = [row[0] for row in paths.SETTINGS.values()]

SHOW = """\
import json, os, sys
import portkit
try:
    import demo_library
except ImportError:
    demo_library = None
keys = ['FO4PORTS_ROOT', 'FO4PORTS_DATA', 'PYTHONPATH', 'PYTHONDONTWRITEBYTECODE', 'DEMO_FILE', 'DEMO_WORD', 'FAKE_D2X'] + %r
print(json.dumps({'argv': sys.argv, 'cwd': os.getcwd(), 'library': bool(demo_library),
                  'env': {key: os.environ[key] for key in keys if key in os.environ}}))
""" % SETTING_VARIABLES

DEMO = """\
[[command]]
name = "demo show"
help = "Print the arguments and the environment."
run = ["python", "demo/show.py", "fixed", "demo/files", "--out=demo/files"]
env = { PYTHONPATH = "demo/lib", DEMO_FILE = "demo/show.py", DEMO_WORD = "plain" }

[[command]]
name = "demo show deep"
help = "A name of three words."
run = ["python", "demo/show.py", "deep"]

[[command]]
name = "demo fail"
help = "Give the exit code 7."
run = ["sh", "demo/fail.sh"]

[[command]]
name = "demo tool"
help = "A program with a path from the root."
run = ["demo/tool.sh"]

[[command]]
name = "demo rig"
help = "A command that needs a file of data/ and a setting."
run = ["python", "demo/show.py"]
needs = ["data/demo/rig/skeleton.hkx", "blender"]

[[command]]
name = "demo d2x"
help = "A command for the Python of d2x."
run = ["python:d2x", "demo/show.py"]
needs = ["data/destiny/extract/venv/bin/python"]

[[check]]
path = "data/demo/rig"
what = "The rig folder of the demo."
make = "./port demo make-rig --from GAME"
"""

FAKE_ESX = """\
#!%s
import json, os, sys
arguments = sys.argv[1:]
project = arguments[arguments.index('build') + 1]
with open(os.path.join(project, 'esx_arguments.json'), 'w') as f:
    json.dump(arguments, f)
if '--fail' in arguments:
    sys.exit(7)
if '--update-lock' in arguments:
    with open(os.path.join(project, 'ids.lock'), 'a') as f:
        f.write('NewRecord = 0x801\\n')
os.makedirs(os.path.join(project, 'build', 'release'), exist_ok=True)
for name in ('DemoPlugin.esp', 'DemoPlugin - Main.ba2', 'DemoPlugin - Textures.ba2'):
    with open(os.path.join(project, 'build', 'release', name), 'w') as f:
        f.write(name)
print('fake esx: ok')
""" % sys.executable


class Layout(unittest.TestCase):
    """A temporary repository (`port`, `portkit/`) with its data folder beside it."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.tmp = os.path.realpath(folder.name)
        self.root, self.data, self.bin = (os.path.join(self.tmp, name) for name in ('repo', 'moved_data', 'bin'))
        for made in (self.root, self.data, self.bin):
            os.makedirs(made)
        shutil.copy2(os.path.join(ROOT, 'port'), self.root)
        shutil.copytree(os.path.join(ROOT, 'portkit'), os.path.join(self.root, 'portkit'), ignore=shutil.ignore_patterns('__pycache__'))
        for shell in ('sh', 'bash'):
            if shutil.which(shell):
                os.symlink(shutil.which(shell), os.path.join(self.bin, shell))
        self.env = {key: value for key, value in os.environ.items() if key not in SETTING_VARIABLES + ['PYTHONPATH']}
        self.env.update(FO4PORTS_DATA=self.data, PATH=self.bin)

    def write(self, path, content='', executable=False):
        """Write a file. `path` is from the temporary folder."""
        path = os.path.join(self.tmp, path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        if executable:
            os.chmod(path, 0o755)
        return path

    def read(self, path):
        with open(os.path.join(self.tmp, path)) as f:
            return f.read()

    def port(self, *arguments, cwd=None, **variables):
        """Run ./port in the temporary repository."""
        return subprocess.run([sys.executable, os.path.join(self.root, 'port'), *arguments], cwd=cwd or self.tmp,
                              env=dict(self.env, **variables), capture_output=True, text=True)

    def demo(self):
        self.write('repo/demo/port.toml', DEMO)
        self.write('repo/demo/show.py', SHOW)
        self.write('repo/demo/lib/demo_library.py', '')
        self.write('repo/demo/files/one.txt', '')
        self.write('repo/demo/fail.sh', 'exit 7\n')
        self.write('repo/demo/tool.sh', '#!/bin/sh\necho "tool $FO4PORTS_ROOT $*"\n', executable=True)


class Settings(Layout):
    def blender(self, **variables):
        done = self.port('paths', '--json', **variables)
        self.assertEqual(done.returncode, 0, done.stderr)
        facts = json.loads(done.stdout)
        self.assertEqual((facts['root'], facts['data']), (self.root, self.data))
        row = next(row for row in facts['settings'] if row['name'] == 'blender')
        return row['value'], row['source']

    def test_order_environment_config_path(self):
        in_path = self.write('bin/blender', '#!/bin/sh\n', executable=True)
        self.write('moved_data/config.toml', 'blender = "/from/config"\n')
        self.assertEqual(self.blender(BLENDER='/from/environment'), ('/from/environment', 'environment'))
        self.assertEqual(self.blender(), ('/from/config', 'config'))
        os.remove(os.path.join(self.data, 'config.toml'))
        self.assertEqual(self.blender(), (in_path, 'path'))
        os.remove(in_path)
        self.assertEqual(self.blender(), (None, None))

    def test_get_one_value(self):
        done = self.port('paths', 'get', 'fo4_data', FO4_DATA='/games/Fallout 4/Data')
        self.assertEqual((done.returncode, done.stdout), (0, '/games/Fallout 4/Data\n'))
        self.assertEqual(self.port('paths', 'get', 'fo4_data').returncode, 1)


class PortToml(unittest.TestCase):
    """load() and match() on a temporary tree, in this process."""

    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = folder.name

    def write(self, path, content):
        path = os.path.join(self.root, path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(textwrap.dedent(content))

    def test_discovery(self):
        entry = '[[command]]\nname = "%s"\nhelp = "Help."\nrun = ["python", "x.py"]\n'
        for number, path in enumerate(('b/c/port.toml', 'a/port.toml', 'data/x/port.toml', '.git/port.toml', 'a/__pycache__/port.toml')):
            self.write(path, entry % ('area c%d' % number))
        commands, checks, problems = cli.load(self.root)
        self.assertEqual(problems, [])
        self.assertEqual(sorted(c['source'] for c in commands.values()), ['a/port.toml', 'b/c/port.toml'])
        self.assertEqual(commands['area c1'], {'name': 'area c1', 'help': 'Help.', 'run': ['python', 'x.py'], 'env': {}, 'needs': [], 'source': 'a/port.toml'})

    def test_validation(self):
        self.write('a/port.toml', '''\
            title = "not a known key"
            [[command]]
            name = "area good"
            help = "A correct command."
            run = ["python", "a/x.py"]
            needs = ["blender", "data/a/rig"]
            [[command]]
            name = "area extra"
            help = "Help."
            run = ["python", "a/x.py"]
            cwd = "a"
            [[command]]
            name = "alone"
            help = "Help."
            run = ["python", "a/x.py"]
            [[command]]
            name = "area with four words"
            help = "Help."
            run = ["python", "a/x.py"]
            [[command]]
            name = "list all"
            help = "Help."
            run = ["python", "a/x.py"]
            [[command]]
            name = "area nohelp"
            run = ["python", "a/x.py"]
            [[command]]
            name = "area norun"
            help = "Help."
            run = ["python"]
            [[command]]
            name = "area badenv"
            help = "Help."
            run = ["sh", "a/x.sh"]
            env = { COUNT = 3 }
            [[command]]
            name = "area badneed"
            help = "Help."
            run = ["sh", "a/x.sh"]
            needs = ["blendr"]
            [[check]]
            path = "data/a/rig"
            what = "The rig."
            make = "./port area make-rig"
            [[check]]
            path = "data/a/rig"
            setting = "blender"
            what = "Two subjects."
            [[check]]
            setting = "blendr"
            what = "Not a setting."
            [[check]]
            setting = "esx"
            ''')
        self.write('b/port.toml', '[[command]]\nname = "area good"\nhelp = "The same name."\nrun = ["python", "b/x.py"]\n')
        self.write('c/port.toml', '[[command]\nname = ')
        commands, checks, problems = cli.load(self.root)
        self.assertEqual(list(commands), ['area good'])
        self.assertEqual(commands['area good']['source'], 'a/port.toml')
        self.assertEqual([(c['path'], c['make'], c['source']) for c in checks], [('data/a/rig', './port area make-rig', 'a/port.toml')])
        text = '\n'.join(problems)
        for part in ('a/port.toml: unknown key `title`', 'command `area extra`: unknown key `cwd`', 'command `alone`: `name` must have two or three words',
                     'command `area with four words`: `name` must have', 'command `list all`: `list` is a command of ./port',
                     'command `area nohelp`: `help` must be', 'command `area norun`: `run` must have a program file after `python`',
                     'command `area badenv`: `env` must be', 'command `area badneed`: `needs`: `blendr` is not a setting',
                     'check `data/a/rig`: give `path` or `setting`', 'check `blendr`: `blendr` is not a setting', 'check `esx`: `what` is necessary',
                     'b/port.toml: command `area good`: the name is also in a/port.toml', 'c/port.toml: '):
            self.assertIn(part, text)
        self.assertEqual(len(problems), 14, text)

    def test_program_file_must_be_there(self):
        self.write('a/port.toml', '''\
            [[command]]
            name = "area there"
            help = "Help."
            run = ["python", "port"]
            [[command]]
            name = "area missing"
            help = "Help."
            run = ["sh", "a/not_there.sh"]
            [[command]]
            name = "area plain"
            help = "A program that is a file but is not executable."
            run = ["portkit/paths.py"]
            [[command]]
            name = "area option"
            help = "The word after the runner must be the program file."
            run = ["python", "-m", "portkit.paths"]
            ''')
        commands, _, problems = cli.load(self.root)
        self.assertEqual(problems, ['a/port.toml: command `area option`: `run` must have a program file after `python` (a path from the root, not an option)'])
        self.assertEqual(cli.program_faults(commands), [
            'a/port.toml: command `area missing`: the program a/not_there.sh is not there',
            'a/port.toml: command `area plain`: the program portkit/paths.py is not executable'])

    def test_check_of_a_need(self):
        checks = [{'path': 'data/rig', 'what': 'Folder.', 'make': 'make folder', 'source': 'a/port.toml'},
                  {'path': 'data/rig/one.hkx', 'what': 'File.', 'source': 'a/port.toml'},
                  {'setting': 'blender', 'what': 'First.', 'make': 'first', 'source': 'a/port.toml'},
                  {'setting': 'blender', 'what': 'Second.', 'make': 'second', 'source': 'b/port.toml'}]
        self.assertEqual(cli.check_for('data/rig/one.hkx', checks)['what'], 'Folder.')
        self.assertEqual(cli.check_for('data/rig/one.hkx', checks[1:])['what'], 'File.')
        self.assertEqual(cli.check_for('data/rig/two.hkx', checks)['what'], 'Folder.')
        self.assertEqual(cli.check_for('data/rig', checks)['what'], 'Folder.')
        self.assertIsNone(cli.check_for('data/rigs/two.hkx', checks))
        self.assertEqual(cli.check_for('blender', checks, 'b/port.toml')['make'], 'second')
        self.assertEqual(cli.check_for('blender', checks, 'c/port.toml')['make'], 'first')
        self.assertIsNone(cli.check_for('esx', checks))

    def test_longest_name_wins(self):
        commands = {name: {'name': name} for name in ('area make', 'area make rig', 'area other')}
        self.assertEqual(cli.match(commands, ['area', 'make', 'rig', 'x']), (commands['area make rig'], ['x']))
        self.assertEqual(cli.match(commands, ['area', 'make', 'x', 'rig']), (commands['area make'], ['x', 'rig']))
        self.assertEqual(cli.match(commands, ['area', 'make']), (commands['area make'], []))
        self.assertEqual(cli.match(commands, ['area']), (None, ['area']))
        self.assertEqual(cli.match(commands, ['area', 'mak', 'rig']), (None, ['area', 'mak', 'rig']))


class Run(Layout):
    def setUp(self):
        super().setUp()
        self.demo()

    def shown(self, *arguments, **variables):
        done = self.port(*arguments, **variables)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_environment_and_command_line(self):
        elsewhere = os.path.join(self.tmp, 'elsewhere')
        os.makedirs(elsewhere)
        done = self.port('demo', 'show', 'my file.glb', '--flag', cwd=elsewhere, BLENDER='/opt/blender', PYTHONPATH='/of/caller')
        self.assertEqual(done.returncode, 0, done.stderr)
        shown = json.loads(done.stdout)
        program = os.path.join(self.root, 'demo', 'show.py')
        files = os.path.join(self.root, 'demo', 'files')
        self.assertEqual(shown['argv'], [program, 'fixed', files, '--out=demo/files', 'my file.glb', '--flag'])
        self.assertEqual(shown['cwd'], elsewhere)
        self.assertTrue(shown['library'])
        self.assertEqual(shown['env'], {
            'FO4PORTS_ROOT': self.root, 'FO4PORTS_DATA': self.data, 'BLENDER': '/opt/blender', 'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONPATH': os.pathsep.join([self.root, os.path.join(self.root, 'demo', 'lib'), '/of/caller']),
            'DEMO_FILE': program, 'DEMO_WORD': 'plain'})
        self.assertEqual([folder for folder, _, _ in os.walk(self.root) if os.path.basename(folder) == '__pycache__'], [])

    def test_each_setting_with_a_value_is_a_variable(self):
        self.write('moved_data/config.toml', 'fo4_data = "/games/Fallout 4/Data"\nmarathon_game = "/games/Marathon"\n')
        env = self.shown('demo', 'show', PROTON_DIR='/proton')['env']
        self.assertEqual({key: env.get(key) for key in SETTING_VARIABLES}, {
            'BLENDER': None, 'ESX_BIN': None, 'FO4_DATA': '/games/Fallout 4/Data', 'PROTON_DIR': '/proton',
            'D2X_GAME': None, 'MARATHON_GAME': '/games/Marathon', 'NVCS_SKELETON': None})

    def test_name_of_three_words(self):
        self.assertEqual(self.shown('demo', 'show', 'deep', 'x')['argv'][1:], ['deep', 'x'])
        self.assertEqual(self.shown('demo', 'show', 'x', 'deep')['argv'][1:], ['fixed', os.path.join(self.root, 'demo', 'files'), '--out=demo/files', 'x', 'deep'])

    def test_exit_code_and_runners(self):
        self.assertEqual(self.port('demo', 'fail').returncode, 7)
        done = self.port('demo', 'tool', 'a', 'b')
        self.assertEqual((done.returncode, done.stdout), (0, 'tool %s a b\n' % self.root))

    def test_port_starts_alone(self):
        done = subprocess.run([os.path.join(self.root, 'port'), '--help'], env=dict(self.env, PATH=os.environ['PATH']), capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        for document in ('README.md', 'docs/ARCHITECTURE.md', 'AGENTS.md'):
            self.assertIn(document, done.stdout)
        self.assertEqual(self.port('help').stdout, done.stdout)
        self.assertEqual(self.port().stdout, done.stdout)

    def test_list(self):
        rows = json.loads(self.port('list', '--json').stdout)
        self.assertEqual([row['name'] for row in rows], ['demo d2x', 'demo fail', 'demo rig', 'demo show', 'demo show deep', 'demo tool'])
        self.assertEqual(rows[3], {'name': 'demo show', 'help': 'Print the arguments and the environment.',
                                   'run': ['python', 'demo/show.py', 'fixed', 'demo/files', '--out=demo/files'],
                                   'env': {'PYTHONPATH': 'demo/lib', 'DEMO_FILE': 'demo/show.py', 'DEMO_WORD': 'plain'},
                                   'needs': [], 'source': 'demo/port.toml'})
        self.assertEqual(rows[2]['needs'], ['data/demo/rig/skeleton.hkx', 'blender'])
        lines = self.port('list').stdout.splitlines()
        self.assertEqual(len(lines), 6)
        self.assertRegex(lines[1], r'^demo fail +Give the exit code 7\.  \[demo/port\.toml\]$')
        for words in (['demo'], ['demo', '--help']):
            area = self.port(*words)
            self.assertEqual((area.returncode, area.stdout.splitlines()), (0, lines))
        self.write('repo/demo/more.sh', 'exit 0\n')
        self.write('repo/demo/more/port.toml', '[[command]]\nname = "demo fail more"\nhelp = "Help."\nrun = ["sh", "demo/more.sh"]\n')
        names = self.port('demo', 'show')
        self.assertEqual(names.returncode, 0)
        self.assertEqual(json.loads(names.stdout)['argv'][1], 'fixed')
        names = self.port('demo', 'fail', '--help')
        self.assertEqual(names.returncode, 7)
        self.write('repo/demo/port.toml', DEMO.replace('"demo fail"', '"demo fail now"'))
        for words in (['demo', 'fail'], ['demo', 'fail', '-h']):
            names = self.port(*words)
            self.assertEqual(names.returncode, 0)
            self.assertEqual([line.split('  ')[0] for line in names.stdout.splitlines()], ['demo fail more', 'demo fail now'])
        self.assertEqual(self.port('demo', 'fail', 'x').returncode, 2)
        self.assertEqual(self.port('list', '--jsn').returncode, 2)

    def test_unknown_command(self):
        done = self.port('demo', 'shwo', 'x')
        self.assertEqual((done.returncode, done.stdout), (2, ''))
        self.assertIn('`demo shwo x` does not start with the name of a command. The nearest names:', done.stderr)
        self.assertIn('  demo show  ', done.stderr)
        self.assertNotIn('demo fail', done.stderr)
        done = self.port('dmo', 'show')
        self.assertEqual(done.returncode, 2)
        self.assertIn('`dmo` is not a command and not an area. The nearest names: demo', done.stderr)
        done = self.port('demo', 'zzzzzz')
        self.assertEqual(done.returncode, 2)
        self.assertIn('The commands of `demo`:', done.stderr)
        self.assertIn('demo fail', done.stderr)

    def test_a_fault_in_a_port_toml_does_not_stop_the_other_commands(self):
        self.write('repo/other/port.toml', '[[command]]\nname = "other broken"\nhelp = "Help."\n')
        self.assertEqual(self.port('demo', 'fail').returncode, 7)
        done = self.port('other', 'broken')
        self.assertEqual(done.returncode, 2)
        self.assertIn('other/port.toml: command `other broken`: `run` must be a list of words', done.stderr)
        self.assertIn('other/port.toml: command `other broken`', self.port('list').stderr)

    def test_needs(self):
        done = self.port('demo', 'rig')
        self.assertEqual((done.returncode, done.stdout), (3, ''))
        self.assertIn('`demo rig` cannot start (demo/port.toml).', done.stderr)
        self.assertIn('data/demo/rig/skeleton.hkx is not there. The rig folder of the demo.', done.stderr)
        self.assertIn('make: ./port demo make-rig --from GAME', done.stderr)
        self.assertIn('The setting `blender` has no value.', done.stderr)
        self.assertIn('environment variable BLENDER', done.stderr)

        self.write('moved_data/demo/rig/skeleton.hkx')
        done = self.port('demo', 'rig', BLENDER=os.path.join(self.tmp, 'no_blender'))
        self.assertEqual(done.returncode, 3)
        self.assertNotIn('skeleton.hkx', done.stderr)
        self.assertIn('The setting `blender` is %s, and that is not there.' % os.path.join(self.tmp, 'no_blender'), done.stderr)

        blender = self.write('tools/blender', executable=True)
        self.assertEqual(self.shown('demo', 'rig', 'x', BLENDER=blender)['argv'][1:], ['x'])

    def test_help_of_a_command_needs_nothing(self):
        self.assertEqual(self.shown('demo', 'rig', '--help')['argv'][1:], ['--help'])

    def test_python_of_d2x(self):
        done = self.port('demo', 'd2x')
        self.assertEqual((done.returncode, done.stdout), (3, ''))
        self.assertEqual(done.stderr.count('data/destiny/extract/venv/bin/python is not there.'), 1)
        self.assertIn('make: ./port destiny setup', done.stderr)
        self.assertEqual(self.port('demo', 'd2x', '--help').returncode, 3)
        self.write('moved_data/destiny/extract/venv/bin/python', '#!/bin/sh\nFAKE_D2X=1 exec "%s" "$@"\n' % sys.executable, executable=True)
        self.assertEqual(self.shown('demo', 'd2x', 'x')['env']['FAKE_D2X'], '1')


class Doctor(Layout):
    def test_doctor(self):
        self.demo()
        done = self.port('doctor', '--json')
        facts = json.loads(done.stdout)
        self.assertEqual((done.returncode, facts['ok']), (1, False))
        self.assertEqual(facts['python']['version'], '%d.%d.%d' % sys.version_info[:3])
        self.assertEqual((facts['root'], facts['data'], facts['config']), (self.root, self.data, os.path.join(self.data, 'config.toml')))
        self.assertEqual([row['name'] for row in facts['settings']], list(paths.SETTINGS))
        self.assertEqual(facts['checks'], [{'path': 'data/demo/rig', 'what': 'The rig folder of the demo.',
                                            'make': './port demo make-rig --from GAME', 'source': 'demo/port.toml', 'ok': False}])
        self.assertEqual(facts['tools'], [{'name': name, 'path': None, 'ok': False} for name in ('git', 'cargo', 'uv', 'ffmpeg')])
        self.assertIn(facts['numpy']['ok'], (True, False))
        self.assertEqual(facts['problems'], [])
        text = self.port('doctor')
        self.assertEqual(text.returncode, 1)
        self.assertIn('MISSING  data/demo/rig  The rig folder of the demo.  [demo/port.toml]', text.stdout)
        self.assertIn('make: ./port demo make-rig --from GAME', text.stdout)
        self.assertIn('not set  blender', text.stdout)
        self.assertIn('unused   fo4_data', text.stdout)

        os.makedirs(os.path.join(self.data, 'demo', 'rig'))
        program = self.write('tools/program', executable=True)
        there = {variable: self.tmp if kind == 'folder' else program for variable, kind, _, _ in paths.SETTINGS.values()}
        done = self.port('doctor', '--json', **there)
        facts = json.loads(done.stdout)
        self.assertEqual((done.returncode, facts['ok'], facts['checks'][0]['ok']), (0, True, True))
        self.assertEqual(self.port('doctor', **there).returncode, 0)


class Selftest(Layout):
    def test_selftest(self):
        self.demo()
        one_test = 'import unittest\nclass One(unittest.TestCase):\n    def test_one(self):\n        self.assertEqual(1, %d)\n'
        self.write('repo/tests/test_one.py', one_test % 1)
        self.write('repo/data/not_source.py', 'this is not Python (\n')
        self.write('moved_data/not_source.py', 'this is not Python (\n')
        done = self.port('selftest')
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        lines = done.stdout.splitlines()
        self.assertEqual(len(lines), 3, done.stdout)
        self.assertRegex(lines[0], r'^ok +python +\d+ files, 0 do not compile$')
        self.assertEqual(lines[1].split(), 'ok port.toml 1 files, 6 commands, 1 checks, 0 faults'.split())
        self.assertEqual(lines[2].split(), 'ok tests 1 test, unittest exit code 0'.split())

        self.write('repo/demo/bad.py', 'def broken(:\n')
        self.write('repo/demo/port.toml', DEMO + '[[command]]\nname = "demo gone"\nhelp = "Help."\nrun = ["sh", "demo/gone.sh"]\ncolor = "red"\n'
                   '[[command]]\nname = "demo lost"\nhelp = "Help."\nrun = ["sh", "demo/lost.sh"]\n')
        self.write('repo/tests/test_one.py', one_test % 2)
        done = self.port('selftest')
        self.assertEqual(done.returncode, 1)
        self.assertRegex(done.stdout, r'(?m)^FAIL +python +\d+ files, 1 do not compile$')
        self.assertIn('demo/bad.py: ', done.stdout)
        self.assertRegex(done.stdout, r'(?m)^FAIL +port.toml +1 files, 7 commands, 1 checks, 2 faults$')
        self.assertIn('demo/port.toml: command `demo gone`: unknown key `color`', done.stdout)
        self.assertIn('demo/port.toml: command `demo lost`: the program demo/lost.sh is not there', done.stdout)
        self.assertRegex(done.stdout, r'(?m)^FAIL +tests +1 test, unittest exit code 1$')
        self.assertEqual([folder for folder, _, _ in os.walk(self.root) if os.path.basename(folder) == '__pycache__'], [])


class Mods(Layout):
    def setUp(self):
        super().setUp()
        self.write('repo/mods/Demo/esx.toml', 'plugin = "DemoPlugin.esp"\n')
        self.write('repo/mods/Demo/items/10-gun.toml', 'name = "Gun"\n')
        self.write('repo/mods/Demo/behavior/gun/gun.bhv', 'graph\n')
        self.write('repo/mods/Demo/ids.lock', 'Gun = 0x800\n')
        self.write('repo/mods/Plain/README.md', 'A mod with no esx.toml.\n')
        self.esx = self.write('tools/esx', FAKE_ESX, executable=True)
        self.game = os.path.join(self.tmp, 'Fallout 4', 'Data')
        os.makedirs(self.game)

    def set_time(self, path, seconds):
        os.utime(os.path.join(self.tmp, path), ns=(seconds * 10**9, seconds * 10**9))

    def test_sync(self):
        self.write('moved_data/mods/Demo/assets/Meshes/gun.nif', 'mesh')
        done = self.port('mod', 'sync', 'Demo')
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.splitlines(), ['new      behavior/gun/gun.bhv', 'new      esx.toml', 'new      ids.lock', 'new      items/10-gun.toml',
                                                    'sync Demo: 4 of 4 files copied to %s.' % os.path.join(self.data, 'mods', 'Demo')])
        self.assertEqual(self.read('moved_data/mods/Demo/items/10-gun.toml'), 'name = "Gun"\n')
        self.assertEqual(self.port('mod', 'sync', 'Demo').stdout.splitlines(), ['sync Demo: 0 of 4 files copied to %s.' % os.path.join(self.data, 'mods', 'Demo')])

        self.write('repo/mods/Demo/items/10-gun.toml', 'name = "Better gun"\n')
        os.remove(os.path.join(self.root, 'mods', 'Demo', 'behavior', 'gun', 'gun.bhv'))
        done = self.port('mod', 'sync', 'mods/Demo/')
        self.assertEqual(done.stdout.splitlines()[0], 'changed  items/10-gun.toml')
        self.assertEqual(self.read('moved_data/mods/Demo/items/10-gun.toml'), 'name = "Better gun"\n')
        self.assertEqual(self.read('moved_data/mods/Demo/behavior/gun/gun.bhv'), 'graph\n')
        self.assertEqual(self.read('moved_data/mods/Demo/assets/Meshes/gun.nif'), 'mesh')

    def test_ids_lock_that_is_newer_in_data_stays(self):
        self.port('mod', 'sync', 'Demo')
        self.write('moved_data/mods/Demo/ids.lock', 'Gun = 0x800\nSight = 0x801\n')
        self.set_time('repo/mods/Demo/ids.lock', 1000)
        self.set_time('moved_data/mods/Demo/ids.lock', 2000)
        done = self.port('mod', 'sync', 'Demo')
        self.assertEqual(done.returncode, 1)
        self.assertIn('kept     ids.lock: the copy in', done.stdout)
        self.assertIn('Run `./port mod build Demo --update-lock` to keep it, or `./port mod sync Demo --force` to replace it.', done.stdout)
        self.assertEqual(self.read('moved_data/mods/Demo/ids.lock'), 'Gun = 0x800\nSight = 0x801\n')
        self.assertIn('different  ids.lock  (the newer file is in %s)' % os.path.join(self.data, 'mods', 'Demo'), self.port('mod', 'status', 'Demo').stdout)

        done = self.port('mod', 'sync', 'Demo', '--force')
        self.assertEqual((done.returncode, done.stdout.splitlines()[0]), (0, 'changed  ids.lock'))
        self.assertEqual(self.read('moved_data/mods/Demo/ids.lock'), 'Gun = 0x800\n')

    def test_ids_lock_that_is_older_in_data_is_replaced(self):
        self.port('mod', 'sync', 'Demo')
        self.write('moved_data/mods/Demo/ids.lock', 'Old = 0x800\n')
        self.set_time('repo/mods/Demo/ids.lock', 2000)
        self.set_time('moved_data/mods/Demo/ids.lock', 1000)
        done = self.port('mod', 'sync', 'Demo')
        self.assertEqual((done.returncode, done.stdout.splitlines()[0]), (0, 'changed  ids.lock'))
        self.assertEqual(self.read('moved_data/mods/Demo/ids.lock'), 'Gun = 0x800\n')

    def test_list_and_status(self):
        self.assertEqual(self.port('mod', 'list').stdout.splitlines(), ['Demo   DemoPlugin.esp  release: no', 'Plain  Plain.esp       release: no'])
        done = self.port('mod', 'status', 'Demo')
        self.assertEqual(done.returncode, 0)
        self.assertIn('missing    esx.toml', done.stdout)
        self.assertIn('Demo (DemoPlugin.esp): 4 of 4 source files differ', done.stdout)
        self.assertIn('release: not there. `./port mod build Demo` makes it.', done.stdout)
        self.port('mod', 'sync', 'Demo')
        self.assertIn('Demo (DemoPlugin.esp): 0 of 4 source files differ', self.port('mod', 'status', 'Demo').stdout)
        done = self.port('mod', 'status', 'Nothing')
        self.assertEqual(done.returncode, 2)
        self.assertIn('no mod has the name `Nothing`. The mods: Demo, Plain.', done.stderr)
        self.assertEqual(self.port('mod', 'sync').returncode, 2)

    def test_build(self):
        done = self.port('mod', 'build', 'Demo', '--update-lock', '--format', 'text', ESX_BIN=self.esx, FO4_DATA=self.game)
        self.assertEqual(done.returncode, 0, done.stderr)
        project = os.path.join(self.data, 'mods', 'Demo')
        self.assertEqual(json.loads(self.read('moved_data/mods/Demo/esx_arguments.json')),
                         ['--data', self.game, 'build', project, '--update-lock', '--format', 'text'])
        self.assertEqual(self.read('repo/mods/Demo/ids.lock'), 'Gun = 0x800\nNewRecord = 0x801\n')
        lines = done.stdout.splitlines()
        self.assertEqual(lines[4:7], ['sync Demo: 4 of 4 files copied to %s.' % project, 'fake esx: ok', 'ids.lock changed: copied to mods/Demo/ids.lock.'])
        files = ('DemoPlugin.esp', 'DemoPlugin - Main.ba2', 'DemoPlugin - Textures.ba2')
        self.assertEqual(lines[7:], ['release %s:' % os.path.join(project, 'build', 'release')] + [
            '%s  %s' % (hashlib.sha256(name.encode()).hexdigest(), name) for name in files])
        self.assertEqual(self.port('mod', 'list').stdout.splitlines()[0], 'Demo   DemoPlugin.esp  release: yes')

    def test_build_that_fails_keeps_the_lock_of_the_source(self):
        self.port('mod', 'sync', 'Demo')
        self.write('moved_data/mods/Demo/ids.lock', 'Gun = 0x800\nSight = 0x801\n')
        self.set_time('repo/mods/Demo/ids.lock', 1000)
        self.set_time('moved_data/mods/Demo/ids.lock', 2000)
        done = self.port('mod', 'build', 'Demo', '--fail', ESX_BIN=self.esx, FO4_DATA=self.game)
        self.assertEqual(done.returncode, 7)
        self.assertIn('The build uses it.', done.stdout)
        self.assertIn('The build failed, thus mods/Demo/ids.lock stays as it is.', done.stdout)
        self.assertNotIn('release', done.stdout)
        self.assertEqual(self.read('repo/mods/Demo/ids.lock'), 'Gun = 0x800\n')
        done = self.port('mod', 'build', 'Demo', ESX_BIN=self.esx, FO4_DATA=self.game)
        self.assertEqual(done.returncode, 0)
        self.assertEqual(self.read('repo/mods/Demo/ids.lock'), 'Gun = 0x800\nSight = 0x801\n')

    def test_build_needs_the_settings(self):
        done = self.port('mod', 'build', 'Demo', ESX_BIN=self.esx)
        self.assertEqual((done.returncode, done.stdout), (3, ''))
        self.assertIn('The setting `fo4_data` has no value.', done.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.data, 'mods', 'Demo')))


if __name__ == '__main__':
    unittest.main()
