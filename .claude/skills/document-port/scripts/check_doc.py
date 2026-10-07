#!/usr/bin/env python3
"""Check the commands, the links and the form of Markdown documents of this repository.

    python3 .claude/skills/document-port/scripts/check_doc.py [--no-help] [--max-lines N] FILE.md [FILE.md ...]

For each file the program finds these faults:

    command    A text `./port WORDS` whose words are not a command of `./port list`.
    option     An option (`--name`) of a `./port` command line that the help of that command
               does not have. The program runs `./port COMMAND --help` one time for each
               command. It does this only for a program that has a help text (its file has
               `argparse` or `--help`): a program with no help text would start its work.
               For the other commands the program checks the name only, and says so.
    link       A Markdown link `[text](path)` whose path is not a file or a folder. A link to
               a web address or to a heading (`#name`) is not checked.
    path       A path of one computer (`/home/NAME`, `/Users/NAME`, `~/`).
    dash       An em dash or an en dash.
    skill      For a file with the name SKILL.md: the front matter does not have exactly the
               keys `name` and `description`, the name is not the name of the folder, the
               description has more than 1024 characters, or the file has more than
               --max-lines lines (default 150).

The exit code is 1 when a file has a fault. `--no-help` does not run a command: the options
are then not checked. The program writes no file.
"""
import argparse
import json
import os
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(ROOT, 'portkit', '__init__.py')) and ROOT != os.path.dirname(ROOT):
    ROOT = os.path.dirname(ROOT)

PORT = os.path.join(ROOT, 'port')
# The commands of ./port itself, with the options of each one. None: each option is permitted
# (`mod build` gives its arguments to esx).
BUILT_IN = {
    'list': {'--json'}, 'doctor': {'--json'}, 'paths': {'--json'}, 'selftest': set(), 'help': set(),
    'mod list': set(), 'mod status': set(), 'mod sync': {'--force'}, 'mod build': None, 'mod': set(),
}
# A program that gets its help text from a module that it imports.
HELP_BY_IMPORT = {'destiny/extract/d2x_cli.py'}
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
PLACEHOLDER = re.compile(r'^[A-Z][A-Z0-9_]*$|^\.+$|^…$')
WORD = re.compile(r'^[a-z][a-z0-9_-]*$')


def commands():
    out = subprocess.run([PORT, 'list', '--json'], capture_output=True, text=True, env=ENV, cwd=ROOT)
    if out.returncode:
        sys.exit('check_doc: `./port list --json` failed: %s' % out.stderr.strip())
    return {c['name']: c for c in json.loads(out.stdout)}


def has_help(command):
    """True when the program of a command has a help text, so `--help` does not start its work."""
    files = [w for w in command['run'][1:] if w.endswith(('.py', '.sh'))]
    if not files:
        return False
    path = files[-1]
    if path in HELP_BY_IMPORT:
        return True
    try:
        with open(os.path.join(ROOT, path), encoding='utf-8') as f:
            text = f.read()
    except OSError:
        return False
    return 'argparse' in text or '--help' in text


class Help:
    def __init__(self, table, run):
        self.table, self.run, self.texts = table, run, {}

    def options(self, name):
        """The set of the options in the help of a command, or None when it is not known."""
        if not self.run or not has_help(self.table[name]):
            return None
        if name not in self.texts:
            out = subprocess.run([PORT] + name.split() + ['--help'], capture_output=True, text=True, env=ENV, cwd=ROOT)
            self.texts[name] = set(re.findall(r'(?<![\w-])--[a-z0-9][a-z0-9-]*', out.stdout + out.stderr))
        return self.texts[name]


def join_lines(text):
    """The lines of a text, with a line that ends in a backslash joined to the next one."""
    lines, buffer, first = [], '', 0
    for number, line in enumerate(text.split('\n'), 1):
        if not buffer:
            first = number
        if line.rstrip().endswith('\\'):
            buffer += line.rstrip()[:-1] + ' '
            continue
        lines.append((first, buffer + line))
        buffer = ''
    if buffer:
        lines.append((first, buffer))
    return lines


