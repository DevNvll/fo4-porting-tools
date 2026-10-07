# Getting started: the setup of each area

This document takes you from a new clone to a setup that works. For each area it gives the
commands, what each one makes, the time when one is known, and how to know that it worked.
Each command runs in the root of the repository.

A new clone has an empty data folder: `data/` holds each file of a game and each result, and
git does not have it ([ARCHITECTURE.md](ARCHITECTURE.md), "The data folder"). So you need
your own copies of the games.

## What you need

| Thing | For | Setting or check |
| --- | --- | --- |
| Linux | Each area was made and tested on Linux. The two Oodle shims are for Linux only. | |
| Python 3.11 or later, with `numpy` and `Pillow` (`pip install -r requirements.txt`) | `numpy`: each area. `Pillow`: the model program and the picture programs. | `./port doctor` prints the versions. A missing `numpy` fails the result. The line `pillow` is a report only. |
| Blender 4.5 | The retarget steps and each check with pictures. It runs with no window. | `blender` |
| Fallout 4, its `Data` folder | The rig folders, the model program, the build of a mod | `fo4_data` |
| The skeleton file of the New Vegas compatibility skeleton mod (NVCS), `Meshes/Characters/_1stPerson/Skeleton.nif` | The rig folder of `fnv/` | `nvcs_skeleton`, or `--nvcs` |
| esx (see "esx" below) | The arm meshes for the checks, the textures and the materials of a model, the build of a mod, the game test | `esx` |
| Proton | The game test on Linux | `proton` |
| Destiny 2, the build `86657.20.08.23.1800.d2_rc` (23 August 2020) | `destiny/extract/` | `destiny_game` |
| Marathon (the build of 2026-10-06) | `marathon/extract/` | `marathon_game` |
| `git`, `cargo`, and `uv` (or a `python3` of 3.12 or later, for `python3 -m venv`) | `./port destiny setup` | `./port doctor` lists them |
| A C compiler, `cargo` | `./port marathon setup` | |
| `ffmpeg` | Each video and each picture sheet | `./port doctor` lists it |
| GStreamer, PipeWire and gamescope | The recording of a game test | |
| `llvm-dis` | `./port marathon notes dxil` only | |

You need only the things of the area that you use. A person who converts New Vegas
animations needs Python, `numpy`, Blender, Fallout 4 and the NVCS skeleton file.

### esx

esx is a separate program: a command line tool that builds a Fallout 4 mod from a project
folder and that starts the game probe. It is a project of the owner of this repository, at
`https://github.com/DevNvll/esx`. On 2026-10-06 that address answered "not found" to a request
with no login, so the repository was not public then: ask the owner for it. Build it with
cargo (its `README.md` has `cargo install --path crates/esx-cli`), and give the program as the
setting `esx`. Version 0.1.0 at the commit `a996de8` made the stored releases. The commit
`d3e520c` (2026-10-06) is the first one with the test world of the game test.

| With no esx | With the arm meshes that esx makes one time (`./port fnv make-rig --arm-meshes`) | Only with esx |
| --- | --- | --- |
| Each extraction. Each conversion (`fnv convert`, `destiny convert`, `marathon convert`). The regress commands. `destiny check gun`, `fingers`, `gun-on-grip`, `third-sheet`. `./port selftest`, `doctor`, `baseline check`. | `destiny check validate`, `touch`, `touch-table`, `contact`, `render` (each check with the hand meshes), `destiny measure-hands` | `destiny model` and `marathon model`, `./port mod build`, `fnv make-rig --arm-meshes`, each `destiny game` command |

The test world of the game test is a file that the user supplies: a ZIP file or a folder
with one plugin (the plugin `TestWorldspace.esp` in the run of 2026-10-06). No document of
this repository or of esx gives its source.

## 1. The settings

```sh
cp -n config.example.toml data/config.toml   # only when the file is not there; then give your own paths in it
./port doctor                                # each setting, each tool and each necessary file: ok or MISSING
./port list                                  # each command with one line of help
```

`config.example.toml` has one line for each setting. A setting comes from its environment
variable, then from `data/config.toml`, then from its default (for a program: the `PATH`).
If `data/config.toml` is there, edit it. A copy of the example over it removes your paths, and
`data/` is not in git.

| Setting | Variable | What it is |
| --- | --- | --- |
| `blender` | `BLENDER` | The Blender program |
| `esx` | `ESX_BIN` | The esx program |
| `fo4_data` | `FO4_DATA` | The `Data` folder of Fallout 4 |
| `proton` | `PROTON_DIR` | The Proton folder for the game test |
| `destiny_game` | `D2X_GAME` | The game folder of Destiny 2 (it has `packages/` and `bin/x64/`) |
| `marathon_game` | `MARATHON_GAME` | The game folder of Marathon (it has `packages/` and `bin/x64/`) |
| `nvcs_skeleton` | `NVCS_SKELETON` | The skeleton file of the NVCS mod |

`FO4PORTS_DATA` moves the data folder.

