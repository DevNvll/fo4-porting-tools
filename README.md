# fo4-ports

Tools that port weapons and their animations to Fallout 4 from three sources: Fallout: New
Vegas, Destiny 2 and Marathon. A person and an AI agent use the same commands, the same
documents and the same checks.

* `fnv/` converts the first-person animations of a New Vegas weapon mod (`.kf`, `.nif`) to
  Fallout 4 clips (HKX).
* `destiny/extract/` exports a weapon of Destiny 2 from the game as glTF files, and
  `destiny/port/` converts those files to Fallout 4 clips, a model, materials, a sight and
  third-person clips.
* `marathon/extract/` exports a weapon of Marathon. Its conversion uses `destiny/port/`.
* `mods/` has the sources of seven esx mod projects, and `./port mod build` builds them.
* One command, `./port`, starts each program. `./port list` shows each command.

No file of a game is in this repository. Each extracted asset and each result is in `data/`,
which git ignores.

## What you need

Linux, Python 3.11 or later with `numpy` and `Pillow` (`requirements.txt`), and Blender 4.5.
Then, for each thing that you do:

| To do this | You need |
| --- | --- |
| Convert New Vegas animations | Fallout 4 (its `Data` folder), and the skeleton file of the New Vegas compatibility skeleton mod |
| Extract a weapon of Destiny 2 | The game (the build of 23 August 2020), `git`, `cargo` |
| Extract a weapon of Marathon | The game, a C compiler, `cargo`, and the setup of the Destiny extraction |
| Convert a weapon of Destiny 2 or Marathon | The two lines above, and Fallout 4 |
| Make a model, build a mod, test in the game | esx, and Proton for the game test. esx is a separate program of the owner of this repository: [docs/getting-started.md](docs/getting-started.md), "esx", says where it is and what works with no esx. |
| Make the check pictures of a Destiny 2 or Marathon port | The arm meshes of Fallout 4, which esx makes one time (`./port fnv make-rig --arm-meshes`) |
| Make videos and picture sheets | `ffmpeg` |

[docs/getting-started.md](docs/getting-started.md) has the complete list and the setup of
each area.

## The first 5 minutes

```sh
cp -n config.example.toml data/config.toml  # only when the file is not there; then give your own paths in it
./port doctor                               # each setting, each tool and each necessary file: ok or MISSING
./port list                                 # each command with one line of help
./port selftest                             # checks that need no game file
./port baseline check                       # each stored result of data/ has the bytes on record
```

`./port doctor` tells you how to make each thing that is missing. `./port AREA COMMAND
--help` shows the arguments of a command. If `data/config.toml` is there, edit it: a copy of
the example over it removes your paths. On a new clone `./port baseline check` reports each
stored result as "not there": that is correct for an empty data folder.

## A map of the folders

| Folder | What it is |
| --- | --- |
| `port`, `portkit/` | The command `./port`, the paths, the local settings, the mod projects |
| `fnv/` | New Vegas animations to Fallout 4 clips. It also has the Fallout 4 library of the other areas: the HKX reader and writer, the archive reader, the hand solver. |
| `destiny/extract/` | `d2x`: a weapon of Destiny 2 as glTF files |
| `destiny/port/` | `d2fo4`: a glTF file of `d2x` or `m2x` to Fallout 4 clips and a model. The checks and the game test programs are here. |
| `marathon/extract/` | `m2x`: a weapon of Marathon as glTF files |
| `marathon/port/` | The set files of the Marathon weapons |
| `mods/` | The sources of the esx mod projects. No asset. |
| `docs/` | The documents for a person |
| `AGENTS.md`, `.claude/skills/` | The instructions for an AI agent |
| `tests/` | The tests of `portkit` |
| `data/` | All that is not source. Not in git. |

The stages of a port:

```
game files -> extract -> glTF + manifest -> convert -> clips, model, materials -> mod project -> build -> checks -> game test
New Vegas mod (.kf, .nif) -----------------> convert -> clips
```

