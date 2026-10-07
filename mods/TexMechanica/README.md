# Tex Mechanica for Fallout 4

This project packs three weapons of Tex Mechanica (Destiny 2) as one Fallout 4 mod: The Last
Word (a revolver), The Chaperone (a shotgun with a lever) and The Huckleberry (a submachine
gun). Each weapon has its gun model, its textures, its weapon records and its clips. The
clips are the Destiny 2 animations, retargeted to the Fallout 4 rigs by the tools in `destiny/port/`
(`d2fo4.py`).

```sh
./port mod build TexMechanica
```

The build makes `TexMechanica.esp` (a light plugin, 664 records), `TexMechanica - Main.ba2` and
`TexMechanica - Textures.ba2` in `data/mods/TexMechanica/build/release/`. To use the mod, copy
these three files into the `Data` folder of the game and enable the plugin. The build does not
write into the game.

This folder (`mods/TexMechanica/`, in git) has the files that a person writes: `esx.toml`,
`items/`, `behavior/thelastword/thelastword.bhv`, `behavior/thechaperone/thechaperone.bhv`,
`behavior/thehuckleberry/thehuckleberry.bhv`, `ids.lock` and this file. The complete esx project
is `data/mods/TexMechanica/` (not in git): a copy of these files, and the files that the tools
make (`meshes/`, `assets/`, the clips of `behavior/NAME/animations/`, `docs/`, `build/`).
`./port mod build TexMechanica` copies the files of this folder into the project and runs
`esx build` there. In this file, a path that starts with `build/`, `docs/`, `meshes/`, `assets/`
or `behavior/` is a path in `data/mods/TexMechanica/`, and an `esx` command with such a path
runs in that folder. Each other command runs in the root of the repository. `mods/README.md` has
the commands of each mod.

The models, the textures and the animations are assets of Destiny 2 (Bungie). Do not publish
this mod.

`mods/TheLastWord` is a mod with The Last Word only. The two mods have a weapon with the same
editor ID (`TheLastWord`) and the same model files. Use one of the two.

## What the mod has

| Weapon | Editor ID | Made from | Ammunition | Capacity | Damage |
| --- | --- | --- | --- | --- | --- |
| The Last Word | `TheLastWord` | the .44 revolver | .44 | 8 | 48 |
| The Chaperone | `TheChaperone` | the combat shotgun | shotgun shells, one projectile for each shot | 6 | 80 |
| The Huckleberry | `TheHuckleberry` | the combat rifle, with its automatic receiver | .45 | 30 | 26 |

The values of The Last Word are those of `mods/TheLastWord`. The capacity and the damage of
the two other weapons, and the time between two shots of The Chaperone (0.857 s), are
choices: the tools do not read the values of Destiny. `items/` has the three item files,
with a comment for each value. Each weapon has a recipe at the chemistry station.

**The Last Word.** The model, the materials, the textures and the 26 clips are copies of
the files of `mods/TheLastWord` (24 first-person clips and 2 third-person clips). Its behavior
source has the prefix `TXL` here.

**The Chaperone.**

* One model, `Weapons\TheChaperone\TheChaperone.nif`, with 8 shapes (2764 vertices) and the
  nodes that the clips move: `WeaponBolt` (the lever), `WeaponMagazine` (the shell that the
  hand puts in) and `WeaponExtra1` (the gate of the loading port). The gun is 48.6 units
  long. 4 materials and 12 textures, with the dyes of the default shader of Destiny.
* The sight part, `TheChaperoneSight.nif`: the glass between the two horns of the rear sight
  (two red rings) and the reticle (a dot with a red ring).
* 30 first-person clips in `behavior/thechaperone/animations/first_person/`: 21 from the
  Destiny clips (idle, sights, shot, shot in the sights, draw, put away, and 7 reload clips)
  and 9 with the weapon motion of the vanilla combat rifle clips (walk, run, jump, sprint,
  gun down).