def words_after(rest):
    """The words of a command line after `./port`, to the end of the command."""
    rest = re.split(r'`|\s\|\s|;|&&|\s#|\s>\s|\)\s|\)$', rest, maxsplit=1)[0]
    words = re.findall(r'"[^"]*"|\'[^\']*\'|\S+', rest)
    out = []
    for w in words:
        if not w.startswith(('"', "'")) and not re.match(r'^\.+$', w):
            w = w.rstrip('.,:')
        if w:
            out.append(w)
    return out


def option_names(words):
    names = []
    for w in words:
        m = re.match(r'^\[?(--[a-z0-9][a-z0-9-]*)', w)
        if m:
            names.append(m.group(1))
    return names


def check_port(lines, table, helps, faults, stats):
    for number, line in lines:
        for m in re.finditer(r'(?<![\w/.])\./port(?![\w./])', line):
            rest = line[m.end():]
            if m.start() and line[m.start() - 1] in '"\'':    # a command in quotes ends at the next quote
                rest = rest.split(line[m.start() - 1], 1)[0]
            words = words_after(rest)
            if not words or not WORD.match(words[0]):
                continue                                    # `./port`, `./port AREA COMMAND`, `./port (text`
            stats['commands'] += 1
            head = [w for w in words[:3]]
            name = None
            for count in (2, 1):                            # the commands of ./port itself
                key = ' '.join(head[:count])
                if key in BUILT_IN:
                    name, allowed = key, BUILT_IN[key]
                    break
            if name is not None:
                if name == 'mod' and len(head) > 1 and not PLACEHOLDER.match(head[1]) and not head[1].startswith('-'):
                    faults.append((number, 'command', '`./port %s` is not a command of ./port mod' % ' '.join(head[:2])))
                elif allowed is not None:
                    for option in option_names(words):
                        if option not in allowed and option != '--help':
                            faults.append((number, 'option', '`./port %s` has no option %s' % (name, option)))
                continue
            for count in (3, 2):
                key = ' '.join(head[:count])
                if key in table:
                    name = key
                    break
            if name is None:
                prefix = []
                for w in head:
                    if not WORD.match(w):
                        break
                    prefix.append(w)
                key = ' '.join(prefix)
                if len(prefix) < 3 and any(n.startswith(key + ' ') for n in table) and all(
                        PLACEHOLDER.match(w) or w.startswith(('-', '[')) for w in head[len(prefix):]):
                    continue                                # `./port destiny`, `./port destiny check ...`, `./port marathon notes NAME`
                faults.append((number, 'command', '`./port %s` is not a command (`./port list`)' % ' '.join(head)))
                continue
            options = [o for o in option_names(words) if o != '--help']
            if not options:
                continue
            known = helps.options(name)
            if known is None:
                stats['not checked'].add(name)
                continue
            stats['options'] += len(options)
            for option in options:
                if option not in known:
                    faults.append((number, 'option', 'the help of `./port %s` has no option %s' % (name, option)))


def check_links(path, text, faults, stats):
    folder = os.path.dirname(os.path.abspath(path))
    in_code = False
    for number, line in enumerate(text.split('\n'), 1):
        if line.lstrip().startswith('```'):
            in_code = not in_code
        if in_code:
            continue
        for m in re.finditer(r'\[[^\]\n]*\]\(([^)\s]+)\)', line):
            target = m.group(1)
            if re.match(r'^[a-z][a-z0-9+.-]*:', target) or target.startswith('#'):
                continue
            stats['links'] += 1
            target = target.split('#', 1)[0]
            if not os.path.exists(os.path.normpath(os.path.join(folder, target))):
                faults.append((number, 'link', 'no target: %s' % m.group(1)))