## One example for each source

Each command runs in the root of the repository. Each example is a weapon that is ported.

On a computer that has the stored results of these weapons, the commands of an example write
over them: the extraction, the clips, the model and the release. The bytes stay the same when
nothing changed. Run `./port baseline check` after an example: `DIFFERENT` names a stored
result that has other bytes now. To try a command with no risk, give it a scratch folder
(`-o`, `--out`, `--work`, `--project`).

### New Vegas: the Walther PPK

```sh
# one time: the rig folder
./port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif

# the clips of an extracted mod, with no conversion file (into data/fnv/out/NAME)
./port fnv convert /path/to/extracted-mod

# the mod project of the PPK: the clips into the project, then the build
./port mod sync PPK
./port fnv convert data/mods/PPK/conversion.toml
./port mod build PPK
./port fnv regress
```

The tools of `fnv/` make only the clips. The mod project needs the extracted mod in
`data/mods/PPK/source/` and a model of the gun in `data/mods/PPK/meshes/`. The model of the
PPK came from the tools at the git tag `before-animation-only`
([docs/porting/fnv.md](docs/porting/fnv.md)).

### Destiny 2: the Khvostov 7G-02

```sh
# one time: the extraction tool and the rig folders
./port destiny setup
./port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif
./port fnv make-rig --arm-meshes
./port destiny make-rig

# the extraction
E=data/destiny/port/extract/khvostov_7g_02
./port destiny find "Khvostov"
./port destiny extract "Khvostov 7G-02" --arms "Ancient Apocalypse Grips" --out data/destiny/port/extract
./port destiny states $E/manifest.json -o $E/states.json
./port destiny reticle "Khvostov 7G-02" -o $E/sight.json
./port destiny third $E/manifest.json

# the clips, the model, the third-person reload, the mod
GLB=$E/khvostov_7g_02_first_person.glb
SET=destiny/port/sets/khvostov_7g_02.toml
M=data/mods/Khvostov
./port destiny convert $GLB --set $SET -o $M/behavior/khvostov/animations/first_person
./port destiny model $GLB --set $SET --mod Khvostov
./port destiny convert $GLB --set $SET third --third-output $M/behavior/khvostov/animations/third_person
./port mod build Khvostov --update-lock
./port destiny regress --only khvostov_7g_02
```

A new weapon needs a set file first (`destiny/port/sets/NAME.toml`).
[docs/porting/destiny.md](docs/porting/destiny.md) has the procedure.

### Marathon: the M77

```sh
# one time
./port destiny setup
./port marathon setup

# the extraction
./port marathon find "M77"
./port marathon extract "M77 Omnipositor" --art "M77 Assault Rifle" \
    --hands data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb

# the clips, the model, the mod
GLB=data/marathon/extract/out/m77_omnipositor/m77_omnipositor_first_person.glb
SET=marathon/port/sets/m77_omnipositor.toml
./port marathon convert $GLB --set $SET -o data/mods/M77/behavior/m77/animations/first_person
./port marathon model $GLB --set $SET
./port mod build M77 --update-lock
./port marathon regress
./port marathon regress-clips
```

Do not start Marathon for this work: it has an anti-cheat program. The tools only read the
game folder. [docs/porting/marathon.md](docs/porting/marathon.md) has the procedure.

The release of a mod is `data/mods/NAME/build/release/`: the plugin and two archives.
`baselines.sha256` has the sha256 of each release that was tested. The game test of a mod is
in [docs/porting/game-test.md](docs/porting/game-test.md).

## Where each document is

