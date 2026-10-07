---
name: diagnose-port-fault
description: Gives the procedure to go from the sign of a fault in a ported weapon to its cause and to the rule that corrects it, with a table of each known sign of the Destiny 2, Marathon and New Vegas ports. Use when the user or a check reports a fault, for example "the hands seems far from the model, not touching it", "the fingers are clipping through", "why are these fingers broken", "finger looks dislocated on this one frame", "the gun is disassembled floating", the gun is not in the hand, a part does not move, a sound plays at the wrong time, the reload ends early, the reticle is too large, the gun is light gray, or a build or a probe op fails.
---

# From the sign of a fault to its cause and its rule

Do not correct a fault before you know its cause. Prove the cause with a number from the
data, then correct the rule, then prove that no other weapon changed.

## When to use it, and when not

* Use it for each fault that the user or a check reports in a port.
* The sign is in [references/signs.md](references/signs.md) with its rule: go to the skill
  that the row names. This skill is then only the frame of the work.
* A fault of a hand or of a finger: this skill finds the stage, and `fix-hand-pose` has the
  correction.

## Steps

### 1. Write the sign in the words of the user

Quote the message. If a word is not clear, say how you read it, and ask. Find the build and
the frame of the picture: the name of the file, the time, the test report. An old picture
can show a fault that is already corrected, and a chat can show the old picture of a file
that was made again with the same name.

Gate: you can name the weapon, the clip, the frame, the view (first or third person) and the
picture.

### 2. Look for the sign in the table

[references/signs.md](references/signs.md) has each known sign with its cause and its rule.
[docs/porting/troubleshooting.md](../../../docs/porting/troubleshooting.md) is the table for a
person. If the sign is there, do the rule and go to step 6.

### 3. Find the stage of the fault

Compare the result with the source in one picture, with one camera
(`./port destiny check render`, `validate-port`). Then:

| What the pictures show | Where the fault is | What to look for |
| --- | --- | --- |
| The source has the fault also | The data of the source game, or the extraction | A pose clip, a second clip for the parts, another render stage, a clip of another rig. For a preview picture: a bone with no keys (`./port destiny check-glb`). |
| The source is correct and the Blender result is wrong | The retarget, or a rule of the set file | The lines `[retarget]` and `[hkx]`, the finger check, the rule that changed last |
| The Blender result is correct and the game is wrong | A rule of the game | Compare with the vanilla weapon in the same session. Read the trace. Then read the graph. |

For a game picture, make the same view in Blender from the game camera (`--views fp`) and
put it beside the game picture. If the two agree, the game plays the clip data exactly, and
the fault is in the clip.

To learn a rule of a graph of Fallout 4 (`esx` is the program of the setting `esx`:
`./port paths get esx`; `FILE` is a graph of the build, for example
`data/mods/MOD/build/behavior/Meshes/Actors/Character/_1stPerson/Behaviors/PREFIXGunBehavior.hkx`):

```sh
esx behavior explain reload --like KEYWORD
esx hkx events FILE --event NAME
esx hkx show FILE --selector 'object(N)'
./port destiny game trace --session ID --weapon EDITORID --loaded N --view first
```

`game trace` needs a game session (`game-test-port`, with the permission of the user). It did
not run in this repository yet.

### 4. Measure the property that is wrong

Use the check that measures the property that the user sees. If no check measures it, write
one, in `destiny/port/check/` with a command in `port.toml` (`change-shared-tool`).

```sh
G=data/destiny/port/extract/NAME/NAME_first_person.glb
W=data/destiny/port/work/NAME ; C=data/mods/MOD/behavior/WEAPON/animations/first_person
./port destiny check touch --glb $G --bake $W/bake/CLIP.npz --poses $C/WPNIdleReady.hkx --parts $W/parts.json --frames 0
./port destiny check fingers $C/WPNReload.hkx --bake $W/bake/CLIP.npz --vanilla data/destiny/port/rig/TEMPLATE
```

`--vanilla` is the clip folder of the template: `combatrifle` also for `combatrifle_parts`.

Gate: you can name the cause with a number from the data (a distance, an angle, a frame, a
time of the graph). A cause from the name of a bone is not a cause: `b_pump` of The Chaperone
is a lever.

### 5. Correct the rule

Correct with a key of the set file (`write-set-file`). Correct the rule, not the one frame.
A new rule in a shared tool is off by default and has a set file key (`change-shared-tool`).

Gate: the check of step 4 fails before the correction and passes after it.

### 6. Prove that nothing else changed

```sh
./port destiny regress
```

Name each clip that changed and say why. Look for the same fault in the other frames of the
clip and in the other clips: the dislocated finger of the M77 at frame 78 had a second place
at the frames 28 to 46. Make the pictures of the fault frames again, with a new file name.
Then test in the game again, with the permission of the user (`game-test-port`). When the
user accepts the change, make the new baseline (`write-set-file`, step 6).

### 7. Write the row

Add the sign, the cause and the rule to the troubleshooting table and to the document of the
weapon (`document-port`).

## Stop and ask the user

* When a word of the message is not clear and the pictures do not decide.
* Before a correction changes the clips of another weapon.
* Before the game starts.
* When you do not find the cause. Report the fault with what you examined. The failed
  `ammo.set` op and the sights that come 2.1 s late are reported faults with no cause.

## Common faults of the diagnosis

| Fault | Event |
| --- | --- |
| A correction with no cause | A step that turned a finger bone out of the gun made the contact count better and opened the hand |
| The first idea was "the game uses the clip in another way" | A Blender render over the game picture showed that the game plays the clip exactly. The fingers were in the grip. |
| A rule for this one case in the shared solver | The first hook rule of the M77 changed the poses of the Destiny guns |
| A passed game test read as a correct clip | Each hand fault passed each game test |
| A fault looked for in the mod after a second agent stopped the session | Run the test again first |
| An answer with no picture of before and after | The user compares each result panel with the source panel |

## What to report

* The cause with its number, and the change. A picture of before and after.
* The clips that changed, and the weapons that kept their bytes. The limit that stays.
* If the fault was your error, say so.

## More

* [references/signs.md](references/signs.md): each sign, by stage.
* [docs/porting/troubleshooting.md](../../../docs/porting/troubleshooting.md),
  [docs/porting/lessons.md](../../../docs/porting/lessons.md),
  [docs/porting/checks.md](../../../docs/porting/checks.md).