**How to know that it worked.** `./port doctor` shows `ok` for each setting that your area
needs. `./port doctor fnv`, `./port doctor destiny` and `./port doctor marathon` look at one
area only, and a path such as `./port doctor destiny/port` looks at one folder. A line
`MISSING` has the command that makes the thing. The exit code is 1 when a line is not ok, or
when Python has no `numpy`. With no `data/config.toml` the command tells you to copy the
example. It names each key of the file that is not a setting (a wrong spelling). A fault in
the file is one line.

## 2. The shared part

```sh
./port selftest
```

It needs no game file. It checks that each Python file compiles, that each `port.toml` is
correct, that the tests of `portkit` pass, and that git has no file that is not source (a
game file ending, or a NUL byte).

**How to know that it worked.** Four lines that start with `ok`: `python`, `port.toml`,
`tests`, `git`.

## 3. New Vegas (`fnv/`)

| Command | What it makes | Time |
| --- | --- | --- |
| `./port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif` | The rig folder `data/fnv/rig`: `1st_skeleton.hkx`, the vanilla clips of the templates `smg` and `pistol10mm`, `nvcs_1st.json`. It reads `Fallout4 - Animations.ba2`. | Not recorded |
| `./port fnv make-rig --arm-meshes` | The first-person arm meshes of Fallout 4 as glTF files, in the same folder. Only the checks of `destiny/port/` read them. It needs `esx`. | Not recorded |
| `./port fnv convert /path/to/extracted-mod` | The clips of a weapon in `data/fnv/out/NAME`, and the work files in `data/fnv/work/NAME` | 27 seconds for the PPK |

**How to know that it worked.** `./port doctor fnv` prints
`Result: each setting and each check is ok.` It can be ok with no esx: the arm meshes are a
check of `destiny/port/`. Then `./port fnv regress`: it converts each
fixture of `data/fnv/fixtures/` again and compares the clips with `data/fnv/out/`. On a new
clone there is no fixture: the command says so, and its exit code is 0. To make the first
fixture, see [porting/fnv.md](porting/fnv.md), step 5.

## 4. The extraction of Destiny 2 (`destiny/extract/`)

| Command | What it makes | Time |
| --- | --- | --- |
| `./port destiny setup` | Below `data/destiny/extract/`: the clones of `tiger-pkg` and `tiger-animation-parser` at fixed commits (`vendor/`), the cargo build of the package reader (`target/`), the Python environment (`venv/`), the Oodle shim and the link to the Oodle library of the game (`runtime/`). It is safe to run again. | Not recorded. The first extraction after it needs 2 minutes 10 seconds. |
| `./port destiny find "TEXT"` | A list of items: item hash, pattern entity, name | 5 seconds |
| `./port destiny extract "NAME" --arms "ARMOR" --out data/destiny/port/extract` | `NAME/` with the glTF files, `textures/`, `raw/`, `manifest.json` | 30 seconds |

The setup does each step that does not need the game first. With no value for
`destiny_game` it stops at the last step (the Oodle link) with the exit code 1. With no `uv`
it needs a `python3` of 3.12 or later for the Python environment (the fixed versions of
`destiny/extract/requirements.txt` need it), and it stops with a message if `python3` is older.

`tiger-pkg` keeps an index of the packages in the cache folder of the user (the folder
`tiger-pkg` in `XDG_CACHE_HOME`, about 50 MB for this game). It is not below `data/`.

