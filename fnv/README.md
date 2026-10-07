# New Vegas weapon animations for Fallout 4

These tools convert the first-person animations of a Fallout: New Vegas weapon mod to
Fallout 4 clips. One command does it, and it needs no conversion file:

```sh
./port fnv convert /path/to/extracted-mod
```

The input is the folder of the extracted mod, with the gun model (`.nif`) and the
first-person animations (`.kf`). The output folder gets one HKX clip for each first-person
clip of a Fallout 4 gun, `WPNIdleReady`, `WPNFireSingleReady`, `WPNReload` and so on, and no
other file.

The same input gives the same bytes. The command prints the animation that each clip comes
from, and the events of each reload.

| Option | Meaning |
| --- | --- |
| `-o OUT` | The output folder. Default: `data/fnv/out/NAME`. |
| `--template NAME` | `pistol10mm` or `smg`. The vanilla weapon that gives the weapon bones, and the motion of each clip that the mod does not have. Default: `pistol10mm` when the animations have the grip code `1hp`, else `smg`. |
| `--name NAME` | The name of the work folder and of the default output folder, in lower case. Default: the name of the model file. |
| `--work DIR` | The work folder. Default: `data/fnv/work/NAME`. |

Run every command from the repository root. Each program also runs without `./port`, so
`python3 fnv/tools/port.py /path/to/extracted-mod` is the same command. `./port fnv` lists
the commands of this area.

## What you need

`./port doctor` shows each of these and tells you how to make one that is missing.

* Python 3.11 or later with `numpy` (`requirements.txt` in the root)
* Blender 4.5, the setting `blender`. It comes from the variable `BLENDER`, then from
  `data/config.toml`, then from `blender` in the `PATH`. Blender runs without a window.
* The rig folder `data/fnv/rig`. It holds files from Fallout 4 and from the New Vegas
  compatibility skeleton (NVCS), so it is not in the repository. Make it once from your own
  files:

  ```sh
  ./port fnv make-rig --nvcs /path/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif
  ```

  The program reads the Fallout 4 skeleton and the clips of each template weapon from
  `Fallout4 - Animations.ba2`. The Data folder of Fallout 4 is the setting `fo4_data`, which
  comes from `FO4_DATA` and then from `data/config.toml`, or the option `--data`.

  `PORT_RIG` names a different rig folder for a program that you start with `python3`.
  `./port` looks for the files in `data/fnv/rig` before it starts a command.

## What the clips are for

* The hands hold the gun of the source mod. The clips are for that gun in Fallout 4 weapon
  space (+Y to the muzzle, +Z up, +X to the right), with its trigger at the trigger of the
  template weapon.
* The moving parts (slide, magazine, trigger) are on the weapon bones of the template, at its
  rest places.
* The work folder `data/fnv/work/NAME` has `out/fo4mesh/parts.json`, which gives each shape
  of the gun in the space of its weapon bone. A Fallout 4 model of the gun must have its
  shapes at these places.
* The clip names come from the template's vanilla first-person graph. Fallout 4 plays
  `WPNReloadEmpty` only with a behavior graph that has such a state.

## The New Vegas names

The tools know these animation names. The grip code at the start, for example `1hp` or
`2ha`, is not part of the name.

| Animation | Clip |
| --- | --- |
| `aim` | `WPNIdleReady` |
| `aimis` | `WPNIdleSighted` |
| `attackright`, `attackleft`, `attack3` | `WPNFireSingleReady` |
| `attackright_a` | `WPNFireSingleReadyA` |
| `attackrightis` | `WPNFireSingleSighted` |
| `equip`, `unequip` | `WPNEquip`, `WPNUnEquip` |
| `reload...` | `WPNReload`. With two reloads, the one with `partial` in its name is `WPNReload` and the other one is `WPNReloadEmpty`. |

A sneak copy, a jam, and a variant for the empty gun or the last shot get no clip. Every
other clip of a gun (walk, run, sprint, automatic fire, gun down) has the weapon motion of
the template's vanilla clip, with the hands of the mod on the gun.

## The conversion file

The command writes a small file, `conversion.toml`, into the work folder and reads it. A
conversion file of your own replaces a value that the tools assume. The program's help text
calls it a "configuration file".

