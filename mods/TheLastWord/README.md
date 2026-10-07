# The Last Word for Fallout 4

This project packs The Last Word, the Destiny 2 hand cannon, as a Fallout 4 mod. It has the
gun model, its textures, the weapon records and 24 first-person clips. 16 of them are the
Destiny 2 first-person animations, which the tools in `destiny/port/` (`d2fo4.py`) retarget
to the Fallout 4 first-person rig. The other 8 put vanilla weapon motion on the Destiny hold
pose.

```sh
./port mod build TheLastWord
```

The build writes three files to `data/mods/TheLastWord/build/release/`: `TheLastWord.esp`, a
light plugin with 62 records, `TheLastWord - Main.ba2` and `TheLastWord - Textures.ba2`. To
use the mod, copy them into the game's `Data` folder and enable the plugin. The build does
not write into the game.

This folder, `mods/TheLastWord/`, is in git and holds the hand-written files and the lock files that esx keeps: `esx.toml`,
`items/`, `behavior/thelastword/thelastword.bhv`, `ids.lock` and this file. The complete esx
project is `data/mods/TheLastWord/`, which is not in git. It has a copy of these files and
what the tools make: `meshes/`, `assets/`, the clips in `behavior/thelastword/animations/`,
`docs/` and `build/`. `./port mod build TheLastWord` copies this folder into the project and
runs `esx build` there.

In this file, a path that starts with `build/`, `docs/`, `meshes/`, `assets/` or `behavior/`
is inside `data/mods/TheLastWord/`, and an `esx` command with such a path runs in that
folder. Run every other command from the repository root. `mods/README.md` has the commands
for each mod.

The model, textures and animations are Destiny 2 assets and belong to Bungie. Do not publish
this mod.

## What the mod has

* One weapon, `The Last Word`, editor ID `TheLastWord`, made from the vanilla .44 revolver.
  It fires .44 rounds and has a capacity of 8, as in Destiny 2, although the model's cylinder
  has 6 chambers. Damage, weight and value are the .44's.
* One model, `Weapons\TheLastWord\TheLastWord.nif`, with 9 shapes and 5998 vertices. It has
  the nodes the clips move. `WeaponMagazine` is the crane, `WeaponMagazineChild1` the
  cylinder, `WeaponMagazineChild2` the yoke, `WeaponMagazineChild5` the rounds and
  `WeaponExtra1` the hammer. The gun keeps the size of the Destiny model, 34 units long.
* 4 materials and 12 textures from the 4 texture sets of the Destiny model.
* 24 first-person clips in `behavior/thelastword/animations/first_person/`. 16 come from the
  Destiny clips: idle, sights, shot, shot in the sights, draw, put away, reload and sprint.
  The other 8 put the weapon motion of the vanilla .44 clips on the Destiny hold pose: walk,
  run, jump and gun down. `destiny/port/README.md` has the table.
* 2 third-person clips in `behavior/thelastword/animations/third_person/`. `WPNReload` is the
  Destiny reload, the player's body with the gun, 127 frames. It is the reload of a pistol,
  because The Last Word has no third-person reload of its own. `WPNAssemblyPose` is the hold
  pose, which sets where the left hand is on the gun in every third-person clip. "The
  third-person clips" in `destiny/port/README.md` says how they are made. Every other
  third-person clip is a vanilla clip of the pistol grip.
* A behavior source, `behavior/thelastword/thelastword.bhv`. The weapon gets its own
  animation keyword and graph copies, so no vanilla weapon changes.
* A chemistry station recipe for the weapon: 4 steel, 1 gold, 1 spring, 2 screws.

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
with the project's clips.

The first three commands make `meshes/`, `assets/` and the clips. `esx.toml`,
`items/10-thelastword.toml` and `behavior/thelastword/thelastword.bhv` were written by hand.
`ids.lock` keeps the object ID of each record.

## Checks that passed

* `esx build` gives 0 issues in the release check and 0 warnings.
* `esx plugin check-weapons build/release/TheLastWord.esp` gives 0 findings. With
  `--reference TheLastWord=44` it gives one warning, that the mesh does not have the node
  `44MagnumReceiver` of the vanilla mesh. That node holds the static shapes of the vanilla
  gun. Here the node `TheLastWordReceiver` does that.
* `esx scene weapon build/release/TheLastWord.esp TheLastWord` gives 0 findings. Every mesh,
  material and texture resolves from the release's two archives.
* `esx render weapon build/release/TheLastWord.esp TheLastWord --sheet` made the picture
  `docs/weapon.png`. Every shape has its texture, and none is pink.
* `data/destiny/port/validation/the_last_word/` has a video of each clip with the source
  beside the result, and the numbers.
* The third-person reload passed its game test.
  `data/destiny/port/validation/the_last_word/game_test_third_person.mp4` is a recording of
  the game with this release, and
  `data/destiny/port/validation/the_last_word/third_person_reload_game.jpg` has 12 pictures
  of it. The game starts the mod's two third-person clips, the cylinder swings out and in,
  and the reload fills the gun from 5 to 8 rounds. 94 ops, 0 failed.
* `data/destiny/port/validation/the_last_word/game_test.mp4` is a recording of the game test
  with this release. It ran headless on a test copy of the game, with
  `esx probe start --mod build/release`. The game loads the weapon, its model and its graphs.
  In first person it plays the draw, the idle, the shots at the hip and in the sights, the
  reload, the gun down pose, the sprint pose and the put-away. In third person it plays a
  shot and a reload. "The game test" in `destiny/port/README.md` lists what the test proves.

## What is not proved

* The walk, run and jump clips in the game, because the game test had no move input.
  `build/test-plan.toml` is the game test plan that `esx probe plan` made, with give, draw,
  graph check and pictures. It was not run.
* The mod in the installed game. The game test used the esx test copy, and the release was
  not copied into the game's `Data` folder.
* The look of the materials in any light other than the test cell's, and against a picture
  from Destiny. The textures now come from the Destiny gear shader. See "The dyes and the
  shaders of Destiny" in `destiny/port/README.md`. This gun has no pixel with a dye and its
  dyes are locked in Destiny, so a shader does not change it.
* The recording `game_test.mp4` is older than that change, and the gun is a little lighter
  in it.
* Third person. Only the reload and the hold pose are from Destiny. "The third-person clips"
  in `destiny/port/README.md` lists what is not done. The recording `game_test.mp4` is older
  and has the vanilla third-person reload.
* Power armor, the workbench and the sounds, which come from the vanilla .44.

## Limits

* The fire rate is the vanilla .44's. The fire clip is 30 frames long.
* The put away clip has the 5 frames of Destiny and 8 more frames of its last pose. The graph
  removes the gun 0.233 s before the end of that clip, so a clip of 5 frames loses the gun
  before the hand moves.
* The recoil, the camera kick at each shot, comes from the vanilla .44 record.
* The gun has no parts for the workbench.
