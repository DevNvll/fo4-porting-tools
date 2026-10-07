# FAMAS F1 for Fallout 4

This project is a port of the New Vegas mod "FAMAS F1" (model by Raynox3D, textures by
Millenia, reload animation by Hitman47101) to Fallout 4.

```sh
./port mod build FAMAS
```

The build makes `FAMAS.esp`, `FAMAS - Main.ba2` and `FAMAS - Textures.ba2` in
`data/mods/FAMAS/build/release/`. To use the mod, copy these three files into the `Data`
folder of the game and enable the plugin. The build does not write into the game.

This folder (`mods/FAMAS/`, in git) has the files that a person writes: `esx.toml`, `items/`,
`behavior/famas/famas.bhv`, `conversion.toml`, `tests/`, the lock files and this file. The
complete esx project is `data/mods/FAMAS/` (not in git): a copy of these files, the extracted
mod (`source/`), and the files that the tools made (`meshes/`, `assets/`, the clips of
`behavior/famas/animations/first_person/`, `docs/`, `build/`). In this file, a path that
starts with `build/`, `docs/`, `meshes/`, `assets/`, `behavior/`, `source/` or `tests/` is a
path in `data/mods/FAMAS/`, and an `esx` command with such a path runs in that folder. Each
other command runs in the root of the repository. `mods/README.md` has the commands of each
mod.

The readme of the source mod says: "Do not edit or redistribute without explicit permission
from Raynox3D and Millenia." This port is for your own game. Get the permission before you
publish it.

## What the mod has

* One weapon, `FAMAS F1` (editor ID `FAMAS`), made from the vanilla submachine gun. It fires
  5.56 rounds from a magazine of 25.
* The receiver model, `Weapons\FAMAS\FAMASReceiver.nif`, with 10 shapes and 2 weapon bones
  (the charging lever and the magazine).
* Three attachments, each with its own mesh, recipe and loose mod:

  | Part | Slot | Made from | Effect |
  | --- | --- | --- | --- |
  | Suppressor | Muzzle (`ap_gun_Muzzle`) | the vanilla submachine gun suppressor | the vanilla suppressor values |
  | Short Scope | Sights (`ap_gun_Scope`) | the vanilla short scope of the combat rifle | the 4x scope overlay |
  | DBAL Laser | `ap_gun_Foregrip` | a part with no effect | the cone of fire from the hip is 30 percent smaller |

  Each slot has a default part with no model: No Muzzle, Standard Sights, No Laser.
* The textures of the source mod at 2048 pixels (the source has 4096), and 5 material files.
* 26 first-person clips in `behavior/famas/animations/first_person/`.
* A chemistry station recipe for the weapon.

## Where each clip comes from

The source mod has one first-person animation, the reload. Each other clip takes the motion
of the weapon bone from the vanilla submachine gun clip and applies it to the hold pose of
the gun. The hold pose is the first frame of the reload. The hands stay on the gun.