def check_form(text, faults):
    for number, line in enumerate(text.split('\n'), 1):
        if re.search(r'/home/[A-Za-z0-9_.-]+|/Users/[A-Za-z0-9_.-]+|(?<![\w.])~/', line):
            faults.append((number, 'path', 'a path of one computer'))
        if '—' in line or '–' in line:
            faults.append((number, 'dash', 'an em dash or an en dash'))


def check_skill(path, text, faults, max_lines):
    lines = text.split('\n')
    if lines[0] != '---' or '---' not in lines[1:]:
        faults.append((1, 'skill', 'the file does not start with a front matter between two lines `---`'))
        return
    end = lines.index('---', 1)
    keys = {}
    for number, line in enumerate(lines[1:end], 2):
        m = re.match(r'^([A-Za-z_-]+):\s?(.*)$', line)
        if not m:
            faults.append((number, 'skill', 'a line of the front matter is not `key: text` on one line'))
            continue
        keys[m.group(1)] = m.group(2)
    if sorted(keys) != ['description', 'name']:
        faults.append((1, 'skill', 'the front matter has the keys %s, not exactly `name` and `description`' % sorted(keys)))
    folder = os.path.basename(os.path.dirname(os.path.abspath(path)))
    name = keys.get('name', '')
    if name != folder or not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', name):
        faults.append((2, 'skill', 'the name `%s` is not the name of the folder `%s` (small letters, digits, hyphens)' % (name, folder)))
    description = keys.get('description', '')
    if not description or len(description) > 1024:
        faults.append((3, 'skill', 'the description has %d characters (1 to 1024 are permitted)' % len(description)))
    if re.search(r':\s', description) or ' #' in description or description[:1] in '\'"`[{>|*&!%@':
        faults.append((3, 'skill', 'the description is not a plain YAML text on one line (it has `: `, ` #`, or a special first character)'))
    count = len(lines) - (1 if lines[-1] == '' else 0)
    if count > max_lines:
        faults.append((count, 'skill', 'the file has %d lines (the limit is %d): move a table to references/' % (count, max_lines)))


def main():
    ap = argparse.ArgumentParser(description='Check the commands, the links and the form of Markdown documents.')
    ap.add_argument('files', nargs='+', help='Markdown files')
    ap.add_argument('--no-help', action='store_true', help='do not run `./port COMMAND --help`: the options are not checked')
    ap.add_argument('--max-lines', type=int, default=150, help='the largest count of lines of a SKILL.md (default 150)')
    a = ap.parse_args()

    table = commands()
    helps = Help(table, not a.no_help)
    bad = 0
    totals = {'commands': 0, 'options': 0, 'links': 0}
    not_checked = set()
    for path in a.files:
        with open(path, encoding='utf-8') as f:
            text = f.read()
        faults = []
        stats = {'commands': 0, 'options': 0, 'links': 0, 'not checked': set()}
        check_port(join_lines(text), table, helps, faults, stats)
        check_links(path, text, faults, stats)
        check_form(text, faults)
        if os.path.basename(path) == 'SKILL.md':
            check_skill(path, text, faults, a.max_lines)
        shown = os.path.relpath(path, ROOT) if os.path.abspath(path).startswith(ROOT + os.sep) else path
        print('%-5s %s: %d command lines, %d options, %d links' % (
            'FAULT' if faults else 'ok', shown, stats['commands'], stats['options'], stats['links']))
        for number, kind, message in sorted(faults):
            print('      line %d, %s: %s' % (number, kind, message))
        bad += 1 if faults else 0
        for key in totals:
            totals[key] += stats[key]
        not_checked |= stats['not checked']
    print('%d files, %d with a fault; %d command lines, %d options against the help, %d links' % (
        len(a.files), bad, totals['commands'], totals['options'], totals['links']))
    if helps.texts:
        print('the help of %d commands was read: %s' % (len(helps.texts), ', '.join(sorted(helps.texts))))
    if not_checked:
        print('the options of these commands were not checked (%s): %s' % (
            'the option --no-help' if a.no_help else 'the program has no help text', ', '.join(sorted(not_checked))))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
