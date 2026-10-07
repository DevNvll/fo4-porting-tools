# The mod projects

Each folder here is the source of one Fallout 4 mod, written as an esx project. `esx` builds
a mod's plugin and its two archives from the project folder.

| Mod | Weapons | Source of the weapons | Set files |
| --- | --- | --- | --- |
| `TheLastWord` | The Last Word (a revolver) | Destiny 2 | `destiny/port/sets/the_last_word.toml` |
| `Khvostov` | Khvostov 7G-02 (an auto rifle) | Destiny 2 | `destiny/port/sets/khvostov_7g_02.toml` |
| `Hammerhead` | Hammerhead (a machine gun) | Destiny 2 | `destiny/port/sets/hammerhead.toml` |
| `TexMechanica` | The Last Word, The Chaperone (a shotgun) and The Huckleberry (a submachine gun), in one plugin | Destiny 2 | `the_last_word.toml`, `the_chaperone.toml`, `the_huckleberry.toml` in `destiny/port/sets/` |
| `M77` | M77 (an assault rifle) | Marathon | `marathon/port/sets/m77_omnipositor.toml` |
| `PPK` | Walther PPK (a pistol) | Fallout: New Vegas | None. It has a conversion file instead, `mods/PPK/conversion.toml`. See `docs/porting/fnv.md`. |
| `FAMAS` | FAMAS F1 (a bullpup rifle) | Fallout: New Vegas | None. Its conversion file is `mods/FAMAS/conversion.toml`. |

`TheLastWord` and `TexMechanica` both have a weapon with the editor ID `TheLastWord`, so use
only one of them in a game.

The models, textures and animations are assets of the games and of the New Vegas mods that two of the ports come from. Do not publish a built
mod.

## What is in git, and what is in the data folder

`mods/NAME/` is in git. It holds only the files you write yourself, plus the two lock files
that esx writes.

| File | Content |
| --- | --- |
| `esx.toml` | The project's plugin name, author and description, and the scale of the model files. |
| `items/*.toml` | Each weapon's records: the vanilla weapon it copies, its values, its parts, its recipe. |
| `behavior/WEAPON/WEAPON.bhv` | Each weapon's behavior source: its animation keyword, its graph copies, and the reload clip for each round count. |
| `ids.lock` | The object ID of every record. esx writes it. It is in git so that every build gives the same IDs. |
| `behavior/WEAPON/WEAPON.lock` | The hash of each vanilla graph the behavior source was built against. esx writes it. |
| `conversion.toml` | New Vegas ports only (`PPK`, `FAMAS`). The conversion data for `./port fnv convert`. |
| `tests/*.toml` | New Vegas ports only. Plans for `esx probe`. They were not run in this repository. |
| `README.md` | What the mod has, how it was made, what is proved, what is not proved, the limits. |

`data/mods/NAME/` is not in git. It is the complete project that esx builds.

| Folder or file | Content | Made by |
| --- | --- | --- |
| a copy of every file in `mods/NAME/` | | `./port mod sync NAME` |
| `behavior/WEAPON/animations/first_person/`, `third_person/`, `power_armor_third_person/` | The clips (HKX). | `./port destiny convert` |
| `meshes/Weapons/WEAPON/` | The model files (`.glb`), their job files (`.mesh.toml`) and the template mesh of a sight. | `./port destiny model` |
| `assets/Textures/Weapons/WEAPON/`, `assets/Materials/Weapons/WEAPON/` | The textures (DDS) and the materials. | `./port destiny model` |
| `behavior/WEAPON/WEAPON.lock`, `build/` | The esx work files, and the release in `build/release/`. | `./port mod build NAME` |
| `docs/` | Pictures of each weapon. | `esx render weapon` |

No tool writes a generated file into `mods/`. Only `ids.lock` and
`behavior/WEAPON/WEAPON.lock` come back, and only when a build changed them.

## The commands

```sh
./port mod list                          # each mod, its plugin, and if it has a release
./port mod status NAME                   # the source files that differ from their copies in data/mods/NAME
./port mod sync NAME                     # copy the files of mods/NAME into data/mods/NAME (it deletes nothing)
./port mod build NAME [--update-lock]    # sync, esx build on data/mods/NAME, the lock files back to mods/NAME
```