| Clip | Source |
| --- | --- |
| `WPNReload` | `2hareloads.kf` of the source mod, 91 frames |
| `WPNIdleReady`, `WPNIdleReadyA` to `D` | The hold pose, with no motion |
| `WPNIdleSighted` | The hold pose, moved so that the eye point of the sights (the node `##SightingNode` of the model) is on the view axis |
| `WPNFireSingleReady`, `A`, `B`, `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack`, `WPNEquip`, `WPNEquipFast`, `WPNUnEquip`, `WPNWalkForwardReady`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNSprint`, `WPNJumpImpactLand`, `WPNIdleGunDown` | The weapon motion of the vanilla clip on the hold pose |
| `WPNFireSingleSighted`, `WPNFireAutoSighted`, `WPNWalkForwardSighted` | The weapon motion of the vanilla clip on the sighted pose |

The tools take the events of the reload from the motion: magazine out at frame 22, magazine
in at frame 51, lever from frame 71 to frame 77. `reloadComplete` is at frame 53 and
`reloadEnd` is at frame 86, when the left hand is on the gun again.

## How the port was made

The folder `source` has the extracted mod. The tools of `fnv/` read it and
`conversion.toml`, and they write the 26 HKX clips into
`behavior/famas/animations/first_person`:

```sh
./port mod sync FAMAS                                   # copy the files of mods/FAMAS into data/mods/FAMAS
./port fnv convert data/mods/FAMAS/conversion.toml      # the 26 clips
./port mod build FAMAS                                  # esx build
```

The tools find the model, the animation, the gun parts, the clips and their events in
`source`, and `./port fnv convert data/mods/FAMAS/conversion.toml show` prints each value that
they assume. The converter evaluates the `.kf` file on the New Vegas skeleton, moves each
pose to the Fallout 4 first-person skeleton and writes the HKX clips. Do not publish `source`.

The tools make only the clips now. The model of this project (`meshes/`), its three
attachments and its textures (`assets/`) came from the tools at the git tag
`before-animation-only` (the history of `fnv/` has it), which had steps for them.
`conversion.toml` still has the tables of those steps.

### Hands

The two finger rules of the tools are on for this weapon (`[fingers] min_bend = 0.3` and
`skin_center = true`, the defaults).

The Fallout 4 hand mesh is modelled with bent fingers (about 45 and 30 degrees at the two
joints). The left thumb of the source is straight on the handguard, and a fully straight
Fallout 4 thumb has lumps at its joints. With the first rule, each joint keeps 30 percent of
its bend in the reference pose, about the hinge of its bone. The last thumb joint can bend
17 degrees back, as in the vanilla clips. The finger is an arch, and its fingertip stays on
its line, so it does not go into the gun.

With the second rule, the skin of each finger is at the skin of the source finger. The thumb
skin of the Fallout 4 hand is 0.5 units to the pad side of the source thumb when the bones
are at one place.

`docs/validation/left_thumb_least_bend.jpg` shows the left thumb of the hold pose with the
rules off and on.

`docs/validation/` has pictures from the camera of the game, each with the source above and
the built clip below, and the contact counts (`hand_contact.txt`). The programs that made
these pictures and counts are not in this repository.

The reload was made for a different FAMAS model, so the source hands are partly in this
model. In the source, the right thumb is 1.6 units inside the frame for the whole clip. The
result has 1.9 units at that place. No hand vertex is inside an attachment mesh at the
8 frames of the check.

## Tests in the game

In the folder `data/mods/FAMAS`:

```sh
esx probe run tests/first-person.toml --proton DIR --label famas -o build/test-first-person
esx probe run tests/parts.toml --proton DIR --label famas -o build/test-parts
```

* `tests/first-person.toml`: the draw, the graph, the reload at one fifth of the game speed
  with six pictures, single and automatic fire, aim, sheathe and third-person pictures.
* `tests/parts.toml`: each attachment alone and the three together, with the part and its
  keywords on the weapon, third-person and first-person pictures, the view through the scope
  and the reload with the three parts.

`docs/game-test/` has the pictures and the two reports.

## What is proved

* The game tests of 2026-10-05, before the move into this repository: 32 of 32 steps
  (`tests/first-person.toml`) and 55 of 55 (`tests/parts.toml`).
* In this repository, on 2026-10-06: the three release files have the sha256 values that
  they had before the move (`release_before_import.sha` in `data/mods/FAMAS/`).
* `./port fnv regress` converts the extracted mod again (the fixture `famas`) and compares
  the 26 clips with `data/fnv/out/famas`. Those clips have the same bytes as the clips of
  this project.

## What is not proved

* The game tests were not repeated in this repository.
* The model, the attachments and the textures cannot be made again with the tools of today.
* The DBAL uses the slot `ap_gun_Foregrip`. The probe cannot read the workbench menu, so the
  name of that slot and the recipes of the parts are not proved in the game.
* The muzzle flash with the suppressor is at the point `P-ProjectileNode` of the suppressor
  mesh. No test proves its place.
* The game test does not prove the look in power armor, held automatic fire or sound.

## Limits

* Only the reload has hand motion from the source. In each other clip the hands do not move
  on the gun: no trigger finger motion, and no hand that goes to the gun in the draw.
* The idle clips have no motion of their own. The graph adds its breathing layers.
* A bullpup gun ejects near the face, so each casing is in view for a moment at the right
  edge. The eject direction is that of the node `ShellCasingNode` of the model.
* The beam of the DBAL (the shape `Laser:0`) is not converted.
* The sounds are the sounds of the vanilla submachine gun. The four sound files of the source
  mod are not used.
* Third person, melee, grenade and mine clips are the vanilla submachine gun clips.