* The left hand has the pose of a pose clip of The Chaperone (`fp_050_80BBD62D_add`) while
  it is on the gun: the thumb is on the left side of the barrel cover and the fingers are
  below it. With the clips of the shotgun class only, the hand was 1.0 cm from the gun.
* The reload puts in one shell at a time, and it ends with a turn of the gun around the
  lever. The behavior source has one line for each count of rounds in the gun
  (`when ammo == 5 play WPNReload1` to `when ammo == 0 play WPNReload6`), so the reload has
  as many shells as the gun has room for: 2.7 s for one shell, 7.2 s for six.
* 8 third-person clips in `behavior/thechaperone/animations/third_person/`: the same seven
  reload clips with the body of the player, and the hold pose (`WPNAssemblyPose`).
  `WPNReload` has no sound event there (`destiny/port/README.md`, "The third-person clips", says
  why).
* 6 clips in `behavior/thechaperone/animations/power_armor_third_person/`. They are copies
  of one vanilla clip of your game (the reload of the combat shotgun in power armor), with
  the names `WPNReload1` to `WPNReload6`. esx needs a file with each of these names for the
  view of the power armor.

**The Huckleberry.**

* One model, `Weapons\TheHuckleberry\TheHuckleberry.nif`, with 7 shapes (12286 vertices)
  and the nodes that the clips move: `WeaponBolt` (the housing of the barrel) and
  `WeaponMagazine` (the magazine). The gun is 43.4 units long. 5 materials and 15 textures.
* The sight part, `TheHuckleberrySight.nif`: the glass of the sight (a border of the color
  of gold and four green marks) and the reticle (a dot with a red ring).
* 27 first-person clips in `behavior/thehuckleberry/animations/first_person/`: 18 from the
  Destiny clips (idle, sights, shot, automatic fire, draw, put away, reload) and 9 with the
  weapon motion of the vanilla combat rifle clips.
* The left hand has the pose of a pose clip of The Huckleberry (`fp_090_80BC11A5_add`) while
  it is on the gun: it holds the magazine.
* 2 third-person clips: the reload of Destiny (91 frames) and the hold pose.

Each weapon has a behavior source (`behavior/NAME/NAME.bhv`) with its own prefix (`TXL`,
`TXC`, `TXH`). Each weapon gets its own animation keyword and graph copies, so no vanilla
weapon changes.

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

`./port destiny regress --only the_chaperone --only the_huckleberry --only the_last_word` makes
the clips of the three weapons again and compares their bytes with the clips of the project (30,
27 and 24 first-person clips; 8, 2 and 2 third-person clips).

`destiny/port/README.md` has the commands that make the files of `data/destiny/port/extract/`
("The Chaperone", "The third-person clips"). `meshes/`, `assets/` and the clips of the two new
guns are outputs of these commands. The files of The Last Word (`meshes/Weapons/TheLastWord`,
`assets/*/Weapons/TheLastWord` and `behavior/thelastword/animations`) were copied from
`mods/TheLastWord`. `esx.toml`, the three files of `items/` and the three `.bhv` files were
written by hand. `ids.lock` keeps the object ID of each record. The two files
`meshes/Weapons/NAME/NAMESight.template.nif` are the templates of the sight meshes: a vanilla
mesh with the names and the texture paths of the weapon, which gives the two effect shaders.

## Checks that passed

* `esx build`: 0 issues in the release check, 0 warnings.
* `esx plugin check-weapons build/release/TexMechanica.esp`: 0 findings for the three
  weapons.
* `esx scene weapon build/release/TexMechanica.esp NAME` for each weapon: each mesh,
  material and texture resolves from the two archives of the release. The Last Word has 0
  findings. The two other weapons have 2 findings each, which are notes: the renderer of esx
  does not draw the two effect materials of a sight.
* `esx render weapon build/release/TexMechanica.esp NAME --sheet`: the pictures
  `docs/TheLastWord.png`, `docs/TheChaperone.png` and `docs/TheHuckleberry.png`. Each shape
  has its texture.