**How to know that it worked.** `./port doctor destiny` is ok. `./port destiny find "last
word"` prints a row with a pattern entity. `./port destiny check-glb FILE.glb` prints `NO
PROBLEMS` for an extracted file. This area has no regress command: to prove the same bytes,
extract into a scratch folder and compare each file with an earlier result
([destiny/extract/README.md](../destiny/extract/README.md#checks)).

## 5. The converter of Destiny 2 and Marathon (`destiny/port/`)

Do the parts 3 and 4 first: this area uses the rig folder of `fnv/` and the environment of
`d2x`.

| Command | What it makes | Time |
| --- | --- | --- |
| `./port fnv make-rig --nvcs FILE`, then `./port fnv make-rig --arm-meshes` | The Fallout 4 skeleton and the arm meshes in `data/fnv/rig` | Not recorded |
| `./port destiny make-rig` | `data/destiny/port/rig/`: the vanilla clips of each template (`revolver44`, `combatrifle`), the third-person skeleton and clips, the clips of the power armor | Not recorded |
| `./port destiny measure-hands FILE.glb` | Only when the hand measurements must change: `data/destiny/port/rig/d2_hands.json`. The tools read `destiny/port/rig/d2_hands.json`, which is in git. | 70 seconds |

**How to know that it worked.** `./port doctor destiny` is ok. Then `./port destiny regress`:
it makes the clips of each weapon of `destiny/port/regress.toml` again and compares the bytes
with the baseline clips of `data/`. On a new clone the data folder has no extraction and no
baseline clip, so make one weapon first ([porting/destiny.md](porting/destiny.md)). On the
computer of the author the result of 2026-10-06 was 6 weapons, 162 first-person clips, 16
third-person clips and 6 clips of the power armor, 0 differ.

## 6. Marathon (`marathon/`)

Do part 4 first (`./port destiny setup`): `m2x` uses the Python environment, the package
reader and the clones of `d2x`. For the port, do part 5 also.

| Command | What it makes | Time |
| --- | --- | --- |
| `./port marathon setup` | Below `data/marathon/extract/`: the Oodle 9 shim (`runtime/liboodle-data-shared.so`, built with the C compiler), a link to the Oodle library of the game, the program `tag64` (built with cargo), and the table of the 64-bit tag hashes (`notes/tag64.tsv`). It is safe to run again. `--force` builds again. | 14 seconds |
| `./port marathon tag64` | The table again. Do this after an update of the game. | |
| `./port marathon find "TEXT"` | A list of items: item hash, name, entity | 2.4 seconds |
| `./port marathon extract "ITEM" [--art "BASE ITEM"] [--hands FILE.glb]` | `data/marathon/extract/out/NAME/` | 13 to 17 seconds |

When a thing is missing (a C compiler, cargo, the game folder, a part of `d2x`), the other
steps of the setup run, the end of the output names each missing thing with what to do, and
the exit code is 1. You can delete `data/marathon/extract/target/` after the build.

**Do not start Marathon for this work.** It has an anti-cheat program. The tools only read
the game folder.

**How to know that it worked.** The last line of the setup is of this form:
`the packages open: 1032829 entries; 50 entries read with no error; 43853 hashes in the table`.
`./port doctor marathon` is ok. Then `./port marathon regress` (17 seconds): it extracts each
weapon of `data/marathon/extract/out/` again and compares the bytes. On a new clone that
folder is empty, so extract one weapon first.

## 7. The mod projects (esx)

```sh
./port mod list                  # each mod, its plugin, and if it has a release
./port mod status NAME           # the source files that differ from their copies in data/mods/NAME
./port mod sync NAME             # copy the files of mods/NAME into data/mods/NAME
./port mod build NAME            # sync, esx build, the lock files back; it prints the sha256 of each release file
```

`mods/NAME/` has the files that a person writes. `data/mods/NAME/` is the complete project:
the convert commands write the meshes, the textures and the clips there
([mods/README.md](../mods/README.md)). On a new clone `data/mods/NAME/` is not there, so a
build needs the convert commands of the mod first (the `README.md` of each mod has them).

**How to know that it worked.** The build has 0 issues and 0 warnings, and
`data/mods/NAME/build/release/` has the plugin and the two archives.

## 8. The game test

The game test needs `esx`, `fo4_data`, `proton`, and for a recording GStreamer, PipeWire and
gamescope. Read [porting/game-test.md](porting/game-test.md) before the first start: the
probe has one session for the computer.

```sh
esx probe status                             # look first
./port destiny game session NAME LABEL       # builds the mod, starts a session, prints its ID
esx probe stop --session ID                  # only the ID that the start command printed
```

## The checks of each area in one table

| Area | The setup is complete | The tools give the stored results |
| --- | --- | --- |
| The shared part | `./port selftest` | |
| `fnv/` | `./port doctor fnv` | `./port fnv regress` |
| `destiny/extract/` | `./port doctor destiny` | A second extraction and `cmp` |
| `destiny/port/` | `./port doctor destiny` | `./port destiny regress` |
| `marathon/extract/` | `./port doctor marathon` | `./port marathon regress` |
| `marathon/port/` | `./port doctor marathon`, `./port doctor destiny` | `./port marathon regress-clips` |
| A mod | `./port mod status NAME` | `./port mod build NAME`, and the sha256 of each release file |
| Each stored result of `data/` | | `./port baseline check`: the baseline clips of the regress commands and the release of each mod have the sha256 of `baselines.sha256` |

## What is not proved

* Each setup ran on one computer (Linux, x86-64). A second computer is not tested.
* The setup of `d2x` on a computer with no caches (the cargo registry, the `uv` cache) was
  not run. The setup with no `uv` was not run in this repository.
* The same bytes on a different computer, with a different version of Blender (4.5.13 was
  used) or of `numpy` (2.3), or on a different platform: not tested.
* The regress commands on a new clone, with an empty data folder: this document says what the
  help texts say. No run of this repository started from an empty data folder for
  `destiny/port/`.
* The time of `./port destiny setup`, `./port fnv make-rig` and `./port destiny make-rig`: no
  source has it.
* esx 0.1.0 (commit `a996de8`) made the arm meshes and built the stored mods. The test world
  of the game test needs esx at the commit `d3e520c` (2026-10-06) or later. On 2026-10-06 esx
  at `d3e520c` built each of the 7 mods from nothing with the bytes of `baselines.sha256`. No
  other version was compared.
* If the repository of esx is public: on 2026-10-06 its address gave "not found" with no
  login. The source of the test world file is not known.
* `./port baseline check` on a new clone: the code reports each stored result as "not there"
  with the exit code 0. No run started from an empty data folder.
