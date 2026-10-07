# Architecture

This repository has the tools that port weapons and their animations to Fallout 4 from three
sources: Fallout: New Vegas, Destiny 2 and Marathon. A person and an AI agent use the same
commands, the same documents and the same checks.

## The areas

| Folder | What it is | Needs |
| --- | --- | --- |
| `portkit/`, `port` | The shared part: paths, local settings, the command `./port`, the mod projects. Standard library of Python only. | Python 3.11 |
| `fnv/` | New Vegas animations (`.kf`, `.nif`) to Fallout 4 clips (HKX). It also has the Fallout 4 library that the other areas use: the HKX reader and writer, the archive reader, the hand solver. | numpy, Blender |
| `destiny/extract/` | `d2x`: a weapon of Destiny 2 (model, textures, rigs, clips) as glTF files. | the game, its own Python environment, cargo |
| `destiny/port/` | `d2fo4`: a glTF file of `d2x` or `m2x` to Fallout 4 clips, a Fallout 4 model, materials, the sight, the third-person clips. The checks and the game tests are here. | `fnv/`, numpy, Blender, esx |
| `marathon/extract/` | `m2x`: a weapon of Marathon as glTF files. It uses the modules of `d2x`. | the game, the environment of `d2x`, cargo |
| `marathon/port/` | The set files of the Marathon weapons. The converter is `destiny/port/`. | `destiny/port/` |
| `mods/` | The sources of the esx mod projects: `esx.toml`, `items/`, `behavior/WEAPON/WEAPON.bhv`, the lock files, `README.md`. No asset. | esx |
| `docs/` | The documents for a person. | |
| `.claude/skills/`, `AGENTS.md` | The instructions for an AI agent. | |
| `baselines.sha256` | The sha256 of each stored result of `data/` (the baseline clips of the regress commands, the clips and the release of each mod). In git. | |
| `requirements.txt` | The Python packages of `fnv/` and `destiny/port/`: `numpy`, `pillow`. `destiny/extract/` has its own file. | |
| `data/` | All that is not source. Not in git. | |

The dependencies go in one direction: `marathon` uses `destiny`, `destiny/port` uses `fnv`,
and each area uses `portkit`. `fnv` and `portkit` use no other area.

## The stages of a port

```
game files -> extract -> glTF + manifest -> convert -> clips, model, materials -> mod project -> build -> checks -> game test
              d2x, m2x                      d2fo4 (set file)                     mods/NAME      esx      check/    esx probe
New Vegas mod (.kf, .nif) ----------------> fnv/tools/port.py -> clips
```

## The data folder

`data/` holds each file of a game, each extracted asset, each work file, each result, each
validation picture and video, each built mod, each third-party clone and build, and the local
settings. Git ignores all of it but `data/README.md`. No tool writes a generated file into the
source tree (the only exception is `__pycache__`, which the tools prevent where they can). The
Blender user folders of the checks are below `data/destiny/port/work/`.

| Folder | Content |
| --- | --- |
| `data/config.toml` | The local settings (`config.example.toml`). |
| `data/fnv/rig/` | The rig folder of `fnv/`: files of Fallout 4 and of the NVCS skeleton, made by `fnv/tools/make_rig.py`. |
| `data/fnv/work/NAME/`, `data/fnv/out/NAME/` | The work files and the clips of a New Vegas port. |
| `data/fnv/fixtures/NAME/` | The extracted New Vegas mods that `fnv regress` converts again. |
| `data/fnv/nvcs/` | A copy of the skeleton of the NVCS mod, for `fnv make-rig` (the setting `nvcs_skeleton`). |
| `data/destiny/extract/out/` | The results of `d2x`, and its cache (`out/cache/`). `handoff/` beside it has an earlier result set. |
| `data/destiny/extract/vendor/`, `runtime/`, `venv/`, `target/` | The third-party clones, the Oodle library link, the Python environment and the cargo build of `d2x`. |
| `data/destiny/port/extract/NAME/` | The extraction of each weapon for a port (`manifest.json`, the glTF files, `states.json`, `dyes.json`, `sight.json`, `third_person/`, `posed/`). |
| `data/destiny/port/rig/` | The vanilla clips of each template weapon (game files, made by `destiny/port/tools/make_rig.py`). |
| `data/destiny/port/work/NAME/`, `out/NAME/`, `validation/NAME/` | The work files, the clips and the validation results of each weapon. |
| `data/marathon/extract/...` | The same for `m2x`: `out/`, `work/`, `runtime/`, `target/`, `notes/`, `validation/`. |
| `data/mods/NAME/` | The complete esx project of each mod: a copy of `mods/NAME/` plus the meshes, the textures, the clips and `build/`. esx builds here. |
| `data/transcripts/`, `data/notes/` | The chat transcripts as short text, and the notes that the documents came from. |

A measurement file that a tool needs and that is not a copy of a game file is in the source
tree: `fnv/rig/finger_tips.json`, `destiny/port/rig/d2_hands.json`. A tool reads such a file
from the source tree (`paths.repo(...)`), not from `data/`.

## The paths and the settings

