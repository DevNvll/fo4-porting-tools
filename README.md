# fo4-porting-tools

Tools that port weapons and their animations to Fallout 4 from Fallout: New Vegas, Destiny 2
and Marathon.

One command, `./port`, runs everything. `./port list` shows what it can do.

* `fnv/` turns the first-person animations of a New Vegas weapon mod, its `.kf` and `.nif`
  files, into Fallout 4 HKX clips.
* `destiny/extract/` pulls a Destiny 2 weapon out of the game as glTF. `destiny/port/` turns
  that into Fallout 4 clips, a model, materials, a sight and third-person clips.
* `marathon/extract/` does the same extraction for Marathon. The conversion reuses
  `destiny/port/`.
* `mods/` holds the sources of seven esx mod projects. `./port mod build NAME` builds one.

No game file is in this repository. Everything extracted or built goes to `data/`, which git
ignores.

## What you need

Linux, Blender 4.5, and Python 3.11 or later with the packages in `requirements.txt`. The
rest depends on the job.

| Job | You also need |
| --- | --- |
| Convert New Vegas animations | Fallout 4, and the skeleton file of the NVCS mod |
| Extract from Destiny 2 | The game build of 23 August 2020, `git`, `cargo` |
| Extract from Marathon | The game, a C compiler, `cargo`, and the Destiny setup |
| Convert a Destiny 2 or Marathon weapon | The extraction above, and Fallout 4 |
| Build a mod or test it in game | esx, plus Proton for the game test |
| Make check pictures for a Destiny 2 or Marathon port | The Fallout 4 arm meshes. esx makes them once with `./port fnv make-rig --arm-meshes`. |
| Make videos and picture sheets | `ffmpeg` |

esx is a separate program by the same author. [docs/getting-started.md](docs/getting-started.md)
says where to get it, what works without it, and how to set up each area.

## Quick start

```sh
git clone https://github.com/DevNvll/fo4-porting-tools.git
cd fo4-porting-tools
cp -n config.example.toml data/config.toml   # then put your own paths in it
./port doctor      # what is set up, what is missing, and how to make it
./port list        # every command, one line each
./port selftest    # checks that need no game file
```

`./port AREA COMMAND --help` shows the arguments of a command.

## Layout

| Folder | What it is |
| --- | --- |
| `port`, `portkit/` | The `./port` command, paths, local settings, mod builds |
| `fnv/` | New Vegas animations to Fallout 4 clips. The other areas also use its HKX reader and writer, its archive reader and its hand solver. |
| `destiny/extract/` | `d2x`, the Destiny 2 extractor |
| `destiny/port/` | `d2fo4`, the converter from glTF to Fallout 4. The checks and the game test programs live here too. |
| `marathon/extract/` | `m2x`, the Marathon extractor |
| `marathon/port/` | Set files for Marathon weapons |
| `mods/` | Sources of the esx mod projects, no assets |
| `docs/` | Documentation |
| `AGENTS.md`, `.claude/skills/` | Instructions for AI agents |
| `tests/` | Tests for `portkit` |
| `data/` | Everything that is not source. Not in git. |

A port goes through these stages.

```
game files -> extract -> glTF + manifest -> convert -> clips, model, materials -> mod project -> build -> checks -> game test
New Vegas mod (.kf, .nif) -----------------> convert -> clips
```

## One example per source

Run every command from the repository root. Each example is a weapon that is already ported.

If your `data/` already holds results for these weapons, the commands write over them. The
bytes stay the same unless you changed something. Run `./port baseline check` afterwards, and
`DIFFERENT` marks a stored result whose bytes changed. To try a command safely, point it at a
scratch folder with `-o`, `--out`, `--work` or `--project`.

### New Vegas, the Walther PPK

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

`fnv/` makes only the clips. The mod project also needs the extracted mod in
`data/mods/PPK/source/` and a gun model in `data/mods/PPK/meshes/`. The PPK model came from
an older version of the tools, at the git tag `before-animation-only`. See
[docs/porting/fnv.md](docs/porting/fnv.md).

### Destiny 2, the Khvostov 7G-02

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

A new weapon needs a set file first, `destiny/port/sets/NAME.toml`.
[docs/porting/destiny.md](docs/porting/destiny.md) walks through it.

### Marathon, the M77

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

Do not start Marathon for this. It has anti-cheat, and the tools only read the game folder.
[docs/porting/marathon.md](docs/porting/marathon.md) has the procedure.

A built mod ends up in `data/mods/NAME/build/release/` as a plugin and two archives.
[docs/porting/game-test.md](docs/porting/game-test.md) covers testing it in game.

## Documentation

| Document | What it covers |
| --- | --- |
| [docs/getting-started.md](docs/getting-started.md) | Setting up each area from scratch |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layout, the data folder, settings, `./port`, mod projects, rules for a change |
| [docs/porting/overview.md](docs/porting/overview.md) | The stages of a port and what counts as correct |
| [docs/porting/destiny.md](docs/porting/destiny.md), [marathon.md](docs/porting/marathon.md), [fnv.md](docs/porting/fnv.md) | The procedure for each source |
| [docs/porting/troubleshooting.md](docs/porting/troubleshooting.md) | Known symptoms, with cause and fix |
| [docs/porting/checks.md](docs/porting/checks.md) | What each check proves and how to read its numbers |
| [docs/porting/game-test.md](docs/porting/game-test.md) | Testing in game with `esx probe` |
| [docs/porting/lessons.md](docs/porting/lessons.md) | What went wrong during the ports, and how it showed |
| [docs/reference/commands.md](docs/reference/commands.md) | Every `./port` command |
| [docs/reference/glossary.md](docs/reference/glossary.md) | The vocabulary |
| [fnv/README.md](fnv/README.md), [destiny/extract/README.md](destiny/extract/README.md), [destiny/port/README.md](destiny/port/README.md), [marathon/README.md](marathon/README.md) | Reference for each area |
| [mods/README.md](mods/README.md) | The mod projects |
| [portkit/README.md](portkit/README.md) | How to add a command to `./port` |
| [AGENTS.md](AGENTS.md) | Start here if you are an AI agent |
