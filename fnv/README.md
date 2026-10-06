# New Vegas weapon animations for Fallout 4

These tools convert the first-person animations of a Fallout: New Vegas weapon mod to
Fallout 4 clips. One command does it, with no configuration file:

```sh
python3 tools/port.py /path/to/extracted-mod -o /path/to/out
```

The input is the folder of the extracted mod: the gun model (`.nif`) and the first-person
animations (`.kf`). The output folder has one HKX clip for each first-person clip of a
Fallout 4 gun (`WPNIdleReady`, `WPNFireSingleReady`, `WPNReload` and so on), and no other
file.

The same input gives the same bytes. The command prints the animation that each clip comes
from, and the events of each reload.

| Option | Meaning |
| --- | --- |
| `-o OUT` | The output folder. Default: `NAME-fo4` in the current folder. |
| `--template NAME` | `pistol10mm` or `smg`: the vanilla weapon that gives the weapon bones, and the motion of each clip that the mod does not have. Default: `pistol10mm` when the animations have the grip code `1hp`, else `smg`. |
| `--name NAME` | The name of the work folder and of the default output folder. Default: the name of the model file. |

## What you need

* Python 3.11 or later with `numpy`
* Blender 4.5: `BLENDER` names the program (default `blender` in the `PATH`). It runs with no
  window.
* The rig folder. It has files of Fallout 4 and of the New Vegas compatibility skeleton
  (NVCS), so it is not in the repository. Make it one time from your own files:

  ```sh
  python3 tools/make_rig.py --data "/path/Fallout 4/Data" \
      --nvcs /path/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif
  ```

  The program reads the Fallout 4 skeleton and the clips of each template weapon from
  `Fallout4 - Animations.ba2`.

## What the clips are for

* The hands hold the gun of the source mod. The clips are for that gun in Fallout 4 weapon
  space (+Y to the muzzle, +Z up, +X to the right), with its trigger at the trigger of the
  template weapon.
* The moving parts (slide, magazine, trigger) are on the weapon bones of the template, at its
  rest places.
* The work folder (`/tmp/NAME-port`) has `out/fo4mesh/parts.json`: each shape of the gun in
  the space of its weapon bone. A Fallout 4 model of the gun must have its shapes at these
  places.
* The clip names are those of the vanilla first-person graph of the template. Fallout 4
  plays `WPNReloadEmpty` only with a behavior graph that has such a state.

## The New Vegas names

The tools know these animation names (the grip code at the start, for example `1hp` or
`2ha`, is not a part of the name):

| Animation | Clip |
| --- | --- |
| `aim` | `WPNIdleReady` |
| `aimis` | `WPNIdleSighted` |
| `attackright`, `attackleft`, `attack3` | `WPNFireSingleReady` |
| `attackright_a` | `WPNFireSingleReadyA` |
| `attackrightis` | `WPNFireSingleSighted` |
| `equip`, `unequip` | `WPNEquip`, `WPNUnEquip` |
| `reload...` | `WPNReload`. With two reloads, the one with `partial` in its name is `WPNReload` and the other one is `WPNReloadEmpty`. |

A sneak copy, a jam, and a variant for the empty gun or the last shot get no clip. Each
other clip of a gun (walk, run, sprint, automatic fire, gun down) has the weapon motion of
the vanilla clip of the template, with the hands of the mod on the gun.

## The configuration file

The command writes a small file into the work folder and reads it. A file of your own
replaces a value that the tools assume:

```sh
python3 tools/port.py /path/to/port.toml
```

```toml
name = "PPK"                    # the name of the work folder
template = "pistol10mm"         # templates/pistol10mm.toml, or "smg"
```

`port.py CONFIG show` prints the complete data, so you can see what the tools assume.

| Value | Default |
| --- | --- |
| `source` | The folder `source` beside the file. |
| `output` | The folder `NAME-fo4` beside the file. |
| `model` | The model (`.nif`) of the source with the fewest shapes, then the shortest name. |
| `animations` | The folder `_1stperson` of the source with the most `.kf` files. |
| `work` | `/tmp/NAME-port`. |
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

`tools/port_defaults.py` has the rules of each default.

## The steps

`port.py CONFIG STEP ...` runs only the steps that you give:

| Step | What it does |
| --- | --- |
| `bake` | Evaluates each `.kf` file on the New Vegas skeleton and writes the matrix of each node for each frame. |
| `parts` | Puts the gun meshes into Fallout 4 weapon space, each on its weapon bone. |
| `retarget` | Moves each pose to the Fallout 4 first-person skeleton (Blender). |
| `synth` | Makes the clips that use the weapon motion of the template weapon (Blender). |
| `hkx` | Writes the HKX clips, and reads each one again to compare it with the poses. |
| `install` | Copies the clips into the output folder. |

