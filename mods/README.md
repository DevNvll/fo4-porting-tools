# The mod projects

Each folder here is the source of one Fallout 4 mod, as an esx project. `esx` builds the
plugin and the two archives of a mod from a project folder.

| Mod | Weapons | Source of the weapons | Set files |
| --- | --- | --- | --- |
| `TheLastWord` | The Last Word (a revolver) | Destiny 2 | `destiny/port/sets/the_last_word.toml` |
| `Khvostov` | Khvostov 7G-02 (an auto rifle) | Destiny 2 | `destiny/port/sets/khvostov_7g_02.toml` |
| `Hammerhead` | Hammerhead (a machine gun) | Destiny 2 | `destiny/port/sets/hammerhead.toml` |
| `TexMechanica` | The Last Word, The Chaperone (a shotgun), The Huckleberry (a submachine gun), in one plugin | Destiny 2 | `the_last_word.toml`, `the_chaperone.toml`, `the_huckleberry.toml` in `destiny/port/sets/` |
| `M77` | M77 (an assault rifle) | Marathon | `marathon/port/sets/m77_omnipositor.toml` |

`TheLastWord` and `TexMechanica` have a weapon with the same editor ID (`TheLastWord`). Use
one of the two in a game.

The models, the textures and the animations are assets of the games (Bungie). Do not
publish a built mod.

## What is in git, and what is in the data folder

`mods/NAME/` (in git) has only the files that a person writes:

| File | Content |
| --- | --- |
| `esx.toml` | The project: the plugin name, the author, the description, and the scale of the model files. |
| `items/*.toml` | The records of each weapon: the vanilla weapon that it copies, its values, its parts, its recipe. |
| `behavior/WEAPON/WEAPON.bhv` | The behavior source of each weapon: its animation keyword, its graph copies, the reload clip of each count of rounds. |
| `ids.lock` | The object ID of each record. esx writes it; it is in git so that a build gives the same IDs. |
| `README.md` | What the mod has, how it was made, what is proved, what is not proved, the limits. |

`data/mods/NAME/` (not in git) is the complete project that esx builds:

| Folder or file | Content | Made by |
| --- | --- | --- |
| a copy of each file of `mods/NAME/` | | `./port mod sync NAME` |
| `behavior/WEAPON/animations/first_person/`, `third_person/`, `power_armor_third_person/` | The clips (HKX). | `./port destiny convert` |
| `meshes/Weapons/WEAPON/` | The model files (`.glb`), their job files (`.mesh.toml`) and the template mesh of a sight. | `./port destiny model` |
| `assets/Textures/Weapons/WEAPON/`, `assets/Materials/Weapons/WEAPON/` | The textures (DDS) and the materials. | `./port destiny model` |
| `behavior/WEAPON/WEAPON.lock`, `build/` | The work files of esx, and the release in `build/release/`. | `./port mod build NAME` |
| `docs/` | Pictures of each weapon. | `esx render weapon` |

A tool does not write a generated file into `mods/`. The only file that comes back is
`ids.lock`, when a build changed it.

## The commands

```sh
./port mod list                          # each mod, its plugin, and if it has a release
./port mod status NAME                   # the source files that differ from their copies in data/mods/NAME
./port mod sync NAME                     # copy the files of mods/NAME into data/mods/NAME (it deletes nothing)
./port mod build NAME [--update-lock]    # sync, esx build on data/mods/NAME, ids.lock back to mods/NAME
```

The release of a mod is `data/mods/NAME/build/release/`: the plugin (`NAME.esp`),
`NAME - Main.ba2` and `NAME - Textures.ba2`. To use the mod, copy these three files into the
`Data` folder of the game and enable the plugin. A build does not write into the game.

To make the generated files of a project again (the example is `Khvostov`; the `README.md`
of each mod has its commands):

```sh
GLB=data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
SET=destiny/port/sets/khvostov_7g_02.toml
M=data/mods/Khvostov
./port destiny convert $GLB --set $SET -o $M/behavior/khvostov/animations/first_person
./port destiny model $GLB --set $SET --mod Khvostov
./port destiny convert $GLB --set $SET third --third-output $M/behavior/khvostov/animations/third_person
./port mod build Khvostov --update-lock
```

The checks of a built mod (esx reads the release; `FO4` is the `Data` folder of the game):

```sh
esx --data "$FO4" plugin check-weapons data/mods/NAME/build/release/NAME.esp
esx --data "$FO4" scene weapon data/mods/NAME/build/release/NAME.esp WEAPON
esx --data "$FO4" render weapon data/mods/NAME/build/release/NAME.esp WEAPON --sheet -o data/mods/NAME/docs/WEAPON.png
./port destiny regress --only WEAPON_NAME     # the clips of the project have the bytes that the converter gives
./port destiny game session NAME LABEL        # the game test: destiny/port/README.md, "The game test"
```

## A new mod

1. Make the folder `mods/NAME/` with `esx.toml`, one file in `items/` for each weapon and one
   behavior source for each weapon. Copy the files of `mods/TexMechanica` and change them
   (`destiny/port/PORTING.md`, "The mod project").
2. Make the clips and the model with the convert commands. They write into `data/mods/NAME/`.
3. `./port mod build NAME --update-lock` makes `ids.lock` and the release.
4. Add the weapon to `destiny/port/regress.toml`, with the clip folders of `data/mods/NAME/`
   as its baseline.
5. Write `mods/NAME/README.md`.

## What is not proved

* The files of `mods/NAME/` are copies of the hand-written files of the five projects. The
  port of the tools to this repository did not run `./port mod build` for them.
* The model program (`./port destiny model`) gives the same bytes as the files of
  `data/mods/` for 196 of the 200 files of `meshes/` and `assets/` of the five projects (run of
  2026-10-06, with scratch projects). The 4 other files are the model files of The Chaperone
  and of The Huckleberry in `data/mods/TexMechanica` (`NAME.glb`, `NAMESight.glb`): they were
  made before the pose clip of the left hand changed the hold pose. Each vertex is at most
  0.000012 units from its place in the new file, and each other value is the same.
