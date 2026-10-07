---
name: port-destiny-weapon
description: Gives the complete procedure to port a Destiny 2 weapon to Fallout 4 with the tools of this repository, from the extraction to the tested mod, and names the skill for each step. Use when the user asks to port a Destiny 2 weapon ("port the khvostov", "port hammerhead now", "port the Chaperone and the Huckleberry"), asks for a Fallout 4 mod of a Destiny gun, or asks to retarget the first-person animations of a Destiny weapon to the Fallout 4 rig. Do not use it for a weapon of Marathon (port-marathon-weapon) or for a New Vegas mod (port-fnv-animations).
---

# Port a Destiny 2 weapon to Fallout 4

This is the order of the work for one weapon. Each step has a gate. Do not start a step
before the gate of the step before it is true. Run each command in the root of the repository.

## When to use it, and when not

* Use it for a complete port: clips, model, mod project, checks, game test, documents.
* Only the files of the game: `extract-game-weapon`. One fault in a port: `diagnose-port-fault`.

## Before the start

1. Run `./port doctor`. The exit code must be 0. If not, load `set-up-workspace`.
2. Read the set file of the nearest weapon in `destiny/port/sets/`: `the_last_word.toml` (a
   hand cannon), `khvostov_7g_02.toml` (a rifle), `hammerhead.toml` (many parts),
   `the_chaperone.toml` (a shotgun), `the_huckleberry.toml` (parts in a second clip).
3. Tell the user early when the weapon is a new class. The tools have three templates
   (`revolver44`, `combatrifle`, `combatrifle_parts`). A bolt action or a bow needs
   programming. A gun can have 13 moving parts at most. Say how you read a short request.

```sh
E=data/destiny/port/extract/NAME        # NAME: the folder name that the extraction makes
G=$E/NAME_first_person.glb              # the first-person file
S=destiny/port/sets/NAME.toml           # the set file
W=data/destiny/port/work/NAME           # the work folder of the converter
A=data/mods/MOD/behavior/WEAPON/animations    # the clip folders in the esx project
```

## Steps

### 1. Extract the weapon

```sh
./port destiny find "TEXT"
./port destiny extract "ITEM" --arms "Ancient Apocalypse Grips" --out data/destiny/port/extract
./port destiny states $E/manifest.json -o $E/states.json
./port destiny dyes "ITEM" -o $E/dyes.json
./port destiny reticle "ITEM" -o $E/sight.json
./port destiny third $E/manifest.json
```

Gate: `manifest.json` and the first-person `.glb` are there. `states.json` has a clip for
`idle`, `ready`, `put_away`, `iron_sight_idle`, and for the reload or its three states. A state
with no clip gets its clip from `[synth]`: write it down. With more than one first-person file,
use the file of the rig entity that the row of the gun in the pattern entity names.

### 2. Examine the data, then write the first pass of the set file

Load `write-set-file`. It has the six points to examine and a script for the first one.

Gate: for each clip that you will use, you know three things. The gun is 0.000 m from the
grip bone, or the set file needs `[gun] rest = true`. You know which clip moves each part. You
know if the clip starts and ends in the hold pose. And the left hand has vertices nearer than
0.5 cm to the gun in the hold pose, or you have a pose clip (`fix-hand-pose`).

### 3. Convert the first-person clips

```sh
./port destiny convert $G --set $S bake parts
./port destiny convert $G --set $S retarget hkx install
```

Gate, from the output:

* `[parts]`: each shape is on the Fallout 4 bone that you expect, and the box of the gun has
  the size of the gun (The Chaperone is 48.6 units long, which is 69 cm).
* `[retarget]`: `wrist` and `weapon` are 0.00 units.
* `[hkx]`: `pos err` is below 0.02 units, and each reload has the events that you expect.
* Pictures of the hold pose (`validate-port`) show none of four defects: fingers through the
  gun, broken or deformed fingers, a wrong wrist rotation, a thumb that is not aligned.

A reload of more than one state, or parts that move in a second clip: `port-staged-reload`.

### 4. The sight, the model and the materials

```sh
./port destiny points $W/parts.json --poses $W/fo4/poses/SIGHTED_CLIP.npz
./port destiny model $G --set $S --mod MOD
```

For the eye that is not on the sight, a glass or a reticle, load `port-sight-and-reticle`. For
wrong colors or a shader, load `port-dyes-and-materials`. After a change of `[sight]`, run the
steps `retarget hkx install` again. Gate: only the clips in the sights changed.

### 5. The third-person clips

Load `port-third-person-clips`. Fallout 4 has a third-person reload and one hold pose for a
weapon. Each other third-person clip is a clip of the grip.

### 6. The mod project and the build

Copy the files of `mods/TexMechanica` to `mods/MOD` and change them: `esx.toml`, one file in
`items/` and one behavior source `behavior/WEAPON/WEAPON.bhv` for each weapon.
[references/mod-project.md](references/mod-project.md) has the rules that the five ports found.

```sh
./port destiny convert $G --set $S -o $A/first_person
./port mod build MOD --update-lock
ESX=$(./port paths get esx); FO4=$(./port paths get fo4_data)
"$ESX" --data "$FO4" plugin check-weapons data/mods/MOD/build/release/MOD.esp
"$ESX" --data "$FO4" scene weapon data/mods/MOD/build/release/MOD.esp WEAPON
```

Gate: the build has 0 issues and 0 warnings. `check-weapons` has 0 findings. `scene weapon`
has 0 findings, or 2 notes for the two effect materials of a sight. Write down the sha256 of
each release file that the build prints.

### 7. Validate

Load `validate-port`. Then add the weapon to `destiny/port/regress.toml`, with the clip
folders of `data/mods/MOD` as its baseline, and run `./port destiny regress`. Gate: each
earlier weapon has 0 different clips.

### 8. The game test, then the documents and the report

Only with the permission of the user: `game-test-port`. Then load `document-port`. Report a
finished request before the next one starts.

## Stop and ask the user

* Before the game starts.
* Before a change of a shared tool changes the bytes of an earlier weapon (`change-shared-tool`).
* When two pose clips fit and the measurements do not decide.
* When `./port destiny find` has no row: the weapon is not in this game build.

## Common faults

| Sign | Cause | What to do |
| --- | --- | --- |
| The numbers are good and the user sees a hand that does not touch the gun | A check against the source does not find a fault that the source has | `./port destiny check touch-table` for each new gun, and look at each hand in each game picture |
| In the sights, or now and then in the idle, the hands have the pose of the vanilla gun | The mod has no clip with a name that the graph asks for | A clip for each name of the graph ([references/mod-project.md](references/mod-project.md)) |
| Much time lost on a set file that does not work | The set file came before the examination of the data | Step 2 first |

## What to report

The result first. Then: what the mod has, each choice (the damage, the capacity, the state
of a glass, the pose clip), what is proved with its command, what is not proved, the limits,
the state of the computer after a game test, and that the assets must not be published.

## More

* [docs/porting/destiny.md](../../../docs/porting/destiny.md): the procedure and the lessons.
* [destiny/port/README.md](../../../destiny/port/README.md): each key, step, check and weapon.
* [docs/porting/overview.md](../../../docs/porting/overview.md),
  [docs/porting/lessons.md](../../../docs/porting/lessons.md).
