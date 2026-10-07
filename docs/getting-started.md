# Getting started: the setup of each area

This takes you from a new clone to a setup that works. For each area it gives the commands,
what each one makes, how long it takes when that is known, and how to tell that it worked.
Run every command from the repository root.

A new clone has an empty data folder. `data/` holds every game file and every result, and git
does not have it, so you need your own copies of the games. "The data folder" in
[ARCHITECTURE.md](ARCHITECTURE.md) describes it.

## What you need

| Thing | For | Setting or check |
| --- | --- | --- |
| Linux | Every area was made and tested on Linux. The two Oodle shims are Linux only. | |
| Python 3.11 or later, with `numpy` and `Pillow` (`pip install -r requirements.txt`) | Every area needs `numpy`. The model program and the picture programs need `Pillow`. | `./port doctor` prints the versions. A missing `numpy` makes it fail. The `pillow` line is a report only. |
| Blender 4.5 | The retarget steps and every check that makes pictures. It runs without a window. | `blender` |
| Fallout 4, its `Data` folder | The rig folders, the model program, the build of a mod | `fo4_data` |
| The skeleton file of the New Vegas compatibility skeleton mod (NVCS), `Meshes/Characters/_1stPerson/Skeleton.nif` | The rig folder of `fnv/` | `nvcs_skeleton`, or `--nvcs` |
| esx (see "esx" below) | The arm meshes for the checks, the textures and the materials of a model, the build of a mod, the game test | `esx` |
| Proton | The game test on Linux | `proton` |
| Destiny 2, the build `86657.20.08.23.1800.d2_rc` (23 August 2020) | `destiny/extract/` | `destiny_game` |
| Marathon (the build of 2026-10-06) | `marathon/extract/` | `marathon_game` |
| `git`, `cargo`, and `uv` (or a `python3` of 3.12 or later, for `python3 -m venv`) | `./port destiny setup` | `./port doctor` lists them |
| A C compiler, `cargo` | `./port marathon setup` | |
| `ffmpeg` | Every video and picture sheet | `./port doctor` lists it |
| GStreamer, PipeWire and gamescope | The recording of a game test | |
| `llvm-dis` | `./port marathon notes dxil` only | |

You only need what your area uses. To convert New Vegas animations, that is Python, `numpy`,
Blender, Fallout 4 and the NVCS skeleton file.

### esx

esx is a separate command line tool by the owner of this repository. It builds a Fallout 4
mod from a project folder and starts the game probe. It lives at
`https://github.com/DevNvll/esx`. On 2026-10-06 that address answered "not found" to a
request without a login, so the repository was not public then. Ask the owner for it. Build
it with cargo, using the `cargo install --path crates/esx-cli` line of its `README.md`, and
give the program as the setting `esx`. Version 0.1.0 at the commit `a996de8` made the stored
releases. The commit `d3e520c` of 2026-10-06 is the first one with the test world of the game
test.

| Without esx | With the arm meshes that esx makes once (`./port fnv make-rig --arm-meshes`) | Only with esx |
| --- | --- | --- |
| Every extraction. Every conversion: `fnv convert`, `destiny convert`, `marathon convert`. The regress commands. `destiny check gun`, `fingers`, `gun-on-grip`, `third-sheet`. `./port selftest`, `doctor`, `baseline check`. | Every check that uses the hand meshes: `destiny check validate`, `touch`, `touch-table`, `contact`, `render`. Also `destiny measure-hands`. | `destiny model` and `marathon model`, `./port mod build`, `fnv make-rig --arm-meshes`, every `destiny game` command |

You supply the test world of the game test yourself. It is a ZIP file or a folder with one
plugin, which was `TestWorldspace.esp` in the run of 2026-10-06. No document of this
repository or of esx gives its source.

## 1. The settings

```sh
cp -n config.example.toml data/config.toml   # only when the file is not there; then give your own paths in it
./port doctor                                # each setting, each tool and each necessary file: ok or MISSING
./port list                                  # each command with one line of help
```

`config.example.toml` has one line per setting. A setting comes from its environment
variable, then from `data/config.toml`, then from its default, which for a program is the
`PATH`. If `data/config.toml` already exists, edit it. Copying the example over it removes
your paths, and git has no copy because `data/` is not in git.

| Setting | Variable | What it is |
| --- | --- | --- |
| `blender` | `BLENDER` | The Blender program |
| `esx` | `ESX_BIN` | The esx program |
| `fo4_data` | `FO4_DATA` | The `Data` folder of Fallout 4 |
| `proton` | `PROTON_DIR` | The Proton folder for the game test |
| `destiny_game` | `D2X_GAME` | The Destiny 2 game folder, the one with `packages/` and `bin/x64/` |
| `marathon_game` | `MARATHON_GAME` | The Marathon game folder, the one with `packages/` and `bin/x64/` |
| `nvcs_skeleton` | `NVCS_SKELETON` | The skeleton file of the NVCS mod |

