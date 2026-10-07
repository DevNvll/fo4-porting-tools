# The commands of `./port`

`./port list` and `./port AREA COMMAND --help` are the source of truth. This document is a
map of the 74 commands that `./port list` had on 2026-10-06, grouped by area and by stage,
each with one line and its most used options. When this document and `--help` disagree,
`--help` is correct.

Run every command from the repository root. Every program also runs without `./port`, as
`python3 PATH/program.py`. `./port` adds the names, the environment and the check of what a
command needs, which [portkit/README.md](../../portkit/README.md) describes.

## The help of a command

Every command has a help text. `./port AREA COMMAND --help` prints it and starts no work.
`destiny check render`, `destiny check touch` and `destiny check contact` start Blender to
print theirs. `./port marathon notes dxil --help` prints its help with exit code 1.

## The commands of `./port` itself

| Command | What it does |
| --- | --- |
| `./port list [--json]` | Every command of every `port.toml`, with one line of help |
| `./port AREA`, `./port AREA WORD` | The commands of one area (`fnv`, `destiny`, `marathon`), or those that start with two words, such as `./port destiny check` |
| `./port AREA COMMAND --help` | The arguments of one command |
| `./port doctor [AREA] [--json]` | Every setting, tool and necessary file as `ok` or `MISSING`, with how to make it. AREA is `fnv`, `destiny`, `marathon`, or a path such as `destiny/port`. Exit code 1 when a line is not ok, or when Python has no `numpy`. The `Pillow` line is a report only. |
| `./port paths [--json]`, `./port paths get NAME` | The folders and the settings |
| `./port selftest` | Four parts: every Python file compiles (`python`), every `port.toml` is correct (`port.toml`), the tests of `portkit` pass (`tests`), and git has no file that is not source (`git`). It needs no game file. |
| `./port baseline check` | Compares every stored result in `data/` with `baselines.sha256`: the baseline clips of the regress commands, and the clips and the release of each mod. Exit code 1 when a file is different. It also reports a missing file and a file that the list does not have. |
| `./port baseline update` | Writes `baselines.sha256` again. Only for a change that the user accepted. Put the file into git with that change. |
| `./port mod list` | Every mod in `mods/`, its plugin, and whether it has a release |
| `./port mod status NAME` | The source files that differ from their copies in `data/mods/NAME` |
| `./port mod sync NAME [--force]` | Copies the files of `mods/NAME/` into `data/mods/NAME/`. It deletes nothing. `--force` replaces a lock file of `data/` that is different and newer. |
| `./port mod build NAME [--update-lock]` | Syncs, runs `esx build` on `data/mods/NAME/`, and copies the lock files back to `mods/NAME/`. It prints the sha256 of each release file. `--format text` after NAME gives text. |

`./port` itself exits with 2 for words that are not a command, with 3 when something that a
command needs is missing and the program did not start, and with 1 for a fault that `doctor`,
`selftest`, `mod sync` or `baseline check` found. `./port` starts a program with `exec`, so a
signal to the process ID of `./port` goes to the program. A program prints a file error as
one line, and `FO4PORTS_TRACEBACK=1` shows the traceback.

## New Vegas: `./port fnv`

| Stage | Command | What it does | Most used options |
| --- | --- | --- | --- |
| Setup | `fnv make-rig` | Makes the rig folder `data/fnv/rig` from the animation archive of Fallout 4 and the skeleton file of the NVCS mod | `--nvcs FILE`, `--arm-meshes` (the arm meshes for the checks of `destiny/port/`; needs esx), `--data DATA`, `--out DIR` |
| Input | `fnv inspect FILE` | Prints the nodes and the shapes of a model (`.nif`), or the tracks and the text keys of an animation (`.kf`) | |
| Input | `fnv list-archive ARCHIVE [PATTERN]` | Lists the files of a general Fallout 4 archive (`.ba2`) whose name has a text | |
| Convert | `fnv convert SOURCE` | Converts the first-person animations of an extracted mod to Fallout 4 clips | `-o OUT`, `--template pistol10mm\|smg`, `--name NAME`, `--work DIR` |
| Convert | `fnv convert CONFIG [STEP ...]` | The same with a conversion file. Steps: `bake parts retarget synth hkx install`. | `show` (every value that the tools assume), `plan` (the source of each clip, the events of each reload) |
| Check | `fnv regress [NAME ...]` | Converts every fixture in `data/fnv/fixtures` again and compares the clips with `data/fnv/out` | `--list` |

