# The Khvostov 7G-02 for Fallout 4

This project packs the Khvostov 7G-02, the Destiny 2 auto rifle, as a Fallout 4 mod. It has
the gun model, its textures, the weapon records and 27 first-person clips. Some clips are the
Destiny 2 first-person animations, which the tools in `destiny/port/` (`d2fo4.py`) retarget
to the Fallout 4 first-person rig. Where Destiny has no clip for a state, the clip has the
weapon motion of the vanilla combat rifle.

```sh
./port mod build Khvostov
```

The build writes three files to `data/mods/Khvostov/build/release/`: `Khvostov.esp`, a light
plugin with 295 records, `Khvostov - Main.ba2` and `Khvostov - Textures.ba2`. To use the mod,
copy them into the game's `Data` folder and enable the plugin. The build does not write into
the game.

This folder, `mods/Khvostov/`, is in git and holds the hand-written files and the lock files that esx keeps: `esx.toml`,
`items/`, `behavior/khvostov/khvostov.bhv`, `ids.lock` and this file. The complete esx
project is `data/mods/Khvostov/`, which is not in git. It has a copy of these files and what
the tools make: `meshes/`, `assets/`, the clips in `behavior/khvostov/animations/`, `docs/`
and `build/`. `./port mod build Khvostov` copies this folder into the project and runs
`esx build` there.

In this file, a path that starts with `build/`, `docs/`, `meshes/`, `assets/` or `behavior/`
is inside `data/mods/Khvostov/`, and an `esx` command with such a path runs in that folder.
Run every other command from the repository root. `mods/README.md` has the commands for each
mod.

The model, textures and animations are Destiny 2 assets and belong to Bungie. Do not publish
this mod.

## What the mod has

* One weapon, `Khvostov 7G-02`, editor ID `Khvostov`, made from the vanilla combat rifle with
  its automatic receiver, so it fires automatically. It fires .45 rounds. Damage, weight and
  value are the combat rifle's. The capacity of 30 is a choice, because the tools do not read
  the Destiny value.
* One model, `Weapons\Khvostov\Khvostov.nif`, with 4 shapes and 11141 vertices. The clips
  move two of its nodes, `WeaponMagazine` for the magazine and `WeaponBolt` for the charging
  handle. The gun keeps the size of the Destiny model, 67 units long.
* 2 materials and 6 textures from the 2 texture sets of the Destiny model, one for the gun
  and one for the sight on the rail.
* The sight part, `Weapons\Khvostov\KhvostovSight.nif`. It is the glass of the sight, with a
  red mark at the left and at the right, one mark below and a dark edge, and the reticle, a
  red dot with four arcs. Its 2 effect materials and 2 textures come from the Destiny game
  files. See "The glass of the sight and the reticle" in `destiny/port/README.md`. The part
  is in the weapon's scope slot, on the gun's connect point `P-Scope`. The reticle always
  shows, like the dot of a vanilla reflex sight.
* 27 first-person clips in `behavior/khvostov/animations/first_person/`. 11 come from the
  Destiny clips: idle and its two small variants, sights, draw, put away and reload. The
  other 16 put the weapon motion of the vanilla combat rifle clips on a Destiny pose. They
  are the shots, single and automatic, at the hip and in the sights, and walk, run, jump,
  sprint and gun down. `destiny/port/README.md` has the table.
* 2 third-person clips in `behavior/khvostov/animations/third_person/`. `WPNReload` is the
  Destiny reload, the player's body with the gun, 105 frames. `WPNAssemblyPose` is the hold
  pose, which puts the left hand on this gun's handguard in every third-person clip. "The
  third-person clips" in `destiny/port/README.md` says how they are made. Every other
  third-person clip is a vanilla clip of the rifle grip.
* A behavior source, `behavior/khvostov/khvostov.bhv`. The weapon gets its own animation
  keyword and graph copies, so no vanilla weapon changes.
* A chemistry station recipe for the weapon: 8 steel, 4 aluminum, 2 springs, 3 screws.

## How the project was made

```sh
GLB=data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
SET=destiny/port/sets/khvostov_7g_02.toml
M=data/mods/Khvostov
./port destiny convert $GLB --set $SET -o $M/behavior/khvostov/animations/first_person
./port destiny model $GLB --set $SET --mod Khvostov
./port destiny convert $GLB --set $SET third --third-output $M/behavior/khvostov/animations/third_person
./port mod build Khvostov --update-lock
```

`./port destiny regress --only khvostov_7g_02` makes the clips again and compares their bytes
with the project's clips.

`destiny/port/tools/d2model.py` reads `data/destiny/port/extract/khvostov_7g_02/sight.json`,
which `destiny/port/tools/d2reticle.py` makes. `destiny/port/README.md` has the command.
`meshes/Weapons/Khvostov/KhvostovSight.template.nif` is the template of the sight mesh. It is
a vanilla mesh with the names and the texture paths of this weapon, and it gives the two
effect shaders.