`port.py CONFIG plan` prints the source of each clip and the events of each reload.
`fnvnif.py FILE` prints the nodes and the shapes of a model, or the tracks and the text keys
of an animation. `ba2.py ARCHIVE PATTERN` lists the files of a game archive.

## What the conversion does

* The arms are solved again for the Fallout 4 bone lengths. Each wrist is at the source wrist.
* Each finger joint is on the line of the source finger. A finger that is too near a gun
  part moves out of it, 1.15 units for each joint at most.
* With `skin_center`, that line is the center of the skin of the source finger, and the
  center of the skin of the Fallout 4 finger goes to it. The skin of a finger is not a tube
  about its bones: the thumb skin of the Fallout 4 hand is 0.4 units to the pad side of its
  bones, and the New Vegas thumb skin is 0.13 units to the nail side. With the bones at one
  place, the Fallout 4 thumb is 0.5 units away from the place of the source thumb on the gun.
  `rig/finger_tips.json` has the two centers of each finger bone.
* With `min_bend`, each finger joint has at least a part of its bend in the Fallout 4
  reference pose, about the hinge of its bone. The Fallout 4 hand mesh is modelled with bent
  fingers (about 45 and 30 degrees), and in the vanilla clips of the two templates no finger
  joint bends to the back of the finger. Only the last thumb joint does, and it can keep 17
  degrees of such a bend. A New Vegas clip can have a straight finger or a joint that bends
  back, and the Fallout 4 mesh has lumps at such a joint. A finger that gets more bend is an
  arch, and its fingertip stays on its line.
* A weapon part follows its node of the source. A part node has its own place in the model,
  so the tools use the rest matrix of the node.
* A clip of `[synth]` takes the motion of the weapon bone from a vanilla clip of the template
  and applies it to a pose of the gun of the mod. The hands stay on the gun.
* New Vegas moves the camera to the node `##SightingNode` when the player aims. Fallout 4 has
  the sights in the clip, so the sighted pose is the aim pose of the mod, moved until that
  node is on the view axis.
* A weapon bone can have a rest rotation (`[rotations]` of the template), so a vanilla clip
  shows the part at its place.

## The folders

| Folder | Content |
| --- | --- |
| `tools/` | The programs. `tools/blender/` has the programs that run in Blender. |
| `templates/` | One file for each template weapon: `smg.toml` (the vanilla submachine gun) and `pistol10mm.toml` (the vanilla 10mm pistol). |
| `rig/` | The Fallout 4 first-person skeleton, the vanilla clips of each template and the New Vegas skeleton (NVCS). These are files of the game and of the NVCS mod, so only `finger_tips.json` (measurements of the two hand meshes) is in the repository. `tools/make_rig.py` makes the other files. |

## What is proved

* Walther PPK (9 `.kf` clips): 27 clips. FAMAS F1 (one `.kf` reload): 26 clips.
* The clips of the two weapons were tested in the game, each in a mod with the gun of the
  source mod. The model and the records of those mods are not from these tools.
* A second complete run gives the same bytes for each clip. A rig folder that
  `tools/make_rig.py` makes from the game files gives the same clips.

## Limits

* Two weapons prove the tools. Each is a magazine gun.
* There are two templates, the submachine gun and the 10mm pistol. A revolver or a
  bolt-action gun needs a new template file and the clips of that vanilla weapon in `rig/`.
* The tools make only the clips. They do not make the model, the textures, the sounds, the
  weapon record or the behavior graph.
* A source set can have clips that the vanilla graph has no place for (a jam, an empty-gun
  pose, a last-shot clip). The tools do not convert them.
* `kfbake.py` reads transform tracks with linear, quadratic and constant keys and Euler
  rotations. It does not read B-spline data.
* `fnvnif.py` reads version 20.2.0.7 of Fallout 3 and New Vegas, with NiTriStrips and
  NiTriShape geometry. A gun with skinned parts is not supported.
* The two hands have different bones. The thumb of the Fallout 4 hand starts 1.6 units away
  from the start of the New Vegas thumb, so the two thumbs cannot agree at each place. The
  tools put the fingertip at its place first.
* The defaults are rules for the names and the motion of the mods that these two weapons
  come from. Read the output of `port.py CONFIG show` for a new mod.
* The repository has no program that shows the result. Look at the clips in the game or in
  an animation tool.

## Origin of one file

`tools/anim_fo4.py` reads and writes the spline-compressed clips of Fallout 4. It is based on
the spline decompression of Dagobaking's skyrim-fo4-animation-conversion, which is based on
PredatorCZ/HavokLib (GPL-3.0).
