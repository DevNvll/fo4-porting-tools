# d2x (destiny/extract)

Tools that unpack Destiny 2 (Tiger engine) packages and export a weapon as glTF: mesh,
textures, skeleton, weapon clips, and the first-person rig with its clips.

Before the monorepo, this tool was the project `destiny-weapons`. The glTF files still have
`"generator": "d2x (destiny-weapons)"`.

The tools were made for this game build and tested on it:

| Item | Value |
| --- | --- |
| Game directory | The setting `destiny_game`. The directory has `packages/` and `bin/x64/`. d2x reads it and does not change it. |
| Build | `86657.20.08.23.1800.d2_rc` (23 August 2020, Season of Arrivals) |
| Package format | Destiny 2 before Beyond Light, `tiger-pkg` version code `d2_sk` |
| Oodle | `bin/x64/oo2core_3_win64.dll` |

## This area in the monorepo

- `destiny/extract/` has only source. `setup.sh` and d2x write every generated or third-party
  file below `data/destiny/extract/`. See "Folders".
- `destiny/port/tools/` imports the d2x modules to read more game data for a port.
  `d2states.py`, `d2dyes.py`, `d2reticle.py`, `d2pose.py` and `d2third.py` all have
  `from d2x import pkg, anim, entity, graph, ...`.
- `marathon/extract/` (`m2x`) imports the d2x modules for the package access, the clip
  decoder and the glTF writer: `pkg.PackageManager`, `anim.Rig`, `export.build_glb`, `graph`,
  `names`, `model` and `texture`. Its Rust program `tag64` builds against d2x's clone of
  tiger-pkg.
- So a change here must keep the names and the behavior of the public functions of the d2x
  modules.
- `destiny/port/` (`d2fo4`) converts the results, which are the first-person `.glb` files and
  `manifest.json`. For a port, extract the weapon to `data/destiny/port/extract/<weapon>/`
  with `--out`.
- A program that imports d2x runs with `data/destiny/extract/venv/bin/python` and with
  `destiny/extract` in `PYTHONPATH`. In a `port.toml` this is `run = ["python:d2x", ...]` and
  `env = { PYTHONPATH = "destiny/extract" }`.

## Quick start

Run the commands from the repository root.

```bash
./port destiny setup                           # one time: clones, patch, cargo build, Python environment
./port destiny find "last word"                # search item names
./port destiny extract "The Last Word" --arms "Ancient Apocalypse Grips"
./port destiny check-glb data/destiny/extract/out/the_last_word/the_last_word_weapon.glb --clips 3
./port destiny check-glb data/destiny/extract/out/the_last_word/the_last_word_first_person_set.glb --view fp --sheet
./port destiny video data/destiny/extract/out/the_last_word/the_last_word_first_person_set.glb \
    --clip reload --clip "iron_sight_idle=ADS" --clip sprint_loop@4 \
    --out data/destiny/extract/out/the_last_word/video/demo.mp4
```

For a port, give the folder of `destiny/port`:

```bash
./port destiny extract "The Chaperone" --arms "Ancient Apocalypse Grips" --out data/destiny/port/extract
```

`destiny/extract/setup.sh` and `destiny/extract/d2x.sh COMMAND` do the same without
`./port`. In d2x, `check-glb` has the name `check`. Both run from any working folder, and a
relative path in an argument is relative to that folder.

The local values are settings. A setting comes from its environment variable, then from
`data/config.toml`, then from its default in `portkit/paths.py`. `./port doctor` shows each
one.

| Setting or variable | Function |
| --- | --- |
| `destiny_game` (`D2X_GAME`) | The game directory. `setup.sh` makes the Oodle link from it. d2x reads `packages/` below it. |
| `blender` (`BLENDER`) | Blender 4.5 for `check-glb` and `video`. Default: `blender` on `PATH`. The old name `BLENDER_BIN` has no function now. |
| `D2X_PACKAGES`, `--packages` | The `packages` directory, if it is not `packages/` of `destiny_game`. |
| `D2X_VERSION`, `--version` | The `tiger-pkg` version code. Default: `d2_sk`. |
| `FO4PORTS_DATA` | Moves the data folder (`data/`). `setup.sh` and d2x then use `destiny/extract/` below it. |

