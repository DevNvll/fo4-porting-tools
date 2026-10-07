# The port of a Marathon weapon to Fallout 4

Marathon runs on a later version of the Destiny 2 engine. Extraction has its own tools, `m2x`
in `marathon/extract/`. Conversion to Fallout 4 uses the Destiny 2 converter in
`destiny/port/` with a set file from `marathon/port/sets/`. One weapon is ported, the M77.

* [marathon/README.md](../../marathon/README.md) covers the two folders of the area and the
  state of the M77.
* [marathon/extract/README.md](../../marathon/extract/README.md) covers the extraction: the
  layouts, what is proved, what is not done.
* [marathon/port/README.md](../../marathon/port/README.md) lists the port commands.
* [destiny.md](destiny.md) is the procedure for the converter. Read it first. This document
  only gives what is different.

**Do not start Marathon for this work.** The game runs the BattlEye anti-cheat program, and
the tools only read the game folder.

## What is the same as for Destiny 2

* A first-person file from `m2x` has the same form as one from `d2x`: one skin, the gun
  pieces on the weapon bones, the camera at `b_utility`, and one animation per clip.
  `./port destiny convert` reads it unchanged.
* Marathon uses the Destiny rig. The bone names and bone axes are the same, so a bone points
  along its local Z and bends about its local Y. The camera bone `b_utility` is at the same
  place, and the gun bone is on `b_r_grip` in every clip.
* Names are FNV-1 hashes of words. The graph's state names are the Destiny 2 words: `idle`,
  `fire`, `iron_sight_idle`, `ready`, `put_away`, `reload_empty`.
* The game aligns the sight at run time, so the set file needs `[sight]`.
* The set file, the checks, the model program, the mod project, the regression and the game
  test are the ones in [destiny.md](destiny.md).

## What is different

| Thing | Destiny 2 | Marathon |
| --- | --- | --- |
| The extraction | `./port destiny extract` | `./port marathon extract`. It has its own setup, `./port marathon setup`, which you run after `./port destiny setup`. |
| Oodle | Oodle 3, with the shim of `tiger-pkg` | Oodle 9. The setup builds a loader for it, on x86-64 Linux only. |
| Tag names | 32-bit tags | 32-bit tags, plus 64-bit hashes for entities, clips and textures. The setup makes a table of them. Run `./port marathon tag64` after a game update. |
| The layouts | From public tools | Every class number and offset comes from the data of one game build. A new build can stop the tools with "no tag of the class ...: the layouts of this file are for another build". |
| A variant item | Not seen | An item can have no entity of its own. Give its base item with `--art`. |
| The weapon | One model with regions | A set of pieces. Each piece is an entity with a model, and a named point of the weapon gives its place. |
| The first-person rig | 75 to 87 bones | 91 bones for the M77 (`fp_rifle_arms`) |
| The hand bones | The reference of the tools | Different lengths. The forearm is 1.2 cm longer, the palm 0.7 cm shorter, and some finger bones 10 to 23 percent shorter. The set file needs `knuckles = "align"` and `closed_fingers = true`. |
| The hand mesh | In the file (`body_hands`) | Not extracted. `--hands FILE.glb` puts the hand mesh of a Destiny 2 file on the rig, for the check pictures only. |
| The gun parts in a reload | In the arm clip, or in an additive clip | In a clip of the gun entity, `weapon_NNN_TAG` in the same file. The game plays both at once, and `[gun.parts]` joins them. |
| The states file | `./port destiny states` writes `states.json` | The extraction writes `states.json` beside the `.glb` file |
| The materials | A texture set and dyes | Three rules: `palette`, `detail`, `constant`. The extraction writes each one as a Destiny 2 texture set. A `detail` material has seven regions, and the colors of six of them are not in the files. |
| The shaders | Direct3D 11 bytecode, `./port destiny shader-text` | DXIL, `./port marathon notes dxil MATERIAL`, which needs `llvm-dis` |
| The third-person clips | `./port destiny third` | Not extracted |
| The frame rate | 30 | 30 is the Destiny 2 value. It does not come from the Marathon files. |

## The procedure

Run every command from the repository root. The example is the M77.

### 1. Prepare (one time)

```sh
./port destiny setup                 # the environment of d2x: m2x uses its Python, its package reader and its clones
./port marathon setup                # the Oodle 9 shim, the link to the Oodle library of the game, tag64, the table of the 64-bit tag hashes
./port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif
./port fnv make-rig --arm-meshes
./port destiny make-rig
./port doctor marathon
./port doctor destiny
```

