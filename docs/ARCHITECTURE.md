# Architecture

This repository holds the tools that port weapons and their animations to Fallout 4 from
Fallout: New Vegas, Destiny 2 and Marathon. People and AI agents use the same commands,
documents and checks.

## The areas

| Folder | What it is | Needs |
| --- | --- | --- |
| `portkit/`, `port` | The shared part: paths, local settings, the `./port` command and the mod projects. Python standard library only. | Python 3.11 |
| `fnv/` | Converts New Vegas animations (`.kf`, `.nif`) to Fallout 4 HKX clips. The other areas also use its HKX reader and writer, its archive reader and its hand solver. | numpy, Blender |
| `destiny/extract/` | `d2x`, the Destiny 2 extractor. It writes the model, textures, rigs and clips of a weapon as glTF files. | the game, its own Python environment, cargo |
| `destiny/port/` | `d2fo4`, the converter. It turns a glTF file from `d2x` or `m2x` into Fallout 4 clips, a model, materials, the sight and the third-person clips. The checks and the game tests live here too. | `fnv/`, numpy, Blender, esx |
| `marathon/extract/` | `m2x`, the Marathon extractor. It writes a weapon as glTF files and reuses the modules of `d2x`. | the game, the environment of `d2x`, cargo |
| `marathon/port/` | Set files for the Marathon weapons. The converter is `destiny/port/`. | `destiny/port/` |
| `mods/` | Sources of the esx mod projects: `esx.toml`, `items/`, `behavior/WEAPON/WEAPON.bhv`, the lock files and `README.md`. No assets. | esx |
| `docs/` | Documentation for people. | |
| `.claude/skills/`, `AGENTS.md` | Instructions for AI agents. | |
| `baselines.sha256` | The sha256 of every stored result in `data/`: the baseline clips of the regress commands, and the clips and release of each mod. In git. | |
| `requirements.txt` | The Python packages for `fnv/` and `destiny/port/`: `numpy` and `pillow`. `destiny/extract/` has its own file. | |
| `data/` | Everything that is not source. Not in git. | |

Dependencies go one way. `marathon` uses `destiny`, `destiny/port` uses `fnv`, and every
area uses `portkit`. `fnv` uses only `portkit`, and `portkit` uses no area.

## The stages of a port

```
game files -> extract -> glTF + manifest -> convert -> clips, model, materials -> mod project -> build -> checks -> game test
              d2x, m2x                      d2fo4 (set file)                     mods/NAME      esx      check/    esx probe
New Vegas mod (.kf, .nif) ----------------> fnv/tools/port.py -> clips
```

## The data folder

`data/` holds every game file, extracted asset, work file, result, validation picture and
video, built mod, third-party clone and build, plus the local settings. Git ignores all of it
except `data/README.md`. No tool writes a generated file into the source tree, except
`__pycache__`, which the tools prevent where they can. The checks keep their Blender user
folders below `data/destiny/port/work/`.

| Folder | Content |
| --- | --- |
| `data/config.toml` | The local settings, copied from `config.example.toml`. |
| `data/fnv/rig/` | The rig folder of `fnv/`: Fallout 4 files and the NVCS skeleton, made by `fnv/tools/make_rig.py`. |
| `data/fnv/work/NAME/`, `data/fnv/out/NAME/` | The work files and the clips of a New Vegas port. |
| `data/fnv/fixtures/NAME/` | The extracted New Vegas mods that `fnv regress` converts again. |
| `data/fnv/nvcs/` | A copy of the skeleton of the NVCS mod, for `fnv make-rig` (the setting `nvcs_skeleton`). |
| `data/destiny/extract/out/` | The results of `d2x`, with its cache in `out/cache/`. `handoff/` beside it holds an earlier result set. |
| `data/destiny/extract/vendor/`, `runtime/`, `venv/`, `target/` | The third-party clones, the Oodle library link, the Python environment and the cargo build of `d2x`. |
| `data/destiny/port/extract/NAME/` | The extraction of each weapon for a port: `manifest.json`, the glTF files, `states.json`, `dyes.json`, `sight.json`, `third_person/` and `posed/`. |
| `data/destiny/port/rig/` | The vanilla clips of each template weapon. They are game files, and `destiny/port/tools/make_rig.py` makes them. |
| `data/destiny/port/work/NAME/`, `out/NAME/`, `validation/NAME/` | The work files, the clips and the validation results of each weapon. |
| `data/marathon/extract/...` | The same for `m2x`: `out/`, `work/`, `runtime/`, `target/`, `notes/`, `validation/`. |
| `data/mods/NAME/` | The complete esx project of each mod: a copy of `mods/NAME/` plus the meshes, the textures, the clips and `build/`. esx builds here. |
| `data/transcripts/`, `data/notes/` | The chat transcripts as short text, and the notes that the documents came from. |

