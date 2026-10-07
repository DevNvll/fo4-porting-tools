---
name: port-marathon-weapon
description: Gives the complete procedure to port a weapon of the game Marathon to Fallout 4 (the extraction with m2x, then the converter d2fo4 of the Destiny area with a set file in marathon/port/sets), and says what differs from a Destiny 2 port (a variant item with --art, the clip of the gun parts in a second clip, the two hand rules knuckles and closed_fingers, gray pieces, no third-person clip, no game start because of the anti-cheat). Use when the user asks to port or extract a Marathon weapon ("now extract the rig and port it to fallout 4", "port the M77", "Overrun AR", "V75 SCAR"), or to change the M77 mod.
---

# Port a weapon of Marathon to Fallout 4

Marathon has a later version of the engine of Destiny 2, and its first-person rig is the rig
of Destiny 2: the same bone names, the same bone axes, the camera bone `b_utility`, the gun
bone on `b_r_grip`. So the extraction has its own tool (`m2x`), and the converter is that of
`destiny/port` with no rig step. The M77 is the one weapon that is ported
(`marathon/port/sets/m77_omnipositor.toml`, the mod `M77`).

## When to use it, and when not

* Use it for a port of a Marathon weapon, and for a change of the M77 port.
* Each step that is the same as for Destiny is in `port-destiny-weapon` and its skills. This
  skill has the order and the differences.

## Before the start

1. `./port doctor`. The exit code must be 0. If not: `set-up-workspace`
   (`./port destiny setup`, then `./port marathon setup`).
2. Do not start Marathon. It has an anti-cheat program (BattlEye). The tools only read the
   game folder. No picture of Marathon is the reference: "correct" is from the game files
   and from pictures of Blender. Tell the user this.
3. After an update of the game: `./port marathon tag64`. If the extraction then stops with
   "no tag of the class ...: the layouts of this file are for another build", load
   `decode-game-data`.

```sh
E=data/marathon/extract/out/NAME          # NAME: the folder that the extraction makes
G=$E/NAME_first_person.glb
S=marathon/port/sets/NAME.toml
A=data/mods/MOD/behavior/WEAPON/animations
```

## Steps

### 1. Extract

```sh
./port marathon find "TEXT"
./port marathon extract "ITEM" --art "BASE ITEM" \
    --hands data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
./port marathon render $E/NAME_weapon.glb data/marathon/extract/work/NAME.png --views side,quarter
```

`--art` is only for an item that `find` shows with `no entity of its own`. `--hands` needs a
first-person file of Destiny 2, for the check pictures (`extract-game-weapon`).

Gate: the last lines of the output have each piece with a place, no clip with an error, and
"the rest places of the gun parts differ by 0.000000". With another value the first-person
file is not correct, and the port stops here: tell the user (`V75 SCAR` has 14 gun bones, and
the arm rig has the 10 gun bones of the M77). Look at the pictures.

### 2. Write the set file

Load `write-set-file`. Copy `marathon/port/sets/m77_omnipositor.toml`, and change `hold`,
`sighted`, `[clips]`, `[auto]`, `[poses]`. `states.json` beside the `.glb` file has the clip
of each state. What differs from a Destiny set file:

| Key | For Marathon |
| --- | --- |
| `knuckles = "align"`, `closed_fingers = true` | Keep the two for a rig of Marathon. The hand bone is at another place in the hand: the forearm is 1.2 cm longer and the palm 0.7 cm shorter (`fix-hand-pose`). |
| `[gun.parts]` | A clip of the arms does not move the gun parts in a reload. The weapon has a clip of its own (`weapon_NNN_TAG`), and the game plays the two at the same time. Give each reload clip of the arms the clip of the weapon with the same length. One frame of difference is normal: 104 and 105 (`port-staged-reload`). |
| `[sight] point` | From the named points of the sight piece (`points` in `manifest.json`), or from `./port destiny points`. Marathon aligns the sight when the game runs, as Destiny does. |
| `[events]` | The reload of an empty gun has the bolt to the rear from frame 0. Put the sound `BoltOpen` at the frame of the pull of the hand (frame 76 for the M77). |
| `[hold_end]` | The put-away of the M77 has 12 frames: 3 more frames, not 8. |
| `dyes`, `[model.shaders]`, `[model.sight]`, `[third]` | Not used. The extraction writes each material as a texture set of Destiny 2 with no dyes. No third-person clip of Marathon is extracted. |