A mod's release is in `data/mods/NAME/build/release/`. It is three files: the plugin
`NAME.esp`, `NAME - Main.ba2` and `NAME - Textures.ba2`. To use the mod, copy them into the
game's `Data` folder and enable the plugin. A build never writes into the game.

`baselines.sha256`, in the repository root and in git, records the sha256 of the release and
the clips of all 7 mods. Those are the releases that passed the game tests.
`./port baseline check` compares the files in `data/mods/` against it. A build replaces the
release, so run the check after every build of a tested mod. `DIFFERENT` means the build did
not give the tested bytes. Run `./port baseline update` only for a change the user accepted.
`mods/port.toml` has the file patterns.

To make a project's generated files again, use the commands in that mod's `README.md`. For
`Khvostov` they are:

```sh
GLB=data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
SET=destiny/port/sets/khvostov_7g_02.toml
M=data/mods/Khvostov
./port destiny convert $GLB --set $SET -o $M/behavior/khvostov/animations/first_person
./port destiny model $GLB --set $SET --mod Khvostov
./port destiny convert $GLB --set $SET third --third-output $M/behavior/khvostov/animations/third_person
./port mod build Khvostov --update-lock
```

These are the checks for a built mod. esx reads the release, and `FO4` is the game's `Data`
folder.

```sh
esx --data "$FO4" plugin check-weapons data/mods/NAME/build/release/NAME.esp
esx --data "$FO4" scene weapon data/mods/NAME/build/release/NAME.esp WEAPON
esx --data "$FO4" render weapon data/mods/NAME/build/release/NAME.esp WEAPON --sheet -o data/mods/NAME/docs/WEAPON.png
./port destiny regress --only WEAPON_NAME     # the clips of the project have the bytes that the converter gives
./port baseline check                         # the clips and the release have the bytes on record
./port destiny game session NAME LABEL        # the game test: docs/porting/game-test.md (--no-build for a release on record)
```

To make a reload faster or slower, put a `speed` line in the `reload` block of the behavior
source, such as `speed 1.5` or `speed reloadSpeedMult * 1.5`. The esx document
`docs/BEHAVIOR.md` describes it. No mod here has such a line, and no build or game test in
this repository used one.

## A new mod

1. Make the folder `mods/NAME/` with `esx.toml`, one file in `items/` per weapon and one
   behavior source per weapon. Start from a copy of the `mods/TexMechanica` files and change
   them. Step 8 of `docs/porting/destiny.md` shows how.
2. Make the clips and the model with the convert commands. They write into `data/mods/NAME/`.
3. Run `./port mod build NAME --update-lock`. It makes `ids.lock` and the release.
4. Add the weapon to `destiny/port/regress.toml`, with the clip folders of `data/mods/NAME/`
   as its baseline.
5. Write `mods/NAME/README.md`.
6. When the user accepts the mod, run `./port baseline update` and put `baselines.sha256`
   into git with the mod.

## What is not proved

* `./port mod build` ran in this repository for `TexMechanica`, `PPK` and `FAMAS`, and each
  release came out with the bytes it had before the move. It did not run for `TheLastWord`,
  `Khvostov`, `Hammerhead` and `M77`.
* One build of each of the 7 mods was compared. On 2026-10-06, esx at commit `d3e520c` built
  a copy of each `data/mods/NAME` in a scratch folder, without its `build/` folder. All 3
  release files of every mod had the bytes of `baselines.sha256`. So a build from nothing
  gives the tested release, and esx `d3e520c` gives the same bytes as the older esx
  `a996de8` that made the stored releases. No other esx version was compared, and neither
  was a build on a second computer.
* `./port destiny model` gives the same bytes as the files in `data/mods/` for 196 of the
  200 files in `meshes/` and `assets/` of the five projects. That run was on 2026-10-06, with
  scratch projects. The other 4 are the model files of The Chaperone and The Huckleberry in
  `data/mods/TexMechanica`, `NAME.glb` and `NAMESight.glb`. They were made before the pose
  clip of the left hand changed the hold pose. Every vertex is within 0.000012 units of its
  place in the new file, and every other value is the same.
