# The M77 of Marathon for Fallout 4

This project packs the M77, the Marathon assault rifle, as a Fallout 4 mod. It has the gun
model, its textures, the weapon records and 27 first-person clips. Some clips are the
Marathon first-person animations, which the tools in `destiny/port/` retarget to the
Fallout 4 first-person rig. Those tools, `d2fo4.py`, were made for Destiny 2. Where a state
has no clip of its own, the clip has the weapon motion of the vanilla combat rifle.

```sh
./port mod build M77
```

The build writes three files to `data/mods/M77/build/release/`: `M77.esp`, a light plugin
with 294 records, `M77 - Main.ba2` and `M77 - Textures.ba2`. To use the mod, copy them into
the game's `Data` folder and enable the plugin. The build does not write into the game.

This folder, `mods/M77/`, is in git and holds the hand-written files and the lock files that esx keeps: `esx.toml`, `items/`,
`behavior/m77/m77.bhv`, `ids.lock` and this file. The complete esx project is
`data/mods/M77/`, which is not in git. It has a copy of these files and what the tools make:
`meshes/`, `assets/`, the clips in `behavior/m77/animations/`, `docs/` and `build/`.
`./port mod build M77` copies this folder into the project and runs `esx build` there.

In this file, a path that starts with `build/`, `docs/`, `meshes/`, `assets/` or `behavior/`
is inside `data/mods/M77/`, and an `esx` command with such a path runs in that folder. Run
every other command from the repository root. `mods/README.md` has the commands for each
mod.

The model, textures and animations are Marathon assets and belong to Bungie. Do not publish
this mod.

## What the mod has

* One weapon, `M77 Assault Rifle`, editor ID `M77`, made from the vanilla combat rifle with
  its automatic receiver, so it fires automatically. It fires .45 rounds. Damage, weight and
  value are the combat rifle's. The capacity of 30 is a choice, because the tools do not read
  the Marathon value.
* One model, `Weapons\M77\M77.nif`, with 12 shapes and 17,783 vertices. The clips move one
  node, `WeaponMagazine`, the magazine. The model has the four pieces of the Marathon weapon:
  the body, the muzzle device, the magazine and the sight unit. The sight unit is a rear
  sight with a box at its side, and a front sight. The gun keeps the size of the source
  model, 54.4 units long, which is 77.7 cm.
* 7 materials and 21 textures. See "The materials" in `marathon/extract/README.md`. The body has the
  flat colors of Marathon: dark gray, red, and a yellow-green mark.
* 27 first-person clips in `behavior/m77/animations/first_person/`. 18 come from the Marathon
  clips: the idle, the sights, three shot clips at the hip and one in the sights, the
  automatic fire made from these, the draw, the put-away and the reload. The other 9 put the
  weapon motion of the vanilla combat rifle clips on a Marathon pose: walk, run, jump, sprint
  and gun down. "The M77 of Marathon" in `destiny/port/README.md` has the table.
* A behavior source, `behavior/m77/m77.bhv`. The weapon gets its own animation keyword and
  graph copies, so no vanilla weapon changes.
* A chemistry station recipe for the weapon: 8 steel, 4 aluminum, 2 springs, 3 screws.

The sights are iron sights in the mesh of the gun, so the weapon has no sight part. Every
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

`./port destiny regress --only m77_omnipositor` makes the clips again and compares their
bytes with the project's clips.

The first command is the extraction, which `marathon/README.md` describes.
`marathon/port/README.md` has the commands of the port.

## What is proved

* `esx build` passes with 0 issues and 0 warnings. `esx plugin check-weapons`,
  `esx scene weapon` and `esx render weapon` have no finding. The picture is
  `docs/weapon.png`.
* The game test ran on a headless test copy of the game, in the cell `QASmoke`, with the
  release that `release_tested.sha` names. Its recording and log are
  `data/destiny/port/validation/m77/game_test.mp4` and `game_test.log`. 40 ops, 0 failed. The
  game loads the plugin, gives and equips the weapon, and starts the graph
  `M77GunBehavior.hkb`. Two bursts use 16 of 30 rounds. The reload ends with the event
  `reloadEnd` and fills the gun from 14 to 30 rounds, while the reserve goes from 100 to 84.
  The weapon goes into the sights, fires there, goes down and up, sprints, is put away and
  drawn again. A second reload runs at one quarter of the speed. In third person the body
  holds the gun, fires and reloads.
* In the sights the top of the front post is at the center of the picture, between the two
  posts of the rear sight. See `game_sights_center.jpg`.
* In the game's reload the left hand takes the magazine out, puts a magazine in, and pulls
  the bolt handle with the index and the middle finger bent around it. See
  `game_reload_frames.jpg`.
* The numbers for each clip are in `data/destiny/port/validation/m77/summary.txt`. The gun is
  at most 0.0102 units from the source gun, and no finger joint bends back but one. The first
  joint of a thumb bends back 3.3 to 4.9 degrees in the reload and in the put-away.

## What is not correct or not done

* The request was the `M77 Omnipositor`. That item has no art row of its own, so the model
  comes from the gun entity of the item `M77 Assault Rifle`. The two item definitions differ
  in one index and in three small values, and the tools do not read the table the index
  points into. So the mod has the name and the look of the base M77.
* The muzzle device, the magazine and the sight unit are gray. Their material has regions,
  and Marathon calculates the color of each region when the game runs. The files have only
  the color of the region 0, a gray that changes nothing.
* Nothing was compared with Marathon. The game was not started, and no reference picture is
  here. "Correct" is from the game files.
* The tools have the measurements of the Destiny hand mesh, in
  `destiny/port/rig/d2_hands.json`. Marathon has the same rig with other bone lengths in the
  hand, and its hand mesh is not extracted. The set file has two rules for this,
  `knuckles = "align"` and `closed_fingers = true`. The source hand in the check pictures is
  the Destiny hand mesh on the Marathon bones.
* The reload is the reload of an empty gun, 104 frames with a pull of the bolt handle.
  Marathon has a shorter reload of 72 frames for a gun with rounds. Fallout 4 gets one clip.
* The bolt has no mesh. The clips move the bone of the bolt, but the body of the gun is one
  rigid mesh in the Marathon files.
* Three things are not in the model. The decals of the body, its text and marks, are another
  render stage. The light of the rear sight is a red surface here. The second magazine that
  Marathon shows in the left hand is not there.
* In third person, the reload and every other clip come from the vanilla combat rifle. The
  left hand has the place of the combat rifle. No third-person clip of Marathon is extracted.
* Sounds, damage and ammunition come from the combat rifle.
* The weapon was tested with the probe, not at the weapons workbench and not in the
  installed game.