## The extraction of Destiny 2: `./port destiny` (`destiny/extract/`)

| Stage | Command | What it does | Most used options |
| --- | --- | --- | --- |
| Setup | `destiny setup` | Prepares d2x below `data/destiny/extract`: the clones, the patch, the cargo build, the Python environment, the Oodle link. It needs `git`, `cargo`, and `uv` or a `python3` of 3.12 or later. | None. Safe to run again. |
| Extract | `destiny find TEXT` | Lists the items whose name has the text: item hash, pattern entity, name | |
| Extract | `destiny extract ITEM ...` | Exports a weapon as glTF files with a manifest: the model, the textures, the rigs, the clips | `--arms ARMOR`, `--out DIR` (`data/destiny/port/extract` for a port), `--transparent`, `--feminine`, `--all` |
| Extract | `destiny tag HASH ...` | Writes the raw data of package entries to files | `--out DIR` |
| Check | `destiny check-glb FILE.glb ...` | Imports a file in Blender, does the checks, renders previews | `--view side\|right\|front\|back\|fp`, `--clip NAME`, `--clips N`, `--sheet`, `--out DIR` |
| Check | `destiny video FILE.glb --clip NAME[=LABEL][@N] --out FILE` | Renders clips from the first-person camera: `.mp4` for a video, `.png` for a frame sheet | `--columns N`, `--width N`, `--view fp\|side\|front` |

## The converter of Destiny 2 and Marathon: `./port destiny` (`destiny/port/`)

### Setup

| Command | What it does | Most used options |
| --- | --- | --- |
| `destiny make-rig` | Puts the vanilla clips of each template weapon into `data/destiny/port/rig` | `--data DATA` |
| `destiny measure-hands FILE.glb` | Measures the Destiny hand mesh against the Fallout 4 hand mesh, for `d2_hands.json`. 70 seconds. | `-o FILE.json` |
| `destiny measure-template FOLDER CLIP ...` | Measures the weapon bones of the vanilla clips of a template folder, for a new template file | |

### More data of the game (these programs read the packages of Destiny 2)

| Command | What it does | Most used options |
| --- | --- | --- |
| `destiny states MANIFEST.json` | The clip of each game state of a weapon, from the animation graph | `-o states.json` |
| `destiny dyes ITEM` | The dyes of a weapon or of a shader item | `-o dyes.json`, `--shader NAME`, `--list TEXT` |
| `destiny reticle ITEM -o sight.json` | The glass of the sight of a weapon and its reticle, with the shader files | `--manifest FILE` |
| `destiny third MANIFEST.json` | The third-person clips of a weapon (the body with the gun) | `--state STATE[=NAME]`, `--additive STATE`, `--base STATE[:FRAME]`, `-o FOLDER` |
| `destiny pose MANIFEST.json` | Clips with the hand pose of a pose clip of the gun, for `[hand_pose]` | `--list`, `--measure`, `--pose TAG`, `--hold CLIP[:FRAME]`, `--clip CLIP`, `--gun-on-grip` |

### Convert

| Command | What it does | Most used options |
| --- | --- | --- |
| `destiny convert FILE.glb --set SET.toml [STEP ...]` | Converts the clips of a set file to Fallout 4 clips. Steps: `bake parts retarget hkx install`, and `third` when you name it. | `-o OUT`, `--third-output DIR`, `--clip CLIP=NAME` (single clips), `--template NAME`, `--hold CLIP[:FRAME]`, `--work DIR` |
| `destiny points WORK/parts.json` | Prints the muzzle, the eye point and a map of the sight of a gun, for a set file | `--poses FILE.npz` |
| `destiny model FILE.glb --set SET.toml` | Makes the model, the materials, the textures and the sight of a weapon in `data/mods/NAME` | `--mod NAME`, `--project DIR` (a scratch project), `--parts FILE` |
| `destiny shader-text FILE.dxbc` | Prints the instructions of a Direct3D 11 shader file of a sight material | |