```sh
./port fnv convert /path/to/ppk.toml
```

```toml
name = "PPK"                    # the name of the work folder
template = "pistol10mm"         # templates/pistol10mm.toml, or "smg"
```

`./port fnv convert CONFIG show` prints the complete data, so you can see what the tools
assume.

| Value | Default |
| --- | --- |
| `source` | The folder `source` beside the file. |
| `output` | `data/fnv/out/NAME`, with the name in lower case. |
| `model` | The model (`.nif`) of the source with the fewest shapes, then the shortest name. |
| `animations` | The folder `_1stperson` of the source with the most `.kf` files. |
| `work` | `data/fnv/work/NAME`, with the name in lower case. |
| `[weapon] trigger` | The center of the shape whose name has "trigger". |
| `[parts]` | Each node `##NAME` of the model that has a shape, by a word in its name (bar, bolt, slide, lever, clip, mag, shell, bullet, trigger, hammer). The template says which bone each kind of part gets. |
| `[fingers] min_bend` | 0.3 |
| `[fingers] skin_center` | `true` |
| `[collision] skip` | The cartridges in the magazine are not colliders for the fingers. |
| `[synth]` | The ready pose is the first frame of the aim clip, or of the reload. The sighted pose has the node `##SightingNode` on the view axis. See `tools/blender/synth.py`. |
| `[clips.NAME]` | Each animation of the source by its New Vegas name. See `tools/port_clips.py`. |
| Reload events | From the motion of the magazine, the bolt and the left hand. |

For example:

```toml
[clips.WPNReload]               # replace the clip that the tools assume
source = "2hareloads"
events = [[21, "SoundPlay.{sound}ReloadMagOut"], [53, "reloadComplete"], [86, "reloadEnd"]]

[clips.WPNSprint]
skip = true                     # no clip of the mod: the game uses the clip of the template
```

`tools/port_defaults.py` has the rules for each default.

## The steps

`./port fnv convert CONFIG STEP ...` runs only the steps that you give:

| Step | What it does |
| --- | --- |
| `bake` | Evaluates each `.kf` file on the New Vegas skeleton and writes the matrix of each node for each frame. |
| `parts` | Puts the gun meshes into Fallout 4 weapon space, each on its weapon bone. |
| `retarget` | Moves each pose to the Fallout 4 first-person skeleton (Blender). |
| `synth` | Makes the clips that use the weapon motion of the template weapon (Blender). |
| `hkx` | Writes the HKX clips, and reads each one again to compare it with the poses. |
| `install` | Copies the clips into the output folder. |

`./port fnv convert CONFIG plan` prints the source of each clip and the events of each
reload. `./port fnv inspect FILE` prints the nodes and the shapes of a model, or the tracks
and the text keys of an animation. `./port fnv list-archive ARCHIVE PATTERN` lists the files
of a game archive.

The `hkx` step writes the clips into `out/fo4/hkx` in the work folder. Only the `install`
step copies them to the output folder. The `retarget` step stops when
`out/fo4mesh/parts.json` is missing, so run `parts` before it.

## What the conversion does

* The tools solve the arms again for the Fallout 4 bone lengths. Each wrist is at the source
  wrist.
* Each finger joint is on the line of the source finger. A finger that is too near a gun
  part moves out of it, at most 1.15 units for each joint.
* With `skin_center`, that line is the center of the skin of the source finger, and the
  center of the skin of the Fallout 4 finger goes to it. The skin of a finger is not a tube
  about its bones. The thumb skin of the Fallout 4 hand is 0.4 units to the pad side of its
  bones, and the New Vegas thumb skin is 0.13 units to the nail side. With the bones in the
  same place, the Fallout 4 thumb is 0.5 units away from the place of the source thumb on
  the gun. `rig/finger_tips.json` has the two centers of each finger bone.
* With `min_bend`, each finger joint has at least a part of its bend in the Fallout 4
  reference pose, about the hinge of its bone. The Fallout 4 hand mesh is modelled with bent
  fingers, about 45 and 30 degrees, and in the vanilla clips of the two templates no finger
  joint bends to the back of the finger. Only the last thumb joint does, and it can keep 17
  degrees of such a bend. A New Vegas clip can have a straight finger or a joint that bends
  back, and the Fallout 4 mesh has lumps at such a joint. A finger that gets more bend is an
  arch, and its fingertip stays on its line.
