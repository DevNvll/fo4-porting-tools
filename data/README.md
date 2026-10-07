# data

This folder holds all that is not source: each file of a game, each extracted asset, each
work file, each result, each validation picture and video, each built mod, the third-party
clones and builds, and the local settings. Git ignores all of it, with the exception of this
file. Do not put a file of this folder into git, and do not publish it: the models, the
textures and the animations belong to the owners of the games.

`docs/ARCHITECTURE.md`, "The data folder", has the table of each folder. In short:

| Folder | Content | Made by |
| --- | --- | --- |
| `config.toml` | The local settings | You, from `config.example.toml` |
| `fnv/` | The rig folder, the work files, the clips and the fixtures of the New Vegas tools | `./port fnv make-rig`, `./port fnv convert` |
| `destiny/extract/` | The clones, the builds and the Python environment of `d2x`, and its default output | `./port destiny setup`, `./port destiny extract` |
| `destiny/port/` | The extraction of each weapon for a port, the rig folder, the work files, the clips and the validation results | `./port destiny extract --out`, `./port destiny make-rig`, `./port destiny convert`, `./port destiny check ...` |
| `marathon/extract/` | The runtime, the results and the validation pictures of `m2x` | `./port marathon setup`, `./port marathon extract` |
| `mods/NAME/` | The complete esx project of each mod, with `build/release/` | `./port mod sync`, the convert commands, `./port mod build` |
| `transcripts/`, `notes/` | The chat transcripts as short text, and the notes that the documents came from | |

The environment variable `FO4PORTS_DATA` moves this folder. `./port doctor` shows which
necessary files are there.

Most files of this folder are results that a command makes again from your own copies of
the games and of the mods. These are not:

* `destiny/extract/handoff/the_last_word_v1/`: a frozen copy of the first extraction of The
  Last Word. The regression of The Last Word reads its first-person file.
* The models and the textures of the mods `PPK` and `FAMAS`: they came from the tools at the
  git tag `before-animation-only`.
* The recordings and the logs of the game tests in `destiny/port/validation/`.
* `transcripts/` and `notes/`.