`FO4PORTS_DATA` moves the data folder.

It worked if `./port doctor` shows `ok` for every setting that your area needs.
`./port doctor fnv`, `./port doctor destiny` and `./port doctor marathon` each look at one
area, and a path such as `./port doctor destiny/port` looks at one folder. A `MISSING` line
gives the command that makes the thing. The exit code is 1 when a line is not ok, or when
Python has no `numpy`. Without `data/config.toml`, the command tells you to copy the example.
It names every key in the file that is not a setting, which catches a wrong spelling. A fault
in the file prints as one line.

## 2. The shared part

```sh
./port selftest
```

It needs no game file. It checks that every Python file compiles, that every `port.toml` is
correct, that the tests of `portkit` pass, and that git has no file that is not source. A
file with a game file ending or a NUL byte is not source.

It worked if you get four lines that start with `ok`: `python`, `port.toml`, `tests` and
`git`.

## 3. New Vegas (`fnv/`)

| Command | What it makes | Time |
| --- | --- | --- |
| `./port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif` | The rig folder `data/fnv/rig`: `1st_skeleton.hkx`, the vanilla clips of the templates `smg` and `pistol10mm`, and `nvcs_1st.json`. It reads `Fallout4 - Animations.ba2`. | Not recorded |
| `./port fnv make-rig --arm-meshes` | The first-person arm meshes of Fallout 4 as glTF files, in the same folder. Only the checks of `destiny/port/` read them. It needs `esx`. | Not recorded |
| `./port fnv convert /path/to/extracted-mod` | The clips of a weapon in `data/fnv/out/NAME`, and the work files in `data/fnv/work/NAME` | 27 seconds for the PPK |

It worked if `./port doctor fnv` prints `Result: each setting and each check is ok.` It can
be ok without esx, because the arm meshes are a check of `destiny/port/`. Then run
`./port fnv regress`. It converts every fixture in `data/fnv/fixtures/` again and compares
the clips with `data/fnv/out/`. A new clone has no fixture. The command says so and exits
with 0. Step 5 of [porting/fnv.md](porting/fnv.md) shows how to make the first fixture.

## 4. The extraction of Destiny 2 (`destiny/extract/`)

| Command | What it makes | Time |
| --- | --- | --- |
| `./port destiny setup` | Below `data/destiny/extract/`: the clones of `tiger-pkg` and `tiger-animation-parser` at fixed commits in `vendor/`, the cargo build of the package reader in `target/`, the Python environment in `venv/`, and the Oodle shim and the link to the game's Oodle library in `runtime/`. Safe to run again. | Not recorded. The first extraction after it takes 2 minutes 10 seconds. |
| `./port destiny find "TEXT"` | A list of items: item hash, pattern entity, name | 5 seconds |
| `./port destiny extract "NAME" --arms "ARMOR" --out data/destiny/port/extract` | `NAME/` with the glTF files, `textures/`, `raw/`, `manifest.json` | 30 seconds |

The setup first does every step that does not need the game. Without a value for
`destiny_game` it stops at the last step, the Oodle link, with exit code 1. Without `uv` it
needs a `python3` of 3.12 or later for the Python environment, because the fixed versions in
`destiny/extract/requirements.txt` need it. It stops with a message if `python3` is older.

`tiger-pkg` keeps an index of the packages in your user cache folder, in `tiger-pkg` below
`XDG_CACHE_HOME`. It is about 50 MB for this game, and it is not below `data/`.

