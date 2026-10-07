# Hammerhead for Fallout 4

This project packs Hammerhead, the Destiny 2 machine gun, as a Fallout 4 mod. It has the gun
model, its textures, the weapon records and 27 first-person clips. Some clips are the
Destiny 2 first-person animations, which the tools in `destiny/port/` (`d2fo4.py`) retarget
to the Fallout 4 first-person rig. Where Destiny has no clip for a state, the clip has the
weapon motion of the vanilla combat rifle.

```sh
./port mod build Hammerhead
```

The build writes three files to `data/mods/Hammerhead/build/release/`: `Hammerhead.esp`, a
light plugin with 303 records, `Hammerhead - Main.ba2` and `Hammerhead - Textures.ba2`. To
use the mod, copy them into the game's `Data` folder and enable the plugin. The build does
not write into the game.

This folder, `mods/Hammerhead/`, is in git and holds the hand-written files and the lock files that esx keeps: `esx.toml`,
`items/`, `behavior/hammerhead/hammerhead.bhv`, `ids.lock` and this file. The complete esx
project is `data/mods/Hammerhead/`, which is not in git. It has a copy of these files and
what the tools make: `meshes/`, `assets/`, the clips in `behavior/hammerhead/animations/`,
`docs/` and `build/`. `./port mod build Hammerhead` copies this folder into the project and
runs `esx build` there.

In this file, a path that starts with `build/`, `docs/`, `meshes/`, `assets/` or `behavior/`
is inside `data/mods/Hammerhead/`, and an `esx` command with such a path runs in that folder.
Run every other command from the repository root. `mods/README.md` has the commands for each
mod.

The model, textures and animations are Destiny 2 assets and belong to Bungie. Do not publish
this mod.

## What the mod has

* One weapon, `Hammerhead`, editor ID `Hammerhead`, made from the vanilla combat rifle with
  its automatic receiver, so it fires automatically. It fires .45 rounds. Damage, weight and
  value are the combat rifle's. The capacity of 60 is a choice, because the tools do not read
  the Destiny value.
* One model, `Weapons\Hammerhead\Hammerhead.nif`, and one copy of it for each shader. It has
  40 shapes, 22683 vertices and the nodes the clips move. `WeaponMagazine` is the ammunition
  box. `WeaponMagazineChild1` to `5` and `WeaponExtra1` to `3` are the 8 links of the belt.
  `WeaponOptics1` is the top cover with the sight, `WeaponOptics2` the latch of the cover and
  `WeaponBolt` the charging handle. The gun keeps the size of the Destiny model, 81 units
  long.
* The Destiny dyes. Hammerhead has no colors in its textures. The game gives it three dyes.
  This mod's textures have the default dyes in them, black paint with red metal and steel
  parts. The weapon also has three more receiver parts with Destiny shaders: Golden Trace,
  Calus's Selected and Monochromatic. Change the shader at the weapons workbench, in the
  receiver slot. "The dyes and the shaders of Destiny" in `destiny/port/README.md` says how
  the textures are made.
* 12 materials and 36 textures, which is 3 texture sets of the Destiny model for each of the
  4 looks, and 4 mesh files with the same shapes.
* The sight part, `Weapons\Hammerhead\HammerheadSight.nif`. It is the glass of the sight and
  the red dot of the reticle. The glass has red graphics: two arcs, two lines, a border and
  three symbols. The dot is in their center. Its 2 effect materials and 2 textures come from
  the Destiny game files. See "The glass of the sight and the reticle" in
  `destiny/port/README.md`. The part is in the weapon's scope slot, on the connect point
  `P-Scope` of the top cover, so it moves with the cover in the reload. The dot always shows,
  like the dot of a vanilla reflex sight.
* 27 first-person clips in `behavior/hammerhead/animations/first_person/`. 15 come from the
  Destiny clips: idle and its two variants, sights, shot, shot in the sights, draw, put away
  and reload. 3 are automatic fire clips made from the Destiny shot clips. The other 9 put
  the weapon motion of the vanilla combat rifle clips on a Destiny pose: walk, run, jump,
  sprint and gun down. `destiny/port/README.md` has the table.
* 2 third-person clips in `behavior/hammerhead/animations/third_person/`. `WPNReload` is the
  Destiny reload, the player's body with the gun, 169 frames. The gun comes down to the
  chest, the cover opens, and the left hand puts the belt in and closes the cover.
  `WPNAssemblyPose` is the hold pose, which puts the left hand on this gun's handguard in
  every third-person clip. "The third-person clips" in `destiny/port/README.md` says how
  they are made. Every other third-person clip is a vanilla clip of the rifle grip.
* A behavior source, `behavior/hammerhead/hammerhead.bhv`. The weapon gets its own animation
  keyword and graph copies, so no vanilla weapon changes.
* A chemistry station recipe for the weapon: 12 steel, 6 aluminum, 3 springs, 4 screws.

## How the project was made

```sh
GLB=data/destiny/port/extract/hammerhead/hammerhead_first_person.glb
SET=destiny/port/sets/hammerhead.toml
M=data/mods/Hammerhead
./port destiny convert $GLB --set $SET -o $M/behavior/hammerhead/animations/first_person
./port destiny model $GLB --set $SET --mod Hammerhead
./port destiny convert $GLB --set $SET third --third-output $M/behavior/hammerhead/animations/third_person
./port mod build Hammerhead --update-lock
```

`./port destiny regress --only hammerhead` makes the clips again and compares their bytes
with the project's clips.