| Document | Content |
| --- | --- |
| [docs/getting-started.md](docs/getting-started.md) | The setup of each area from nothing |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | The layout, the data folder, the settings, the command `./port`, the mod projects, the rules for a change |
| [docs/porting/overview.md](docs/porting/overview.md) | The stages of a port, the gate of each stage, what "correct" means, the rules for each source |
| [docs/porting/destiny.md](docs/porting/destiny.md) | The procedure for a weapon of Destiny 2 |
| [docs/porting/marathon.md](docs/porting/marathon.md) | The procedure for a weapon of Marathon |
| [docs/porting/fnv.md](docs/porting/fnv.md) | The procedure for a weapon of New Vegas |
| [docs/porting/troubleshooting.md](docs/porting/troubleshooting.md) | Each known sign, with its cause and its rule |
| [docs/porting/checks.md](docs/porting/checks.md) | Each check, what it proves, how to read its numbers |
| [docs/porting/game-test.md](docs/porting/game-test.md) | The test in the game with `esx probe` |
| [docs/porting/lessons.md](docs/porting/lessons.md) | The history: each correction of the user, and each fault with how it showed |
| [docs/reference/commands.md](docs/reference/commands.md) | Each command of `./port` |
| [docs/reference/glossary.md](docs/reference/glossary.md) | Each special word |
| [fnv/README.md](fnv/README.md), [destiny/extract/README.md](destiny/extract/README.md), [destiny/port/README.md](destiny/port/README.md), [marathon/README.md](marathon/README.md), [marathon/extract/README.md](marathon/extract/README.md), [marathon/port/README.md](marathon/port/README.md) | The reference of each area |
| [mods/README.md](mods/README.md), `mods/NAME/README.md` | The mod projects, and each mod |
| [portkit/README.md](portkit/README.md) | The command `./port` and `port.toml`, for a person who adds a command |
| `AGENTS.md`, `.claude/skills/` | The instructions for an AI agent |

## What is in git, and what is not

In git: the programs, the set files, the templates, the hand-written files of each mod
(`esx.toml`, the item files, the behavior sources, the lock files), two measurement files
(`fnv/rig/finger_tips.json`, `destiny/port/rig/d2_hands.json`), `baselines.sha256`, and the
documents.

Not in git: `data/`, with the exception of [data/README.md](data/README.md). It has each
file of a game, each extracted model, texture and animation, each work file, each clip, each
validation picture and video, each built mod, the third-party clones and builds, and the
local settings (`data/config.toml`). No tool writes a generated file into the source tree.

No file of a game, no part of one and no asset that a tool made from one is in git. Three
kinds of tracked files have numbers that were calculated from game files. The two
measurement files have lengths and skin centers of the hand meshes. The lock files have the
object ID of each record and the hashes of the vanilla graphs. `baselines.sha256` has the
sha256 of each stored result. `./port selftest` fails when git has, or can add, a file with a
game file ending or with a NUL byte.

## The state

Eight weapons are ported. Each row gives the clips that the tools make and how the weapon
was tested.

| Weapon | Source | Mod | Clips | The game test | The regression in this repository |
| --- | --- | --- | --- | --- | --- |
| The Last Word (a hand cannon) | Destiny 2 | `TheLastWord`, `TexMechanica` | 24 first person, 2 third person | 2026-10-06, the mod `TexMechanica`: first person 44 ops, third person 73 ops, 0 failed. The mod `TheLastWord`: third person 94 ops, 0 failed; its first-person recording is older and has 44 ops with 1 failed op (`ammo.set` with no reserve count). | `./port destiny regress`: the same bytes |
| Khvostov 7G-02 (an auto rifle) | Destiny 2 | `Khvostov` | 27 first person, 2 third person | 2026-10-06: first person 40 ops, third person 88 ops, 0 failed | The same bytes |
| Hammerhead (a machine gun) | Destiny 2 | `Hammerhead` | 27 first person, 2 third person | 2026-10-06: first person 40 ops, third person 109 ops, 0 failed | The same bytes |
| The Chaperone (a shotgun with a lever) | Destiny 2 | `TexMechanica` | 30 first person, 8 third person, 6 copies of a vanilla clip for power armor | 2026-10-06: first person 44 ops, third person 94 ops, 12 reloads (one for each count of rounds in each view), 0 failed | The same bytes |
| The Huckleberry (a submachine gun) | Destiny 2 | `TexMechanica` | 27 first person, 2 third person | 2026-10-06: first person 40 ops, third person 88 ops, 0 failed | The same bytes |
| M77 (an assault rifle) | Marathon | `M77` | 27 first person | 2026-10-06: 40 ops, 0 failed | `./port marathon regress` and `regress-clips`: the same bytes |
| Walther PPK (a pistol) | New Vegas | `PPK` | 27 first person | 2026-10-05: 34 of 34 steps, and 27 of 27 with the suppressor | `./port fnv regress`: the same bytes |
| FAMAS F1 (a bullpup rifle) | New Vegas | `FAMAS` | 26 first person | 2026-10-05: 32 of 32 steps, and 55 of 55 with the parts | The same bytes |

