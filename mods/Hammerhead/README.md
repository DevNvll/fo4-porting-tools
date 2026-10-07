# Hammerhead for Fallout 4

This project packs Hammerhead (the Destiny 2 machine gun) as a Fallout 4 mod: the gun model, its
textures, the weapon records and 27 first-person clips. The clips are the Destiny 2 first-person
animations, retargeted to the Fallout 4 first-person rig by the tools in `destiny/port/`
(`d2fo4.py`), and clips with the weapon motion of the vanilla combat rifle for the states that
Destiny has no clip for.

```sh
./port mod build Hammerhead
```

The build makes `Hammerhead.esp` (a light plugin, 303 records), `Hammerhead - Main.ba2` and
`Hammerhead - Textures.ba2` in `data/mods/Hammerhead/build/release/`. To use the mod, copy these
three files into the `Data` folder of the game and enable the plugin. The build does not write
into the game.

This folder (`mods/Hammerhead/`, in git) has the files that a person writes: `esx.toml`,
`items/`, `behavior/hammerhead/hammerhead.bhv`, `ids.lock` and this file. The complete esx
project is `data/mods/Hammerhead/` (not in git): a copy of these files, and the files that the
tools make (`meshes/`, `assets/`, the clips of `behavior/hammerhead/animations/`, `docs/`,
`build/`). `./port mod build Hammerhead` copies the files of this folder into the project and
runs `esx build` there. In this file, a path that starts with `build/`, `docs/`, `meshes/`,
`assets/` or `behavior/` is a path in `data/mods/Hammerhead/`, and an `esx` command with such a
path runs in that folder. Each other command runs in the root of the repository.
`mods/README.md` has the commands of each mod.

The model, the textures and the animations are assets of Destiny 2 (Bungie). Do not publish
this mod.

## What the mod has

* One weapon, `Hammerhead` (editor ID `Hammerhead`), made from the vanilla combat rifle with
  its automatic receiver: the weapon fires automatically. It fires .45 rounds. Damage, weight
  and value are those of the combat rifle. The capacity is 60: a choice (the tools do not
  read the Destiny value).
* One model, `Weapons\Hammerhead\Hammerhead.nif` (and one copy for each shader), with 40 shapes
  (22683 vertices) and the nodes that the clips move: `WeaponMagazine` (the ammunition box),
  `WeaponMagazineChild1` to `5` and `WeaponExtra1` to `3` (the 8 links of the belt),
  `WeaponOptics1` (the top cover with the sight), `WeaponOptics2` (the latch of the cover) and
  `WeaponBolt` (the charging handle). The gun has the size of the Destiny model: 81 units long.
* The dyes of Destiny. Hammerhead has no colors in its textures: the game gives it three
  dyes. The textures of this mod have the default dyes in them (black paint with red metal
  and steel parts), and the weapon has three more receiver parts with shaders of Destiny:
  Golden Trace, Calus's Selected and Monochromatic. Change the shader at the weapons
  workbench, in the receiver slot. `destiny/port/README.md`, "The dyes and the shaders of
  Destiny", says how the textures are made.
* 12 materials and 36 textures: 3 texture sets of the Destiny model for each of the 4 looks,
  and 4 mesh files with the same shapes.
* The sight part, `Weapons\Hammerhead\HammerheadSight.nif`: the glass of the sight with its
  red graphics (two arcs, two lines, a border, three symbols) and the red dot of the reticle
  in their center. It has 2 effect materials and 2 textures, from the game files of Destiny
  (`destiny/port/README.md`, "The glass of the sight and the reticle"). The part is in the scope
  slot of the weapon, on the connect point `P-Scope` of the top cover, so it moves with the
  cover in the reload. The dot shows at each time, as the dot of a vanilla reflex sight.
* 27 first-person clips in `behavior/hammerhead/animations/first_person/`: 15 from the
  Destiny clips (idle and its two variants, sights, shot, shot in the sights, draw, put away,
  reload), 3 automatic fire clips made from the Destiny shot clips, and 9 with the weapon
  motion of the vanilla combat rifle clips on a Destiny pose (walk, run, jump, sprint, gun
  down). `destiny/port/README.md` has the table.
* 2 third-person clips in `behavior/hammerhead/animations/third_person/`: the reload of
  Destiny (`WPNReload`: the body of the player with the gun, 169 frames; the gun comes down
  to the chest, the cover opens, the left hand puts the belt in and closes the cover) and the
  hold pose (`WPNAssemblyPose`), which puts the left hand on the handguard of this gun in
  each third-person clip. `destiny/port/README.md`, "The third-person clips", says how they are
  made. Each other third-person clip is a vanilla clip of the rifle grip.
* A behavior source, `behavior/hammerhead/hammerhead.bhv`. The weapon gets its own animation
  keyword and graph copies, so no vanilla weapon changes.
* A chemistry station recipe for the weapon (12 steel, 6 aluminum, 3 springs, 4 screws).

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

`./port destiny regress --only hammerhead` makes the clips again and compares their bytes with
the clips of the project.

`destiny/port/tools/d2model.py` reads `data/destiny/port/extract/hammerhead/dyes*.json`
(`destiny/port/tools/d2dyes.py`) and `data/destiny/port/extract/hammerhead/sight.json`
(`destiny/port/tools/d2reticle.py`); `destiny/port/README.md` has the two commands.
`meshes/Weapons/Hammerhead/HammerheadSight.template.nif` is the template of the sight mesh: a
vanilla mesh with the names and the texture paths of this weapon, which gives the two effect
shaders.