`destiny/port/tools/d2model.py` reads two inputs. `destiny/port/tools/d2dyes.py` makes
`data/destiny/port/extract/hammerhead/dyes*.json`, and `destiny/port/tools/d2reticle.py`
makes `data/destiny/port/extract/hammerhead/sight.json`. `destiny/port/README.md` has the
two commands. `meshes/Weapons/Hammerhead/HammerheadSight.template.nif` is the template of
the sight mesh. It is a vanilla mesh with the names and the texture paths of this weapon,
and it gives the two effect shaders.

The first three commands make `meshes/`, `assets/` and the clips. `esx.toml`,
`items/10-hammerhead.toml` and `behavior/hammerhead/hammerhead.bhv` were written by hand.
`ids.lock` keeps the object ID of each record. "Hammerhead" in `destiny/port/README.md` says
how the file `$GLB` was made. The records are the `mods/Khvostov` records with other names
and values: `like AnimsCombatShotgun`, the keyword `AnimsCombatRifle` removed, and the
automatic receiver.

## Checks that passed

* `esx build` gives 0 issues in the release check and 0 warnings.
* `esx plugin check-weapons build/release/Hammerhead.esp` gives 0 findings, and 0 findings
  with `--reference Hammerhead=CombatRifle`.
* `esx scene weapon build/release/Hammerhead.esp Hammerhead` resolves every mesh, material
  and texture from the release's two archives. Its 2 findings are notes that the esx renderer
  does not draw the sight's two effect materials.
* `esx render weapon build/release/Hammerhead.esp Hammerhead --sheet` made the picture
  `docs/weapon.png`. Every shape has its texture, and none is pink. The picture was made
  before the sight part, so it does not show the glass of the sight.
* `data/destiny/port/validation/hammerhead/` has a video of each clip with the source beside
  the result, and the numbers.
* The third-person reload passed its game test.
  `data/destiny/port/validation/hammerhead/game_test_third_person.mp4` is a recording of the
  game with this release, and
  `data/destiny/port/validation/hammerhead/third_person_reload_game.jpg` has 12 pictures of
  it. The game starts the mod's two third-person clips, the cover, the belt and the charging
  handle move, and the reload fills the box from 57 to 60 rounds. 109 ops, 0 failed.
* The sight part passed its game test.
  `data/destiny/port/validation/hammerhead/game_test_red_dot.mp4` is a recording of the game
  with this release, and `data/destiny/port/validation/hammerhead/red_dot_game.jpg` shows the
  sight. In the sights the red dot is at the center of the screen, less than 1 pixel away in
  a picture of 1280 x 720, in the center of the two arcs of the glass. In the reload the
  glass moves with the top cover. 40 ops, 0 failed, and the same clips as before.
* `data/destiny/port/validation/hammerhead/game_test_default_shader.mp4` is a recording of
  the game test with the default shader. It used the release from before the sight part, and
  the gun has black paint, red metal and steel. The older recording below shows a light gray
  gun, because it is from before the dyes.
* `data/destiny/port/validation/hammerhead/game_test.mp4` is a recording of the game test
  with the first release. It ran headless on a test copy of the game, with
  `esx probe start --mod build/release`. The game loads the weapon, its model and its graph.
  In first person it plays the draw, the idle, automatic bursts at the hip and in the sights,
  the reload, the gun down pose, the sprint pose and the put-away. In third person it plays a
  burst and a reload. "The game test of Hammerhead" in `destiny/port/README.md` lists what
  the test proves.

## What is not proved

* The walk, run and jump clips in the game, and the single shot clips. The game test had no
  move input, and the weapon is automatic.
* The mod in the installed game. The game test used the esx test copy, and the release was
  not copied into the game's `Data` folder.
* The look of the materials in any light other than the test cell's, and against a picture
  from Destiny. No reference picture is here.
* The shader parts and the sight part at the weapons workbench. The game test attached each
  shader with the probe, and the sight part is in the default combination of the weapon.
* Power armor, the workbench and the sounds. The sounds come from the vanilla combat rifle
  and, in the reload, from the combat shotgun, as they do for the vanilla combat rifle.

## Limits

* In third person only the reload and the hold pose are from Destiny. In that reload the box
  stays in the gun because the Destiny gun clip does not move it, the legs do not move, and
  the right hand has the grip of the first-person hold pose while it is on the grip.
  `destiny/port/README.md` lists what is not done. In Destiny the gun is at the hip in this
  reload. In the other third-person clips of Fallout 4 it is at the shoulder.
* The automatic fire clips start the Destiny shot clip again at each shot of the vanilla
  automatic clip, which has 20 shots in 67 frames. The fire rate and the recoil, which is the
  camera kick, come from the vanilla combat rifle with its automatic receiver.
* The sprint clip is the Destiny sprint pose, a single pose, with the motion of the vanilla
  sprint clip.
* The reticle is on the glass of the sight and always shows. In Destiny it shows only in the
  sights, and it stays on the aim axis when the gun moves.
* The glass has the colors of one state of the sight, and its graphics do not move or change
  their brightness. `destiny/port/README.md` lists what is not done.
* In the sights the gun is 3.40 units lower than in the Destiny clip, which puts the reticle
  at the center of the screen. `[sight]` in the set file sets this.
* The put away clip has the 4 frames of Destiny and 8 more frames of its last pose.
* `reloadComplete` comes 2 frames after the cover closes, at frame 105 of 180 or 3.5 s, and
  not when the box is in the gun.
* The right thumb is in the receiver above the grip, 3.0 units deep in the hold pose. The
  Destiny thumb is 1.3 units deep. It is out of view in first person.
* The gun has no barrel, stock, magazine or muzzle parts for the workbench, only the shaders
  and the one sight part.
