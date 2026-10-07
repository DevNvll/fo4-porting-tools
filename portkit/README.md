# portkit

The shared part of the repository. It uses only the standard library of Python 3.11 or later.

| File | What it does |
| --- | --- |
| `paths.py` | The folders and the local settings. Each program asks this module for a path. |
| `cli.py` | The command `./port`: it finds the commands in the `port.toml` files and runs them. |
| `mods.py` | `./port mod`: the copy from `mods/NAME/` to `data/mods/NAME/`, and the build with esx. |
| `../port` | The entry point. It calls `cli.main`. |
| `../tests/test_portkit.py` | The tests. They need no game file and no network. |

`docs/ARCHITECTURE.md` is the contract. This file is the reference for a person who adds a
command.

## The commands of `./port` itself

| Command | What it does | Exit code |
| --- | --- | --- |
| `./port help`, `./port --help`, `./port` | The usage. | 0 |
| `./port list [--json]` | Each command of each `port.toml`, sorted by name. | 0 |
| `./port AREA`, `./port AREA WORD` | The commands of one area, or the commands whose name starts with the two words (`./port destiny check`). | 0 |
| `./port AREA COMMAND [ARGUMENTS]` | Run a command. | That of the program |
| `./port doctor [AREA] [--json]` | The Python version, numpy, Pillow (a report only), each setting, each `[[check]]`, and the programs `git`, `cargo`, `uv`, `ffmpeg`. AREA is `fnv`, `destiny`, `marathon`, or a path such as `destiny/port`: only the `port.toml` files below that folder. It names each key of `data/config.toml` that is not a setting. | 1 when a setting or a check is not ok, or when Python has no numpy |
| `./port paths [--json]`, `./port paths get NAME` | The folders and the settings. | 0 (`get`: 1 when there is no value) |
| `./port mod list`, `status NAME`, `sync NAME [--force]`, `build NAME [...]` | The mod projects. See below. | See below |
| `./port selftest` | Four parts. `python`: each `.py` file compiles. `port.toml`: each table is correct and each program file is there. `tests`: the tests of `tests/` pass. `git`: no file that git has, or can add, has a game file ending or a NUL byte. | 1 when a part fails |
| `./port baseline check` | Compares each file of the `[[baseline]]` patterns with `baselines.sha256`. It prints `DIFFERENT`, `not there` or `not in the list` for a file, and one line with the counts. | 1 when a file is different. 1 when `baselines.sha256` is not there. |
| `./port baseline update` | Writes `baselines.sha256` again: the sha256 and the path below `data/` of each file of the patterns. Only for a change that the user accepted. | 0 |

Other exit codes of `./port`:

* 2: the words are not a command, an argument is wrong, or the program file of the command is
  not there. For words that are not a command, `./port` prints the nearest names.
* 3: a thing that the command needs is missing. The program did not start. The message tells
  what is missing and how to make it.

A program can also give 2 or 3. The message of `./port` starts with `port:`. `./port` starts
a program with `exec`, so the program takes its place: the exit code is that of the program,
and a signal to the process ID of `./port` goes to the program. A program that imports
`portkit` shows a file error as one line (`FO4PORTS_TRACEBACK=1` shows the traceback). A
fault in `data/config.toml` is one line also.

## Add a command

Put a `port.toml` in the folder of your area (any folder of the source tree; `./port` does not
look below `data/` or `.git/`). Then run `./port selftest`.

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
| `name` | yes | Two or three words with one space between them. A word has small letters, digits, `-` and `_`. The first word is the area. It cannot be `list`, `doctor`, `paths`, `mod`, `selftest`, `baseline` or `help`. Each name is in only one `port.toml`. |
| `help` | yes | One line of text. |
| `run` | yes | A list of words: the start of the command line. The arguments of the user go after it. |
| `env` | no | A table of text values: variables for the program. |
| `needs` | no | A list. Each entry is a setting of `paths.py` (`blender`, `esx`, `fo4_data`, `proton`, `destiny_game`, `marathon_game`, `nvcs_skeleton`) or a path from the root. A path has a `/` in it. |

No other key is permitted.

The first word of `run` is the runner:

| First word | What starts the program |
| --- | --- |
| `python` | The Python that runs `./port`. |
| `python:d2x` | `data/destiny/extract/venv/bin/python`. When it is not there, `./port` stops with the exit code 3 and tells the user to run `./port destiny setup`. |
| `sh`, `bash` | That shell, from the `PATH`. |
| a path from the root | That file. It must be executable. |

The word after `python`, `python:d2x`, `sh` or `bash` is the program file: a path from the
root. An option of the runner (`-m`, `-u`, `-e`) is not permitted there.

The paths:

* A path from the root that starts with `data/` is a path in the data folder. Thus it is
  correct when `FO4PORTS_DATA` moves the data folder.
* The program file, each entry of `needs` that is not a setting, and each part of
  `PYTHONPATH` in `env` are always paths from the root.
