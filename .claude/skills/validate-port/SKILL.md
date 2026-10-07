---
name: validate-port
description: Gives the checks that an agent must do before it says that a port, a clip or a change of a tool is correct in this repository, with what each check proves and what it does not prove (byte regression, the numbers of each clip, the distance of each hand to the gun, pictures of the source beside the result, pictures from the game camera, the esx checks of a built mod). Use before a report with the words "works", "correct", "done" or "fixed", after each conversion, after each change of a set file or a tool, and when the user asks to "validate the retarget with blender before testing ingame".
---

# Validate a port before you say that it is correct

In the chats that made these tools, the tests passed many times while the result was wrong.
The user found in a picture each hand fault that had passed the checks. So a number alone is
not a proof, and a passed game test alone is not a proof. Do each step below, and read what
each check does not prove.

## When to use it, and when not

* Use it for the clips of the converter `d2fo4` (Destiny 2 and Marathon), and for its rules.
* The clips of `fnv/`: its check programs with pictures are only in git, at the tag
  `before-animation-only`. `port-fnv-animations` says how to get them.
* A test in the game is the next stage: `game-test-port`.

## Before the start

The clips are in the mod project or in `data/destiny/port/out/NAME`. The arm meshes for the
check pictures are in the rig folder (`./port doctor`).

```sh
E=data/destiny/port/extract/NAME ; G=$E/NAME_first_person.glb ; S=destiny/port/sets/NAME.toml
W=data/destiny/port/work/NAME    ; C=data/mods/MOD/behavior/WEAPON/animations/first_person
V=data/destiny/port/validation/NAME
```

## Steps

### 1. The bytes

```sh
./port destiny regress                 # each ported weapon; --only NAME for one
./port fnv regress                     # after a change below fnv/
./port marathon regress-clips          # the M77
```

Gate: 0 clips differ, or you can name each clip that changed and say why. For a new weapon
that is not in `destiny/port/regress.toml`: convert a second time with another `--work` and
`-o`, and compare each file with `cmp`. This check proves that the same input gives the same
bytes. It does not prove that a clip is correct. Then run `./port baseline check`: it proves
that nobody replaced a stored result (the baseline clips, the release of each mod). Gate:
`0 different`.

### 2. The numbers of each clip

```sh
./port destiny check validate $G --set $S --out $V --clips $C --no-video
```

Gate, in `$V/summary.txt` (one line for each clip) and `$V/NAME.txt`:

* The largest distance of a gun vertex to the source is at most about 0.015 units (the six
  ports have 0.003 to 0.015 in a clip). A larger value is a fault of the parts or of the clip.
* Each wrist is at most 0.003 units from the source wrist. With `knuckles = "align"` (a rig of
  Marathon) the wrist line of `NAME.txt` is about 1.02 units: that is the rule, not a fault.
* `joints bent back: none`. The M77 has the first joint of a thumb (`Finger11-2`) at 3.3 to
  4.9 degrees. A value for another joint is a fault.
* A finger turn in one frame of more than about 30 degrees that the source does not have:
  look at those frames in pictures (step 4). 170 degrees was a finger that pointed to the wrist.

Run the finger check on each clip before the first look at pictures. A gate that fails for a
finger: `fix-hand-pose`. For the gun or a wrist: `diagnose-port-fault`.

### 3. The distance of each hand to the gun

```sh
./port destiny check touch-table $G --set $S --clips $C --out $V/hand_distance.txt
```

Gate: in the hold pose each hand that holds the gun has at least 5 percent of its vertices
nearer than 0.5 cm to the gun. That is the lowest value of the five Destiny ports (5 to 42
percent). If the source hand has 0 percent, the gun needs a pose clip: `fix-hand-pose`. A
value above 0 does not prove the place of the hand: The Huckleberry had 12.4 percent with its
wrist 2.5 cm from its place. Measure each pose clip candidate of the gun (`fix-hand-pose`, 3A).

This is the check that the first port of The Chaperone did not have. Its left hand was 1.0 cm
from the gun in the result and 0.9 cm in the source. Each check against the source passed.

### 4. Pictures of the source beside the result

```sh
./port destiny check render --glb $G --clip IDLE_CLIP --poses $C/WPNIdleReady.hkx --parts $W/parts.json \
    --out $W/look --template TEMPLATE --frames 0 --views fp,r_thumb,r_back,l_thumb,l_palm,gun_left,gun_right
./port destiny check look-sheet $W/look IDLE_CLIP 0 $W/look/hold.jpg fp,r_thumb,r_back,l_thumb,l_palm,gun_left,gun_right
```

Do the same for the reload with `--frames all`, and make a sheet of each frame in which a
hand takes or lets go a part (`./port destiny check sheet DIR CLIP VIEW "0 10 20" OUT.jpg`).
Open each picture. Look at the whole picture, not only at the part that you made it for.

Gate: you looked for the four defects of the first task in each hand: fingers through the
gun, broken or deformed fingers, a wrong wrist rotation, a thumb that is not aligned. Compare
each result panel with the source panel above it, also in a close view.

### 5. The videos that a person must see

Videos of each clip need about 10 minutes for each clip. Make them for one reload and the idle:

```sh
./port destiny check validate $G --set $S --out $V --clips $C --left-hand --only WPNReload
```

Stop a long run by its process ID. `pkill -f validate.py` also stops the shell that has that
text in its command line.

### 6. The built mod

`./port mod build MOD --update-lock`, then the checks of esx
([the mod project](../port-destiny-weapon/references/mod-project.md)). Gate: 0 issues, 0
warnings, 0 findings. For a mod that passed a game test, run `./port baseline check` after the
build: `DIFFERENT` for a release file says that the build did not give the tested bytes. Stop
and tell the user. Do not run `./port baseline update` before the user accepts the change.

### 7. The proof of each statement

For each statement of the report, name the check that proves it. Put each other statement
under "What is not proved". [references/checks.md](references/checks.md) has what each check
proves.

## Stop and ask the user

* Before the game starts.
* Before you accept new baseline clips after a change that moved a finger.

## Common faults

| Fault | What to do |
| --- | --- |
| A check against the source for a fault that the source has also | Measure the property that the user sees (the hand touches the gun), not only the difference to the source |
| A count of vertices inside the gun as a proof that the hand holds the gun | `check contact` does not show a hand that is 1 cm away. Use `check touch`. |
| A check for a rule that changes the source (`[gun]`, `[compose]`, `[hand_pose]`) | The check compares with the pose after the rule. Only a picture of the source game, or the game, proves such a rule. |
| A game picture that was made for another purpose | Look at each hand in it. The left hand was in the pictures that were made for the sight. |
| A picture of an unfinished step shown to the user | Do not show it |
| A picture that is made again with the same file name | Give it a new file name: a chat can show the old picture |

## What to report

Each check with its command and its result. The numbers against the ranges. The pictures
that you looked at. The part "What is not proved". Give a number its true precision.

## More

* [references/checks.md](references/checks.md): what each check proves, the faults that passed it, the numbers, the views.
* [docs/porting/checks.md](../../../docs/porting/checks.md),
  [docs/porting/lessons.md](../../../docs/porting/lessons.md).
* [destiny/port/README.md](../../../destiny/port/README.md), "Checks" and "What is proved".