### Checks

| Command | What it does | Most used options |
| --- | --- | --- |
| `destiny regress` | Makes the clips of every ported weapon again and compares the bytes with the baseline clips that `destiny/port/regress.toml` names | `--only NAME`, `--jobs N`, `--list`, `--no-run`, `--against DIR` |
| `destiny check validate FILE.glb --set SET.toml --out FOLDER` | The numbers and the videos of every clip of a set | `--clips FOLDER`, `--no-video`, `--left-hand`, `--only NAME`, `--resume` |
| `destiny check gun-on-grip MANIFEST.json` | The distance from the gun bone to the grip bone in every full-pose clip of an extraction. Run it before you write a set file. | `--clip CLIP` (only these clips; exit code 1 when one is not correct), `--rig N`, `--limit M` |
| `destiny check gun FILE.glb CLIP WORK/parts.json CLIP.hkx` | Compares the gun of a clip with the gun of the source, vertex by vertex | |
| `destiny check fingers CLIP.hkx` | The finger joints of a clip against the vanilla clips of the template | `--bake FILE.npz`, `--vanilla FOLDER` (the folder of `revolver44` by default; for a long gun `data/destiny/port/rig/combatrifle`) |
| `destiny check contact --glb FILE.glb --bake FILE.npz --poses CLIP.hkx --parts FILE.json` | The hand vertices inside the gun, source and result (in Blender) | `--frames all`, `--quiet`, `--out FILE.json` |
| `destiny check contact-table FILE.json` | A short table of a file of `check contact` | |
| `destiny check touch --glb FILE.glb --bake FILE.npz --poses CLIP.hkx --parts FILE.json` | How near each hand is to the gun, source and result (in Blender) | `--frames 0` |
| `destiny check touch-table FILE.glb --set SET.toml --clips FOLDER` | The distance from each hand to the gun in every clip of a set | `--out FILE.txt`, `--only NAME` |
| `destiny check render --glb FILE.glb --clip CLIP --poses CLIP.hkx --parts FILE.json --out DIR` | Pictures of the source and of the result of a clip (in Blender) | `--frames 0,10,20\|all`, `--views fp,l_thumb,...`, `--kinds src,fo4`, `--template NAME` (default `revolver44`, so give the template of the set file) |
| `destiny check sheet DIR CLIP VIEW "0 10 20" OUT.jpg` | Pictures of `check render` in one picture, the source above the result | |
| `destiny check look-sheet DIR CLIP FRAME OUT.jpg VIEW[,VIEW...]` | One frame from more views, the source above the result | |
| `destiny check frame-sheet DIR TAG OUT.jpg` | Every frame of one view in one picture | `--columns N`, `--view fp` |
| `destiny check hand-sheet --before DIR --after DIR --clip CLIP --out OUT.jpg` | One hand before and after a change, as game pictures and as check pictures | `--before-game PNG`, `--after-game PNG`, `--views` |
| `destiny check video DIR CLIP OUT.mp4 VIEW [VIEW2] [RATE]` | A video from the pictures of `check render`, the source beside the result | |
| `destiny check strip VIDEO OUT.jpg [COUNT] [WIDTH]` | Frames of a video at equal steps, in one row | |
| `destiny check video-sheet VIDEO OUT.jpg` | Frames of a video at equal steps with the time of each one, in rows | `--count N`, `--columns N` |
| `destiny check third-sheet SOURCE.npz RESULT.npz OUT.png` | A third-person clip as lines, the source above the result | `--frames N` |

[checks.md](../porting/checks.md) says how to read each result.

### The game test

The probe has one session at a time for the whole computer. Read
[game-test.md](../porting/game-test.md) before the first start.