`meshes/`, `assets/` and the clips are outputs of the first three commands. `esx.toml`,
`items/10-hammerhead.toml` and `behavior/hammerhead/hammerhead.bhv` were written by hand.
`ids.lock` keeps the object ID of each record. `destiny/port/README.md` ("Hammerhead") says how the
file `$GLB` was made. The records are those of `mods/Khvostov` with other names and values
(`like AnimsCombatShotgun`, the keyword `AnimsCombatRifle` removed, the automatic receiver).

## Checks that passed

* `esx build`: 0 issues in the release check, 0 warnings.
* `esx plugin check-weapons build/release/Hammerhead.esp`: 0 findings, and 0 findings with
  `--reference Hammerhead=CombatRifle`.
* `esx scene weapon build/release/Hammerhead.esp Hammerhead`: each mesh, material and
  texture resolves from the two archives of the release. The 2 findings are notes: the
  renderer of esx does not draw the two effect materials of the sight.
* `esx render weapon build/release/Hammerhead.esp Hammerhead --sheet`: the picture
  `docs/weapon.png`, made before the sight part. Each shape has its texture, and no shape is
  pink. The picture does not show the glass of the sight.
* The clips: `data/destiny/port/validation/hammerhead/` has a video of each clip with the source
  beside the result, and the numbers.
* The game test of the third-person reload:
  `data/destiny/port/validation/hammerhead/game_test_third_person.mp4` is a recording of the
  game with this release, and
  `data/destiny/port/validation/hammerhead/third_person_reload_game.jpg` has 12 pictures of it.
  The game starts the two third-person clips of this mod, the cover, the belt and the charging
  handle move, and the reload fills the box (57 to 60 rounds). 109 ops, 0 failed.
* The game test with the sight part:
  `data/destiny/port/validation/hammerhead/game_test_red_dot.mp4` is a recording of the game
  with this release, and `data/destiny/port/validation/hammerhead/red_dot_game.jpg` shows the
  sight. In the sights the red dot is at the center of the screen (less than 1 pixel away in a
  picture of 1280 x 720), in the center of the two arcs of the glass. In the reload the glass
  moves with the top cover. 40 ops, 0 failed, and the same clips as before.
* The game test with the default shader:
  `data/destiny/port/validation/hammerhead/game_test_default_shader.mp4` is a recording of the
  game with the release before the sight part (black paint, red metal and steel). The older
  recording below shows a light gray gun, because it is from before the dyes.
* The game test: `data/destiny/port/validation/hammerhead/game_test.mp4` is a recording of the
  game with the first release (`esx probe start --mod build/release`, a test copy of the game,
  headless). The game loads the weapon, its model and its graph, and plays the draw, the idle,
  automatic bursts (hip and sights), the reload, the gun down pose, the sprint pose and the
  put-away in first person, and a burst and a reload in third person. `destiny/port/README.md`,
  "The game test of Hammerhead", has the list of what the test proves.

## What is not proved

* The walk, run and jump clips in the game, and the single shot clips: the game test had no
  move input, and the weapon is automatic.
* The mod in the installed game. The game test used the test copy of esx; the release was
  not copied into the `Data` folder of the game.
* The look of the materials in other light than that of the test cell, and against a
  picture of the game Destiny (no reference picture is here).
* The shader parts and the sight part at the weapons workbench. The game test attached each
  shader with the probe, and the sight part is in the default combination of the weapon.
* Power armor, the workbench, the sounds (they are the sounds of the vanilla combat rifle
  and, in the reload, of the combat shotgun, as for the vanilla combat rifle).

## Limits

* In third person only the reload and the hold pose are from Destiny. Each other
  third-person clip is a vanilla clip of the rifle grip. In the third-person reload the box
  stays in the gun (the gun clip of Destiny does not move it), the legs do not move, and the
  right hand has the grip of the first-person hold pose while it is on the grip
  (`destiny/port/README.md` has the list of what is not done). In Destiny the gun is at the hip in
  this reload; in the other third-person clips of Fallout 4 it is at the shoulder.
* The automatic fire clips start the Destiny shot clip again at each shot of the vanilla
  automatic clip (20 shots in 67 frames). The fire rate and the recoil (the camera kick) are
  those of the vanilla combat rifle with its automatic receiver.
* The sprint clip is the sprint pose of Destiny (one pose) with the motion of the vanilla
  sprint clip.
* The reticle is on the glass of the sight and shows at each time. In Destiny it shows only
  in the sights, and it stays on the aim axis when the gun moves.
* The colors of the glass are those of one state of the sight, and its graphics do not move
  or change their brightness (`destiny/port/README.md` has the list of what is not done).
* In the sights, the gun is 3.40 units lower than in the Destiny clip, so that the reticle
  is at the center of the screen (`[sight]` of the set file).
* The put away clip has the 4 frames of Destiny and 8 more frames of its last pose.
* `reloadComplete` is 2 frames after the cover is closed (frame 105 of 180, 3.5 s), not at
  the time when the box is in the gun.
* The right thumb is in the receiver above the grip (3.0 units deep in the hold pose; the
  Destiny thumb is 1.3 units deep). It is not in the view in first person.
* The gun has no barrel, stock, magazine or muzzle parts for the workbench: only the shaders
  and the one sight part.