### 3. Convert, make the model, build

```sh
./port marathon convert $G --set $S -o $A/first_person
./port marathon model $G --set $S --mod MOD
./port mod build MOD --update-lock
```

`marathon convert` and `marathon model` are the programs of `destiny convert` and
`destiny model`. The work files are in `data/destiny/port/work/NAME/`, and the model program
reads `parts.json` from there: do the convert first.

Gate: the gates of step 3 of `port-destiny-weapon` (`wrist`, `weapon`, `pos err`). The line
`[retarget]` of each clip has the count of fingers with the rule for a closed finger. The
build has 0 issues and 0 warnings.

### 4. Check

```sh
V=data/destiny/port/validation/NAME
./port marathon regress
./port marathon regress-clips
./port destiny check validate $G --set $S --out $V --clips $A/first_person --no-video
./port destiny check touch-table $G --set $S --clips $A/first_person --out $V/hand_distance.txt
```

`marathon regress` extracts each stored weapon again and compares the bytes.
`marathon regress-clips` is `./port destiny regress --only m77_omnipositor`: for a new
weapon, add it to `destiny/port/regress.toml` and run `./port destiny regress --only NAME`.

Then load `validate-port`. Make pictures of each hand in the reload, from four sides, for
each frame in which a hand takes or lets go a part. The user saw a dislocated finger at
frame 78 of the reload of the M77, and the agent had looked at pictures from the camera only.

Gate: the numbers of the M77 are the reference: the gun at most 0.0102 units from the source
gun, no finger joint that bends back, hand vertices in the gun 6.1 to 10.6 percent (source
8.3 to 24.1).

### 5. The game test and the documents

Only with the permission of the user: `game-test-port`. The test starts Fallout 4, not
Marathon. Then `document-port`.

## Stop and ask the user

* Before the game starts.
* When the weapon has other gun bones than the arm rig.
* Before a change of the solver for a Marathon hand: the Destiny weapons use the same solver
  (`change-shared-tool`).

## Common faults

| Sign | Cause | What to do |
| --- | --- | --- |
| `extract` stops: "has no row in the art table. Give --art ITEM" | A variant item | `--art "BASE ITEM"` |
| The packages do not open, or SIGSEGV when they open | The runtime folder of m2x is not complete | `./port marathon setup` (`--force` builds again) |
| A finger points to the wrist in one frame | A closed finger with the base rule | `closed_fingers = true` |
| The fingertips are 1 unit from the source | The knuckles are 1.42 units from the source knuckles | `knuckles = "align"` |
| Three pieces are gray | The game calculates the colors of the regions when it runs | A limit. Say so. |
| The sound `BoltOpen` is at frame 0 | The bolt is to the rear from frame 0 | `[events]` |

## What to report

As for a Destiny port, and the limits of a Marathon port: the mod has the name and the look
of the base item when the item is a variant; the pieces that are gray; the solver uses the
measurements of the Destiny hand mesh, because the hand mesh of Marathon is not extracted;
each third-person clip is a vanilla clip; no comparison with Marathon; the two hand rules
are tested on one weapon and one template; the frame rate of 30 is the value of Destiny 2.

## More

* [marathon/README.md](../../../marathon/README.md): the order of the commands, and the
  state of the M77 port.
* [marathon/extract/README.md](../../../marathon/extract/README.md),
  [marathon/port/README.md](../../../marathon/port/README.md).
* [destiny/port/README.md](../../../destiny/port/README.md), "The M77 of Marathon".
* [docs/porting/marathon.md](../../../docs/porting/marathon.md),
  [mods/M77/README.md](../../../mods/M77/README.md).