A measurement file that a tool needs and that is not a copy of a game file lives in the
source tree, like `fnv/rig/finger_tips.json` and `destiny/port/rig/d2_hands.json`. Tools read
it with `paths.repo(...)`, not from `data/`.

## The paths and the settings

No program hard-codes a path of one computer. It asks `portkit.paths`:

```python
from portkit import paths
paths.repo('fnv', 'tools')                    # a path in the source tree
paths.data('destiny', 'port', 'work', name)   # a path below data/
paths.program('blender')                      # an external program, or None
paths.require('fo4_data')                     # a setting that must be there; stops with advice if not
paths.setting('name', env='NAME')             # a value that is not in the table SETTINGS of paths.py
```

A setting comes from its environment variable, then from `data/config.toml`, then from its
default, which for a program is the `PATH`. The `SETTINGS` table of `portkit/paths.py` has
the seven. `blender` reads `BLENDER`, `esx` reads `ESX_BIN`, `fo4_data` reads `FO4_DATA`,
`proton` reads `PROTON_DIR`, `destiny_game` reads `D2X_GAME`, `marathon_game` reads
`MARATHON_GAME` and `nvcs_skeleton` reads `NVCS_SKELETON`. `FO4PORTS_DATA` moves the data
folder.

A shell script gets a value with `python3 "$ROOT/portkit/paths.py" get blender`, or from the
variables that `./port` sets, as described below. A fault in `data/config.toml`, such as
invalid TOML or a value that is not text, prints as one line. `./port doctor` names every key
in the file that is not a setting.

A program that imports `portkit` prints a file error, such as a wrong file name on the
command line, as one line. Set `FO4PORTS_TRACEBACK=1` to see the traceback.

Every Python program can start without `./port`, and a program in Blender always does. So
each one has these lines before its first import from the repository:

```python
import os, sys
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths
```

`d2x` has its own Python environment in `data/destiny/extract/venv`. A program that imports
`d2x` runs with `data/destiny/extract/venv/bin/python` and with `destiny/extract` in
`PYTHONPATH`.

## The command `./port`

`./port` is the one entry point. It finds the commands of each area in the `port.toml` files:
`fnv/port.toml`, `destiny/extract/port.toml`, `destiny/port/port.toml`,
`marathon/extract/port.toml` and `marathon/port/port.toml`. It reads every file named
`port.toml` in the source tree and skips `data/`, `.git/`, `__pycache__/`, `.venv/` and
`target/`. Every program still runs alone with `python3 PATH/program.py`. `./port` adds the
names, the help, the environment and the checks. `portkit/README.md` is the reference for the
command and for `port.toml`.

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

* The first word of `run` is `python` for the Python that runs `./port`, `python:d2x` for the
  Python of the `d2x` environment, `sh`, `bash`, or a program given as a path from the root.
  The program file comes right after `python`, `python:d2x`, `sh` or `bash`. An option cannot
  go there.
* Every path in `run`, `env` and `needs` starts at the repository root. A path that starts
  with `data/` resolves below the data folder, even when `FO4PORTS_DATA` moves it.
* A name has two or three words made of lowercase letters, digits, `-` and `_`. The first
  word cannot be one that `./port` uses itself: `list`, `doctor`, `paths`, `mod`, `selftest`,
  `baseline` or `help`.
* `./port` starts the program with `exec`. The program takes the place of `./port`, so a
  signal sent to the process ID of `./port` reaches the program. A regress command starts its
  converters as child processes. Stop such a run with Ctrl-C, or stop its children too.
* `./port` runs the command in the caller's working folder. It passes `FO4PORTS_ROOT`,
  `FO4PORTS_DATA`, `PYTHONDONTWRITEBYTECODE=1` and the variable of each setting that has a
  value, such as `BLENDER`. `PYTHONPATH` has the root first, then the folders of `env`, then
  the caller's `PYTHONPATH`. The exit code is the program's.
* An entry of `needs` is the name of a setting or a path with a `/`. When one is missing,
  `./port` stops before the program starts, with exit code 3, and says which command makes
  it. With `--help` in the arguments, `./port` skips `needs`. `python:d2x` always needs the
  `d2x` environment.
* `./port` itself exits with 2 for wrong words or a missing program file, 3 for a missing
  need, and 1 for a fault that `doctor`, `selftest`, `mod sync` or `baseline check` found.
