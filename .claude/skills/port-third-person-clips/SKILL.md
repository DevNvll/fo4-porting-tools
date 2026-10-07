---
name: port-third-person-clips
description: Gives the procedure to port the third-person clips of a Destiny 2 weapon that is already ported to Fallout 4 in first person (the reload of the player body with the gun, and the hold pose WPNAssemblyPose), with the tool d2third, the step "third" of the converter and the keys of [third] in a set file. Use when the user asks to "port the third person animation", when the game plays the vanilla reload in third person, when the left hand goes to the grip or is at the place for the vanilla gun in third person, when the left arm is too short, or when the right fingers are open on the grip.
---

# The third-person clips of a ported weapon

Fallout 4 has few third-person clips of its own for a weapon: the reload (`WPNReload`), a
hold pose (`WPNAssemblyPose`) and two shot clips that move only gun parts. Each other
third-person clip (idle, walk, aim, shot) is a clip of the grip, which many weapons share.
So the port is the reload and the hold pose. Tell the user this first.

## When to use it, and when not

* Use it after the first-person clips of the weapon convert and are in the mod project.
* A shotgun, or a gun whose gun entity has no clip: load `port-staged-reload` also.
* A weapon of Marathon: no third-person clip of Marathon is extracted. Each third-person
  clip of the M77 is a vanilla clip of the combat rifle. Say so, and do not use this skill.

## Before the start

The steps `parts`, `retarget` and `hkx` of the first-person conversion ran: the step `third`
uses their results. So a later change of the first-person clips changes the third-person
clips also. The variables are those of `port-destiny-weapon`: `E`, `G`, `S`, `A`.

## Steps

### 1. Read the body clip from the game packages

```sh
./port destiny third $E/manifest.json
```

It writes `$E/third_person/reload.npz` (the world matrix of each bone of the body and of the
gun for each frame) and `states.json` (each state that has a leaf for the weapon). With no
`--state` it bakes the state `reload`.

Gate: read the lines `[third]`. They have the tags of the weapon, the clip, its leaf and its
frame count. Compare the frame count with the first-person reload (105 and 105 for the
Khvostov, 169 and 180 for Hammerhead, 127 and 127 for The Last Word). A frame count of
another weapon class says that the tag list is wrong. If the tool says "the clip has offsets
only", the clip is additive: give `--additive STATE`, and `--base` for another base pose.

### 2. Write `[third]` in the set file

```toml
[third]
folder = "third_person"

[third.clips]
WPNReload = "reload"

[third.poses]
WPNAssemblyPose = "WPNReload:0"
```

`WPNAssemblyPose` is necessary: the game takes the place of the left hand on the gun in each
third-person clip of the grip from this pose.

### 3. Run the step `third`

```sh
./port destiny convert $G --set $S third --third-output $A/third_person
```

Gate, from the line `[third]` of each clip:

| Value | Must be true |
| --- | --- |
| `left hand to gun` | 0.0000 units: the left hand has its place of the source against the gun. |
| `shoulder shift` | Small. With a large value, write `gun = "source"` and `blend = 8` in `[third]` and run the step again. The left arm was up to 8.3 units too short for Hammerhead with the default, 3.7 units for The Last Word. |
| `right hand on the grip` | The count of frames that you expect (105 of 105 for the Khvostov, 138 of 169 for Hammerhead). |
| `bone length` | Near zero (0.0004 to 0.028 units in the three first ports). |

The converter also prints the count of frames by which the events of the first-person clip
are later or earlier in this clip (+3 for the Khvostov, -2 for Hammerhead, 0 for The Last Word).

### 4. Draw the source above the result

```sh
D=data/destiny/port
./port destiny check third-sheet $E/third_person/reload.npz $D/work/NAME/third/poses/WPNReload.npz OUT.png
```

Look at the picture. It shows the body as lines. It does not show the fingers, and it does
not show the hand IK of the game.

### 5. Check the bytes of the first-person clips

Run `./port destiny regress --only NAME`. Gate: the first-person clips kept their bytes.

### 6. Build, then test in the game

`./port mod build MOD --update-lock`, then load `game-test-port`:

```sh
./port destiny game third --session ID --weapon EDITORID --capacity N --record --out DIR
./port destiny game trace --session ID --weapon EDITORID --loaded K --view third
```

The test takes pictures of a slow reload from three sides. Look at each picture: the left
hand, the right fingers on the grip, each gun part.

Gate: the game starts `WPNReload` and `WPNAssemblyPose` of the weapon in its third-person
graph. The reload fills the gun. The trace has `reloadEnd` at the time of the event of the
clip, and only the sounds of this clip. After a burst the left hand is on the handguard of
this gun. A test with 0 failed ops is not sufficient: one passed with a reload that ended 12
frames early and with the sounds of another clip.

## Stop and ask the user

* Before the game starts.
* When the user named no weapon. In the first work the agent ported three weapons and said so.

## Common faults

| Sign | Cause | Rule |
| --- | --- | --- |
| In the game the left hand goes to the grip in the reload | `WeaponIKTargetL` was at its rest place | The bone has the matrix of the left hand (in the tool) |
| In each clip of the grip the left hand is at the place for the vanilla gun | `WPNAssemblyPose` is the vanilla one, or a wrong one | `[third.poses] WPNAssemblyPose = "WPNReload:0"` |
| The right fingers are open on the grip | The third-person data of Destiny | `right_hand = "hold"`, the default |
| The left arm is too short | Destiny holds the gun at another place than the vanilla stance | `gun = "source"` |
| The events are early or late | The rule that gives the frame shift looked at the wrong part | `align`: the weapon bones whose first motion gives the shift (default: the bolt of the template) |
| The reload is that of another weapon class | A wrong tag list | Compare the frame count with the first-person reload |
| The gun parts do not move | The gun entity has no clip for the state | `[third.parts]` (a choice) |
| The reload ends early, sounds of another clip, the build stops for power armor | The third-person graph | `port-staged-reload` |

## What to report

What Fallout 4 has in third person, which clips you converted and which not, the values of
the line `[third]`, the result of the game test, and the limits: the legs and the pelvis do
not move, the rule for the right hand is a choice, a body in power armor has the vanilla
reload and was not tested, and no test had a reload while the player walks.

## More

* [references/third-person-facts.md](references/third-person-facts.md): the graphs of the
  two games, each key of `[third]`, what is not done.
* [destiny/port/README.md](../../../destiny/port/README.md), "The third-person clips".
* [docs/porting/destiny.md](../../../docs/porting/destiny.md),
  [docs/porting/game-test.md](../../../docs/porting/game-test.md).