**Gate.** Both doctor commands print `Result: each setting and each check is ok.` The setup
ends with a line like this one:
`the packages open: 1032829 entries; 50 entries read with no error; 43853 hashes in the table`.

### 2. Find the item and extract it

```sh
./port marathon find "M77"
./port marathon extract "M77 Omnipositor" --art "M77 Assault Rifle" \
    --hands data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
./port marathon render data/marathon/extract/out/m77_omnipositor/m77_omnipositor_weapon.glb \
    data/marathon/extract/work/m77.png --views side,quarter
./port marathon regress
```

* `find` prints the item hash, the name and the entity. `no entity of its own` means the item
  is a variant, so give its base item with `--art`. Without it, `extract` stops with "has no
  row in the art table. Give --art ITEM".
* `--hands` needs a first-person file from a Destiny 2 extraction.
* Read the last lines of the `extract` output: the count of pieces with a place, the clips
  with an error, and "the rest places of the gun parts differ by". Any value other than
  0.000000 means the arm rig lacks the bones of this weapon. `V75 SCAR` gives 1.000000.
* Render the weapon file and some frames of first-person clips with
  `--action fp_NNN_TAG --frame N`, then look at the pictures.

**Time.** `find` takes 2.4 seconds, `extract` 13 to 17 seconds, and `regress` 17 seconds.

**Gate.** Every piece the gun needs has a place. The rest places of the gun parts differ by
0.000000. The pictures show the gun with its pieces in place. `./port marathon regress`
prints `same` for each stored weapon.

### 3. Examine the data and write the set file

`states.json`, beside the first-person file, gives the clip of each state for the weapon tag.
Copy `marathon/port/sets/m77_omnipositor.toml` to `marathon/port/sets/NAME.toml` and change
it.

1. `hold`, `sighted`, `[clips]`, `[auto]` and `[poses]` come from `states.json`. A state can
   have several clips with thresholds, and the M77's `fire` state has three. A state can also
   have a clip per condition. The M77 has a reload of 104 frames for the value `empty` and
   one of 72 frames for `partial`.
2. In `[gun.parts]`, give each arm reload clip the weapon clip of the same length. A
   difference of one frame is normal (104 and 105 frames). Look at pictures. In every frame
   where the magazine is out, it must be in the left hand.
3. `[sight] point` comes from the named points of the sight piece, the `points` of
   `manifest.json`, or from `./port destiny points`. The M77's sight unit has two points,
   27.2 cm apart at the same height. The chat read them as the aim point and the eye point.
4. `[events]` needs one correction. The reload of an empty gun starts with its bolt to the
   rear, so the tools put `BoltOpen` at frame 0. Put it at the frame where the hand pulls the
   handle.
5. The game removes the gun 0.233 s before the put-away clip ends, so `[hold_end]` adds
   frames to the clip. The M77 clip has 12 frames and adds 3.
6. Keep `knuckles = "align"` and `closed_fingers = true` for a Marathon rig.

**Gate.** Each rule has its measurement as a comment. Points 1 to 4 of step 3 of
[destiny.md](destiny.md) are true for every clip you use.

### 4. Convert and check

```sh
GLB=data/marathon/extract/out/m77_omnipositor/m77_omnipositor_first_person.glb
SET=marathon/port/sets/m77_omnipositor.toml
M=data/mods/M77
./port marathon convert $GLB --set $SET -o $M/behavior/m77/animations/first_person
./port destiny check validate $GLB --set $SET --out data/destiny/port/validation/m77 \
    --clips $M/behavior/m77/animations/first_person --no-video
./port destiny check touch-table $GLB --set $SET --clips $M/behavior/m77/animations/first_person \
    --out data/destiny/port/validation/m77/hand_distance.txt
```

The last command ran for the M77 in this repository on 2026-10-06. In the hold pose, 23.4
percent of the vertices of the left Fallout 4 hand are nearer than 0.5 cm to the gun. The
Marathon hand of the source has 30.0 percent. The right hand has 28.9 percent.

Without `-o`, the clips go to `data/destiny/port/out/m77_omnipositor/`. The work files are in
`data/destiny/port/work/m77_omnipositor/`.

* Read the `[retarget]` lines. `closed` counts the fingers that got the closed-finger rule.
* Run the finger check from [checks.md](checks.md) on each clip before you first look at
  pictures. A turn of more than about 30 degrees in one frame needs a look if the source
  does not have it.
* Then render each hand in the reload from 4 views, for every frame where a hand takes or
  lets go of a part. Use `./port destiny check render` and `look-sheet`.

