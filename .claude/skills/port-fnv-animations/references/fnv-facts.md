# Facts about the New Vegas tool

From [fnv/README.md](../../../../fnv/README.md) and from the notes of the chat that made the
tool. Units: Fallout 4 game units. Each clip has 30 frames for each second.

## The New Vegas names

The grip code at the start of a name (`1hp`, `2ha`, `2hr`, `2hh`, `2hl`, `1hm`, `2hm`, `1md`,
`1gt`, `1lm`, `h2h`) is not a part of the name.

| Animation | Clip |
| --- | --- |
| `aim` | `WPNIdleReady` |
| `aimis` | `WPNIdleSighted` |
| `attackright`, `attackleft`, `attack3` | `WPNFireSingleReady` |
| `attackright_a` | `WPNFireSingleReadyA` |
| `attackrightis` | `WPNFireSingleSighted` |
| `equip`, `unequip` | `WPNEquip`, `WPNUnEquip` |
| `reload...` | `WPNReload`. With two reloads, the one with `partial` in its name is `WPNReload` and the other one is `WPNReloadEmpty`. |

* A sneak copy, a jam, and a name with `empty` or `lastshot` get no clip.
* The variants `WPNIdleReadyA` to `D`, `WPNFireSingleReadyA`, `B` and `WPNEquipFast` take the
  clip that they are a variant of.
* A source clip with one pose becomes 30 frames of that pose.
* Each other clip of a gun (walk, run, sprint, jump, automatic fire, gun down) has the
  weapon motion of the vanilla clip of the template, with the hands of the mod on the gun.
* The standard set has 26 clips. The PPK has 27 (with `WPNReloadEmpty`), the FAMAS 26.
* Not connected, because the vanilla graph has no place: empty-gun poses, a last shot, a jam,
  draw variants, an inspect clip, an ammunition check, dry fire.

## The conversion file

`./port fnv convert CONFIG show` prints each value. A conversion file of your own replaces a
value (the help text of the program has the words "configuration file" for it).

| Value | Default |
| --- | --- |
| `name`, `template` | The name of the model file; `pistol10mm` for the grip code `1hp`, else `smg` |
| `source` | The folder `source` beside the file |
| `output` | `data/fnv/out/NAME` |
| `work` | `data/fnv/work/NAME` |
| `model` | The model of the source with the fewest shapes, then the shortest name |
| `animations` | The folder `_1stperson` of the source with the most `.kf` files |
| `[weapon] trigger` | The center of the shape whose name has "trigger" |
| `[parts]` | Each node `##NAME` of the model that has a shape, by a word in its name: bar, bolt, slide, lever (the bolt); clip, mag (the magazine); shell, bullet (the cartridges); trigger; hammer |
| `[fingers] min_bend`, `skin_center` | 0.3, `true` |
| `[collision] skip` | The cartridges in the magazine are not colliders |
| `[clips.NAME]` | `source`, `events`, or `skip = true` |

The steps of `./port fnv convert CONFIG STEP ...`: `bake`, `parts`, `retarget`, `synth`,
`hkx`, `install`. The step `hkx` writes into `out/fo4/hkx` of the work folder, and only
`install` copies to the output folder. The step `retarget` stops when `out/fo4mesh/parts.json`
is not there.

## The templates

| | `smg` | `pistol10mm` |
| --- | --- | --- |
| Vanilla weapon | The submachine gun | The 10mm pistol |
| Sound name of the events | `WPNRifleSubmachineGun` | `WPNPistol10mm` (it has no `BoltOpen`) |
| Vanilla record and keyword of the two mods | `from = "SubmachineGun"`, `like AnimsSubmachineGun` | `from = "10mm"`, `like AnimsFP10mm` |

The vanilla Deliverer is a PPK, but it does not draw in the test game of the probe, also
with no mod. The cause is not known. So the PPK uses the 10mm pistol.

## The events of a reload

| Event | Rule |
| --- | --- |
| `SoundPlay.<sound>ReloadMagOut` | The first frame where the magazine is more than 0.3 units from its place of the last frame |
| `SoundPlay.<sound>ReloadMagIn` | The last such frame |
| `reloadComplete` | 2 frames after the magazine is in. The game fills the gun at this event. |
| `...BoltOpen`, `...BoltClose` | The bolt is away more than 0.1 units: the first frame (only when that is not frame 0) and the last frame |
| `reloadEnd` | The left hand is within 6 units of its place of the last frame and stays there, and not before 2 frames after the last part event. `initiateStart` is one frame before. |

