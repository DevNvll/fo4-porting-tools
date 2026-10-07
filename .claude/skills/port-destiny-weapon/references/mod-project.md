# The mod project of a ported weapon: the rules that the ports found

Read this file when you write `mods/MOD/` for a new weapon, or when `esx build` stops.
[mods/README.md](../../../../mods/README.md) has the layout and the commands of a project.

## The files

`mods/MOD/` (in git) has only the files that a person writes. `data/mods/MOD/` (not in git) is
the project that esx builds. `./port mod build MOD` copies the first into the second.

| File | Content | Copy it from |
| --- | --- | --- |
| `esx.toml` | The plugin name, the author, the description, and `[meshes] scale = 1.0` (the model files are in game units). | `mods/TexMechanica/esx.toml` |
| `items/NN-WEAPON.toml` | The records of one weapon. `esx help-topic items` gives the keys. | `mods/TexMechanica/items/` |
| `behavior/WEAPON/WEAPON.bhv` | The behavior source of one weapon, with its own `prefix`. | `mods/TexMechanica/behavior/` |
| `ids.lock`, `behavior/WEAPON/WEAPON.lock` | esx writes them. They are in git so that a build gives the same IDs. | not copied: `--update-lock` makes them |
| `README.md` | What the mod has, the choices, what is proved, what is not proved, the limits. | the skill `document-port` |

One project can have more than one weapon. `TheLastWord` and `TexMechanica` have a weapon
with the same editor ID (`TheLastWord`): use one of the two in a game.

## The item file

| Rule | Example | Why |
| --- | --- | --- |
| The weapon is a copy of a vanilla weapon. | `from = "CombatRifle"`, `from = "44"` | The vanilla record gives the behavior graph, the ammunition, the sounds and the third-person clips of the grip. |
| A long gun uses the graphs of the combat shotgun. | `remove_keywords = ["AnimsCombatRifle"]`, and `like AnimsCombatShotgun` in the behavior source | The combat rifle has two animation keywords. `like AnimsCombatRifle` has no rules for power armor, and the build stops: "no matching subgraph rules for PowerArmorRace". |
| A copy of the vanilla .44 has no flag `Bolt Action`. | `flags = { "Bolt Action" = false }` | With the flag the game plays a hammer clip (`WPNBoltChargeReady`) after each shot, and esx warns `WEAPON_BOLT_ACTION`. |
| `reload_seconds` is the time of the event `reloadEnd` in `WPNReload`. It is not the length of the clip. | The Last Word: frame 102 of 127, 3.4. The Chaperone: frame 217 of 226, 7.2333. | The converter prints each event with its frame and its time (`[hkx]`). The time is the frame divided by 30. |
| A field with no key of its own. | `set = { 'FNAM\# Projectiles' = 1, 'DNAM\Attack Delay' = 0.857 }` | |
| The receiver part has the whole gun. | `[part.Receiver]` with `model = 'Weapons\NAME\NAME.nif'` | The model program makes one model with each moving part below the node of its weapon bone. |
| A sight with a glass is a second part. | `[part.Sight]` with `from = "mod_CombatRifle_Scope_SightsIron"` | esx makes no new effect shader (`port-sight-and-reticle`). |
| A shader of Destiny is one more receiver part. | `[part.ReceiverGoldenTrace]` | Fallout 4 has no dyes (`port-dyes-and-materials`). |
| The damage, the capacity and the time between two shots are choices. | "Capacity 30: this is my choice." | The tools do not read the values of Destiny. Write each one as a choice in the file and in the report. |

## The behavior source

```
mod TheChaperone {
  plugin "TexMechanica.esp"
  prefix TXC
}

weapon TheChaperone like AnimsCombatShotgun {
  reload {
    when ammo == 0 play WPNReload6
    when ammo == 5 play WPNReload1
  }
}
```

* The keyword after `like` is the vanilla animation keyword: `Anims44` for a copy of the .44,
  `AnimsCombatShotgun` for a long gun.
* The graphs of the mod get the prefix and the vanilla name: `TLWGunBehavior`,
  `KHVGunBehavior`, `TXCGunBehavior`. The game test looks for these names.
