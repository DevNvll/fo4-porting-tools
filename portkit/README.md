# portkit

The shared part of the repository. It uses only the standard library of Python 3.11 or later.

| File | What it does |
| --- | --- |
| `paths.py` | The folders and the local settings. Every program asks this module for a path. |
| `cli.py` | The `./port` command. It finds the commands in the `port.toml` files and runs them. |
| `mods.py` | `./port mod`. It copies `mods/NAME/` to `data/mods/NAME/` and builds with esx. |
| `../port` | The entry point. It calls `cli.main`. |
| `../tests/test_portkit.py` | The tests. They need no game file and no network. |

`docs/ARCHITECTURE.md` is the contract. This file is the reference for adding a command.

## The commands of `./port` itself

| Command | What it does | Exit code |
| --- | --- | --- |
| `./port help`, `./port --help`, `./port` | The usage. | 0 |
| `./port list [--json]` | Every command of every `port.toml`, sorted by name. | 0 |
| `./port AREA`, `./port AREA WORD` | The commands of one area, or the commands whose name starts with the two words, such as `./port destiny check`. | 0 |
| `./port AREA COMMAND [ARGUMENTS]` | Runs a command. | That of the program |
| `./port doctor [AREA] [--json]` | The Python version, numpy, Pillow as a report only, every setting, every `[[check]]`, and the programs `git`, `cargo`, `uv`, `ffmpeg`. AREA is `fnv`, `destiny`, `marathon`, or a path such as `destiny/port`, and limits the command to the `port.toml` files below that folder. The command names every key of `data/config.toml` that is not a setting. | 1 when a setting or a check is not ok, or when Python has no numpy |
| `./port paths [--json]`, `./port paths get NAME` | The folders and the settings. | 0. `get` gives 1 when there is no value. |
| `./port mod list`, `status NAME`, `sync NAME [--force]`, `build NAME [...]` | The mod projects. See below. | See below |
| `./port selftest` | Four parts. `python` compiles every `.py` file. `port.toml` checks that every table is correct and every program file exists. `tests` runs the tests of `tests/`. `git` checks that no file that git has, or can add, has a game file ending or a NUL byte. | 1 when a part fails |
| `./port baseline check` | Compares every file of the `[[baseline]]` patterns with `baselines.sha256`. It prints `DIFFERENT`, `not there` or `not in the list` for a file, and one line with the counts. | 1 when a file is different, or when `baselines.sha256` is missing |
| `./port baseline update` | Writes `baselines.sha256` again, with the sha256 and the path below `data/` of every file of the patterns. Only for a change that the user accepted. | 0 |

Other exit codes of `./port`:

* 2 means that the words are not a command, an argument is wrong, or the program file of the
  command is missing. For words that are not a command, `./port` prints the nearest names.
* 3 means that something the command needs is missing and the program did not start. The
  message says what is missing and how to make it.

A program can also exit with 2 or 3. A message from `./port` itself starts with `port:`.
`./port` starts a program with `exec`, so the program takes its place. The exit code is the
program's, and a signal to the process ID of `./port` goes to the program. A program that
imports `portkit` prints a file error as one line, and `FO4PORTS_TRACEBACK=1` shows the
traceback. A fault in `data/config.toml` is one line too.

## Add a command

Put a `port.toml` in the folder of your area. Any folder of the source tree works, but
`./port` does not look below `data/` or `.git/`. Then run `./port selftest`.

```toml
[[command]]
name = "destiny convert"
help = "Convert the clips of a set file to Fallout 4 clips."
run = ["python", "destiny/port/d2fo4.py"]
env = { PYTHONPATH = "destiny/extract" }
needs = ["blender", "data/fnv/rig/1st_skeleton.hkx"]

[[check]]
path = "data/fnv/rig/1st_skeleton.hkx"
what = "The rig folder of fnv: files of Fallout 4 and of the NVCS skeleton."
make = "./port fnv make-rig --nvcs /path/to/NVCS/Skeleton.nif"
```

### `[[command]]`

| Key | Necessary | Rule |
| --- | --- | --- |
| `name` | yes | Two or three words with one space between them. A word has lowercase letters, digits, `-` and `_`. The first word is the area. It cannot be `list`, `doctor`, `paths`, `mod`, `selftest`, `baseline` or `help`. A name can be in only one `port.toml`. |
| `help` | yes | One line of text. |
| `run` | yes | A list of words that starts the command line. The arguments of the user go after it. |
| `env` | no | A table of text values, the variables for the program. |
| `needs` | no | A list. Each entry is a setting of `paths.py` (`blender`, `esx`, `fo4_data`, `proton`, `destiny_game`, `marathon_game`, `nvcs_skeleton`) or a path from the root. A path has a `/` in it. |

No other key is allowed.

The first word of `run` is the runner:

| First word | What starts the program |
| --- | --- |
| `python` | The Python that runs `./port`. |
| `python:d2x` | `data/destiny/extract/venv/bin/python`. If it is missing, `./port` stops with exit code 3 and tells you to run `./port destiny setup`. |
| `sh`, `bash` | That shell, from the `PATH`. |
| a path from the root | That file. It must be executable. |

The word after `python`, `python:d2x`, `sh` or `bash` is the program file, as a path from the
root. A runner option such as `-m`, `-u` or `-e` is not allowed there.

The paths:

* A path from the root that starts with `data/` is a path in the data folder, so it stays
  correct when `FO4PORTS_DATA` moves that folder.
* The program file, every entry of `needs` that is not a setting, and every part of
  `PYTHONPATH` in `env` are always paths from the root.