**Gate.** The values of "The numbers of a correct port" in [checks.md](checks.md). For the
M77 the gun is at most 0.0102 units from the source gun, no finger joint bends back, and the
first joint of a thumb (`Finger11-2` in `summary.txt`) is 3.3 to 4.9 degrees back. The wrist
line of `NAME.txt` is about 1.02 units because `knuckles = "align"` moves each wrist. That is
the rule, not a fault. The `[retarget]` line of the converter has `wrist` 0.00, because it
measures against the moved place.

### 5. The model, the mod, the byte checks

```sh
./port marathon model $GLB --set $SET            # reads parts.json of the work folder: do the convert first
./port mod build M77 --update-lock
./port marathon regress-clips                    # the clips of the M77 against the baseline clips
./port baseline check                            # no stored result (a baseline clip, the release) was replaced
```

`./port marathon regress-clips` is `./port destiny regress --only m77_omnipositor`. For a new
weapon, add it to `destiny/port/regress.toml` and run `./port destiny regress --only NAME`.

The mod project is the same as for a Destiny 2 long gun: a copy of the combat rifle, the
behavior source `weapon M77 like AnimsCombatShotgun`, and
`remove_keywords = ["AnimsCombatRifle"]` in the item file.

`reload_seconds` is the time of the event `reloadEnd`. For the M77 the converter prints
`reloadEnd` at frame 90 of 104, which is 3.0000 s, with `initiateStart` at frame 89. The M77
item file has `reload_seconds = 3.0333`, the time of frame 91, one frame after the event. The
game test passed with that value.

**Gate.** The build has 0 issues and 0 warnings. `./port marathon regress-clips` prints 0
clips that differ. `./port baseline check` has `0 different`.

### 6. The game test

Run it only with the user's permission. [game-test.md](game-test.md) has the rules.

```sh
esx probe status
./port destiny game session M77 LABEL --no-build
./port destiny game record --session ID --weapon M77 --capacity 30 --auto --out DIR
esx probe stop --session ID
```

`--no-build` starts the session with the release that is on record. For a new weapon, leave
it out and the program builds the mod.

**Gate.** 0 failed ops. No finger has a wrong shape in the frames of the reload. In the
sights, the sight is at the center of the picture.

## The M77

The set file is `marathon/port/sets/m77_omnipositor.toml`, with the template `combatrifle`.
The input is `data/marathon/extract/out/m77_omnipositor/m77_omnipositor_first_person.glb`. It
has 91 bones, 68 arm clips and 10 weapon clips.

| Fallout 4 clip | Source |
| --- | --- |
| `WPNIdleReady`, `A` to `D` | The state `idle` (stand), `fp_049_80A5E5CA`, 97 frames |
| `WPNIdleSighted`, `WPNIdleSightedWobble` | `iron_sight_idle`, `fp_012_80A5E5B1`, 97 frames, one pose |
| `WPNFireSingleReady`, `A`, `B` | `fire`, three clips with the thresholds 0.333, 0.667 and 1.0, 15 frames each |
| `WPNFireSingleSighted` | `iron_sight_fire`, `fp_020_80A5E66F`, 14 frames |
| `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack`, `WPNFireAutoSighted` | `[auto]`, the clip of one shot with the length and the events of the vanilla clip (67 frames, 20 shots) |
| `WPNEquip`, `WPNEquipFast` | `ready`, `fp_004_80A5E847`, 22 frames |
| `WPNUnEquip` | `put_away`, `fp_003_80A5E6E8`, 12 frames, and 3 more frames of its last pose |
| `WPNReload` | The reload of an empty gun, `fp_088_80A5E82E`, 104 frames, with the gun parts of `weapon_000_80A5E484` |
| `WPNSprint`, walk (2), run (3), run gun down, jump, idle gun down | `[synth]` and `[static]`, the weapon motion of the vanilla combat rifle on a pose of Marathon |

This port added two keys to the converter.

| Key | What it does | The numbers of the M77 |
| --- | --- | --- |
| `knuckles = "align"` | Each wrist of the Fallout 4 rig moves so that the thumb root and the mean of the four knuckles are at the same distance from those of the source hand. By default each wrist is at the source wrist. | With each wrist at the source wrist, the knuckles are 1.42 units (2 cm) from the source knuckles and the thumb root is 0.64 units away. For Destiny the two values are 0.50 and 0.35. With the rule the wrist moves 1.02 units and both distances are 0.41 units. The mean distance of a fingertip to its place went from 1.06 to 0.64 units. |
| `closed_fingers = true` | A closed finger, such as a hook on a handle or a fist, keeps the bends of its last two bones, with its tip at the source fingertip. By default each joint is on the line of the source finger. | In the reload the left index finger is a hook on the bolt handle in frames 74 to 83. The default rule turned its first bone 170 degrees in one frame. The largest distance of a fingertip to its place in the reload went from 6.20 to 2.15 units. |