* Blender does not read `PYTHONDONTWRITEBYTECODE`. A program that runs in Blender sets
  `sys.dont_write_bytecode = True` before its first import from the repository.

A `port.toml` also says how to make everything its commands need. `./port doctor` shows each
one:

```toml
[[check]]
path = "data/fnv/rig/1st_skeleton.hkx"     # a path from the root; or: setting = "blender"
what = "The rig folder of fnv: files of Fallout 4 and of the NVCS skeleton."
make = "./port fnv make-rig --nvcs /path/to/NVCS/Skeleton.nif"
```

`what` is required and `make` is optional. A check of a folder also covers every path below
it. `./port doctor` exits with 1 when a check is not ok, when a setting that a command or a
check uses is not ok, or when Python has no `numpy`. Its `Pillow` line is a report only. If
you use one area, `./port doctor AREA` looks only at the `port.toml` files below one folder.
AREA is `fnv`, `destiny`, `marathon`, or a path such as `destiny/port`. The check of the arm
meshes is in `destiny/port/port.toml`, so `./port doctor fnv` can be ok without esx.

A `port.toml` also names the stored results of its area:

```toml
[[baseline]]
files = "data/fnv/out/*/*.hkx"     # a pattern that starts with data/ (`**` is each folder below)
what = "The clips of each fixture: the baseline of `fnv regress`."
```

`./port baseline update` writes the sha256 and the path of every file that matches a pattern
into `baselines.sha256`. On 2026-10-06 that was 602 files from 8 patterns. `mods/port.toml`
has the patterns of the mods. `./port baseline check` compares the files in `data/` with that
list. For a file with other bytes it prints `DIFFERENT` and exits with 1. It also reports a
missing file, or one that the list does not have, and then exits with 0.

A regress command compares new results with the stored results, and the baseline check proves
that nobody replaced a stored result. So run it after a regress command passes. Run
`./port baseline update` only for a change that the user accepted, and put the file into git
with that change.

`./port selftest` has four parts. `python` compiles every `.py` file. `port.toml` checks that
every table is correct and every program file exists. `tests` runs the tests in `tests/`.
`git` checks that no file that git has, or can add, has a game file ending or a NUL byte.

Every area that converts has an `AREA regress` command. It makes the results of each ported
weapon again in a scratch folder below `data/`, compares the bytes with the results already
in `data/`, prints one line per weapon, and exits with 1 when a file differs.

## The mod projects

`mods/NAME/` has the hand-written files: `esx.toml`, `items/`, `behavior/WEAPON/WEAPON.bhv`,
`README.md`, and for a New Vegas port `conversion.toml` and `tests/`. It also has the lock
files that esx keeps. `ids.lock` holds the object ID of each record, and
`behavior/WEAPON/WEAPON.lock` holds the hashes of the vanilla graphs. `data/mods/NAME/` is
the project that esx builds.

* `./port mod sync NAME` copies the files of `mods/NAME/` into `data/mods/NAME/` and deletes
  nothing there. If a lock file in `data/` is different and newer, it keeps that file and
  exits with 1. `--force` replaces it. `./port mod status NAME` shows the files that differ.
* The convert commands write the meshes, the materials, the textures and the clips into
  `data/mods/NAME/`.
* `./port mod build NAME [--update-lock]` syncs, runs `esx build` on `data/mods/NAME/`, and
  copies a lock file back to `mods/NAME/` when esx changed it and the build passed. It prints
  the sha256 of each release file. esx prints JSON when its output is not a terminal. Add
  `--format text` after NAME to get text.
* A release is `data/mods/NAME/build/release/`.
* The mods are `TheLastWord`, `Khvostov`, `Hammerhead` and `TexMechanica` from Destiny 2,
  `M77` from Marathon, and `PPK` and `FAMAS` from New Vegas. The model and the textures of
  the two New Vegas mods came from the tools at the tag `before-animation-only`. Today's
  tools make their clips.

## Rules for a change

1. A change to a converter must keep the bytes of every clip of every ported weapon, or say
   which clips differ and why. Each area has a regress command that compares new results with
   the results in `data/`. After it, `./port baseline check` proves that the results in
   `data/` are the ones on record.
2. A document tells the reader which command proves each statement. A statement without proof
   goes in a part titled "What is not proved".
3. A rule in a set file carries the measurement that gave it as a comment.
4. No game file, no part of one and no asset made from one goes into git. The measurement
   files, the lock files and `baselines.sha256` hold numbers and hashes calculated from game
   files. The `git` part of `./port selftest` fails for a file that is not source.
5. The documents use plain technical English and follow the rules that
   [README.md](../README.md) shows by example: short, direct, each fact with the command that
   proves it.