`setup.sh` needs `git`, `cargo` and `python3`, which must be 3.11 or later for `portkit`. It
makes the Python environment with `uv` and Python 3.13, or with `python3 -m venv` if `uv` is
not there. Without `uv`, that `python3` must be 3.12 or later, because the fixed versions of
`requirements.txt` need it. The setup stops with a message if it is older. A `.mp4` video
needs `ffmpeg`.

## Folders

They are all below `data/destiny/extract/`, which is not in git. `./port doctor` shows which
ones are there.

| Folder | Content | Made by |
| --- | --- | --- |
| `vendor/tiger-pkg`, `vendor/tiger-animation-parser` | The clones at fixed commits. The parser has the `d2_sk` patch. | `setup.sh` |
| `target/` | The cargo build of `tigerpkg-ffi`: `release/libtigerpkg_ffi.so` and `release/tigerx`. | `setup.sh` |
| `venv/` | The Python environment. `requirements.txt` gives the exact versions. | `setup.sh` |
| `runtime/` | `liblinoodle3.so`, a copy from the clone of tiger-pkg, and the link `oo2core_3_win64.dll` to the DLL of the game. | `setup.sh` |
| `out/` | The default output of `extract` and of `tag`. | d2x |
| `out/cache/` | `player_body_<version>.json` is the player body entity, found one time, which takes about 2 minutes. `refs_<version>.npz` is the reference index of `d2x/refs.py`, if a program makes it. | d2x |
| `handoff/the_last_word_v1/` | A frozen copy of the first extraction of The Last Word, with `HANDOFF.md`, the facts for the first port. It is older than `out/the_last_word/` and has no animation set file, no `states` and no camera node. `destiny/port` still reads it for The Last Word. | the first d2x session |
| `work/` | Scratch folders. Safe to delete. | you |

`setup.sh` is safe to run again, because it skips every step that is complete. It does the
steps that do not need the game first. If the setting `destiny_game` has no value, it stops
at the last step, the Oodle link, with exit code 1 and tells you what to do.

One thing is not below `data/`. `tiger-pkg` keeps an index of the packages in the user's
cache folder, in the folder `tiger-pkg` in `XDG_CACHE_HOME`. It is about 50 MB for this game,
and d2x does not control it. cargo and `uv` also use their own caches.

`tigerpkg-ffi/Cargo.toml` names `tiger-pkg` by its git commit. `setup.sh` gives cargo the
clone with `--config patch...path=...`. So cargo does not fetch `tiger-pkg`, the build works
for any data folder, and `--locked` keeps `Cargo.lock` as it is. The commit is in `setup.sh`
and in `Cargo.toml`, and the two must be the same. `setup.sh` checks this.

## Commands

| Command | Function |
| --- | --- |
| `./port destiny setup` | Prepares the folders above. |
| `./port destiny find TEXT` | Lists items whose name contains TEXT, with item hash and pattern entity. |
| `./port destiny extract ITEM...` | Exports weapons. ITEM is a name or an item hash. |
| `./port destiny check-glb FILE.glb...` | Imports the file in Blender, does checks, and renders previews. |
| `./port destiny video FILE.glb --clip NAME[=LABEL][@N]... --out FILE` | Renders clips from the first-person camera. `.mp4` gives one video, `.png` gives a frame sheet. `@N` plays a clip N times. |
| `./port destiny tag HASH...` | Writes raw tag data (for example `80BC8633`) to `data/destiny/extract/out/raw`. |
| `data/destiny/extract/target/release/tigerx` | Lists or dumps package entries (Rust, no Python). |

`./port destiny COMMAND --help` shows the options. `destiny/extract/port.toml` has the
commands and what each one needs. Each d2x subcommand has its own command, because they need
different things. `find`, `extract` and `tag` read the game, and `check-glb` and `video` use
Blender only.

Options of `extract`:

- `--arms ARMOR` adds an armor item to the first-person rig. Use it again for more items.
- `--feminine` uses the feminine body and armor meshes.
- `--transparent` also exports decal and transparent parts.
- `--all` exports all items that match the name.
- `--out DIR` sets the output directory. The default is `data/destiny/extract/out/`.

Options of `check-glb`: `--view side|right|front|back|fp`, `--clips N`, `--clip NAME`,
`--frames N`, `--hide TEXT`, `--sheet` (one image with the middle frame of each clip),
`--out DIR`.

`tigerx` needs the folders on its command line, and an output folder for `get` and `dump`:

```bash
data/destiny/extract/target/release/tigerx --packages GAME/packages --runtime data/destiny/extract/runtime \
    get --output data/destiny/extract/out/raw 80BC8633
```

## Output

The output is in `data/destiny/extract/out/<weapon>/`, or in `DIR/<weapon>/` with
`--out DIR`.

| File | Content |
| --- | --- |
| `<weapon>_weapon.glb` | Weapon mesh, weapon skeleton, materials, weapon clips. |
| `<weapon>_first_person_set.glb` | The animation set of this weapon. The same rig, with only the clips that the game uses for this weapon, named by game state (`idle`, `iron_sight_idle`, `reload`, `ready`, `put_away`, `sprint_enter`, `sprint_loop`, `sprint_exit`, `fire`, ...). It also has the first-person camera (`fp_view`) and the aim eye point (`ads_eye`). |
| `<weapon>_first_person.glb` | First-person rig: player body bones and weapon bones, weapon mesh, hands, optional armor, all first-person clips of the weapon type (names `fp_<order>_<tag>`). |
| `<weapon>_first_person_N.glb` | More rigs, if the weapon links to more than one. |
| `textures/` | Albedo, normal, and gstack plates as PNG. |
| `raw/` | Unpacked tag data (skeleton, rig, clips). The vendor parser can read these files directly. |
| `manifest.json` | Hashes, tags, bone names, and one record for each clip. |
| `preview/` | Blender renders and reports from `check-glb`. |

The `.glb` files have +Y up, +Z forward, meters and 30 frames per second. The game has +Z
up and +X forward. Blender shows the weapon along -Y after import.

Every clip has keys for all bones, with one key for a bone that does not move. So a clip
shows the same pose in Blender, whichever clip was shown before it.

Clip names in the full file are `<prefix>_<order in set>_<clip tag>`. The animation set
file (`_set.glb`) has the names of the game states. For each rig, `manifest.json` has the list `states` with the state
name, the name hashes and the clip of each choice. Each clip record in `manifest.json` has
frames, seconds, package, `moving_weapon_bones` and `additive`.

The first-person camera is the bone `b_utility`. Its position is the eye point and its +Z
axis is the view direction. The animation set file has a camera object on that bone. In
`iron_sight_idle` the weapon sight is on the view axis. The node `ads_eye`, a child of
`b_handle`, is that eye point in weapon space.

| You want | Game state | Notes |
| --- | --- | --- |
| Aim down sights | `iron_sight_idle`, `iron_sight_fire` | The aim pose is in the clip. The game blends between `idle` and `iron_sight_idle`, and there is no clip for the transition. |
| Reload | `reload` | One clip for `reload_empty`, `reload_full`, and `reload_special`. |
| Sprint | `sprint_enter`, `sprint_loop`, `sprint_exit` | |
| Equip | `ready` | |
| Unequip | `put_away` | Very short (the game blends it). |

Clips with `_add` in the name are additive and hold offsets only. The export applies them to
the first frame of the first full-pose clip, which is `shown_on` in the manifest, so that
they show a correct pose.

The results have no time stamp and no path of the computer. The same game build, the same
code and the same Python packages give the same bytes. See "Checks".

## How it works