* A weapon with one reload clip needs no `reload` block.
* A faster or a slower reload: a line `speed 1.5` (or `speed reloadSpeedMult * 1.5`) in the
  `reload` block. The document of esx says that this line changes the playback speed of the
  reload clips (`docs/BEHAVIOR.md` of esx, "Mod sources"). No mod of this repository has such
  a line, and no test of this repository used it: build, then test in the game. No key of a
  set file changes the speed of a clip. Do not change `reload_seconds` to make a reload
  faster: it is the field `FNAM\Animation Reload Seconds` of the record, and what the game
  does with it at another speed is not verified.
* The first-person graph asks for clips by name. A clip that the mod does not have is the
  vanilla clip, with the hands of the vanilla gun. So give the mod a clip for each name:
  `WPNIdleReadyA` to `D`, `WPNIdleSightedWobble`, `WPNEquipFast`, `WPNFireSingleReadyA` and
  `B`. [the clip table](../../write-set-file/references/clips-and-templates.md) has each name.

## The checks of a built mod

```sh
ESX=$(./port paths get esx); FO4=$(./port paths get fo4_data); R=data/mods/MOD/build/release
./port mod build MOD --update-lock
"$ESX" --data "$FO4" plugin check-weapons $R/MOD.esp
"$ESX" --data "$FO4" scene weapon $R/MOD.esp WEAPON
"$ESX" --data "$FO4" render weapon $R/MOD.esp WEAPON --sheet -o data/mods/MOD/docs/WEAPON.png
```

| Check | Expected | It does not prove |
| --- | --- | --- |
| `./port mod build` | 0 issues, 0 warnings, and the sha256 of each release file | That a clip is correct |
| `./port baseline check` | `0 different`: each stored clip and each release has the bytes on record in `baselines.sha256` | That the bytes on record are correct |
| `plugin check-weapons` | 0 findings | The look in the light of the game |
| `scene weapon` | 0 findings, or 2 notes for the two effect materials of a sight | A glass |
| `render weapon` | A picture of the gun. `--overwrite` when the file is there. | A glass: `esx render` draws no effect material (the note `SCENE_NOT_DRAWN`). Only a game test shows it. |

## Faults of a build

| Sign | Cause | Correction |
| --- | --- | --- |
| The build stops: "no matching subgraph rules for PowerArmorRace" | `like AnimsCombatRifle` | `like AnimsCombatShotgun`, and `remove_keywords = ["AnimsCombatRifle"]` in the item file |
| The warning `WEAPON_BOLT_ACTION` | The flag of the vanilla .44 | `flags = { "Bolt Action" = false }` |
| `plugin check-weapons --reference` warns about `WeaponOptics1` and `WeaponOptics2` | The template of the converter has no such node | Add the two nodes to the template file |
| The build stops with `CLIP_MISSING`: no folder of `power_armor_third_person` has the clip | The two third-person views have one graph, and a clip with a new name must be there for the two | `[third.power_armor]` in the set file (`port-third-person-clips`) |
| The plugin of one build has other bytes than the builds after it | Seen one time: the first build after a change of a behavior source. The cause is not known. | Do the last tests after the last build. Compare the sha256 of the release before and after the tests. |
| `./port baseline check` prints `DIFFERENT` for a release file | A build replaced a release that was tested | Stop and tell the user. `./port baseline update` only for a change that the user accepted. |
| `./port mod sync` has the exit code 1 | `ids.lock` of `data/mods/MOD/` is different and newer | `./port mod build MOD --update-lock` keeps it and copies it back. `./port mod sync MOD --force` replaces it. |

A change of a comment in an item file gives the same release hashes. A build with another
esx version can give other bytes than a release that was tested before, so run
`./port baseline check` after each build of a tested mod. One comparison was made, on
2026-10-06: esx at the commit `d3e520c` built each of the 7 mods from nothing (a copy of the
project with no `build/` folder), and each release had the bytes of `baselines.sha256`. The
older esx (`a996de8`) made those stored releases.

The models, the textures and the animations of a built mod are assets of the game. Do not
publish a built mod.
