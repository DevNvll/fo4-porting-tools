---
name: fix-hand-pose
description: Gives the procedure to correct a hand or a finger of a ported weapon in Fallout 4, from the measurement to the rule (a pose clip of the gun with [hand_pose], knuckles = "align" and closed_fingers = true for a rig of Marathon, [fingers] min_bend and skin_center for a New Vegas port). Use when the user sends a picture and says "the hands seems far from the model, not touching it", "the fingers are clipping through", "why are these fingers broken", "the fingers are a bit deformed", "the thumb is kinda misaligned", "finger looks dislocated on this one frame", when "./port destiny check touch" gives 0 percent for a hand that holds the gun, when a finger joint bends back, or when a finger turns more than about 30 degrees in one frame and the source does not.
---

# Correct a hand or a finger

Each hand fault of the three chats was found by the user in a picture, not by a number of
the agent. So this skill starts with the picture, measures the property that the user sees,
and corrects the rule, not the one frame.

## When to use it, and when not

* Use it when the fault is a hand or a finger: away from the gun, in the gun, bent wrong.
* The gun is not in the hand at all (the hands hold no gun): `write-set-file`, `[gun] rest`.
* In third person the left hand goes to the grip: `port-third-person-clips`.

## Before the start

Find the build and the frame of the picture of the user. An old picture can show a fault
that is already corrected. The variables are those of `validate-port`: `E`, `G`, `S`, `W`, `C`.

## Steps

### 1. Make the pictures of the fault

Render that hand at the frame, and 4 frames before and after, the source above the result,
from four sides:

```sh
./port destiny check render --glb $G --clip CLIP --poses $C/WPNReload.hkx --parts $W/parts.json \
    --out $W/fault --template TEMPLATE --frames 74,75,76,77,78,79,80,81,82 --views l_thumb,l_back,l_front,l_palm
./port destiny check sheet $W/fault CLIP l_thumb "74 76 78 80 82" $W/fault/l_thumb_a.jpg
```

Gate: you see the fault of the user in your own picture. If you do not, you have the wrong
frame, the wrong clip or an old build.

### 2. Measure

```sh
./port destiny check fingers $C/WPNReload.hkx --bake $W/bake/CLIP.npz --vanilla data/destiny/port/rig/TEMPLATE
./port destiny check touch --glb $G --bake $W/bake/IDLE_CLIP.npz --poses $C/WPNIdleReady.hkx --parts $W/parts.json --frames 0
```

The first command gives the frame and the bone of a joint that bends back or turns too far
in one frame. The second gives the distance of the nearest vertex of each hand to the gun, and
the percent of vertices nearer than 0.5 cm and 1.5 cm, for the source and for the result.

Gate: you know which of the four cases you have.

| Case | Sign in the numbers |
| --- | --- |
| A. The source has the fault | The source hand has 0 percent nearer than 0.5 cm in the hold pose, or its wrist is at another place than in a clip of this gun |
| B. The solver has the fault | The source finger is correct, and the result finger points to the wrist, is straight, or turns far in one frame |
| C. A New Vegas port | A straight finger with lumps, a joint that bends back, a thumb beside its place |
| D. A finger is deeper in the gun than the source | `summary.txt` of `./port destiny check validate`: "deeper than the source" |

### 3A. A pose clip of the gun

Most clips of the hands are clips of the weapon class. The file of a gun also has short
additive clips (2 or 3 frames, offsets only) that no state of the graph names. With the
correct one the left hand is on this gun.

```sh
M=$E/manifest.json
./port destiny pose $M --measure --hold IDLE_CLIP:0                # the two hands with no pose clip
./port destiny pose $M --list                                      # each candidate with its offsets
./port destiny pose $M --measure --pose TAG --hold IDLE_CLIP:0     # one candidate
./port destiny pose $M --pose TAG --hold IDLE_CLIP:0 --clip CLIP --clip CLIP2
```