* Each other word of `run`, and each part of each other value of `env` (the parts have `:`
  between them), is a path from the root only when it has a `/` and its first part is `data`
  or the name of a file or a folder of the root (`fnv`, `destiny`, `marathon`, ...). `./port`
  makes such a word an absolute path. All other words go to the program with no change:
  `"convert"`, `"--"`, `"--out=data/x"`.

When two names start with the same words, the longest name wins: with `destiny check` and
`destiny check render`, the words `./port destiny check render x` run the second command.

### What the program gets

* The working folder of the caller. Thus a path that the user gives is correct.
* `FO4PORTS_ROOT` and `FO4PORTS_DATA`.
* One variable for each setting that has a value: `BLENDER`, `ESX_BIN`, `FO4_DATA`,
  `PROTON_DIR`, `D2X_GAME`, `MARATHON_GAME`, `NVCS_SKELETON`. A setting with no value gives no
  variable.
* `PYTHONDONTWRITEBYTECODE=1`.
* `PYTHONPATH`: the root, then the folders of `env`, then the `PYTHONPATH` of the caller.
* The other variables of `env`, and the environment of the caller.

### `needs`

Before the program starts, `./port` looks at each entry. A setting must have a value, and its
file or folder must be there. A path must be there. If one is missing, `./port` prints each
missing entry with the `make` line of its `[[check]]`, and gives the exit code 3.

When the arguments of the user have `--help` or `-h`, `./port` does not look at `needs`, so
that the help of a command is always available. The Python of `python:d2x` is still necessary.

### `[[check]]`

| Key | Necessary | Rule |
| --- | --- | --- |
| `path` or `setting` | one of them | A path from the root, or the name of a setting of `paths.py`. |
| `what` | yes | What this thing is. |
| `make` | no | How the user makes it: a command, or a short instruction. |

`./port doctor` shows each check. For a missing entry of `needs`, `./port` uses the check with
the same path or setting. If there is none, it uses the check of the nearest folder above the
path. A check with `make` is before a check without it, and a check of the same `port.toml` is
before a check of a different file.

### `[[baseline]]`

| Key | Necessary | Rule |
| --- | --- | --- |
| `files` | yes | A pattern that starts with `data/` (`*` is one name, `**` is each folder below). The files are stored results: a baseline of a regress command, or a release. |
| `what` | yes | What these files are. |

`./port baseline update` writes the sha256 of each file of each pattern into
`baselines.sha256`, in the root, and `./port baseline check` compares the files with that
list. A regress command compares new results with the stored results. The baseline check
proves that nobody replaced a stored result. `mods/port.toml` has only such tables.

### A fault in a `port.toml`

`./port selftest` shows each fault and gives the exit code 1. The other commands do not use a
table that has a fault, and they continue with the other tables. `./port list` and
`./port doctor` print each fault as a `port: fault:` line (stderr).

## The settings

`paths.py` has the table `SETTINGS`. A value comes from the environment variable, then from
`data/config.toml`, then from the `PATH` (a program only).

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

`mods/NAME/` has the files that a person writes. `data/mods/NAME/` is the complete esx project.

| Command | What it does | Exit code |
| --- | --- | --- |
| `./port mod list` | Each mod of `mods/`, its plugin (`plugin` of `esx.toml`, or `NAME.esp`), and if `data/mods/NAME/build/release` has files. | 0 |
| `./port mod status NAME` | Each source file that is different in `data/mods/NAME/` or is not there, and the release. | 0 |
| `./port mod sync NAME [--force]` | Copy each new or changed file of `mods/NAME/` to the same place in `data/mods/NAME/`. It deletes nothing. It prints each file that it copies. | 1 when it kept `ids.lock` |
| `./port mod build NAME [--update-lock] [ARGUMENTS]` | Sync. Then `esx --data FO4_DATA build data/mods/NAME ARGUMENTS`. Then copy each lock file back. Then print each release file with its sha256. | That of esx; 3 when `esx` or `fo4_data` has no value |

The rule for the lock files (`ids.lock` and `behavior/WEAPON/WEAPON.lock`; the text below says `ids.lock` for each of them):

* `sync` does not replace an `ids.lock` of `data/mods/NAME/` that is different and newer than
  the file of `mods/NAME/`. It tells you so. `./port mod build NAME --update-lock` keeps the
  file of `data/` and copies it back. `./port mod sync NAME --force` replaces it.
* `build` copies `data/mods/NAME/ids.lock` to `mods/NAME/ids.lock` when the two are different
  and esx gave the exit code 0. When esx fails, `mods/NAME/ids.lock` stays as it is.

`build` gives each argument after `NAME` to `esx build`. esx prints one JSON document when its
output is not a terminal. `--format text` gives text.

## The tests

```sh
./port selftest
python3 -B -m unittest discover -s tests     # the tests only
```

The tests make a temporary copy of `port` and `portkit/`, add their own `port.toml` files and
mods, and run `./port` there with `FO4PORTS_DATA`. They use a small program in the place of
esx. `./port selftest` compiles each `.py` file of the source tree from its source and writes
no `.pyc` file. It does not look below `data/`, `.git/`, `__pycache__`, `.venv` or `target`.
