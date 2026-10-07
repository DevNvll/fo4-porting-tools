---
name: port-staged-reload
description: Gives the procedure for a reload that is more than one clip in a port to Fallout 4 with the converter d2fo4. One case is a gun that loads one round at a time (a shotgun, a reload of three states, one reload clip for each count of rounds with [compose], [piece_events] and "when ammo == N play CLIP"). The other case is a gun whose parts move in a second clip ([gun.parts]). Use when the reload of a weapon has the states reload_enter and chamber_1, when a part does not move in the clip of the hands, when a sound of another reload plays, or when a reload ends before its motion ends.
---

# Port a reload that is more than one clip

Destiny 2 and Marathon do not have one clip for each reload. This skill has the two cases
that the ports found. The set file of The Chaperone (`destiny/port/sets/the_chaperone.toml`)
is the model of case A. The set files of The Huckleberry and of the M77 are the models of
case B.

## When to use it, and when not

* Case A: `states.json` has no reload state with one clip, and it has `reload_enter`, a state
  for one round and `chamber_1`.
* Case B: the hands move in the reload clip and a part of the gun does not.
* A reload of one clip with its parts in it needs only `[clips]` (`write-set-file`).

## Before the start

The first pass of the set file converts (`write-set-file`). The variables are those of
`port-destiny-weapon`: `E`, `G`, `S`, and `A` (the clip folders of the weapon in the esx project).

## Case A: one clip for each count of rounds

### 1. Find the states and look at each piece

A shotgun has three states: `reload_enter`, the state `6C41757C` for one shell (its name is
not known), and `chamber_1`. The game plays the shell state one time for each round.

```sh
./port destiny video $G --clip CLIP --columns 8 --width 640 --out data/destiny/port/work/NAME/probe/CLIP.png
```

Measure the gap between the last pose of each piece and the first pose of the next one. The
last pose of the shell clip of The Chaperone is not its first pose: the left hand is 34 cm
away, below the view.

Gate: you know the frame of each event in each piece from the pictures: the round is in its
place, the lever opens and closes, the left hand is back on the gun.

### 2. Write the set file

1. One `[compose.reload_N]` for each count of rounds: `clips = ["ENTER", "SHELL*N", "END"]`,
   `blend` (the count of frames in which a difference between two pieces goes to zero) and
   `cut` (the bones with no such blend). A part that the game hides is at a far place: the
   shell of The Chaperone is behind the camera, or 1.4 m away. Such a bone must be in `cut`,
   or it moves across the view at each join.
2. `[piece_events]`: the events of each piece. Each use of a piece gives its events. A frame
   below zero is before the piece: `reloadComplete` at -15 of the last piece is frame 12 of
   the last shell piece. Give the sound of each round, `reloadComplete`, the sounds of the
   lever, `initiateStart` and `reloadEnd`. A composed clip gets no event from the motion of
   the parts.
3. `[clips]`: `WPNReload1 = "reload_1"` to `WPNReloadN = "reload_N"`, and `WPNReload` = the clip
   with the most rounds, for a reload that no rule of the behavior source selects.

### 3. Write the behavior source and the item file

One line for each count in `mods/MOD/behavior/WEAPON/WEAPON.bhv`. For a capacity of 6:
`when ammo == 5 play WPNReload1` to `when ammo == 0 play WPNReload6`. In the item file,
`reload_seconds` is the time of `reloadEnd` in `WPNReload` (frame 217 of 226 is 7.2333).

### 4. The third-person clips

```sh
./port destiny third $E/manifest.json --state reload_enter --state 6C41757C=reload_loop \
    --state chamber_1 --additive reload_enter --additive 6C41757C --additive chamber_1
```

The third-person clips of a shotgun have offsets only. The tool does not find each such clip
by itself, so name each one with `--additive`. Then write, as in the model set file:

| Table | Why |
| --- | --- |
| `[third.compose.reload_N]`, `[third.piece_events]`, `[third.clips]` | As in first person, with state files. |
| `[third.hold_end]`, 16 frames for each reload clip | The third-person graph sends `reloadEnd` 0.5 s before the end of the clip. A clip that moves until its last frames ended at frame 22 of the 38 frames of `chamber_1`. |
| `silent = ["WPNReload"]` | The graph has a second clip node for the gun parts, and it plays `WPNReload` at the same time as the clip with a new name. A reload with one shell had the sounds of three shells. |
| `[third.power_armor]`, each `WPNReloadN = "wpnreload"` | The body and the body in power armor have one graph. esx builds a clip with a new name only when the two views have it. Else the build stops with `CLIP_MISSING`. |

### 5. Convert, build and test each count

```sh
./port destiny convert $G --set $S -o $A/first_person
./port destiny convert $G --set $S third --third-output $A/third_person
./port mod build MOD --update-lock
```

The step `third` also writes the folder `power_armor_third_person` beside the folder of
`--third-output`. With the permission of the user (`game-test-port`; `game trace` did not run here):

```sh
./port destiny game reloads --session ID --weapon EDITORID --capacity N --out DIR
./port destiny game trace --session ID --weapon EDITORID --loaded K --view third
```

Gate (the values of The Chaperone, `game_test_reloads.txt` of its validation folder): one
reload for each count in each view, 12 reloads, 0 failed. Each one played the clip of its
count, filled the gun to 6 rounds, started one round sound for each round and the two sounds
of the lever one time, and ended at the event of its clip (7.23 s to 2.75 s in first person,
6.28 s to 2.45 s in third person). A passed test is not sufficient: read the trace.

## Case B: the parts move in a second clip

1. Find the second clip. It is an additive clip of the file with the same frame count
   (`fp_103_80EF5692_add` for The Huckleberry), or a clip of the gun entity on the same
   skeleton (`weapon_000_80A5E484` for the M77). The frame counts can differ by one: 104 and
   105 for the M77.
2. Show that the two clips are a pair: the same frames move. In the reload of The
   Huckleberry the housing of the barrel moves from frame 3 to frame 61 in the clip of the
   parts, and the left hand is away from the gun from frame 3 to frame 61 in the clip of the
   hands. For the M77 the magazine is in the left hand in each frame in which it is out.
3. Write `[gun.parts]`: `CLIP = "CLIP2"`. Each part gets its motion in CLIP2 against the first
   frame of CLIP2, on its rest place.
4. Convert, and read the events of the reload in the lines `[hkx]`. Correct an event that
   the motion of a part puts at a wrong frame, with `[events]`
   ([the events](../write-set-file/references/clips-and-templates.md)).
5. For the third-person clip of a gun whose gun entity has no clip: `[third.parts]`,
   `STATE = "FIRST_PERSON_CLIP"`. That is a choice: no file says that the parts move in third
   person.

Gate: pictures of the reload show each part with the hand that moves it, in each frame.

## Stop and ask the user

* Before the game starts for the test of the counts.
* When two candidates for the second clip have the same frame count.

## Common faults

| Sign | Cause | Rule |
| --- | --- | --- |
| A part moves across the view where two pieces join | The game hides the part at a far place | `cut` |
| The tool says "the clip has offsets only" | An additive third-person clip | `--additive STATE`, with `--base` for another base pose |
| Third person: the reload ends before its motion ends | `reloadEnd` of the graph, 0.5 s before the end of the clip | `[third.hold_end]` |
| Third person: sounds of another reload clip | The second clip node plays `WPNReload` | A clip with a new name for each count, and `silent` |
| The build stops for `power_armor_third_person` | One graph for two views | `[third.power_armor]` |
| The clip of the gun parts is that of another state | A pair by the frame count only | The graph of the gun entity gives the clip (in the tool). Compare the motion in pictures. |

## What to report

The states and the clip of each one. The frames of each reload clip, and each event with its
frame. The result of the test of each count. What is not proved: the proof that two clips are
a pair is the same frames and the pictures, and it is not a picture of the source game.

## More

* [destiny/port/README.md](../../../destiny/port/README.md): "The Chaperone", "The
  Huckleberry", "The reload of a shotgun, and a gun with no clip of its parts".
* [docs/porting/destiny.md](../../../docs/porting/destiny.md), [docs/porting/troubleshooting.md](../../../docs/porting/troubleshooting.md).