| Command | What it does | Most used options |
| --- | --- | --- |
| `destiny game session NAME LABEL` | Builds a mod, starts a game test session with its release and prints the session ID. When the session file has a session with a different label, it stops nothing and exits with 1. | `--cell ID` (default `QASmoke`), `--world` (the cell of the test world), `--no-build` (the release that is already built), `--take-over` (stops the session of a different label, so ask the user first) |
| `destiny game record --session ID --weapon EDITORID --out DIR` | Records the first-person game test of a weapon as a video | `--capacity N`, `--auto` |
| `destiny game third --session ID --weapon EDITORID --out DIR` | The game test of the third-person clips, with pictures from three sides | `--capacity N`, `--record` |
| `destiny game reloads --session ID --weapon EDITORID --capacity N --out DIR` | One reload for each count of rounds, in the two views | |
| `destiny game sight --session ID --weapon EDITORID --capacity N --out DIR` | Game pictures of a weapon at the hip and in the sights | |
| `destiny game trace --session ID --weapon EDITORID --loaded N` | Prints the clips and the events of one reload in the game | `--view first\|third` |
| `destiny game shots --session ID --loaded N --from T0 --to T1 --count N --out DIR` | Game pictures of the gun in a slow third-person reload | `--weapon EDITORID`, `--speed`, `--yaw` |
| `destiny game all --session ID --weapon EDITORID:CAPACITY[:auto][:reloads] ... --out DIR` | Every game test of the weapons of a mod in one session. It neither starts nor stops a session. Without `--session` it takes the ID of the shared session file, so give `--session ID`. | `--wait SECONDS` (the age of the session at which the first test starts; default 140), `--mod NAME`, `--tested FILE` (the three `sha256sum` lines of the release, with or without a folder before each name), `--dry-run` |
| `destiny game results --out FOLDER` | Copies the results of the game tests of a weapon into its validation folder and prints the numbers | `--record DIR`, `--third DIR`, `--sight DIR`, `--reloads DIR` |

### The analysis programs of the game data

These programs print the data that the tools were made from. They read the packages of
Destiny 2.

| Command | What it does |
| --- | --- |
| `destiny notes weapon-tags MANIFEST.json` | Prints the weapon tags that the pattern entity of a weapon lists |
| `destiny notes graph-tags MANIFEST.json` | Prints the weapon tag tree and the leaves of the main states of each first-person rig |
| `destiny notes third-graph-dump OUT.json` | Writes every state and leaf of the third-person graph of the player body |
| `destiny notes third-clip-index OUT.npy` | Writes a table of every animation clip tag of the game: name hash, frames, bones |
| `destiny notes dyes-explore ITEM_HASH ...` | Finds the dye tables of the game build |
| `destiny notes dye-values ITEM_HASH ...` | Prints the values of the dyes of an item |
| `destiny notes dye-slots ITEM_HASH ...` | Prints the dye slot data of each mesh part of an item |
| `destiny notes dye-dump WRAPPER_TAG ...` | Prints the data of the tag of a dye |

## Marathon: `./port marathon`

| Stage | Command | What it does | Most used options |
| --- | --- | --- | --- |
| Setup | `marathon setup` | Prepares m2x below `data/marathon/extract`: the Oodle 9 shim, the link to the Oodle library of the game, `tag64`, the table of the 64-bit tag hashes | `--table`, `--force`. Safe to run again. |
| Setup | `marathon tag64` | Makes the table of the 64-bit tag hashes again. Do this after an update of the game. | |
| Extract | `marathon find TEXT` | Lists the items whose name has a text: item hash, name, entity | |
| Extract | `marathon extract ITEM` | Extracts a weapon as glTF files with textures, `manifest.json` and `states.json` | `--art ITEM` (the base item of a variant), `--hands FILE.glb`, `--arms N`, `--out OUT` |
| Check | `marathon render FILE.glb OUT.png` | Makes pictures of a `.glb` file (in Blender) | `--views side,top,front,quarter`, `--action NAME`, `--frame N`, `--frames FIRST:LAST` |
| Check | `marathon regress [NAME ...]` | Extracts every weapon in `data/marathon/extract/out` again and compares the bytes | `--keep` |
| Convert | `marathon convert FILE.glb --set SET.toml` | The program of `destiny convert`, for a set file of `marathon/port/sets/` | `-o OUT` |
| Convert | `marathon model FILE.glb --set SET.toml` | The program of `destiny model` | `--mod NAME` |
| Check | `marathon regress-clips` | `destiny regress --only m77_omnipositor`: the clips of the M77 against the baseline clips | |