Measure each candidate. The name does not say which one is correct: two candidates of The
Chaperone have the same offsets with opposite signs. Give the last command each clip of the
set file. It writes `$E/posed/CLIP.npz`. Add `--gun-on-grip` when the set file has
`[gun] rest = true`. Then write `[hand_pose] folder = "posed"` in the set file, with the
measurements of each candidate as a comment and the word "choice".

Gate: the measure prints the count of vertices of each hand (1903 for the Destiny hand). A
smaller count says that the measure reads a part of the mesh only. With the pose clip the
left Fallout 4 hand has at least 5 percent of its vertices nearer than 0.5 cm in the hold
pose (The Chaperone: 0.0 to 5.2 percent. The Huckleberry: 12.4 to 20.9).

### 3B. The knuckles and a closed finger

Measure the cause before a change: the distance of the Fallout 4 knuckles and of the thumb
root to those of the source, with the wrists at one place. Destiny has 0.50 and 0.35 units.
Marathon has 1.42 and 0.64.

* `knuckles = "align"` moves each wrist so that the thumb root and the mean of the four
  knuckles are at the same distance from those of the source.
* `closed_fingers = true` makes a finger that is a hook or a fist keep the bends of its last
  two bones, with its tip at the source fingertip.

The two keys are off by default. The line `[retarget]` of each clip has `closed` (the count
of fingers with the rule), and the report of the retarget step has `knuckles` and
`max_wrist_move_for_the_knuckles`. Do not give the two keys to a Destiny weapon that passed
its game test: the rule for a closed finger changes 4 of the 5 Destiny clip sets, 1.4 units
at most. If no key corrects the fault, the solver needs a new rule: `change-shared-tool`.

### 3C. A New Vegas port

The configuration file of `./port fnv convert` has `[fingers] min_bend` (default 0.3) and
`skin_center` (default `true`). `./port fnv convert CONFIG show` prints the values. The tool has
no key for one finger or one frame ([the rules](../port-fnv-animations/references/fnv-facts.md)).

### 3D. A finger that is deeper than the source

The collision step moves a finger 1.15 units at most. The right thumb of Hammerhead is 3.0
units deep in the receiver (source 1.3). Report such a finger as a limit. Zero vertices in
the gun is not the target: the source hands are partly in the gun.

### 4. Make the clips again and prove the rest

1. Convert the first-person clips again, then run the step `third` again (it uses their results).
2. `./port destiny check touch-table $G --set $S --clips $C --out data/destiny/port/validation/NAME/hand_distance.txt`.
3. Look for the same fault in the other frames and clips. Make the pictures of step 1 again,
   with a new file name.
4. `./port destiny regress`: each other weapon keeps its bytes.
5. With the permission of the user, a game picture of the hold pose (`game-test-port`).

Gate: the numbers of step 2 are better, the pictures show a correct hand, and you can name
each clip that changed.

## Stop and ask the user

* When two pose clips fit and the measurements do not decide. For The Huckleberry the agent
  took the clip that comes from a clip of this gun, and said that it is a choice.
* Before a rule changes the clips of a weapon that passed its game test, or the game starts.

## Common faults

| Fault | Event |
| --- | --- |
| The retarget corrected for a fault of the source | The result was equal to the source. The first-person graph of Fallout 4 has no hand IK, so the game does not correct the hand. |
| A rule for one frame in the shared solver | It changed the other weapons. The rule went behind a set key. |
| The picture from the camera only | The dislocated finger showed in the views of the hand. Run the finger check on each clip before the first look at pictures. |
| A straight Fallout 4 finger accepted | The Fallout 4 hand mesh is modelled with bent fingers, and a straight finger has lumps |

## What to report

The cause with its numbers, the rule, the picture of before and after, the percent of each
hand before and after, the clips that changed, and the limit that stays. A pose clip is a
choice: no file says which state uses it.

## More

* [destiny/port/README.md](../../../destiny/port/README.md), "The left hand on the gun", "The
  M77 of Marathon"; [fnv/README.md](../../../fnv/README.md), "What the conversion does".
* [docs/porting/troubleshooting.md](../../../docs/porting/troubleshooting.md), [docs/porting/checks.md](../../../docs/porting/checks.md).