Examples: the PPK `WPNReload` has the events at the frames 21, 87, 89, 108 and 109 (3.6333
s). `WPNReloadEmpty` has 21, 87, 89, 107 (the bolt closes), 128 and 129 (4.3 s). In an item
file, `reload_seconds` is the frame of `reloadEnd` divided by 30 (PPK 3.6333, FAMAS 2.8667).

## The rules of the hand solver

`destiny/port` uses the same solver (`fnv/tools/blender/solver.py`).

| Rule | Value | Reason |
| --- | --- | --- |
| The wrist | At the source wrist. No shift. | The two palms have the same outline to 0.5 units. A shift of 0.6 units put the magazine through the palm. |
| The fingers | Each joint on the line of the source finger, with the Fallout 4 bone lengths | A copy of the rotations put the shorter Fallout 4 fingers into the gun (1563 of 6209 hand vertices in the gun at the idle) |
| The collision floor | The center line of a finger bone is at least 0.65 x its radius from a gun surface | |
| The largest move | 1.15 units for each joint | A cap, so that a finger does not open |
| A time filter | Sigma 1.5 frames, on the moves of the collision step | The collision step works on one frame |
| `min_bend` 0.3 | Each joint has at least 0.3 x its rest bend, about the hinge of its bone | The Fallout 4 hand mesh is modelled with bent fingers (about 45 and 30 degrees). A straight finger has lumps. |
| The thumb | The last thumb joint can bend 17 degrees back | The vanilla 10mm clips hold the left thumb at that value |
| `skin_center` | The line of the finger is the center of its skin | The thumb skin of the Fallout 4 hand is 0.4 units to the pad side of its bones. The New Vegas thumb skin is 0.13 units to the nail side. |

* In the 53 vanilla first-person clips of the two templates that the reader can read, no
  finger joint bends back. Only the last thumb joint does (13 to 17 degrees, 23 at most).
* The four first values were tuned with pictures of one weapon (the MP7). The FAMAS and the
  PPK were ported later with the same values. A hand below a rifle handguard or on a
  revolver is not tested.
* The two thumbs cannot agree at each place: the Fallout 4 thumb starts 1.6 units from the
  start of the New Vegas thumb. The tools put the fingertip at its place first.
* The source hands are partly in the gun (4 to 16 percent of the skin in one reload). Zero
  is not the target.
* The tool has no key for a correction of one finger, one frame range or one offset.

## Rules of the vanilla clips

* The four `WeaponIKTarget` bones keep their reference local transform. Do not copy hand
  poses into them.
* `WPNIdleSightedWobble` and each `*Add` clip are additive. Do not replace one with a full pose.
* `WPNIdleReadyA` to `D` are the plain idle: the graph plays them at random, one directly
  after the draw.
* A movement clip keeps the `Camera Control` values of the vanilla clip.
* The vanilla idle clips have the lossless format, and the reader cannot read them.
* The game camera is the `Camera` bone. The horizontal view angle is about 87 degrees at 16:9.

## The HKX clips of this area

The writer of `fnv/` asks for 40-bit rotations. The vanilla clips have 48-bit rotations, and
`destiny/port` selects 48 bits through the same function. No test looks at the effect of the
40 bits on a clip of `fnv/`. The Destiny work found a noise of 0.03 to 0.09 units at the
muzzle in an idle clip with 40 bits.

## What is not proved, and the limits

* No command of this repository proves that the clips are correct in the game. The clips of
  the two weapons were tested in the game on 2026-10-05, each in a mod with the gun of the
  source mod, with clips of the same bytes.
* A game test cannot prove: held input (sprint, aim hold, held automatic fire), sound, power
  armor, the workbench menu, the look.
* Third person, melee and throw clips are the vanilla clips of the template. The gun can be
  smaller than the template gun.
* The sounds are those of the template. The sound files of the mod are not used.
* `kfbake.py` does not read B-spline data. `fnvnif.py` reads version 20.2.0.7, and a gun
  with skinned parts is not supported.
* The check programs with pictures of the first work are not in the work tree. They are in
  git at the tag `before-animation-only` (`tools/validate_clip.sh`, `tools/closeup.sh`,
  `tools/blender/render_fo4.py`, `render_source.py`, `hand_contact.py`), with the paths of the
  old layout. Nobody adapted or ran them in this repository.
* `fnv/tools/anim_fo4.py` is based on code with a GPL-3.0 origin (`fnv/README.md`, "Origin of
  one file").