The analysis programs of the packages of Marathon:

| Command | What it does |
| --- | --- |
| `marathon notes class-graph [SAMPLES]` | The count, the sizes, the package groups and the classes that its entries name, for every tag class |
| `marathon notes scan-text TEXT [TEXT ...]` | Searches every package entry for a text. It takes minutes. The complete scan of the first work took 1,093 seconds. |
| `marathon notes paths PREFIX [PREFIX ...]` | Lists the development paths in the tags of the packages whose name starts with a prefix |
| `marathon notes find-value VALUE [VALUE ...]` | Finds the tags that have a 32-bit value (a tag, a name hash). Options: `--all`, `--pkg PREFIX`. |
| `marathon notes describe TAG [TAG ...]` | Describes tags: the texts, the tags that each one names, the inner class numbers. Option: `--limit N`. |
| `marathon notes walk ENTITY` | Prints the tree of entities below an entity, with the models, the graphs, the clips and the skeletons. Option: `--depth N`. |
| `marathon notes dxil MATERIAL` | Prints the pixel shader of a material as LLVM text. It needs `llvm-dis`. Options: `--vs`, `-o FILE.ll`. |

## The commands of esx that the documents use

esx is a separate program that the setting `esx` names. These are not `./port` commands, and
this repository does not check them.

| Command | What it does |
| --- | --- |
| `esx --data DATA build PROJECT [--update-lock]` | Builds a mod. `./port mod build NAME` runs it. |
| `esx --data DATA plugin check-weapons PLUGIN.esp` | The weapon checks of a built plugin |
| `esx --data DATA scene weapon PLUGIN.esp WEAPON` | Checks that every mesh, material and texture of a weapon resolves |
| `esx --data DATA render weapon PLUGIN.esp WEAPON --sheet -o FILE.png` | A picture of the weapon. It does not draw an effect material. |
| `esx item new weapon RECORD --standalone --all-parts -o FILE` | The values and the parts of a vanilla weapon |
| `esx record show Fallout4.esm RECORD` | Every field of a record |
| `esx behavior explain reload --like KEYWORD`, `esx hkx events FILE --event NAME`, `esx hkx show FILE --selector 'object(N)'` | The rules of a behavior graph |
| `esx probe status`, `start`, `call OP`, `stop --session ID`, `run PLAN`, `install --world FILE` | The game test ([game-test.md](../porting/game-test.md)) |

## The settings

| Setting | Variable | Used by |
| --- | --- | --- |
| `blender` | `BLENDER` | Every retarget step and every check with pictures |
| `esx` | `ESX_BIN` | `fnv make-rig --arm-meshes`, `destiny model`, `mod build`, the game test |
| `fo4_data` | `FO4_DATA` | `fnv make-rig`, `destiny make-rig`, `destiny model`, `mod build`, `destiny game session` |
| `proton` | `PROTON_DIR` | `destiny game session` |
| `destiny_game` | `D2X_GAME` | The extraction of Destiny 2, and `destiny states`, `dyes`, `reticle`, `third`, `pose`, `notes` |
| `marathon_game` | `MARATHON_GAME` | The extraction of Marathon |
| `nvcs_skeleton` | `NVCS_SKELETON` | `fnv make-rig` |

`FO4PORTS_DATA` moves the data folder. `PORT_RIG` names a different rig folder of `fnv/` for
a program that you start with `python3`. `FO4PORTS_TRACEBACK=1` shows the traceback of a file
error. `./port doctor` names every key of `data/config.toml` that is not a setting.

## What is not proved

* The lines of this document come from `./port list` and from the `--help` of each command
  on 2026-10-06. The author ran no converter, no build and no game test for it.
* Nobody ran `./port baseline update` for this document. `./port baseline check` ran and
  reported 602 files, 0 different.
* The esx commands come from the chats and from the documents of the areas.
