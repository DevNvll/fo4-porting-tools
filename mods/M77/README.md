# The M77 of Marathon for Fallout 4

This project packs the M77 (the assault rifle of Marathon) as a Fallout 4 mod: the gun model,
its textures, the weapon records and 27 first-person clips. The clips are the first-person
animations of Marathon, retargeted to the Fallout 4 first-person rig by the tools in `destiny/port/`
(`d2fo4.py`, made for Destiny 2), and clips with the weapon motion of the vanilla combat
rifle for the states that have no clip of their own.

```sh
./port mod build M77
```

The build makes `M77.esp` (a light plugin, 294 records), `M77 - Main.ba2` and
`M77 - Textures.ba2` in `data/mods/M77/build/release/`. To use the mod, copy these three files
into the `Data` folder of the game and enable the plugin. The build does not write into the
game.

This folder (`mods/M77/`, in git) has the files that a person writes: `esx.toml`, `items/`,
`behavior/m77/m77.bhv`, `ids.lock` and this file. The complete esx project is `data/mods/M77/`
(not in git): a copy of these files, and the files that the tools make (`meshes/`, `assets/`,
the clips of `behavior/m77/animations/`, `docs/`, `build/`). `./port mod build M77` copies the
files of this folder into the project and runs `esx build` there. In this file, a path that
starts with `build/`, `docs/`, `meshes/`, `assets/` or `behavior/` is a path in
`data/mods/M77/`, and an `esx` command with such a path runs in that folder. Each other command
runs in the root of the repository. `mods/README.md` has the commands of each mod.

The model, the textures and the animations are assets of Marathon (Bungie). Do not publish
this mod.

## What the mod has

* One weapon, `M77 Assault Rifle` (editor ID `M77`), made from the vanilla combat rifle with
  its automatic receiver: the weapon fires automatically. It fires .45 rounds. Damage, weight
  and value are those of the combat rifle. The capacity is 30: a choice (the tools do not
  read the value of Marathon).
* One model, `Weapons\M77\M77.nif`, with 12 shapes (17,783 vertices) and the node that the
  clips move: `WeaponMagazine` (the magazine). It has the four pieces of the weapon of
  Marathon: the body, the muzzle device, the magazine and the sight unit (a rear sight with
  a box at its side, and a front sight). The gun has the size of the source model: 54.4 units
  long (77.7 cm).
* 7 materials and 21 textures (`marathon/README.md`, "The materials"). The body has
  the flat colors of Marathon: dark gray, red, and a yellow-green mark.
* 27 first-person clips in `behavior/m77/animations/first_person/`: 18 from the clips of
  Marathon (the idle, the sights, three shot clips at the hip and one in the sights, the
  automatic fire from these, the draw, the put-away, the reload) and 9 with the weapon
  motion of the vanilla combat rifle clips on a pose of Marathon (walk, run, jump, sprint,
  gun down). `destiny/port/README.md`, "The M77 of Marathon", has the table.
* A behavior source, `behavior/m77/m77.bhv`. The weapon gets its own animation keyword and
  graph copies, so no vanilla weapon changes.
* A chemistry station recipe for the weapon (8 steel, 4 aluminum, 2 springs, 3 screws).

The sights are iron sights in the mesh of the gun: the weapon has no sight part. Each
third-person clip is a vanilla clip of the combat rifle.

## How the project was made

```sh
./port marathon extract "M77 Omnipositor" --art "M77 Assault Rifle" \
    --hands data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
GLB=data/marathon/extract/out/m77_omnipositor/m77_omnipositor_first_person.glb
SET=marathon/port/sets/m77_omnipositor.toml
M=data/mods/M77
./port destiny convert $GLB --set $SET -o $M/behavior/m77/animations/first_person
./port destiny model $GLB --set $SET --mod M77
./port mod build M77 --update-lock
```

`./port destiny regress --only m77_omnipositor` makes the clips again and compares their bytes
with the clips of the project.

`marathon/README.md` has the extraction (the first command), and `marathon/port/README.md` has
the commands of the port.

## What is proved

* `esx build` passes with 0 issues and 0 warnings. `esx plugin check-weapons`,
  `esx scene weapon` and `esx render weapon` have no finding (`docs/weapon.png`).
* The game test (`data/destiny/port/validation/m77/game_test.mp4`, `game_test.log`): a headless
  test copy of the game with this release (`release_tested.sha`), in the cell `QASmoke`. 40
  steps, 0 failed. The game loads the plugin, gives and equips the weapon, and starts the graph
  `M77GunBehavior.hkb`. Two bursts use 16 of 30 rounds. The reload ends with the event
  `reloadEnd` and fills the gun (14 to 30 rounds, 100 to 84 in reserve). The weapon goes into
  the sights, fires there, goes down and up, sprints, is put away and drawn again. A second
  reload runs at one quarter of the speed. In third person the body holds the gun, fires and
  reloads.
* In the sights the top of the front post is at the center of the picture, between the two
  posts of the rear sight (`game_sights_center.jpg`).
* In the reload of the game the left hand takes the magazine out, puts a magazine in, and
  pulls the bolt handle with the index and the middle finger bent around it
  (`game_reload_frames.jpg`).
* The numbers of each clip are in `data/destiny/port/validation/m77/summary.txt`: the gun is at most
  0.0102 units from the source gun, and no finger joint bends back (the first joint of a
  thumb bends back 3.3 to 4.9 degrees in the reload and in the put-away).

## What is not correct or not done

* **The item.** The request was the `M77 Omnipositor`. That item has no art row of its own:
  the model is that of the weapon entity of the item `M77 Assault Rifle`. The two item
  definitions differ in one index and in three small values, and the tools do not read the
  table that the index points into. So the mod has the name and the look of the base M77.
* **The colors of three pieces.** The muzzle device, the magazine and the sight unit are
  gray. Their material has regions, and Marathon calculates the color of each region when
  the game runs. The files have only the color of the region 0, a gray that changes nothing.
* **No comparison with Marathon.** Marathon was not started, and no reference picture is
  here. "Correct" is from the game files.
* **The hands.** The tools have the measurements of the Destiny hand mesh
  (`destiny/port/rig/d2_hands.json`). Marathon has the same rig, with other bone lengths in the
  hand, and its hand mesh is not extracted. The set file has two rules for this
  (`knuckles = "align"`, `closed_fingers = true`). The source hand in the check pictures is the
  hand mesh of Destiny on the bones of Marathon.
* **The reload is the reload of an empty gun** (104 frames, with a pull of the bolt handle).
  Marathon has a shorter reload for a gun with rounds (72 frames). Fallout 4 gets one clip.
* **The bolt has no mesh.** The clips move the bone of the bolt, and the body of the gun is
  one rigid mesh in the files of Marathon.
* **Not in the model:** the decals of the body (text and marks: another render stage), the
  light of the rear sight (it is a red surface here), and the second magazine that Marathon
  shows in the left hand.
* **Third person.** The reload and each other third-person clip are those of the vanilla
  combat rifle. The left hand has the place of the combat rifle. No third-person clip of
  Marathon is extracted.
* **Sounds, damage, ammunition** are those of the combat rifle.
* The weapon was tested with the probe, not at the weapons workbench and not in the
  installed game.