Both keys are off by default, and no Destiny set file has them. The closed-finger rule
changes 4 of the 5 Destiny clip sets, by 1.4 units at most, and those are tested in the game.
After the tool changes, each pose file of the five Destiny sets was equal to the file from
before, with a largest difference of 0.0.

Other values of the set file:

* `[sight] point = [0.0, 0.49, 7.62]` is the top of the front post. In the clip the eye is at
  z 11.18, so every clip in the sights moves 3.56 units up.
* `[events] WPNReload = [[76, "SoundPlay.WPNShotgunCombatReloadBoltOpen"]]`. The tools find
  `MagOut` at frame 15, `MagIn` at 58, `reloadComplete` at 60 and `BoltClose` at 82.
* `[hold_end] WPNUnEquip = 3`.
* The item has capacity 30, which is a choice, ammunition `.45`, and
  `reload_seconds = 3.0333`. The event `reloadEnd` of the clip is at 3.0000 s (step 5).

## The state of the M77 port

The port was made on 2026-10-06 in one chat. The chat's last message is a final report, so
no step was left in progress.

Finished:

* The extraction: 4 pieces on the weapon skeleton, 13 textures of 7 materials, the
  first-person rig, 160 files.
* 27 Fallout 4 clips. 18 come from Marathon clips, and 9 have the weapon motion of vanilla
  clips on a pose of Marathon.
* The mod `M77` in `mods/M77/`: 294 records, one model with 12 shapes (17,783 vertices, 54.4
  units long), 7 materials, 21 textures.
* The game test: 40 ops, 0 failed. Two bursts use 16 of 30 rounds. The reload fills the gun
  from 14 to 30 rounds. In the sights the top of the front post is at the center of the
  picture.

Not done:

* The mod has the name and the look of the base item `M77 Assault Rifle`. The table that
  makes the `M77 Omnipositor` different is not decoded.
* The muzzle device, the magazine and the sight unit are gray, because Marathon calculates
  their colors at run time.
* The Marathon hand mesh is not extracted. The solver uses the measurements of the Destiny
  hand mesh in `destiny/port/rig/d2_hands.json`.
* The port has one reload clip, the 104 frames for an empty gun. Marathon also has a shorter
  one, 72 frames, for a gun with rounds.
* In frame 83 of the reload a finger turns 61.8 degrees more than the source.
* Every third-person clip is a vanilla clip of the combat rifle.
* The model lacks the decals of the body, a mesh for the bolt, the light of the rear sight
  and the second magazine in the left hand.
* The validation folder of the M77 has numbers and pictures, but no video of each clip.
* No comparison with Marathon. Not tested at the weapons workbench or in the installed game.

## What is proved

* `./port marathon regress` printed `m77_omnipositor: same (160 files, 37620297 bytes)` on
  2026-10-06, so the extraction of this repository gives the files of the first work.
* `./port marathon regress-clips` gave 27 clips with 0 differences on 2026-10-06, for each of
  the two baseline folders. See [marathon/port/README.md](../../marathon/port/README.md).
* The three release files in `data/mods/M77/build/release/` have the sha256 values of the
  release of the game test, `data/destiny/port/validation/m77/release_tested.sha`. The same
  values are in `baselines.sha256`, and `./port baseline check` compares against them.
* On 2026-10-06 esx at the commit `d3e520c` built the mod `M77` from nothing, from a copy of
  the project with no `build/` folder. The three release files had the bytes on record.
* `data/destiny/port/validation/m77/summary.txt` has the numbers of each clip, and
  `reload_bolt_handle_frames.jpg` shows the left hand on the bolt handle in frames 74 to 84,
  the source above the result.

## What is not proved

* No picture or video of Marathon is the reference. "Correct" comes from the game files and
  from Blender pictures.
* The game test of the M77 was not repeated in this repository. See "The state of the game
  test programs" in [game-test.md](game-test.md).
* The two hand rules are tested on one weapon and one template.
* No second Marathon weapon is ported. `Overrun AR` extracts without a change to the tools.
  `V75 SCAR` has other gun bones, and its first-person file is not correct.
* What the two named points of the sight unit mean is the chat's reading. The game test
  agrees, with the front post at the center of the picture.
* The pairing of an arm clip with a weapon clip comes from the frame counts. The pictures
  agree.
* Which of the two animation systems of an arm entity the game uses for a state. The graph
  that the tools read gives clips that fit.
* No game build after 2026-10-06 is tested.
* The setup of `m2x` ran on one computer, Linux on x86-64.
