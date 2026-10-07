---
name: port-destiny-weapon
description: Gives the complete procedure to port a Destiny 2 weapon to Fallout 4 with the tools of this repository, from the extraction to the tested mod, and names the skill for each step. Use when the user asks to port a Destiny 2 weapon ("port the khvostov", "port hammerhead now", "port the Chaperone and the Huckleberry"), asks for a Fallout 4 mod of a Destiny gun, asks to retarget the first-person animations of a Destiny weapon to the Fallout 4 rig, or asks for a change of the item file or of the behavior source of a ported weapon ("make the reload faster"). Do not use it for a weapon of Marathon (port-marathon-weapon) or for a New Vegas mod (port-fnv-animations).
---

# Port a Destiny 2 weapon to Fallout 4

This is the order of the work for one weapon. The steps have the numbers of
[docs/porting/destiny.md](../../../docs/porting/destiny.md). Each step has a gate: do not start
a step before the gate of the step before it is true. Run each command in the root.

## When to use it, and when not

* Use it for a complete port. Only the files of the game: `extract-game-weapon`. One fault
  in a port: `diagnose-port-fault`.
* A faster reload, or a value of the weapon: [references/mod-project.md](references/mod-project.md).

```sh
E=data/destiny/port/extract/NAME        # NAME: the folder name that the extraction makes
G=$E/NAME_first_person.glb              # the first-person file
S=destiny/port/sets/NAME.toml           # the set file
W=data/destiny/port/work/NAME           # the work folder of the converter
A=data/mods/MOD/behavior/WEAPON/animations    # the clip folders in the esx project
```

## Steps

### 1. Prepare

Run `./port doctor destiny`. The exit code must be 0. If not, load `set-up-workspace`. Read
the set file of the nearest weapon in `destiny/port/sets/` (a hand cannon, a rifle, a machine
gun, a shotgun, a submachine gun). Say how you read a short request.

### 2. Extract the weapon

```sh
./port destiny find "TEXT"
./port destiny extract "ITEM" --arms "Ancient Apocalypse Grips" --out data/destiny/port/extract
./port destiny states $E/manifest.json -o $E/states.json
./port destiny dyes "ITEM" -o $E/dyes.json
./port destiny reticle "ITEM" -o $E/sight.json
./port destiny third $E/manifest.json
```

* `find` has no row (exit code 1): the weapon is not in this game build. Stop.
* `reticle` stops with "has no part in the stages transparent and reticle": no glass. No fault.
* `third` stops with "the graph has no state reload for this weapon": the reload is more than
  one state (a shotgun). Load `port-staged-reload`.
* More than one first-person file: `./port destiny notes weapon-tags $E/manifest.json` prints
  the rows of the pattern entity. Use the file of the rig entity that the row of the gun names.

Gate: `manifest.json` and the first-person `.glb` are there. `states.json` has a clip for
`idle`, `ready`, `put_away`, `iron_sight_idle`, and for the reload or its three states. A state
with no clip gets its clip from `[synth]`: write it down.

### 3. Examine the data

Load `write-set-file` and do its step 1 (six points) before you write the set file. Gate:
for each clip that you will use, you know four things. The gun is 0.000 m from the grip bone
(`./port destiny check gun-on-grip`), or the set file needs `[gun] rest = true`. You know
which clip moves each part. You know if the clip starts and ends in the hold pose. And the
left hand is on this gun in the hold pose, or you have a pose clip (`fix-hand-pose`). Some
vertices nearer than 0.5 cm are not sufficient (The Huckleberry: 12.4 percent, and the wrist
2.5 cm from its place): measure each pose clip candidate of the gun also.

### 4. Select the template

`write-set-file`, step 2: `revolver44`, `combatrifle` or `combatrifle_parts` (13 moving parts
at most). A bolt action or a bow needs a new template and programming: tell the user early.

### 5. Write the set file and convert the first-person clips

```sh
./port destiny convert $G --set $S bake parts
./port destiny convert $G --set $S retarget hkx install
```

Gate, from the output (a value that is not in its range: `diagnose-port-fault`):

* `[parts]`: each shape is on the Fallout 4 bone that you expect. The box has the size of the gun.
* `[retarget]`: `wrist` and `weapon` are 0.00 units. `[hkx]`: `pos err` is below 0.02 units,
  and each reload has the events that you expect.
* The finger check of each clip, before the first look at pictures (`validate-port`, step 2).
* Pictures of the hold pose (`validate-port`, step 4) show none of four defects: fingers
  through the gun, broken or deformed fingers, a wrong wrist rotation, a thumb that is not aligned.
* A reload of more than one state, or parts that move in a second clip: `port-staged-reload`.

### 6. The sight, the model and the materials

```sh
./port destiny points $W/parts.json --poses $W/fo4/poses/SIGHTED_CLIP.npz
./port destiny model $G --set $S --mod MOD
```

The eye is not on the sight, a glass or a reticle: `port-sight-and-reticle`. Wrong colors or a
shader: `port-dyes-and-materials`. After a change of `[sight]`, run `retarget hkx install`
again. Gate: only the clips in the sights changed.

### 7. The third-person clips

Load `port-third-person-clips`. Fallout 4 has a third-person reload and one hold pose for a
weapon. Each other third-person clip is a clip of the grip.

### 8. The mod project and the build

Copy `esx.toml`, one file of `items/` and one behavior source (`behavior/WEAPON/WEAPON.bhv`) of
`mods/TexMechanica` to `mods/MOD` and change them ([references/mod-project.md](references/mod-project.md)).

```sh
./port destiny convert $G --set $S -o $A/first_person
./port mod build MOD --update-lock
ESX=$(./port paths get esx); FO4=$(./port paths get fo4_data)
"$ESX" --data "$FO4" plugin check-weapons data/mods/MOD/build/release/MOD.esp
"$ESX" --data "$FO4" scene weapon data/mods/MOD/build/release/MOD.esp WEAPON
```

Gate: the build has 0 issues and 0 warnings. `check-weapons` has 0 findings. `scene weapon`
has 0 findings, or 2 notes for the two effect materials of a sight.

### 9. Validate before the game

Load `validate-port`: the bytes, the numbers of each clip, the distance of each hand to the
gun, the pictures. Add the weapon to `destiny/port/regress.toml` (its baseline: the clip
folders of `data/mods/MOD`). Run `./port destiny regress`, then `./port baseline check`. Gate:
each earlier weapon has 0 different clips, and no stored result is different.

### 10. The game test

Only with the permission of the user: `game-test-port`.

### 11. The documents and the report

Load `document-port`. When the user accepts the port, run `./port baseline update`: it puts
the new clips and the new release on record in `baselines.sha256`. Say that this file changed.

## Stop and ask the user

* Before the game starts. When `find` has no row. When two pose clips fit and the measurements
  do not decide. Before a change of a shared tool changes an earlier weapon (`change-shared-tool`).

## What to report

* The result first. What the mod has. Each choice (damage, capacity, a glass, the pose clip).
* What is proved, with its command. What is not proved, and the limits.
* The state of the computer after a game test. The assets must not be published.

## More

* [destiny/port/README.md](../../../destiny/port/README.md): each key, step, check and weapon.
* [docs/porting/troubleshooting.md](../../../docs/porting/troubleshooting.md), [docs/porting/lessons.md](../../../docs/porting/lessons.md).