No program has a path of one computer in it. A program asks `portkit.paths`:

```python
from portkit import paths
paths.repo('fnv', 'tools')                    # a path in the source tree
paths.data('destiny', 'port', 'work', name)   # a path below data/
paths.program('blender')                      # an external program, or None
paths.require('fo4_data')                     # a setting that must be there; stops with advice if not
paths.setting('name', env='NAME')             # a value that is not in the table SETTINGS of paths.py
```

A setting comes from its environment variable, then from `data/config.toml`, then from its
default (for a program: the `PATH`). The names: `blender` (`BLENDER`), `esx` (`ESX_BIN`),
`fo4_data` (`FO4_DATA`), `proton` (`PROTON_DIR`), `destiny_game` (`D2X_GAME`), `marathon_game`
(`MARATHON_GAME`), `nvcs_skeleton` (`NVCS_SKELETON`). The seven are in the table `SETTINGS` of
`portkit/paths.py`. `FO4PORTS_DATA` moves the data folder. A shell script gets a value with
`python3 "$ROOT/portkit/paths.py" get blender`, or from the variables that `./port` sets
(below). A fault in `data/config.toml` (TOML that is not correct, a value that is not a text)
is one line, and `./port doctor` names each key of the file that is not a setting.

A program that imports `portkit` shows a file error (a wrong file name on the command line)
as one line. `FO4PORTS_TRACEBACK=1` shows the traceback.

A Python program that can start with no `./port` (each program can, and a program in Blender
always does) has these lines before its first import of the repository:

```python
import os, sys
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths
```

The Python environment of `d2x` is `data/destiny/extract/venv`. A program that imports `d2x`
runs with `data/destiny/extract/venv/bin/python` and with `destiny/extract` in `PYTHONPATH`.

## The command `./port`

`./port` is the one entry point. It finds the commands of each area in the `port.toml` files
(`fnv/port.toml`, `destiny/extract/port.toml`, `destiny/port/port.toml`,
`marathon/extract/port.toml`, `marathon/port/port.toml`). It reads each file with the name
`port.toml` in the source tree, and it does not look below `data/`, `.git/`, `__pycache__/`,
`.venv/` and `target/`. Each program still runs alone with `python3 PATH/program.py`;
`./port` adds the names, the help, the environment and the checks. `portkit/README.md` is the
reference of the command and of `port.toml`.

```sh
./port list [--json]          # each command with one line of help
./port doctor [AREA] [--json] # each setting, each tool and each necessary file: there or missing, and how to make it
./port paths [--json]
./port mod list | status NAME | sync NAME [--force] | build NAME [--update-lock]
./port AREA                   # the commands of one area; ./port AREA WORD: the commands that start with the two words
./port selftest               # checks that need no game file: Python files, port.toml files, the tests of portkit, the files of git
./port baseline check         # each stored result of data/ has the sha256 of baselines.sha256
./port baseline update        # write baselines.sha256 again, after a change that the user accepted
./port AREA COMMAND [ARGUMENTS]     # for example: ./port destiny convert FILE.glb --set SET.toml
./port AREA COMMAND --help
```

`port.toml`:

```toml
[[command]]
name = "destiny convert"        # the words after ./port (two or three words; the first is the area)
help = "Convert the clips of a set file to Fallout 4 clips."
run = ["python", "destiny/port/d2fo4.py"]   # the start of the command line; the arguments of the user go after it
env = { PYTHONPATH = "destiny/extract" }    # optional
needs = ["blender", "data/fnv/rig/1st_skeleton.hkx"]   # optional: settings, or paths from the root, that must be there
```

* The first word of `run`: `python` (the Python that runs `./port`), `python:d2x` (the Python
  of the environment of `d2x`), `sh`, `bash`, or a program with a path from the root. After
  `python`, `python:d2x`, `sh` or `bash` comes the program file, not an option.
* Each path in `run`, `env` and `needs` is a path from the root of the repository. A path
  that starts with `data/` is below the data folder, also when `FO4PORTS_DATA` moves it.
* A name has two or three words of small letters, digits, `-` and `_`. The first word cannot
  be a word of `./port` itself (`list`, `doctor`, `paths`, `mod`, `selftest`, `baseline`, `help`).
* `./port` starts the program with `exec`: the program takes the place of `./port`, so a
  signal to the process ID of `./port` goes to the program. A regress command starts its
  converters as child processes: stop such a run with Ctrl-C, or stop its children also.
* `./port` runs the command in the working folder of the caller, and gives it
  `FO4PORTS_ROOT`, `FO4PORTS_DATA` and one variable for each setting that has a value
  (`BLENDER`, `ESX_BIN`, `FO4_DATA`, `PROTON_DIR`, `D2X_GAME`, `MARATHON_GAME`,
  `NVCS_SKELETON`), `PYTHONDONTWRITEBYTECODE=1`, and a `PYTHONPATH` with the root first, then
  the folders of `env`, then the `PYTHONPATH` of the caller. The exit code is the exit code
  of the program.
