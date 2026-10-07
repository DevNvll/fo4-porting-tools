---
name: write-set-file
description: Gives the procedure to write or change a set file of the converter d2fo4 (destiny/port/sets/NAME.toml or marathon/port/sets/NAME.toml), with the examination of the data before the file, the two passes, the gate of each pass and the measurement that each rule needs as a comment. Use when the user or a port needs a new set file, a new key in a set file, the clip of a game state for a Fallout 4 clip, a rule such as [gun], [synth], [hold_end], [events] or [roles], or when the converter prints a wrist, weapon or pos err value that is not near zero.
---

# Write a set file

A set file tells the converter which clip of the first-person file is each Fallout 4 clip,
and it has the rules and the model data of one weapon. Measure first, then write the rule.
Each rule has the measurement that gave it as a comment above it.

## When to use it, and when not

* Use it for a new weapon, and for each change of a set file. A reload from more than one
  clip: load `port-staged-reload` also.
* `[sight]` and `[model.sight]`: `port-sight-and-reticle`. `[third]`: `port-third-person-clips`.
  `dyes` and `[model.shaders]`: `port-dyes-and-materials`. `[hand_pose]`, `knuckles`,
  `closed_fingers`: `fix-hand-pose`.
* A change of the converter itself is not a change of a set file: `change-shared-tool`.

## Before the start

The extraction of the weapon is there, with `manifest.json`, the first-person `.glb` and
`states.json` (`extract-game-weapon`). A file or a folder that a set file names is beside the
`.glb` file, not beside the set file.

```sh
E=data/destiny/port/extract/NAME ; G=$E/NAME_first_person.glb
S=destiny/port/sets/NAME.toml    ; W=data/destiny/port/work/NAME
```

For a weapon of Marathon: `E=data/marathon/extract/out/NAME` and `S=marathon/port/sets/NAME.toml`.

## Steps

### 1. Examine the data (six points)

1. **The clip of each state.** Read `$E/states.json`. Write the clip of each state into a
   table ([references/clips-and-templates.md](references/clips-and-templates.md) has the
   Fallout 4 clip of each state). The graph says which clip a weapon uses. The clip list of
   the file does not: most of its clips are clips of other weapons of the class.
2. **The gun is in the hand.** For each clip that you will use:

   ```sh
   python3 .claude/skills/write-set-file/scripts/gun_on_grip.py $E/manifest.json --clip CLIP --clip CLIP2
   ```

   A correct clip has the gun bone 0.000 m from the grip bone. With no `--clip` the script
   lists each full-pose clip of the file. A clip that fails needs `[gun] rest = true`. The
   node count alone does not find the fault for each gun, so measure each clip.
3. **The parts.** For each weapon bone: the count of its vertices (the lines `[parts]` of
   the step `parts`), and the clips in which it moves (`moving_weapon_bones` in `manifest.json`).
   A bone with no vertex needs no Fallout 4 bone. A bone name is not a part name.
4. **The clip that moves each part.** It can be the clip of the hands, an additive clip with
   the same frame count, or a clip of the gun entity (`weapon_NNN_TAG`).
5. **The two ends of each clip.** Compare the first and the last pose with the first frame
   of the idle. A clip that does not start or end in the hold pose is a part of a sequence.
6. **Pictures and the left hand.**

   ```sh
   ./port destiny video $G --clip CLIP --columns 8 --width 640 --out $W/probe/sheet.png
   ./port destiny pose $E/manifest.json --measure --hold CLIP:0
   ```

   Read the motion from the pictures. A hand that holds the gun has many vertices nearer
   than 0.5 cm. If the left hand has none, load `fix-hand-pose`.

Gate: for each clip you can answer the four questions of step 2 of `port-destiny-weapon`.

### 2. Select the template

`combatrifle` for a long gun (11 weapon bones), `combatrifle_parts` for a gun with more
moving parts (13 bones, all that the Fallout 4 skeleton has), `revolver44` for a hand cannon.
Gate: the template has a Fallout 4 bone for each moving part that has vertices. If no
template fits, stop and tell the user ([the templates](references/clips-and-templates.md)).

### 3. First pass

Copy the set file of the nearest weapon and change it. Write `template`, `hold`, `sighted`,
`[poses]`, `[roles]` or `[bones]`, `[clips]`, `[synth]`, `[static]`, `[hold_end]`, `[events]`,
and if the data needs them `[gun]`, `[auto]`, `part_rest`.
[references/keys.md](references/keys.md) has each key with the sign that asks for it.

```sh
./port destiny convert $G --set $S bake parts
./port destiny convert $G --set $S retarget hkx install
```

Gate, from the output:

| Line | Must be true |
| --- | --- |
| `[parts]` | Each shape is on the Fallout 4 bone that you expect. The box of the gun has the size of the gun. |
| `[retarget]` | `wrist` and `weapon` are 0.00 units. |
| `[hkx]` | `pos err` is below 0.02 units. Each reload has `reloadComplete` and `reloadEnd` at the frames that the pictures show. |
| each name of the graph | The set has a clip for it (the clip table). |

Then look at pictures of the hold pose and of one reload, the source beside the result
(`validate-port`).

### 4. Second pass

```sh
./port destiny points $W/parts.json --poses $W/fo4/poses/SIGHTED_CLIP.npz
```

It prints the size of the gun, the front of the barrel (for `muzzle`), the eye point of the
clip in the sights and a map of the sight. Write `[sight]`, `[model]`, `[model.sight]` and
`[third]` with the skills of the list above. After a change of `[sight]`, convert again.

### 5. The comments

Above each rule write the measurement that gave it: the frames, the distances, the counts.
Write the word "choice" where the data does not decide (a pose clip, the state of a glass, the
motion of the parts in third person). The set files of `destiny/port/sets/` are the model.

### 6. The regression

For a change of a set file of a ported weapon, run `./port destiny regress --only NAME`. Say
which clips are different and why. Gate: no other clip changed.

## Stop and ask the user

* Before a rule changes the clips of a weapon that passed its game test.
* When two candidates fit and the measurements do not decide.

## Common faults

| Sign | Cause | Rule |
| --- | --- | --- |
| The hands hold no gun in the pictures | The gun bone is at the origin of the world in that clip | `[gun] rest = true` |
| A state has no clip for this weapon | The graph has no entry for the tags of the weapon | `[synth]` |
| The sprint loop is one pose | The file has no motion there | `[synth]` with `pose = "sprint"` |
| The gun is out of the hand before the hand moves in the put-away | The graph removes the gun 0.233 s before the end of the clip | `[hold_end] WPNUnEquip = 8` for a clip of 4 or 5 frames |
| A weapon bone has a hash, not a name | The name is not in the word list | `[roles]` or `[bones]` |

[The troubleshooting table](../../../docs/porting/troubleshooting.md) and `diagnose-port-fault` have each sign.

## What to report

The table of the clips with the source of each one, each rule with its measurement, each choice,
the clips with vanilla weapon motion, the states with no clip, and the output lines of the gates.

## More

* [references/keys.md](references/keys.md): each key, with the sign and an example.
* [references/clips-and-templates.md](references/clips-and-templates.md): states, templates, events.
* [destiny/port/README.md](../../../destiny/port/README.md), "The keys of a set file".
* [docs/porting/destiny.md](../../../docs/porting/destiny.md),
  [docs/porting/marathon.md](../../../docs/porting/marathon.md).
