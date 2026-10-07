# Tex Mechanica for Fallout 4

This project packs three Tex Mechanica weapons from Destiny 2 as one Fallout 4 mod. The Last
Word is a revolver, The Chaperone a shotgun with a lever and The Huckleberry a submachine
gun. Each weapon has its gun model, textures, weapon records and clips. The clips are the
Destiny 2 animations, which the tools in `destiny/port/` (`d2fo4.py`) retarget to the
Fallout 4 rigs.

```sh
./port mod build TexMechanica
```

The build writes three files to `data/mods/TexMechanica/build/release/`: `TexMechanica.esp`,
a light plugin with 664 records, `TexMechanica - Main.ba2` and `TexMechanica - Textures.ba2`.
To use the mod, copy them into the game's `Data` folder and enable the plugin. The build does
not write into the game.

This folder, `mods/TexMechanica/`, is in git and holds the hand-written files and the lock files that esx keeps: `esx.toml`,
`items/`, `behavior/thelastword/thelastword.bhv`, `behavior/thechaperone/thechaperone.bhv`,
`behavior/thehuckleberry/thehuckleberry.bhv`, `ids.lock` and this file. The complete esx
project is `data/mods/TexMechanica/`, which is not in git. It has a copy of these files and
what the tools make: `meshes/`, `assets/`, the clips in `behavior/NAME/animations/`, `docs/`
and `build/`. `./port mod build TexMechanica` copies this folder into the project and runs
`esx build` there.

In this file, a path that starts with `build/`, `docs/`, `meshes/`, `assets/` or `behavior/`
is inside `data/mods/TexMechanica/`, and an `esx` command with such a path runs in that
folder. Run every other command from the repository root. `mods/README.md` has the commands
for each mod.

The models, textures and animations are Destiny 2 assets and belong to Bungie. Do not publish
this mod.

`mods/TheLastWord` is a mod with The Last Word only. Both mods have a weapon with the editor
ID `TheLastWord` and the same model files, so use only one of them.

## What the mod has

| Weapon | Editor ID | Made from | Ammunition | Capacity | Damage |
| --- | --- | --- | --- | --- | --- |
| The Last Word | `TheLastWord` | the .44 revolver | .44 | 8 | 48 |
| The Chaperone | `TheChaperone` | the combat shotgun | shotgun shells, one projectile for each shot | 6 | 80 |
| The Huckleberry | `TheHuckleberry` | the combat rifle, with its automatic receiver | .45 | 30 | 26 |

The Last Word has the values of `mods/TheLastWord`. For the other two weapons the capacity
and the damage are choices, and so is the 0.857 s between two shots of The Chaperone, because
the tools do not read the Destiny values. `items/` has the three item files, with a comment
for each value. Each weapon has a recipe at the chemistry station.

**The Last Word.** The model, materials, textures and 26 clips are copies of the files in
`mods/TheLastWord`. 24 of the clips are first-person and 2 are third-person. Its behavior
source has the prefix `TXL` here.

**The Chaperone.**

* One model, `Weapons\TheChaperone\TheChaperone.nif`, with 8 shapes and 2764 vertices. It has
  the nodes the clips move. `WeaponBolt` is the lever, `WeaponMagazine` the shell that the
  hand puts in and `WeaponExtra1` the gate of the loading port. The gun is 48.6 units long.
  It has 4 materials and 12 textures, with the dyes of the default Destiny shader.
* The sight part, `TheChaperoneSight.nif`. It is the glass with two red rings between the
  two horns of the rear sight, and the reticle, a dot with a red ring.
* 30 first-person clips in `behavior/thechaperone/animations/first_person/`. 21 come from the
  Destiny clips: idle, sights, shot, shot in the sights, draw, put away and 7 reload clips.
  The other 9 have the weapon motion of the vanilla combat rifle clips: walk, run, jump,
  sprint and gun down.
* While the left hand is on the gun, it has the pose of a pose clip of The Chaperone,
  `fp_050_80BBD62D_add`. The thumb is on the left side of the barrel cover and the fingers
  are below it. With only the clips of the shotgun class, the hand was 1.0 cm from the gun.
* The reload puts in one shell at a time and ends with a turn of the gun around the lever.
  The behavior source has one line for each count of rounds in the gun, from
  `when ammo == 5 play WPNReload1` to `when ammo == 0 play WPNReload6`, so the reload has as
  many shells as the gun has room for. That is 2.7 s for one shell and 7.2 s for six.
