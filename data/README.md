# data

This folder holds everything that is not source: game files, extracted assets, work files,
results, validation pictures and videos, built mods, the third-party clones and builds, and
the local settings. Git ignores all of it except this file. Do not put a file from this
folder into git, and do not publish it. The models, the textures and the animations belong
to the owners of the games.

"The data folder" in `docs/ARCHITECTURE.md` has the full table. In short:

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
necessary files are present. `./port baseline check` compares the stored results in this
folder with `baselines.sha256` in the root, and shows a stored result that a command
replaced. The stored results are the baseline clips of the regress commands, and the clips
and the release of each mod.

Most files here are results that a command can make again from your own copies of the games
and of the mods. These are not:

* `destiny/extract/handoff/the_last_word_v1/`, a frozen copy of the first extraction of The
  Last Word. The regression of The Last Word reads its first-person file.
* The models and the textures of the mods `PPK` and `FAMAS`, which came from the tools at the
  git tag `before-animation-only`.
* The recordings and the logs of the game tests in `destiny/port/validation/`.
* `transcripts/` and `notes/`.