1. `tigerpkg-ffi/` opens the packages. It is a small Rust library and CLI on
   [tiger-pkg](https://github.com/v4nguard/tiger-pkg), and it decrypts and decompresses
   entries. On Linux, `liblinoodle3.so` from tiger-pkg loads the game's Windows Oodle DLL
   from the working directory, so the library goes to `runtime/` for the moment that it opens
   the packages. Python loads the library with `ctypes` in `d2x/pkg.py`, which also has the
   folders of d2x.
2. `d2x/investment.py` goes from an item to its entities. It finds every table by class hash:
   - item name: display map `80805CDB` -> display definition `80805CE1` -> string container
     list `80805F98`
   - item definition: item map `80807BE4` -> `80807BEA`; translation block at `+0x88`
     (art arrangement index, dyes, weapon pattern index at `+0x58`)
   - weapon pattern: table `80805B78` (0x30 rows) -> global tag id -> list `80809780` ->
     pattern entity (skeleton, runtime rig, weapon clips, links to the first-person rig)
   - art arrangement: table `80805DF5` -> entity assignment hashes -> map `808056EA` ->
     wrapper `8080744A` -> art entities (render meshes)
3. `d2x/entity.py` reads the entities. An entity is `80809C0F` and a resource is `80809C36`.
   The resource kinds are skeleton `80808545/80808546`, model `808072B8/808072BD`, runtime
   rig `80808F96/80808F8F`, and animation `80803466/8080344B` -> animation set `808036F6` ->
   clips `80808F49`.
4. `d2x/model.py` reads the meshes. A model is `808073A5`. The vertex layout comes from the
   input signature of the material's vertex shader. Weapons use rigid skinning, with the bone
   index in the position W value. By default the export has only render stage 0, which is
   opaque, and the highest level of detail.
5. `d2x/texture.py` reads the textures: plate set `808072D2` -> plates `80809EBB` -> textures
   (BC1, BC7). The gstack channels are R occlusion, G smoothness, B alpha test and emission,
   A metalness (0 to 32) and dye mask.
6. `d2x/anim.py` reads the clips.
   [tiger-animation-parser](https://github.com/SolUnshadowed/tiger-animation-parser) decodes
   them (codecs 0 to 3) and solves the runtime rig.
   `patches/tiger-animation-parser-d2_sk.patch` adds the skeleton and rig layouts of this
   game version.
7. `d2x/graph.py` reads the animation graph. The animation resource has a graph, `80803465`,
   and a weapon tag tree, `80808EE1`. The graph maps each state name hash to a decision tree
   over player conditions and weapon tags, for example `pistol` > `revolver` >
   `the_last_word`. The tree leaf gives an entry of the animation set, which gives the clip.
   The names of the states and tags were found with a word list against the FNV-1 hashes
   (`STATE_WORDS`, `TAG_WORDS`). A state with an unknown name is `state_<hash>`.
8. `d2x/export.py` builds the first-person rig. The weapon pattern entity links to an entity
   whose skeleton has the 72 player bones plus the weapon bones, with the parent `b_r_grip`.
   The export moves the weapon mesh to these bones. The hands come from the player body
   entity. Armor from `--arms` uses the same body bones.
9. `blender/check_glb.py` and `blender/render_clips.py` do the Blender check. They import the
   file, check it (one armature, weights, vertex groups, finite keys, keys for all bones) and
   render it.

The struct layouts for this game version have two sources.
[Charm](https://github.com/MontagueM/Charm) gave the entity, model, material, texture and
string structs. Analysis of the game data gave the investment tables, texture plates, runtime
rig and animation sets.

## Results on this build

- The Last Word, item 1364093401, was exported and checked in Blender 4.5.13. The weapon has
  8 bones (`b_handle`, `b_hammer`, `b_release_1`, `b_release_button`, `b_trigger`,
  `b_release_2`, `b_chamber`, `b_ammo`) and 3 clips. The first-person rig has 80 bones and
  119 clips, 44 of them additive. The animation set has 71 named clips of 59 game states, and
  24 of the 59 state names are recovered. `ready`, `fire`, and `iron_sight_fire` are The Last
  Word's own clips, with the spin on equip and the fan fire.
  `data/destiny/extract/out/the_last_word/video/tlw_animation_set_v1.mp4` and `.png` show the
  main states.
- Hawkmoon is not in this build. There is no item and no string, and item hash 3856705927 is
  not in the item table. Hawkmoon came with Season of the Hunt (December 2020, Beyond Light),
  which is a later build.
- Also tested before the monorepo: Ace of Spades, SUROS Regime, Whisper of the Worm.
- Extracted for the ports, into `data/destiny/port/extract/`: The Chaperone (first-person rig
  with 77 bones and 101 clips), The Huckleberry (76 bones, 116 clips), Khvostov 7G-02 (3
  first-person rigs with 76, 76 and 75 bones) and Hammerhead (87 bones, 96 clips).

## Checks

Each statement here has the command that proves it.

- `./port doctor` checks the setup. It shows the settings and every file of "Folders" as `ok`
  or `MISSING`, with the command that makes it. `./port selftest` checks that every Python
  file compiles and that `port.toml` is correct. Neither needs a game file.
- The extraction gives the same bytes again. Extract into a scratch folder and compare with
  an earlier result. A file that only the earlier folder has is not a difference. Those are
  `preview/`, `video/` and the files of the port tools: `states.json`, `dyes.json`,
  `sight.json`, `third_person/` and `posed/`.

  ```bash
  ./port destiny extract "The Chaperone" --arms "Ancient Apocalypse Grips" --out data/destiny/extract/work/verify
  cd data/destiny
  for f in $(cd extract/work/verify/the_chaperone && find . -type f); do
      cmp -s "port/extract/the_chaperone/$f" "extract/work/verify/the_chaperone/$f" || echo "DIFFERENT $f"
  done
  ```

  In the monorepo layout, with a new Python environment and a new cargo build, no file is
  different. That is 154 files for The Last Word against
  `data/destiny/extract/out/the_last_word/`, and 141 for The Chaperone, 151 for The
  Huckleberry, 222 for Khvostov 7G-02 and 128 for Hammerhead against
  `data/destiny/port/extract/`. The files are `manifest.json`, the `.glb` files,
  `textures/*.png` and `raw/*.bin`.
- The setup works from nothing. With `FO4PORTS_DATA` set to an empty folder and `D2X_GAME`
  set, `destiny/extract/setup.sh` clones the two projects, applies the patch, builds, and
  makes the environment and the Oodle link. Then
  `d2x.sh extract "The Huckleberry" --arms "Ancient Apocalypse Grips"` gives the same 151
  files. With no cache that takes 2 minutes 10 seconds, and the search for the player body
  entity is the larger part.
- A file is correct for Blender. `./port destiny check-glb FILE.glb` prints `NO PROBLEMS`, or
  the list of problems with exit code 1, and writes `<file>_report.json`. It reports an
  action that has bones without keys.
- A clip is the clip that you think it is.
  `./port destiny video FILE_set.glb --clip NAME --out sheet.png` gives a frame sheet from
  the first-person camera. Look at it. In `iron_sight_idle` the sight is in the middle of
  each frame.

Do the comparison again if you change a d2x module, a clone commit or `requirements.txt`,
which has the versions of numpy, pillow and texture2ddecoder. `destiny/port` converts these
files, and its own regression, `./port destiny regress`, starts from them.

## Limits

- 35 of the 59 states of the hand cannon graph have no recovered name and are
  `state_<hash>`. Add a name to `STATE_WORDS` in `d2x/graph.py` when you find one.
- The animation set file does not have every main state for every weapon. That of The
  Chaperone, for example, has no state `ready`, `fire` or `reload`, as `states` of its
  `manifest.json` shows. For a port, `./port destiny states MANIFEST.json`
  (`destiny/port/tools/d2states.py`) reads the graph again.
- Some weapon bones have no recovered name and are `bone_<hash>`. Add a word to
  `WEAPON_BONE_WORDS` in `d2x/names.py` when you find one. A new name changes the bone names
  in the files of that weapon.
- Dyes are not applied. Weapons that get their colors from dyes, such as Ace of Spades, look
  gray. The Last Word has its colors in the albedo texture. `destiny/port/tools/d2dyes.py`
  reads the dyes for a port.
- The glTF materials approximate the game shader. The export uses the green channel of the
  normal map as stored.
- First-person clips move the arms only. The other body bones do not have useful poses.
- The hands have no color texture.
- Other game versions need other class hashes and offsets. `tiger-pkg` reads the packages of
  all versions, and the animation parser has layouts for `d1_roi`, `d2_eof`, and `marathon`.
- Linux only. The Oodle shim and the link are for Linux.

## What is not proved

- The rule for the weapon tags is content group, then the base type of its class, then the
  class, then `rifle`. It is proved on The Last Word only, by pictures of its clips. For the
  other weapons the set file is made with the same rule, and `destiny/port` checks the clips
  that it uses.
- The labels of the player conditions, `alt` and `sprint`, are not game names. They come from
  the clips that each value selects. The first choice of a state has the plain state name.
- The test that finds an additive clip, `Rig.is_additive` in `d2x/anim.py`, uses limits from
  the clips of The Last Word. No game flag for "additive" is known.
- The setup was not run on a computer without the cargo registry, a compiler cache and the
  `uv` cache. The times above are with these caches.
- The setup without `uv`, with `python3 -m venv` and `pip`, was not run in this layout.
- Nobody tested for the same bytes on a different computer, a different Python 3.13 patch
  version or a different platform. The comparison above is on one computer.
- `--all` of `extract` and `dump` of `tigerx` were not run in this layout. `--feminine` and
  `--transparent` ran with no error, but there is no earlier result to compare with.