The first three commands make `meshes/`, `assets/` and the clips. `esx.toml`,
`items/10-khvostov.toml` and `behavior/khvostov/khvostov.bhv` were written by hand.
`ids.lock` keeps the object ID of each record. "The Khvostov 7G-02" in
`destiny/port/README.md` says how the file `$GLB` was made.

Two things about the records:

* The combat rifle has two animation keywords. `AnimsCombatShotgun` gives the graphs and the
  clips of each view, because the combat rifle has the clips of the combat shotgun.
  `AnimsCombatRifle` gives one first-person clip of its own. The behavior source is
  `weapon Khvostov like AnimsCombatShotgun`, and the item file removes `AnimsCombatRifle`.
  With `like AnimsCombatRifle` the build stops, because that keyword has no rules for power
  armor.
* The receiver part is a copy of `mod_CombatRifle_Receiver_Automatic1`, which makes the
  weapon automatic.

## Checks that passed

* `esx build` gives 0 issues in the release check and 0 warnings.
* `esx plugin check-weapons build/release/Khvostov.esp` gives 0 findings, and 0 findings with
  `--reference Khvostov=CombatRifle`.
* `esx scene weapon build/release/Khvostov.esp Khvostov` resolves every mesh, material and
  texture from the release's two archives. Its 2 findings are notes that the esx renderer
  does not draw the sight's two effect materials.
* `esx render weapon build/release/Khvostov.esp Khvostov --sheet` made the picture
  `docs/weapon.png`. Every shape has its texture, and none is pink. The picture was made
  before the sight part, so it does not show the glass of the sight.
* `data/destiny/port/validation/khvostov_7g_02/` has a video of each clip with the source
  beside the result, and the numbers.
* The sight part passed its game test.
  `data/destiny/port/validation/khvostov_7g_02/game_test_red_dot.mp4` is a recording of the
  game with this release, and `data/destiny/port/validation/khvostov_7g_02/red_dot_game.jpg`
  shows the sight. In the sights the reticle is at the center of the screen, less than 1
  pixel away in a picture of 1280 x 720, between the two red marks of the glass. 40 ops, 0
  failed, and the same clips as in the first recording. The gun is a dark worn metal in it.
* The third-person reload passed its game test.
  `data/destiny/port/validation/khvostov_7g_02/game_test_third_person.mp4` is a recording of
  the game with this release, and
  `data/destiny/port/validation/khvostov_7g_02/third_person_reload_game.jpg` has 12 pictures
  of it. The game starts the mod's two third-person clips, and the reload fills the magazine
  from 27 to 30 rounds. 88 ops, 0 failed.
* `data/destiny/port/validation/khvostov_7g_02/game_test.mp4` is a recording of the game test
  with the first release. It ran headless on a test copy of the game, with
  `esx probe start --mod build/release`. The game loads the weapon, its model and its graph.
  In first person it plays the draw, the idle, automatic bursts at the hip and in the sights,
  the reload, the gun down pose, the sprint pose and the put-away. In third person it plays a
  burst and a reload. "The game test of the Khvostov" in `destiny/port/README.md` lists what
  the test proves.

## What is not proved

* The walk, run and jump clips in the game, and the single shot clips. The game test had no
  move input, and the weapon is automatic.
* The mod in the installed game. The game test used the esx test copy, and the release was
  not copied into the game's `Data` folder.
* The look of the materials in any light other than the test cell's, and against a picture
  from Destiny. The textures now come from the Destiny gear shader, so the gun is a dark worn
  metal in the game. See "The dyes and the shaders of Destiny" in `destiny/port/README.md`.
  This gun has no pixel with a dye, so a Destiny shader does not change it.
* The recording `game_test.mp4` is older than that change and shows a light gray gun.
  `game_test_red_dot.mp4` was recorded after it.
* The sight part at the weapons workbench. It is in the default combination of the weapon.
* Power armor, the workbench and the sounds. The sounds come from the vanilla combat rifle
  and, in the reload, from the combat shotgun, as they do for the vanilla combat rifle.

## Limits

* Destiny has no first-person clip for this rifle's shot, so every shot clip has the recoil
  motion of the vanilla combat rifle on the Destiny pose. The fire rate and the recoil, which
  is the camera kick, come from the vanilla combat rifle with its automatic receiver.
* The sprint clip is the Destiny sprint pose, a single pose, with the motion of the vanilla
  sprint clip.
* The reticle is on the glass of the sight and always shows. In Destiny it shows only in the
  sights, and it stays on the aim axis when the gun moves.
* The glass has its marks and its dark edge, but not its mirror picture, its dust or its
  change of brightness. `destiny/port/README.md` lists what is not done.
* In the sights the gun is 2.69 units higher than in the Destiny clip, which puts the reticle
  at the center of the screen. `[sight]` in the set file sets this.
* The put away clip has the 4 frames of Destiny and 8 more frames of its last pose.
* In third person only the reload and the hold pose are from Destiny. In that reload the
  magazine stays in the gun because the Destiny gun clip does not move it, the legs do not
  move, and the right hand has the grip of the first-person hold pose.
  `destiny/port/README.md` lists what is not done.
* The gun has no parts for the workbench.
