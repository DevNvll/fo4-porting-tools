# Walther PPK for Fallout 4

This project ports the New Vegas mod "FNV Anim Set - Walther PPK", its models and
first-person animations, to Fallout 4.

```sh
./port mod build PPK
```

The build writes three files to `data/mods/PPK/build/release/`: `PPK.esp`, `PPK - Main.ba2`
and `PPK - Textures.ba2`. To use the mod, copy them into the game's `Data` folder and enable
the plugin. The build does not write into the game.

This folder, `mods/PPK/`, is in git and holds the hand-written files: `esx.toml`, `items/`,
`behavior/ppk/ppk.bhv`, `conversion.toml`, `tests/`, the lock files and this file. The
complete esx project is `data/mods/PPK/`, which is not in git. It has a copy of these files,
the extracted mod in `source/`, and what the tools made: `meshes/`, `assets/`, the clips in
`behavior/ppk/animations/first_person/`, `docs/` and `build/`.

In this file, a path that starts with `build/`, `docs/`, `meshes/`, `assets/`, `behavior/`,
`source/` or `tests/` is inside `data/mods/PPK/`, and an `esx` command with such a path runs
in that folder. Run every other command from the repository root. `mods/README.md` has the
commands for each mod.

Read the permissions of the source mod and of its base mod before you publish this port.

## What the mod has

* One weapon, `Walther PPK`, editor ID `PPK`, made from the vanilla 10mm pistol. It fires
  .38 rounds from a magazine of 7.
* The receiver model, `Weapons\PPK\PPKReceiver.nif`, with 10 shapes and 6 weapon bones: the
  slide, the magazine, the cartridges, the trigger, the hammer and the safety.
* One attachment, the suppressor of the source mod, with a recipe and a loose mod. The
  muzzle slot has the default part No Muzzle.
* 27 first-person clips in `behavior/ppk/animations/first_person/`.
* A behavior source, `behavior/ppk/ppk.bhv`. It adds `WPNReloadEmpty`, the reload of the
  empty gun, to the vanilla pistol graph.
* A chemistry station recipe for the weapon.

## The textures are stand-in colors

The source mod's archive has no texture file. Its models use the textures of the base mod,
under `textures\tigerx87\weapons\ppk\...`, and the base mod was not available. So each
material has one color, from `[textures.stand_in]` in `conversion.toml`.

The tools that made the textures are at the git tag `before-animation-only`. With the base
mod's `textures` folder in `source/`, their textures step converts every file it finds.
Today's tools make only the clips, and they do not read that table.

## Where each clip comes from

| Clip | Source |
| --- | --- |
| `WPNIdleReady`, `WPNIdleReadyA` to `D` | `1hpaim.kf`, one pose |
| `WPNIdleSighted` | `1hpaimIS.kf`, moved so that the node `##SightingNode` is on the view axis |
| `WPNFireSingleReady`, `WPNFireSingleReadyB` | `1hpAttackRight.kf` |
| `WPNFireSingleReadyA` | `1hpattackright_a.kf` |
| `WPNFireSingleSighted` | `1hpattackrightis.kf`, with the move of the sighted pose |
| `WPNEquip`, `WPNEquipFast` | `1hpequip.kf` (76 frames) |
| `WPNUnEquip` | `1hpunequip.kf` |
| `WPNReload` | `1hpreload_partial.kf`, the reload with rounds in the magazine |
| `WPNReloadEmpty` | `1hpreloadL.kf`, the reload of the empty gun, with the slide back |
| `WPNWalkForwardReady`, `WPNWalkForwardSighted`, `WPNRunForwardReady`, `WPNRunLeftReady`, `WPNRunRightReady`, `WPNRunGunDown`, `WPNSprint`, `WPNJumpImpactLand`, `WPNIdleGunDown`, `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack`, `WPNFireAutoSighted` | The weapon motion of the vanilla 10mm pistol clip on the ready pose or the sighted pose |

New Vegas moves the camera to the sight node when the player aims. Fallout 4 has the sights
in the clip, so the tools move the aim pose until the node is on the view axis.

The tools take the events of the two reloads from the motion. The magazine is away from
frame 21 to frame 87, the slide of the empty gun is forward at frame 107, and the left hand
is back at frame 109, or frame 129 for the empty gun.

## What is not connected

The source set has more clips than the vanilla pistol graph has places for:

* the poses of the empty gun with the slide back (`PPK_EM`), and the last shot that locks the
  slide (`PPK_LS`). After the last shot the slide is closed, as in every vanilla pistol.
* the jam (`1hpjamL.kf`)
* the draw that puts the suppressor on (`PPK_SIL_7`, `PPK_SIL_9`), and the draw variants for
  each round count (`PPK_1` to `PPK_8`)
* the fire variants `PPK_FS`
* the set of the unique weapon (`PPK_UN`), the black finish, the extended magazine and the
  unique model

## How the port was made

The folder `source` has the extracted mod. The `fnv/` tools read it and `conversion.toml`,
and write the 27 HKX clips into `behavior/ppk/animations/first_person`:

```sh
./port mod sync PPK                                   # copy the files of mods/PPK into data/mods/PPK
./port fnv convert data/mods/PPK/conversion.toml      # the 27 clips
./port mod build PPK                                  # esx build
```

The tools find the model, the animations, the gun parts, the clips and their events in
`source`. `./port fnv convert data/mods/PPK/conversion.toml show` prints every value they
assume. Do not publish `source`.

The tools make only the clips now. The model in `meshes/`, its suppressor and the textures in
`assets/` came from the tools at the git tag `before-animation-only`, which had steps for
them. The history of `fnv/` has that tag. `conversion.toml` still has the tables of those
steps.

The template is `pistol10mm`, the vanilla 10mm pistol. It gives the records, the graph
(`like AnimsFP10mm`), the sounds, the third-person clips and the rest place of each weapon
bone. The vanilla Deliverer is a PPK, but its animation graph does not become active in the
test game of `esx probe`. That was with the vanilla record and no mod. So no game test can
prove a port on it.

Both finger rules of the tools are on: `[fingers] min_bend = 0.3` and `skin_center = true`,
the defaults. No finger joint bends to the back of the finger, and the skin of each finger is
at the skin of the source finger. Without them the right thumb was 0.7 units in front of its
place on the grip at frame 88 of the reload, and its first joint was bent 12 degrees back.

## Checks

`docs/validation/` has pictures from the game's camera, each with the source above and the
built clip below, and the contact counts in `hand_contact.txt`. In the source, 1 to 6 percent
of the hand skin vertices are inside the gun, 0.18 to 0.62 units deep. In the result, 0.3 to
1.7 percent are inside, 0.09 to 0.41 units deep. The programs that made these pictures and
counts are not in this repository.

The game tests run in the folder `data/mods/PPK`:

```sh
esx probe run tests/first-person.toml --proton DIR --label ppk -o build/test-first-person
esx probe run tests/parts.toml --proton DIR --label ppk -o build/test-parts
```

`docs/game-test/` has the pictures and the reports of the two plans. `tests/draw-only.toml`
is a short plan. It gives the weapon, draws it and takes one picture, to show whether the
weapon's animation graph becomes active.

## What is proved

* The game tests of 2026-10-05, before the move into this repository, passed 34 of 34 steps
  of `tests/first-person.toml` and 27 of 27 of `tests/parts.toml`, the suppressor plan.
* In this repository, on 2026-10-06, `./port mod sync PPK`,
  `./port fnv convert data/mods/PPK/conversion.toml` and `./port mod build PPK` ran. The 27
  clips have the same bytes as before, and the three release files have the sha256 values
  they had before the move. Those values are in `release_before_import.sha` in
  `data/mods/PPK/`.
* `./port fnv regress` converts the extracted mod again, as the fixture `ppk`, and compares
  the 27 clips with `data/fnv/out/ppk`. Those clips have the same bytes as this project's
  clips.

## What is not proved

* The game tests were not repeated in this repository.
* Today's tools cannot make the model, the suppressor or the textures again.
* The probe cannot read the workbench menu, so the recipe of the suppressor is not proved in
  the game.
* The game test does not prove the look in power armor or sound.

## Limits

* The textures are stand-in colors.
* The sounds are those of the vanilla 10mm pistol. The 35 sound files of the source mod are
  not used.
* The draw of the source is 2.5 s long. The two draw clips use it.
* The jump clip uses the weapon motion of the vanilla clip, which goes below the view. The
  arms cannot reach that far, so the tools move the shoulders by 10 units in that clip. The
  gun is out of view at that time.
* Third person, melee, grenade and mine clips are the vanilla 10mm pistol clips. The PPK is
  smaller than the 10mm pistol.
