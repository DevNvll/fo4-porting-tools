# The Last Word for Fallout 4

This project packs The Last Word (the Destiny 2 hand cannon) as a Fallout 4 mod: the gun
model, its textures, the weapon records and 24 first-person clips. The clips are the
Destiny 2 first-person animations, retargeted to the Fallout 4 first-person rig by the tools
in `destiny/port/` (`d2fo4.py`).

```sh
./port mod build TheLastWord
```

The build makes `TheLastWord.esp` (a light plugin, 62 records), `TheLastWord - Main.ba2` and
`TheLastWord - Textures.ba2` in `data/mods/TheLastWord/build/release/`. To use the mod, copy
these three files into the `Data` folder of the game and enable the plugin. The build does not
write into the game.

This folder (`mods/TheLastWord/`, in git) has the files that a person writes: `esx.toml`,
`items/`, `behavior/thelastword/thelastword.bhv`, `ids.lock` and this file. The complete esx
project is `data/mods/TheLastWord/` (not in git): a copy of these files, and the files that the
tools make (`meshes/`, `assets/`, the clips of `behavior/thelastword/animations/`, `docs/`,
`build/`). `./port mod build TheLastWord` copies the files of this folder into the project and
runs `esx build` there. In this file, a path that starts with `build/`, `docs/`, `meshes/`,
`assets/` or `behavior/` is a path in `data/mods/TheLastWord/`, and an `esx` command with such a
path runs in that folder. Each other command runs in the root of the repository.
`mods/README.md` has the commands of each mod.

The model, the textures and the animations are assets of Destiny 2 (Bungie). Do not publish
this mod.

## What the mod has

* One weapon, `The Last Word` (editor ID `TheLastWord`), made from the vanilla .44 revolver.
  It fires .44 rounds and has a capacity of 8, as in Destiny 2 (the cylinder of the model has
  6 chambers). Damage, weight and value are those of the .44.
* One model, `Weapons\TheLastWord\TheLastWord.nif`, with 9 shapes (5998 vertices) and the
  nodes that the clips move: `WeaponMagazine` (the crane), `WeaponMagazineChild1` (the
  cylinder), `WeaponMagazineChild2` (the yoke), `WeaponMagazineChild5` (the rounds) and
  `WeaponExtra1` (the hammer). The gun has the size of the Destiny model: 34 units long.
* 4 materials and 12 textures from the 4 texture sets of the Destiny model.
* 24 first-person clips in `behavior/thelastword/animations/first_person/`: 16 from the
  Destiny clips (idle, sights, shot, shot in the sights, draw, put away, reload, sprint) and
  8 with the weapon motion of the vanilla .44 clips on the Destiny hold pose (walk, run,
  jump, gun down). `destiny/port/README.md` has the table.
* 2 third-person clips in `behavior/thelastword/animations/third_person/`: the reload of
  Destiny (`WPNReload`: the body of the player with the gun, 127 frames; it is the reload of
  a pistol, because The Last Word has no third-person reload of its own) and the hold pose
  (`WPNAssemblyPose`), which gives the place of the left hand on the gun in each
  third-person clip. `destiny/port/README.md`, "The third-person clips", says how they are made.
  Each other third-person clip is a vanilla clip of the pistol grip.
* A behavior source, `behavior/thelastword/thelastword.bhv`. The weapon gets its own
  animation keyword and graph copies, so no vanilla weapon changes.
* A chemistry station recipe for the weapon (4 steel, 1 gold, 1 spring, 2 screws).

## How the project was made

```sh
GLB=data/destiny/extract/handoff/the_last_word_v1/the_last_word_first_person.glb
SET=destiny/port/sets/the_last_word.toml
M=data/mods/TheLastWord
./port destiny convert $GLB --set $SET -o $M/behavior/thelastword/animations/first_person
./port destiny model $GLB --set $SET --mod TheLastWord
./port destiny convert $GLB --set $SET third --third-output $M/behavior/thelastword/animations/third_person
./port mod build TheLastWord --update-lock
```

`./port destiny regress --only the_last_word` makes the clips again and compares their bytes
with the clips of the project.

`meshes/`, `assets/` and the clips are outputs of the first three commands. `esx.toml`,
`items/10-thelastword.toml` and `behavior/thelastword/thelastword.bhv` were written by hand.
`ids.lock` keeps the object ID of each record.

## Checks that passed

* `esx build`: 0 issues in the release check, 0 warnings.
* `esx plugin check-weapons build/release/TheLastWord.esp`: 0 findings. With
  `--reference TheLastWord=44`, one warning: the mesh does not have the node
  `44MagnumReceiver` of the vanilla mesh. That node holds the static shapes of the vanilla
  gun, and here the node `TheLastWordReceiver` does that.
* `esx scene weapon build/release/TheLastWord.esp TheLastWord`: 0 findings. Each mesh,
  material and texture resolves from the two archives of the release.
* `esx render weapon build/release/TheLastWord.esp TheLastWord --sheet`: the picture
  `docs/weapon.png`. Each shape has its texture, and no shape is pink.
* The clips: `data/destiny/port/validation/the_last_word/` has a video of each clip with the source
  beside the result, and the numbers.
* The game test of the third-person reload:
  `data/destiny/port/validation/the_last_word/game_test_third_person.mp4` is a recording of the
  game with this release, and
  `data/destiny/port/validation/the_last_word/third_person_reload_game.jpg` has 12 pictures of
  it. The game starts the two third-person clips of this mod, the cylinder swings out and in,
  and the reload fills the gun (5 to 8 rounds). 94 ops, 0 failed.
* The game test: `data/destiny/port/validation/the_last_word/game_test.mp4` is a recording of
  the game with this release (`esx probe start --mod build/release`, a test copy of the game,
  headless). The game loads the weapon, its model and its graphs, and plays the draw, the idle,
  the shots (hip and sights), the reload, the gun down pose, the sprint pose and the put-away in
  first person, and a shot and a reload in third person. `destiny/port/README.md`, "The game
  test", has the list of what the test proves.

## What is not proved

* The walk, run and jump clips in the game: the game test had no move input.
  `build/test-plan.toml` is the game test plan of `esx probe plan` (give, draw, graph check,
  pictures); it was not run.
* The mod in the installed game. The game test used the test copy of esx; the release was
  not copied into the `Data` folder of the game.
* The look of the materials in other light than that of the test cell, and against a
  picture of the game Destiny. The textures now come from the gear shader of Destiny
  (`destiny/port/README.md`, "The dyes and the shaders of Destiny"). This gun has no pixel with a
  dye, and its dyes are locked in Destiny: a shader does not change it.
* The recording `game_test.mp4` is older than that change: the gun is a little lighter in it.
* Third person. Only the reload and the hold pose are from Destiny
  (`destiny/port/README.md`, "The third-person clips", has the list of what is not done). Each
  other third-person clip is a vanilla clip of the pistol grip. The recording `game_test.mp4`
  is older: it has the vanilla third-person reload.
* Power armor, the workbench, the sounds (they are the sounds of the vanilla .44).

## Limits

* The fire rate is that of the vanilla .44. The fire clip is 30 frames long.
* The put away clip has the 5 frames of Destiny and 8 more frames of its last pose. The graph
  removes the gun 0.233 s before the end of that clip, so a clip of 5 frames loses the gun
  before the hand moves.
* The recoil (the camera kick at each shot) is that of the vanilla .44 record.
* The gun has no parts for the workbench.