* A weapon part follows its node in the source. A part node has its own place in the model,
  so the tools use the node's rest matrix.
* A `[synth]` clip takes the motion of the weapon bone from a vanilla clip of the template
  and applies it to a pose of the mod's gun. The hands stay on the gun.
* New Vegas moves the camera to the node `##SightingNode` when the player aims. Fallout 4 has
  the sights in the clip, so the sighted pose is the aim pose of the mod, moved until that
  node is on the view axis.
* A weapon bone can have a rest rotation, in `[rotations]` of the template, so a vanilla clip
  shows the part at its place.

## The folders

The source of this area is in `fnv/`:

| Folder | Content |
| --- | --- |
| `tools/` | The programs. `tools/blender/` has the programs that run in Blender. |
| `templates/` | One file for each template weapon: `smg.toml` (the vanilla submachine gun) and `pistol10mm.toml` (the vanilla 10mm pistol). |
| `rig/` | Only `finger_tips.json`, the measurements of the two hand meshes. Each tool reads it here. |
| `port.toml` | The commands of this area for `./port`, and what they need. |

Everything a tool makes goes to `data/fnv/`, which is not in git:

| Folder | Content |
| --- | --- |
| `data/fnv/rig/` | The rig folder: the Fallout 4 first-person skeleton, the vanilla clips of each template and the New Vegas skeleton (NVCS). These are files of the game and of the NVCS mod. `./port fnv make-rig` makes them. |
| `data/fnv/work/NAME/` | The work folder of a conversion: `conversion.toml` and `out/` (the bake files, `fo4mesh/parts.json`, the poses, the clips before the `install` step). |
| `data/fnv/out/NAME/` | The clips of a conversion. |
| `data/fnv/fixtures/NAME/` | The extracted mod of each weapon that the regression converts. |

No tool writes a file into `fnv/`.

## The regression

```sh
./port fnv regress
```

The command converts every folder in `data/fnv/fixtures/` again, into a scratch folder below
`data/fnv/work/_regress/`, and compares each clip with the clip in `data/fnv/out/NAME/`. It
prints one line for each fixture, and the exit code is 1 when a clip is different. Run it
after every change to a tool. A change must keep the bytes of every clip, or you must say
which clips are different and why. Then run `./port baseline check`. `baselines.sha256` has
the sha256 of every clip in `data/fnv/out/`, so the check shows a stored clip that a command
replaced. Run `./port baseline update` only for a change the user accepted.

To add a weapon, copy the extracted mod to `data/fnv/fixtures/NAME`, run
`./port fnv convert data/fnv/fixtures/NAME --name NAME`, and check the clips. They are then
the results that the regression compares with.

## This area in the monorepo

This area uses `portkit/` for the paths and the settings, and no other area. `destiny/port/`
uses this area as its Fallout 4 library. A change to one of the things in this table can
change the clips of the Destiny and Marathon weapons, so run `./port destiny regress` too.

| What | Where | What it gives |
| --- | --- | --- |
| The HKX reader and writer | `tools/anim_fo4.py` | Reads a Fallout 4 skeleton and a spline-compressed clip, and writes a clip (`load_fo4_skeleton`, `load_fo4_animation`, `write_fo4_animation`, the block compressor). |
| The clip functions | `tools/port_hkx.py` | The local tracks of a list of world poses, the writer of a clip with its events, and the check that reads the clip again (`local_tracks`, `world_from_local`, `compose`, `write_clip`, `check_clip`). |
| The archive reader | `tools/ba2.py` | Reads a file from a general Fallout 4 archive (`Ba2`). |
| The hand solver | `tools/blender/solver.py`, `tools/blender/common.py` | The arm solver, the finger rules, the collision step and the skeleton helpers (`Retargeter`, `Collider`, `solve_finger_path`, `bend_least`, `hinge_axes`, `relax_out`, `aim_x`, `THUMB_BACK`, `load_target`, `trs`). |
| The hand measurements | `rig/finger_tips.json` | The length, the radius and the skin center of each finger bone of the Fallout 4 hand. |
| The rig folder | `data/fnv/rig/` | The Fallout 4 first-person skeleton. With `./port fnv make-rig --arm-meshes` also the first-person arm meshes as glTF files, which the checks of `destiny/port/` read. That option needs the setting `esx`. |