* Each game test of the table ran in the test copy of the game of `esx probe`, with no
  window, before the tools came into this repository. The clips of today have the same bytes
  as the clips of those tests (the regress commands, 2026-10-06). One more run was in this
  repository: the three weapons of `TexMechanica` in the test world, 10 commands, 0 failed
  ([docs/porting/game-test.md](docs/porting/game-test.md)).
* The release of each of the 7 mods is on record in `baselines.sha256`. On 2026-10-06 esx at
  the commit `d3e520c` built each of the 7 mods from nothing (a copy of the project with no
  `build/` folder, in a scratch folder): each of the 21 release files had the bytes on record.
  The older esx (`a996de8`) made the stored releases.
* The Destiny and Marathon weapons also have the numbers of each clip in
  `data/destiny/port/validation/NAME/` ([docs/porting/checks.md](docs/porting/checks.md)).
* The models and the textures of the two New Vegas mods came from the tools at the git tag
  `before-animation-only`. The tools of today make their clips.

## What is not proved

* **The game test programs in this repository.** They were adapted to the layout of this
  repository. [docs/porting/game-test.md](docs/porting/game-test.md), "The state of the game
  test programs", says what ran in it.
* **A comparison with the source game.** No port was compared with a picture of Destiny 2 or
  of Marathon. Marathon was not started.
* **A person in the game.** Nobody played a mod with a keyboard and a mouse. No mod was in
  the installed game. The weapons workbench, power armor and the sound were not tested.
* **The clips that did not play.** The game tests send no move input, so the walk, run and
  jump clips did not play.
* **The hands of a New Vegas port.** `fnv/` has no check with pictures. Its regression
  compares bytes only.
* **A second computer.** Each setup and each "same bytes" result is from one computer
  (Linux, Blender 4.5.13, `numpy` 2.3). The same bytes on a second computer are not proved.
* **The regression with new data.** `./port destiny regress` reads the frozen first
  extraction of The Last Word (`data/destiny/extract/handoff/the_last_word_v1/`), not a new
  extraction. It also needs the extraction of the M77 of Marathon, because the M77 is in its
  table. With no such data it fails for those weapons (`--only NAME` does one weapon).
* **The builds.** `./port mod build` ran in this repository for `TexMechanica`, `PPK` and
  `FAMAS`. For the 7 mods there is the one comparison of "The state" (a build from nothing
  with esx `d3e520c`). No other esx version was compared.
* **A new weapon class.** The tools have templates for a revolver, a combat rifle, a
  submachine gun and a 10mm pistol. A different class needs a new template, and can need
  programming.
* **A new build of a game.** The extraction of Destiny 2 is for one build of 2020. The
  extraction of Marathon is for the build of 2026-10-06.

Each area document and each mod document has its own part "What is not proved".

## The license and the assets

This repository has no license file yet. One file has an origin with the license GPL-3.0
([fnv/README.md](fnv/README.md), "Origin of one file").

The models, the textures and the animations of the games belong to their owners, and they
are not in git. A built mod has such assets. Do not publish a built mod, and read the
permissions of a New Vegas mod before you publish a port of it.
