# The Khvostov 7G-02 for Fallout 4

This project packs the Khvostov 7G-02 (the Destiny 2 auto rifle) as a Fallout 4 mod: the gun
model, its textures, the weapon records and 27 first-person clips. The clips are the Destiny 2
first-person animations, retargeted to the Fallout 4 first-person rig by the tools in
`destiny/port/` (`d2fo4.py`), and clips with the weapon motion of the vanilla combat rifle for
the states that Destiny has no clip for.

```sh
./port mod build Khvostov
```

The build makes `Khvostov.esp` (a light plugin, 295 records), `Khvostov - Main.ba2` and
`Khvostov - Textures.ba2` in `data/mods/Khvostov/build/release/`. To use the mod, copy these
three files into the `Data` folder of the game and enable the plugin. The build does not write
into the game.

This folder (`mods/Khvostov/`, in git) has the files that a person writes: `esx.toml`, `items/`,
`behavior/khvostov/khvostov.bhv`, `ids.lock` and this file. The complete esx project is
`data/mods/Khvostov/` (not in git): a copy of these files, and the files that the tools make
(`meshes/`, `assets/`, the clips of `behavior/khvostov/animations/`, `docs/`, `build/`).
`./port mod build Khvostov` copies the files of this folder into the project and runs
`esx build` there. In this file, a path that starts with `build/`, `docs/`, `meshes/`, `assets/`
or `behavior/` is a path in `data/mods/Khvostov/`, and an `esx` command with such a path runs in
that folder. Each other command runs in the root of the repository. `mods/README.md` has the
commands of each mod.

The model, the textures and the animations are assets of Destiny 2 (Bungie). Do not publish
this mod.

## What the mod has

* One weapon, `Khvostov 7G-02` (editor ID `Khvostov`), made from the vanilla combat rifle
  with its automatic receiver: the weapon fires automatically. It fires .45 rounds. Damage,
  weight and value are those of the combat rifle. The capacity is 30: a choice (the tools do
  not read the Destiny value).
* One model, `Weapons\Khvostov\Khvostov.nif`, with 4 shapes (11141 vertices) and the nodes
  that the clips move: `WeaponMagazine` (the magazine) and `WeaponBolt` (the charging
  handle). The gun has the size of the Destiny model: 67 units long.
* 2 materials and 6 textures from the 2 texture sets of the Destiny model (the gun, and the
  sight on the rail).
* The sight part, `Weapons\Khvostov\KhvostovSight.nif`: the glass of the sight (a red mark
  at the left and at the right, one mark below, a dark edge) and the reticle, a red dot with
  four arcs. It has 2 effect materials and 2 textures, from the game files of Destiny
  (`destiny/port/README.md`, "The glass of the sight and the reticle"). The part is in the scope
  slot of the weapon, on the connect point `P-Scope` of the gun. The reticle shows at each
  time, as the dot of a vanilla reflex sight.
* 27 first-person clips in `behavior/khvostov/animations/first_person/`: 11 from the Destiny
  clips (idle and its two small variants, sights, draw, put away, reload) and 16 with the
  weapon motion of the vanilla combat rifle clips on a Destiny pose (the shots, single and
  automatic, at the hip and in the sights; walk, run, jump, sprint, gun down).
  `destiny/port/README.md` has the table.
* 2 third-person clips in `behavior/khvostov/animations/third_person/`: the reload of Destiny
  (`WPNReload`: the body of the player with the gun, 105 frames) and the hold pose
  (`WPNAssemblyPose`), which puts the left hand on the handguard of this gun in each
  third-person clip. `destiny/port/README.md`, "The third-person clips", says how they are made.
  Each other third-person clip is a vanilla clip of the rifle grip.
* A behavior source, `behavior/khvostov/khvostov.bhv`. The weapon gets its own animation
  keyword and graph copies, so no vanilla weapon changes.
* A chemistry station recipe for the weapon (8 steel, 4 aluminum, 2 springs, 3 screws).

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
with the clips of the project.

`destiny/port/tools/d2model.py` reads `data/destiny/port/extract/khvostov_7g_02/sight.json`
(`destiny/port/tools/d2reticle.py`; `destiny/port/README.md` has the command).
`meshes/Weapons/Khvostov/KhvostovSight.template.nif` is the template of the sight mesh: a
vanilla mesh with the names and the texture paths of this weapon, which gives the two effect
shaders.

`meshes/`, `assets/` and the clips are outputs of the first three commands. `esx.toml`,
`items/10-khvostov.toml` and `behavior/khvostov/khvostov.bhv` were written by hand. `ids.lock`
keeps the object ID of each record. `destiny/port/README.md` ("The Khvostov 7G-02") says how the
file `$GLB` was made.

Two points of the records:

* The combat rifle has two animation keywords. `AnimsCombatShotgun` gives the graphs and the
  clips of each view (the combat rifle has the clips of the combat shotgun), and
  `AnimsCombatRifle` gives one first-person clip of its own. The behavior source is
  `weapon Khvostov like AnimsCombatShotgun`, and the item file removes `AnimsCombatRifle`.
  With `like AnimsCombatRifle` the build stops: that keyword has no rules for power armor.
* The receiver part is a copy of `mod_CombatRifle_Receiver_Automatic1`, which makes the
  weapon automatic.

## Checks that passed

* `esx build`: 0 issues in the release check, 0 warnings.
* `esx plugin check-weapons build/release/Khvostov.esp`: 0 findings, and 0 findings with
  `--reference Khvostov=CombatRifle`.
* `esx scene weapon build/release/Khvostov.esp Khvostov`: each mesh, material and texture
  resolves from the two archives of the release. The 2 findings are notes: the renderer of
  esx does not draw the two effect materials of the sight.
* `esx render weapon build/release/Khvostov.esp Khvostov --sheet`: the picture
  `docs/weapon.png`, made before the sight part. Each shape has its texture, and no shape is
  pink. The picture does not show the glass of the sight.
* The clips: `data/destiny/port/validation/khvostov_7g_02/` has a video of each clip with the source
  beside the result, and the numbers.
* The game test with the sight part:
  `data/destiny/port/validation/khvostov_7g_02/game_test_red_dot.mp4` is a recording of the game
  with this release, and `data/destiny/port/validation/khvostov_7g_02/red_dot_game.jpg` shows
  the sight. In the sights the reticle is at the center of the screen (less than 1 pixel away in
  a picture of 1280 x 720), between the two red marks of the glass. 40 ops, 0 failed, and the
  same clips as in the first recording. The gun is a dark worn metal in it.
* The game test of the third-person reload:
  `data/destiny/port/validation/khvostov_7g_02/game_test_third_person.mp4` is a recording of the
  game with this release, and
  `data/destiny/port/validation/khvostov_7g_02/third_person_reload_game.jpg` has 12 pictures of
  it. The game starts the two third-person clips of this mod, and the reload fills the magazine
  (27 to 30 rounds). 88 ops, 0 failed.
* The game test: `data/destiny/port/validation/khvostov_7g_02/game_test.mp4` is a recording of
  the game with the first release (`esx probe start --mod build/release`, a test copy of the
  game, headless). The game loads the weapon, its model and its graph, and plays the draw, the
  idle, automatic bursts (hip and sights), the reload, the gun down pose, the sprint pose and
  the put-away in first person, and a burst and a reload in third person.
  `destiny/port/README.md`, "The game test of the Khvostov", has the list of what the test
  proves.

## What is not proved

* The walk, run and jump clips in the game, and the single shot clips: the game test had no
  move input, and the weapon is automatic.
* The mod in the installed game. The game test used the test copy of esx; the release was
  not copied into the `Data` folder of the game.
* The look of the materials in other light than that of the test cell, and against a
  picture of the game Destiny. The textures now come from the gear shader of Destiny
  (`destiny/port/README.md`, "The dyes and the shaders of Destiny"): the gun is a dark worn metal in
  the game. This gun has no pixel with a dye, so a shader of Destiny does not change it.
* The recording `game_test.mp4` is older than that change: it shows a light gray gun.
  `game_test_red_dot.mp4` is a recording after it.
* The sight part at the weapons workbench. It is in the default combination of the weapon.
* Power armor, the workbench, the sounds (they are the sounds of the vanilla combat rifle
  and, in the reload, of the combat shotgun, as for the vanilla combat rifle).

## Limits

* Destiny has no first-person clip for the shot of this rifle, so each shot clip has the
  recoil motion of the vanilla combat rifle on the Destiny pose. The fire rate and the recoil
  (the camera kick) are those of the vanilla combat rifle with its automatic receiver.
* The sprint clip is the sprint pose of Destiny (one pose) with the motion of the vanilla
  sprint clip.
* The reticle is on the glass of the sight and shows at each time. In Destiny it shows only
  in the sights, and it stays on the aim axis when the gun moves.
* The glass has its marks and its dark edge, but not its mirror picture, its dust and its
  change of brightness (`destiny/port/README.md` has the list of what is not done).
* In the sights, the gun is 2.69 units higher than in the Destiny clip, so that the reticle
  is at the center of the screen (`[sight]` of the set file).
* The put away clip has the 4 frames of Destiny and 8 more frames of its last pose.
* In third person only the reload and the hold pose are from Destiny. Each other
  third-person clip is a vanilla clip of the rifle grip. In the third-person reload the
  magazine stays in the gun (the gun clip of Destiny does not move it), the legs do not move,
  and the right hand has the grip of the first-person hold pose (`destiny/port/README.md` has the
  list of what is not done).
* The gun has no parts for the workbench.