Keep the name and the behavior of every public function in these modules.

A program that runs in Blender has `sys.dont_write_bytecode = True` before its first import
of a repository module. Blender does not read the variable `PYTHONDONTWRITEBYTECODE`, so
without that line it writes `__pycache__` folders into `tools/`.

## What is proved

Each statement has the command that proves it. The fixtures are the extracted mods of the
Walther PPK, with 9 `.kf` clips, and of the FAMAS F1, with one `.kf` reload.

* The two fixtures give 27 clips for the PPK and 26 clips for the FAMAS, and a new run gives
  the same bytes as the results in `data/fnv/out/`. The command is `./port fnv regress`.
* A rig folder that `./port fnv make-rig` makes from the game files gives the same clips.
  Make a second rig folder, and run the regression with it:

  ```sh
  python3 fnv/tools/make_rig.py --nvcs /path/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif --out data/fnv/work/_rig
  PORT_RIG=$PWD/data/fnv/work/_rig python3 fnv/tools/regress.py
  ```

  This also proves that the tools read `finger_tips.json` from `fnv/rig/`, because the second
  rig folder does not have that file.
* The commands and the checks of `port.toml` have no fault, and every program compiles. The
  command is `./port selftest`.

## What is not proved

* No command of this repository proves that the clips are correct in the game. The clips of
  the two weapons were tested in the game on 2026-10-05, each in a mod with the gun of the
  source mod. Those mod projects are `mods/PPK` and `mods/FAMAS`, and `docs/porting/fnv.md`
  describes them. Their models and their records are not from these tools. On the author's
  computer, the results in `data/fnv/out/` are the same bytes as the clips of those mods.
* The regression compares bytes. It does not look at the hands. A change that moves a finger
  needs a person or an agent who looks at pictures of the hands on the gun.
* Every run used Blender 4.5.13 and `numpy` 2.3 on Linux. No test shows that a different
  version of Blender or `numpy` gives the same bytes.
* With esx 0.1.0, commit a996de8, `./port fnv make-rig --arm-meshes` gives the same two glTF
  files as the files in `data/fnv/rig/`. No test uses a different version of esx.

## Limits

* Two weapons prove the tools. Both are magazine guns.
* There are two templates, the submachine gun and the 10mm pistol. A revolver or a
  bolt-action gun needs a new template file and the clips of that vanilla weapon in the rig
  folder.
* The tools make only the clips. They do not make the model, the textures, the sounds, the
  weapon record or the behavior graph.
* A source set can have clips that the vanilla graph has no place for, such as a jam, an
  empty-gun pose or a last-shot clip. The tools do not convert them.
* `kfbake.py` reads transform tracks with linear, quadratic and constant keys and Euler
  rotations. It does not read B-spline data.
* `fnvnif.py` reads version 20.2.0.7 of Fallout 3 and New Vegas, with NiTriStrips and
  NiTriShape geometry. A gun with skinned parts is not supported.
* The two hands have different bones. The thumb of the Fallout 4 hand starts 1.6 units away
  from the start of the New Vegas thumb, so the two thumbs cannot agree everywhere. The tools
  put the fingertip at its place first.
* The defaults are rules for the names and the motion of the mods that these two weapons
  come from. Read the output of `./port fnv convert CONFIG show` for a new mod.
* The work tree of this area has no program that shows the result. The check programs of
  the first work made pictures of the source above the result, and contact counts. They are
  in git at the tag `before-animation-only`, with the paths of the old layout:
  `tools/validate_clip.sh`, `tools/blender/render_fo4.py`, `render_source.py` and
  `hand_contact.py`. Nobody adapted them or ran them in this repository. Look at pictures of
  the hands before a game test, as step 4 of `docs/porting/fnv.md` says. `destiny/port/` has
  check programs with pictures for its own weapons.

## Origin of one file

`tools/anim_fo4.py` reads and writes the spline-compressed clips of Fallout 4. It is based on
the spline decompression of Dagobaking's skyrim-fo4-animation-conversion, which is based on
PredatorCZ/HavokLib (GPL-3.0).