* An entry of `needs` is the name of a setting or a path with a `/`. When one is missing,
  `./port` stops before the program starts (exit code 3), and tells the user which command
  makes it. With `--help` in the arguments `./port` does not look at `needs`. `python:d2x`
  needs the environment of `d2x` always.
* The exit codes of `./port` itself: 2 for wrong words or a program file that is not there,
  3 for a missing need, 1 for a fault that `doctor`, `selftest`, `mod sync` or
  `baseline check` found.
* Blender does not read `PYTHONDONTWRITEBYTECODE`. Each program that runs in Blender has
  `sys.dont_write_bytecode = True` before its first import of the repository.

A `port.toml` also says how to make each thing that its commands need. `./port doctor` shows
each one:

```toml
[[check]]
path = "data/fnv/rig/1st_skeleton.hkx"     # a path from the root; or: setting = "blender"
what = "The rig folder of fnv: files of Fallout 4 and of the NVCS skeleton."
make = "./port fnv make-rig --nvcs /path/to/NVCS/Skeleton.nif"
```

`what` is necessary and `make` is optional. A check of a folder is also the check of each
path below it. `./port doctor` has the exit code 1 when a check is not ok, or a setting that
a command or a check uses, or when Python has no `numpy`. It prints a line for `Pillow` (a
report only). `./port doctor AREA` looks only at the `port.toml` files below one folder
(`fnv`, `destiny`, `marathon`, or a path such as `destiny/port`), for a person who uses one
area. The check of the arm meshes is in `destiny/port/port.toml`, so `./port doctor fnv` can
be ok with no esx.

A `port.toml` also names the stored results of its area:

```toml
[[baseline]]
files = "data/fnv/out/*/*.hkx"     # a pattern that starts with data/ (`**` is each folder below)
what = "The clips of each fixture: the baseline of `fnv regress`."
```

`./port baseline update` writes the sha256 and the path of each file of each pattern into
`baselines.sha256` (602 files of 8 patterns on 2026-10-06; `mods/port.toml` has the patterns
of the mods). `./port baseline check` compares the files of `data/` with that list. It prints
`DIFFERENT` for a file with other bytes and has the exit code 1. It reports a file that is not
there and a file that the list does not have, with the exit code 0. A regress command compares
new results with the stored results. The baseline check proves that nobody replaced a stored
result. So run it after a regress command passes. Run `./port baseline update` only for a
change that the user accepted, and put the file into git with that change.

`./port selftest` has four parts: `python` (each `.py` file compiles), `port.toml` (each table
is correct, and each program file is there), `tests` (the tests of `tests/`), and `git` (no
file that git has, or can add, has a game file ending or a NUL byte).

Each area that converts has a command with the name `AREA regress`. It makes the results of
each ported weapon again in a scratch folder below `data/`, compares the bytes with the
results that `data/` has, prints one line for each weapon, and has the exit code 1 when a
file is different.

## The mod projects

`mods/NAME/` has the files that a person writes (`esx.toml`, `items/`,
`behavior/WEAPON/WEAPON.bhv`, `README.md`, and for a New Vegas port `conversion.toml` and
`tests/`) and the lock files that esx keeps (`ids.lock` with the object ID of each record,
`behavior/WEAPON/WEAPON.lock` with the hashes of the vanilla graphs). `data/mods/NAME/` is the
project that esx builds.

* `./port mod sync NAME` copies the files of `mods/NAME/` into `data/mods/NAME/`. It does not
  delete a file of `data/mods/NAME/`. It keeps a lock file of `data/` that is different and
  newer (exit code 1); `--force` replaces it. `./port mod status NAME` shows the files that
  differ.
* The convert commands write the meshes, the materials, the textures and the clips into
  `data/mods/NAME/`.
* `./port mod build NAME [--update-lock]` does the sync, runs `esx build` on
  `data/mods/NAME/`, and copies each lock file back to `mods/NAME/` when esx changed it and
  the build passed. It prints the sha256 of each release file. esx prints JSON when its
  output is not a terminal; `--format text` after NAME gives text.
* A release is `data/mods/NAME/build/release/`.
* The mods: `TheLastWord`, `Khvostov`, `Hammerhead`, `TexMechanica` (Destiny 2), `M77`
  (Marathon), `PPK`, `FAMAS` (New Vegas). The model and the textures of the two New Vegas
  mods came from the tools at the tag `before-animation-only`; the tools of today make their
  clips.

## Rules for a change

1. A change of a converter must keep the bytes of each clip of each weapon that is already
   ported, or the change must say which clips are different and why. Each area has a
   regression command that compares new results with the results in `data/`. After it,
   `./port baseline check` proves that the results in `data/` are those on record.
2. A document tells the reader which command proves each statement. A statement with no
   proof is in a part with the title "What is not proved".
3. A rule in a set file has the measurement that gave it as a comment.
4. No file of a game, no part of one and no asset made from one is in git. The measurement
   files, the lock files and `baselines.sha256` have numbers and hashes that were calculated
   from game files. `./port selftest` (the part `git`) fails for a file that is not source.
5. The documents use simple English: short sentences, the active voice, one word for one
   thing, no dash between clauses.
