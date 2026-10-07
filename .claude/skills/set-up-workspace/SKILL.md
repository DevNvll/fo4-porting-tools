---
name: set-up-workspace
description: Gives the procedure to prepare this repository on a computer, or to repair it, so that each command of the repository has what it needs (data/config.toml with the settings blender, esx, fo4_data, proton, destiny_game, marathon_game and nvcs_skeleton, the environment of d2x, the runtime of m2x, the two rig folders). Use when "./port doctor" shows MISSING, when a command stops with the exit code 3 and a line that starts with "port:", on a new computer or a new clone, after an update of a game, or when the packages of a game do not open.
---

# Prepare or repair the workspace

Each thing that is not source is below `data/`, which is not in git: the settings, the files
of the games, the third-party clones and builds, the rig folders. `./port doctor` shows each
one, and tells which command makes it. Do what it says, in the order below.

## When to use it, and when not

* Use it before the first work on a computer, and when a command stops for a missing thing.
* A fault of a tool that has all that it needs: `diagnose-port-fault`.

## Before the start

You need the games on the computer: Fallout 4, and for an extraction Destiny 2 or Marathon.
The tools only read a game folder. Do not write into one, and do not start a game for this
work. Do not put a path of this computer into a source file: each local value is a setting
in `data/config.toml`, or an environment variable.

## Steps

### 1. Look

```sh
./port doctor            # or: ./port doctor fnv | destiny | marathon, for one area
./port paths
```

The exit code is 1 when a setting or a check is not ok. Each line has `ok` or `MISSING`, what
the thing is, and the command that makes it.

### 2. The settings

```sh
cp config.example.toml data/config.toml
```

Then give each setting that you need in `data/config.toml`. An environment variable replaces
the value of the file.

| Setting | Variable | What | Who needs it |
| --- | --- | --- | --- |
| `blender` | `BLENDER` | Blender 4.5. Default: `blender` in the `PATH`. | The steps `retarget` and `third`, each check with pictures |
| `esx` | `ESX_BIN` | The esx command. Default: `esx` in the `PATH`. | The model, a build, the game test, the arm meshes |
| `fo4_data` | `FO4_DATA` | The `Data` folder of Fallout 4 | The rig folders, the model, a build |
| `proton` | `PROTON_DIR` | The Proton folder | The game test (Linux) |
| `destiny_game` | `D2X_GAME` | The game folder of Destiny 2 (it has `packages/` and `bin/x64/`) | `./port destiny setup`, an extraction |
| `marathon_game` | `MARATHON_GAME` | The game folder of Marathon | `./port marathon setup`, an extraction |
| `nvcs_skeleton` | `NVCS_SKELETON` | `Meshes/Characters/_1stPerson/Skeleton.nif` of the NVCS mod | `./port fnv make-rig` |

Ask the user for a path that you cannot find. Do not search the whole disk, and do not
download a game file.

### 3. The tools, in this order

```sh
./port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif
./port fnv make-rig --arm-meshes       # the arm meshes for the check pictures (needs esx)
./port destiny make-rig                # the vanilla clips of each template
./port destiny setup                   # d2x: clones, patch, cargo build, Python environment, Oodle link
./port marathon setup                  # m2x: the Oodle 9 shim, the link, tag64, the table of the tag hashes
```

* An area that you do not use needs no setup. `fnv` needs only the first line.
  `destiny/port` needs the first three. An extraction of Destiny 2 needs `destiny setup`.
  Marathon needs `destiny setup`, then `marathon setup`.
* Each setup command is safe to run again: it skips each step that is complete.
* `./port destiny setup` needs `git`, `cargo` and `python3`. It uses `uv` if it is there. It
  uses the network: the two clones, the packages of cargo and the Python packages.
* `./port marathon setup` needs a C compiler and `cargo`. It is for Linux on x86-64. Its last
  step opens the packages and reads 50 entries. `--force` builds again.
* A video needs `ffmpeg`. A shader of Marathon as text needs `llvm-dis`.

### 4. Check

```sh
./port doctor
./port selftest
./port fnv regress
./port destiny regress
./port marathon regress
```

Gate: `./port doctor` has the exit code 0, or each `MISSING` line is for an area that you do
not use. `./port selftest` has the exit code 0: it needs no game file. The three regressions
compare with the results of the ported weapons in `data/`. On a computer with no such
results they cannot pass, and that is not a fault of the setup (`./port fnv regress` then
prints `NO RESULT`).

## Stop and ask the user

* For each path of a game, of Blender, of esx or of Proton that the settings do not have.
* Before a download that is not one of the two clones or the Python packages of
  `./port destiny setup`.
* Before you delete a folder below `data/`. Much of it cannot be made again with no game.

## Common faults

| Sign | Cause | What to do |
| --- | --- | --- |
| `port:` and the exit code 3 | A thing that the command needs is missing | The message names it, and the command that makes it |
| `port:` and the exit code 2 | The words are not a command, or the program file is not there | `./port list`. The message prints the nearest names. |
| A command that reads the packages stops, with exit code 3 | The Python environment of d2x is not there | `./port destiny setup` |
| The packages of Marathon do not open, or SIGSEGV when they open | The runtime folder of m2x | `./port marathon setup`. `OODLE9_DEBUG=1` makes the shim print. |
| m2x stops: "no tag of the class ...: the layouts of this file are for another build" | A game update | `./port marathon tag64`. If it stays: `decode-game-data`. |
| `./port destiny setup` ends with the exit code 1 at its last step | The setting `destiny_game` has no value | Give it. The other steps are complete. |
| A plain `ls` hangs for minutes | The data folder is large, and the shell can have an alias for `ls` with git status | `command ls`, or `find` |
| A shorter clip list of `fnv convert`, with no error | The rig folder has no clip of the template | `./port fnv make-rig` |

## What to report

Each setting with its source (the file, a variable, the `PATH`) but not its value in a
document, each command that you ran, the last output of `./port doctor`, and each thing that
stays missing with the reason.

## More

* [docs/getting-started.md](../../../docs/getting-started.md).
* [docs/ARCHITECTURE.md](../../../docs/ARCHITECTURE.md): the data folder, the settings, the
  command `./port`.
* [portkit/README.md](../../../portkit/README.md): the exit codes and `needs`.
* [destiny/extract/README.md](../../../destiny/extract/README.md), "Folders";
  [marathon/extract/README.md](../../../marathon/extract/README.md), "What the setup makes".