* Every other word of `run` is a path from the root only when it has a `/` and its first
  part is `data` or the name of a file or a folder of the root (`fnv`, `destiny`,
  `marathon`, ...). The same goes for the other values of `env`, which `./port` splits at
  `:`. `./port` makes such a word an absolute path. All other words go to the program
  unchanged: `"convert"`, `"--"`, `"--out=data/x"`.

When two names start with the same words, the longest name wins. With `destiny check` and
`destiny check render`, the words `./port destiny check render x` run the second command.

### What the program gets

* The working folder of the caller, so a path that the user gives stays correct.
* `FO4PORTS_ROOT` and `FO4PORTS_DATA`.
* One variable for each setting that has a value: `BLENDER`, `ESX_BIN`, `FO4_DATA`,
  `PROTON_DIR`, `D2X_GAME`, `MARATHON_GAME`, `NVCS_SKELETON`. A setting without a value gives
  no variable.
* `PYTHONDONTWRITEBYTECODE=1`.
* `PYTHONPATH` with the root, then the folders of `env`, then the caller's `PYTHONPATH`.
* The other variables of `env`, and the environment of the caller.

### `needs`

Before the program starts, `./port` looks at every entry. A setting must have a value, and
its file or folder must exist. A path must exist. If one is missing, `./port` prints every
missing entry with the `make` line of its `[[check]]` and exits with 3.

When the arguments of the user have `--help` or `-h`, `./port` skips `needs`, so the help of
a command is always available. `python:d2x` still needs its Python.

### `[[check]]`

| Key | Necessary | Rule |
| --- | --- | --- |
| `path` or `setting` | one of them | A path from the root, or the name of a setting of `paths.py`. |
| `what` | yes | What this thing is. |
| `make` | no | How the user makes it, as a command or a short instruction. |

`./port doctor` shows every check. For a missing entry of `needs`, `./port` uses the check
with the same path or setting. If there is none, it uses the check of the nearest folder
above the path. A check with `make` comes before one without, and a check of the same
`port.toml` comes before a check of a different file.

### `[[baseline]]`

| Key | Necessary | Rule |
| --- | --- | --- |
| `files` | yes | A pattern that starts with `data/`. `*` is one name and `**` is each folder below. The files are stored results, either a baseline of a regress command or a release. |
| `what` | yes | What these files are. |

`./port baseline update` writes the sha256 of every file that matches a pattern into
`baselines.sha256`, in the root, and `./port baseline check` compares the files with that
list. A regress command compares new results with the stored results. The baseline check
proves that nobody replaced a stored result. `mods/port.toml` has only such tables.

### A fault in a `port.toml`

`./port selftest` shows every fault and exits with 1. The other commands skip a table that
has a fault and continue with the other tables. `./port list` and `./port doctor` print each
fault as a `port: fault:` line on stderr.

## The settings

`paths.py` has the table `SETTINGS`. A value comes from the environment variable, then from
`data/config.toml`, then, for a program only, from the `PATH`.

```python
from portkit import paths
paths.repo('fnv', 'tools')          # a path in the source tree
paths.data('fnv', 'rig')            # a path in the data folder
paths.program('blender')            # the value, or None
paths.require('fo4_data')           # the value; it stops with advice when there is none
paths.setting('name', env='NAME')   # a setting that is not in the table
paths.short(path)                   # a path for a message: from the root when it is in the repository
paths.advice('blender')             # the sentence that tells where to give the value
```

## The mod projects

`mods/NAME/` has the hand-written files. `data/mods/NAME/` is the complete esx project.

| Command | What it does | Exit code |
| --- | --- | --- |
| `./port mod list` | Every mod in `mods/`, its plugin (`plugin` of `esx.toml`, or `NAME.esp`), and whether `data/mods/NAME/build/release` has files. | 0 |
| `./port mod status NAME` | Every source file that is different in `data/mods/NAME/` or is not there, and the release. | 0 |
| `./port mod sync NAME [--force]` | Copies every new or changed file of `mods/NAME/` to the same place in `data/mods/NAME/`. It deletes nothing, and it prints each file that it copies. | 1 when it kept `ids.lock` |
| `./port mod build NAME [--update-lock] [ARGUMENTS]` | Syncs, runs `esx --data FO4_DATA build data/mods/NAME ARGUMENTS`, copies each lock file back, then prints each release file with its sha256. | That of esx. 3 when `esx` or `fo4_data` has no value. |

The lock files are `ids.lock` and `behavior/WEAPON/WEAPON.lock`. The two rules below say
`ids.lock` for both.

* `sync` does not replace an `ids.lock` of `data/mods/NAME/` that is different and newer than
  the file of `mods/NAME/`, and it tells you so. `./port mod build NAME --update-lock` keeps
  the file of `data/` and copies it back. `./port mod sync NAME --force` replaces it.
* `build` copies `data/mods/NAME/ids.lock` to `mods/NAME/ids.lock` when the two differ and
  esx exited with 0. When esx fails, `mods/NAME/ids.lock` stays as it is.

`build` passes every argument after `NAME` to `esx build`. esx prints one JSON document when
its output is not a terminal, and `--format text` gives text.

## The tests

```sh
./port selftest
python3 -B -m unittest discover -s tests     # the tests only
```

The tests make a temporary copy of `port` and `portkit/`, add their own `port.toml` files and
mods, and run `./port` there with `FO4PORTS_DATA`. A small program stands in for esx.
`./port selftest` compiles every `.py` file of the source tree from its source and writes no
`.pyc` file. It does not look below `data/`, `.git/`, `__pycache__`, `.venv` or `target`.