* 8 third-person clips in `behavior/thechaperone/animations/third_person/`: the same seven
  reload clips with the player's body, and the hold pose `WPNAssemblyPose`. `WPNReload` has
  no sound event there. "The third-person clips" in `destiny/port/README.md` says why.
* 6 clips in `behavior/thechaperone/animations/power_armor_third_person/`. They are copies
  of one vanilla clip from your game, the reload of the combat shotgun in power armor, with
  the names `WPNReload1` to `WPNReload6`. esx needs a file with each of these names for the
  power armor view.

**The Huckleberry.**

* One model, `Weapons\TheHuckleberry\TheHuckleberry.nif`, with 7 shapes and 12286 vertices.
  The clips move two of its nodes, `WeaponBolt` for the housing of the barrel and
  `WeaponMagazine` for the magazine. The gun is 43.4 units long. It has 5 materials and 15
  textures.
* The sight part, `TheHuckleberrySight.nif`. It is the glass of the sight, with a gold
  colored border and four green marks, and the reticle, a dot with a red ring.
* 27 first-person clips in `behavior/thehuckleberry/animations/first_person/`. 18 come from
  the Destiny clips: idle, sights, shot, automatic fire, draw, put away and reload. The other
  9 have the weapon motion of the vanilla combat rifle clips.
* While the left hand is on the gun, it has the pose of a pose clip of The Huckleberry,
  `fp_090_80BC11A5_add`, and holds the magazine.
* 2 third-person clips: the Destiny reload, 91 frames, and the hold pose.

Each weapon has a behavior source, `behavior/NAME/NAME.bhv`, with its own prefix: `TXL`,
`TXC` or `TXH`. Each gets its own animation keyword and graph copies, so no vanilla weapon
changes.

## How the project was made

```sh
C=data/destiny/port/extract/the_chaperone/the_chaperone_first_person.glb
H=data/destiny/port/extract/the_huckleberry/the_huckleberry_first_person.glb
M=data/mods/TexMechanica
./port destiny make-rig                                      # the vanilla clips of the templates
# data/destiny/port/extract/NAME/posed/ must be there ([hand_pose] of each set file):
# `./port destiny pose` makes it, and the comment above [hand_pose] in each set file has the command
./port destiny convert $C --set destiny/port/sets/the_chaperone.toml -o $M/behavior/thechaperone/animations/first_person
./port destiny model $C --set destiny/port/sets/the_chaperone.toml --mod TexMechanica
./port destiny convert $C --set destiny/port/sets/the_chaperone.toml third \
    --third-output $M/behavior/thechaperone/animations/third_person
./port destiny convert $H --set destiny/port/sets/the_huckleberry.toml -o $M/behavior/thehuckleberry/animations/first_person
./port destiny model $H --set destiny/port/sets/the_huckleberry.toml --mod TexMechanica
./port destiny convert $H --set destiny/port/sets/the_huckleberry.toml third \
    --third-output $M/behavior/thehuckleberry/animations/third_person
./port mod build TexMechanica --update-lock
```

`./port destiny regress --only the_chaperone --only the_huckleberry --only the_last_word`
makes the clips of the three weapons again and compares their bytes with the project's clips.
That is 30, 27 and 24 first-person clips, and 8, 2 and 2 third-person clips.

`destiny/port/README.md` has the commands that make the files in
`data/destiny/port/extract/`, under "The Chaperone" and "The third-person clips". The
commands above make `meshes/`, `assets/` and the clips of the two new guns. The files of The
Last Word were copied from `mods/TheLastWord`: `meshes/Weapons/TheLastWord`,
`assets/*/Weapons/TheLastWord` and `behavior/thelastword/animations`. `esx.toml`, the three
files in `items/` and the three `.bhv` files were written by hand. `ids.lock` keeps the
object ID of each record. The two files `meshes/Weapons/NAME/NAMESight.template.nif` are the
templates of the sight meshes. Each is a vanilla mesh with the names and the texture paths of
the weapon, and it gives the two effect shaders.

## Checks that passed

* `esx build` gives 0 issues in the release check and 0 warnings.
* `esx plugin check-weapons build/release/TexMechanica.esp` gives 0 findings for the three
  weapons.
* `esx scene weapon build/release/TexMechanica.esp NAME`, run for each weapon, resolves every
  mesh, material and texture from the release's two archives. The Last Word has 0 findings.
  The other two weapons have 2 findings each. They are notes that the esx renderer does not
  draw a sight's two effect materials.