* The numbers of each clip of the two new guns:
  `data/destiny/port/validation/the_chaperone/summary.txt` and
  `data/destiny/port/validation/the_huckleberry/summary.txt`. A vertex of the gun is at most
  0.012 units from its place in the source, and no finger joint bends to the back.
* The distance of each hand to the gun in each clip (`destiny/port/check/touch.py`):
  `data/destiny/port/validation/NAME/hand_distance.txt`. In the hold pose 5.2 percent of the
  vertices of the left hand are nearer than 0.5 cm to The Chaperone (0.0 percent before the pose
  clip), and 20.9 percent to The Huckleberry (12.4 percent before).
  `data/destiny/port/validation/NAME/left_hand_before_after.jpg` shows the hold pose in the game
  before and after.
* The game tests, each with the release that
  `data/destiny/port/validation/tex_mechanica/release_tested.sha` names (a test copy of the game,
  headless; `esx probe start --mod build/release`):
  * First person, `destiny/port/check/game_record.py`: The Chaperone 44 ops, The Huckleberry 40
    ops, The Last Word 44 ops, each with 0 failed ops. The game loads each weapon, its model and
    its graphs, and plays the draw, the idle, the shots (hip and sights), the reload, the gun
    down pose, the sprint pose and the put-away.
    `data/destiny/port/validation/the_chaperone/game_test.mp4`,
    `data/destiny/port/validation/the_huckleberry/game_test.mp4` and
    `data/destiny/port/validation/tex_mechanica/game_test_the_last_word.mp4`.
  * Third person, `destiny/port/check/game_third.py`: 94, 88 and 73 ops, each with 0 failed ops. The
    reload fills the gun. `data/destiny/port/validation/NAME/game_test_third_person.mp4`.
  * The 12 reloads of The Chaperone, `destiny/port/check/game_reloads.py`: one for each count of
    rounds from 0 to 5, in first person and in third person. Each one plays the clip of its
    count, fills the gun to 6 rounds, and starts one shell sound for each shell
    (`data/destiny/port/validation/the_chaperone/game_test_reloads.txt`).
  * The sights: the dot of the reticle is at the center of the screen in the sights, within
    1 pixel of 1280 x 720 (`data/destiny/port/validation/NAME/red_dot_game.jpg`).
  `destiny/port/README.md`, "The game test of the Tex Mechanica mod", has the list of what the tests
  prove.

## What is not proved

* The walk, run and jump clips in the game: the game tests had no move input.
* The mod in the installed game. The game tests used the test copy of esx; the release was
  not copied into the `Data` folder of the game.
* Power armor. The first-person clips are for the two bodies. In third person a body in
  power armor has the vanilla reload of the combat shotgun (The Chaperone, The Huckleberry)
  or of the .44 (The Last Word). I did not test a body in power armor.
* The reload of The Huckleberry against a picture of Destiny (`destiny/port/README.md`, "What is
  not proved").
* The look of the materials in other light than that of the test cell, and against a
  picture of the game Destiny.
* The workbench, and the sounds: they are the sounds of the vanilla combat shotgun, combat
  rifle and .44, and the shell sound of the vanilla double-barrel shotgun. The sound was not
  recorded.

## Limits

* The reload of The Chaperone with 6 shells is 7.2 s long: the clips have the speed of the
  files of Destiny. A `speed` line in `behavior/thechaperone/thechaperone.bhv` makes each
  reload faster.
* The shot of The Chaperone at the hip has no motion of the lever (the file of Destiny has
  none there). The shot in the sights has it.
* In third person I think that the lever of The Chaperone does not open in a reload with 1
  to 5 shells, and the shell does not show (`destiny/port/README.md`, "The third-person clips").
* The glass of the two sights shows at each time, also at the hip. The glass of The
  Huckleberry has half of the brightness of Destiny in the sights, with no tint and no
  mirror picture.
* The Huckleberry has no single shot mode: its receiver is the automatic receiver of the
  combat rifle.
* The recoil (the camera kick at each shot) is that of the vanilla record of each weapon.
* The guns have no parts for the workbench.