It worked if `./port doctor destiny` is ok, `./port destiny find "last word"` prints a row
with a pattern entity, and `./port destiny check-glb FILE.glb` prints `NO PROBLEMS` for an
extracted file. This area has no regress command. To prove the same bytes, extract into a
scratch folder and compare each file with an earlier result, as
[destiny/extract/README.md](../destiny/extract/README.md#checks) shows.

## 5. The converter of Destiny 2 and Marathon (`destiny/port/`)

Do parts 3 and 4 first. This area uses the rig folder of `fnv/` and the `d2x` environment.

| Command | What it makes | Time |
| --- | --- | --- |
| `./port fnv make-rig --nvcs FILE`, then `./port fnv make-rig --arm-meshes` | The Fallout 4 skeleton and the arm meshes in `data/fnv/rig` | Not recorded |
| `./port destiny make-rig` | `data/destiny/port/rig/`: the vanilla clips of each template (`revolver44`, `combatrifle`), the third-person skeleton and clips, the clips of the power armor | Not recorded |
| `./port destiny measure-hands FILE.glb` | `data/destiny/port/rig/d2_hands.json`. Run it only when the hand measurements must change. The tools read `destiny/port/rig/d2_hands.json`, which is in git. | 70 seconds |

It worked if `./port doctor destiny` is ok. Then run `./port destiny regress`. It makes the
clips of every weapon in `destiny/port/regress.toml` again and compares the bytes with the
baseline clips in `data/`. On a new clone the data folder has no extraction and no baseline
clip, so make one weapon first with [porting/destiny.md](porting/destiny.md). On the
author's computer the result of 2026-10-06 was 6 weapons, 162 first-person clips, 16
third-person clips and 6 clips of the power armor, 0 differ.

## 6. Marathon (`marathon/`)

Do part 4 first, `./port destiny setup`. `m2x` uses the Python environment, the package
reader and the clones of `d2x`. For the port, do part 5 too.

| Command | What it makes | Time |
| --- | --- | --- |
| `./port marathon setup` | Below `data/marathon/extract/`. The C compiler builds the Oodle 9 shim `runtime/liboodle-data-shared.so`, and cargo builds the program `tag64`. The setup also makes a link to the game's Oodle library and the table of the 64-bit tag hashes, `notes/tag64.tsv`. Safe to run again. `--force` builds again. | 14 seconds |
| `./port marathon tag64` | The table again. Run it after an update of the game. | |
| `./port marathon find "TEXT"` | A list of items: item hash, name, entity | 2.4 seconds |
| `./port marathon extract "ITEM" [--art "BASE ITEM"] [--hands FILE.glb]` | `data/marathon/extract/out/NAME/` | 13 to 17 seconds |

When something is missing, such as a C compiler, cargo, the game folder or a part of `d2x`,
the other steps of the setup still run. The end of the output names each missing thing with
what to do, and the exit code is 1. You can delete `data/marathon/extract/target/` after the
build.

**Do not start Marathon for this work.** It has an anti-cheat program. The tools only read
the game folder.

It worked if the last line of the setup looks like this:
`the packages open: 1032829 entries; 50 entries read with no error; 43853 hashes in the table`.
`./port doctor marathon` is ok too. Then run `./port marathon regress`, which takes 17
seconds. It extracts every weapon in `data/marathon/extract/out/` again and compares the
bytes. On a new clone that folder is empty, so extract one weapon first.

## 7. The mod projects (esx)

```sh
./port mod list                  # each mod, its plugin, and if it has a release
./port mod status NAME           # the source files that differ from their copies in data/mods/NAME
./port mod sync NAME             # copy the files of mods/NAME into data/mods/NAME
./port mod build NAME            # sync, esx build, the lock files back; it prints the sha256 of each release file
```

`mods/NAME/` has the hand-written files. `data/mods/NAME/` is the complete project, where the
convert commands write the meshes, the textures and the clips.
[mods/README.md](../mods/README.md) describes it. A new clone has no `data/mods/NAME/`, so
run the convert commands of the mod before a build. The `README.md` of each mod has them.

It worked if the build has 0 issues and 0 warnings, and `data/mods/NAME/build/release/` has
the plugin and the two archives.

## 8. The game test

The game test needs `esx`, `fo4_data` and `proton`, plus GStreamer, PipeWire and gamescope
for a recording. Read [porting/game-test.md](porting/game-test.md) before the first start,
because the probe has one session for the computer.

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
| Every stored result in `data/` | | `./port baseline check`. The baseline clips of the regress commands and the release of each mod have the sha256 of `baselines.sha256`. |

## What is not proved

* Every setup ran on one computer, Linux on x86-64. A second computer is not tested.
* The `d2x` setup never ran on a computer without the cargo registry and `uv` caches. The
  setup without `uv` never ran in this repository.
* Nobody tested for the same bytes on a different computer, on a different platform, or with
  a version other than Blender 4.5.13 and `numpy` 2.3.
* For the regress commands on a new clone with an empty data folder, this document repeats
  the help texts. No run of `destiny/port/` in this repository started from an empty data
  folder.
* No source has the time of `./port destiny setup`, `./port fnv make-rig` and
  `./port destiny make-rig`.
* esx 0.1.0 at the commit `a996de8` made the arm meshes and built the stored mods. The test
  world of the game test needs esx at the commit `d3e520c` or later. On 2026-10-06 esx at
  `d3e520c` built each of the 7 mods from nothing with the bytes of `baselines.sha256`.
  Nobody compared another version.
* Whether the esx repository is public, after the "not found" of 2026-10-06. The source of
  the test world file is not known either.
* `./port baseline check` on a new clone. The code reports every stored result as "not there"
  with exit code 0, but no run started from an empty data folder.