* `esx render weapon build/release/TexMechanica.esp NAME --sheet` made the pictures
  `docs/TheLastWord.png`, `docs/TheChaperone.png` and `docs/TheHuckleberry.png`. Every shape
  has its texture.
* The numbers for every clip of the two new guns are in
  `data/destiny/port/validation/the_chaperone/summary.txt` and
  `data/destiny/port/validation/the_huckleberry/summary.txt`. A vertex of the gun is at most
  0.012 units from its place in the source, and no finger joint bends to the back.
* `destiny/port/check/touch.py` measures the distance of each hand to the gun in each clip.
  Its output is `data/destiny/port/validation/NAME/hand_distance.txt`. In the hold pose, 5.2
  percent of the left hand's vertices are nearer than 0.5 cm to The Chaperone, up from 0.0
  percent before the pose clip. For The Huckleberry it is 20.9 percent, up from 12.4 percent.
  `data/destiny/port/validation/NAME/left_hand_before_after.jpg` shows the hold pose in the
  game before and after.
* The game tests. Each used the release that
  `data/destiny/port/validation/tex_mechanica/release_tested.sha` names, and ran headless on
  a test copy of the game with `esx probe start --mod build/release`.
  * First person, with `destiny/port/check/game_record.py`. The Chaperone had 44 ops, The
    Huckleberry 40 and The Last Word 44, each with 0 failed ops. The game loads each weapon,
    its model and its graphs, and plays the draw, the idle, the shots at the hip and in the
    sights, the reload, the gun down pose, the sprint pose and the put-away. The recordings
    are `data/destiny/port/validation/the_chaperone/game_test.mp4`,
    `data/destiny/port/validation/the_huckleberry/game_test.mp4` and
    `data/destiny/port/validation/tex_mechanica/game_test_the_last_word.mp4`.
  * Third person, with `destiny/port/check/game_third.py`. 94, 88 and 73 ops, each with 0
    failed ops. The reload fills the gun. The recordings are
    `data/destiny/port/validation/NAME/game_test_third_person.mp4`.
  * The 12 reloads of The Chaperone, with `destiny/port/check/game_reloads.py`. There is one
    for each count of rounds from 0 to 5, in first person and in third person. Each plays the
    clip of its count, fills the gun to 6 rounds and starts one shell sound for each shell.
    The result is in `data/destiny/port/validation/the_chaperone/game_test_reloads.txt`.
  * The sights. The dot of the reticle is at the center of the screen in the sights, within
    1 pixel of 1280 x 720. `data/destiny/port/validation/NAME/red_dot_game.jpg` shows it.

  "The game test of the Tex Mechanica mod" in `destiny/port/README.md` lists what the tests
  prove.

## What is not proved

* The walk, run and jump clips in the game, because the game tests had no move input.
* The mod in the installed game. The game tests used the esx test copy, and the release was
  not copied into the game's `Data` folder.
* Power armor. The first-person clips are for the two bodies. In third person a body in
  power armor has the vanilla reload of the combat shotgun for The Chaperone and The
  Huckleberry, or of the .44 for The Last Word. I did not test a body in power armor.
* The reload of The Huckleberry against a picture from Destiny. See "What is not proved" in
  `destiny/port/README.md`.
* The look of the materials in any light other than the test cell's, and against a picture
  from Destiny.
* The workbench and the sounds. The sounds come from the vanilla combat shotgun, combat rifle
  and .44, plus the shell sound of the vanilla double-barrel shotgun. The sound was not
  recorded.

## Limits

* The reload of The Chaperone with 6 shells is 7.2 s long, because the clips have the speed
  of the Destiny files. The esx document `docs/BEHAVIOR.md` says that a `speed` line such as
  `speed 1.5` in the `reload` block of `behavior/thechaperone/thechaperone.bhv` makes each
  reload faster. This mod has no such line, and it was not tested.
* The shot of The Chaperone at the hip has no motion of the lever, because the Destiny file
  has none there. The shot in the sights has it.
* In third person I think the lever of The Chaperone does not open in a reload with 1 to 5
  shells, and the shell does not show. See "The third-person clips" in
  `destiny/port/README.md`.
* The glass of both sights always shows, at the hip too. In the sights, the glass of The
  Huckleberry has half of the Destiny brightness, with no tint and no mirror picture.
* The Huckleberry has no single shot mode, because its receiver is the automatic receiver of
  the combat rifle.
* The recoil, the camera kick at each shot, comes from each weapon's vanilla record.
* The guns have no parts for the workbench.
