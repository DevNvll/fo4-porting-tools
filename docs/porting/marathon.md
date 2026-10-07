# The port of a Marathon weapon to Fallout 4

Marathon has a later version of the engine of Destiny 2. The extraction of a weapon has its
own tools (`m2x`, `marathon/extract/`). The conversion to Fallout 4 uses the converter of
Destiny 2 (`destiny/port/`) with a set file of `marathon/port/sets/`. One weapon is ported:
the M77.

* [marathon/README.md](../../marathon/README.md) has the two folders of the area and the
  state of the M77.
* [marathon/extract/README.md](../../marathon/extract/README.md) has the extraction: the
  layouts, what is proved, what is not done.
* [marathon/port/README.md](../../marathon/port/README.md) has the commands of the port.
* [destiny.md](destiny.md) has the procedure of the converter. Read it first: this document
  gives only what is different.

**Do not start Marathon for this work.** The game has an anti-cheat program (BattlEye). The
tools only read the game folder.

## What is the same as for Destiny 2

* The first-person file of `m2x` has the form of a first-person file of `d2x`: one skin, the
  pieces of the gun on the weapon bones, the camera at `b_utility`, and one animation for
  each clip. `./port destiny convert` reads it with no change.
* The rig of Marathon is the rig of Destiny: the same bone names, the same bone axes (a bone
  points along its local Z and bends about its local Y), the camera bone `b_utility` at the
  same place, and the gun bone on `b_r_grip` in each clip.
* The names are FNV-1 hashes of words. The state names of the graph are the words of
  Destiny 2 (`idle`, `fire`, `iron_sight_idle`, `ready`, `put_away`, `reload_empty`).
* The game aligns the sight when it runs, so the set file needs `[sight]`.
* The set file, the checks, the model program, the mod project, the regression and the game
  test are those of [destiny.md](destiny.md).

## What is different

| Thing | Destiny 2 | Marathon |
| --- | --- | --- |
| The extraction | `./port destiny extract` | `./port marathon extract`. Its own setup: `./port marathon setup`, after `./port destiny setup`. |
| Oodle | Oodle 3, with the shim of `tiger-pkg` | Oodle 9. The setup builds a loader for it (Linux on x86-64 only). |
| Tag names | 32-bit tags | 32-bit tags, and 64-bit hashes for entities, clips and textures. The setup makes a table of them. After an update of the game: `./port marathon tag64`. |
| The layouts | From public tools | Each class number and each offset is from the data of one build of the game. A new build can stop the tools: "no tag of the class ...: the layouts of this file are for another build". |
| A variant item | Not seen | An item can have no entity of its own. Give its base item with `--art`. |
| The weapon | One model with regions | A set of pieces. Each piece is an entity with a model, and a named point of the weapon gives its place. |
| The first-person rig | 75 to 87 bones | 91 bones for the M77 (`fp_rifle_arms`) |
| The hand bones | The reference of the tools | Other lengths: the forearm is 1.2 cm longer, the palm 0.7 cm shorter, some finger bones 10 to 23 percent shorter. The set file needs `knuckles = "align"` and `closed_fingers = true`. |
| The hand mesh | In the file (`body_hands`) | Not extracted. `--hands FILE.glb` puts the hand mesh of a Destiny 2 file on the rig, for the check pictures only. |
| The gun parts in a reload | In the clip of the arms, or in an additive clip | In a clip of the gun entity (`weapon_NNN_TAG` in the same file). The game plays the two at the same time. `[gun.parts]` joins them. |
| The states file | `./port destiny states` writes `states.json` | The extraction writes `states.json` beside the `.glb` file |
| The materials | A texture set and dyes | Three rules: `palette`, `detail`, `constant`. The extraction writes each one as a texture set of Destiny 2. The colors of six of the seven regions of a `detail` material are not in the files. |
| The shaders | Direct3D 11 bytecode: `./port destiny shader-text` | DXIL: `./port marathon notes dxil MATERIAL` (it needs `llvm-dis`) |
| The third-person clips | `./port destiny third` | Not extracted |
| The frame rate | 30 | 30 is the value of Destiny 2. It is not a value from the files of Marathon. |

## The procedure

Each command runs in the root of the repository. The example is the M77.

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

**Gate.** The two doctor commands print `Result: each setting and each check is ok.` The
last line of the setup is of this form:
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

* `find` prints the item hash, the name and the entity. `no entity of its own` says that the
  item is a variant: give its base item with `--art`. Without it, `extract` stops with "has
  no row in the art table. Give --art ITEM".
* `--hands` needs a first-person file of a Destiny 2 extraction.
* Read the last lines of the output of `extract`: the count of pieces with a place, the
  clips with an error, and "the rest places of the gun parts differ by". A value that is not
  0.000000 says that the arm rig does not have the bones of this weapon (`V75 SCAR`: 1.000000).
* Make pictures of the weapon file and of some frames of first-person clips
  (`--action fp_NNN_TAG --frame N`). Look at them.

**Time.** `find` 2.4 seconds. `extract` 13 to 17 seconds. `regress` 17 seconds.

**Gate.** Each piece that the gun needs has a place. The rest places of the gun parts differ
by 0.000000. The pictures show the gun with its pieces at their places. `./port marathon
regress` prints `same` for each stored weapon.

### 3. Examine the data and write the set file

`states.json` beside the first-person file has the clip of each state for the weapon tag.
Copy `marathon/port/sets/m77_omnipositor.toml` to `marathon/port/sets/NAME.toml` and change
it.

1. `hold`, `sighted`, `[clips]`, `[auto]`, `[poses]`: from `states.json`. A state can have
   more than one clip with thresholds (the state `fire` of the M77 has three). A state can
   have a clip for each condition: the M77 has a reload of 104 frames for the value `empty`
   and one of 72 frames for `partial`.
2. `[gun.parts]`: give each reload clip of the arms the clip of the weapon with the same
   length. One frame of difference is normal (104 and 105 frames). Look at pictures: in each
   frame in which the magazine is out, it must be in the left hand.
3. `[sight] point`: from the named points of the sight piece (`points` of `manifest.json`),
   or from `./port destiny points`. The sight unit of the M77 has two points, 27.2 cm apart
   at one height. The chat read them as the aim point and the eye point.
4. `[events]`: the reload of an empty gun has its bolt to the rear from the first frame, so
   the tools put `BoltOpen` at frame 0. Put it at the frame where the hand pulls the handle.
5. `[hold_end]`: the game removes the gun 0.233 s before the end of the put-away clip. The
   clip of the M77 has 12 frames and adds 3.
6. Keep `knuckles = "align"` and `closed_fingers = true` for a rig of Marathon.

**Gate.** Each rule has its measurement as a comment. The points 1 to 4 of step 3 of
[destiny.md](destiny.md) are true for each clip that you use.

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

The last command ran for the M77 in this repository on 2026-10-06. In the hold pose 23.4
percent of the vertices of the left Fallout 4 hand are nearer than 0.5 cm to the gun (the
Marathon hand of the source: 30.0 percent), and the right hand has 28.9 percent.

With no `-o`, the clips go to `data/destiny/port/out/m77_omnipositor/`. The work files are in
`data/destiny/port/work/m77_omnipositor/`.

* Read the lines `[retarget]`: the count `closed` is the count of fingers with the rule for
  a closed finger.
* Run the finger check on each clip before the first look at pictures
  ([checks.md](checks.md)). A turn of more than about 30 degrees in one frame that the
  source does not have needs a look.
* Then make pictures of each hand in the reload, 4 views, for each frame in which a hand
  takes or lets go a part (`./port destiny check render`, `look-sheet`).

**Gate.** The values of [checks.md](checks.md), "The numbers of a correct port". For the M77:
the gun 0.0102 units at most from the source gun, no finger joint bent back, and the first
joint of a thumb (`Finger11-2` in `summary.txt`) 3.3 to 4.9 degrees back. The wrist line of
`NAME.txt` is about 1.02 units, because `knuckles = "align"` moves each wrist: that is the
rule, not a fault. The line `[retarget]` of the converter has `wrist` 0.00 (it measures
against the moved place).

### 5. The model, the mod, the byte checks

```sh
./port marathon model $GLB --set $SET            # reads parts.json of the work folder: do the convert first
./port mod build M77 --update-lock
./port marathon regress-clips                    # the clips of the M77 against the baseline clips
./port baseline check                            # no stored result (a baseline clip, the release) was replaced
```

`./port marathon regress-clips` is `./port destiny regress --only m77_omnipositor`. For a new
weapon, add it to `destiny/port/regress.toml` and run `./port destiny regress --only NAME`.

The mod project is as for a long gun of Destiny 2: a copy of the combat rifle, the behavior
source `weapon M77 like AnimsCombatShotgun`, and `remove_keywords = ["AnimsCombatRifle"]` in
the item file. `reload_seconds` is the time of the event `reloadEnd`. For the M77 the
converter prints `reloadEnd` at frame 90 of 104 (3.0000 s; `initiateStart` is at frame 89).
The item file of the M77 has `reload_seconds = 3.0333`, the time of frame 91: one frame more
than the event. The game test passed with that value.

**Gate.** The build has 0 issues and 0 warnings. `./port marathon regress-clips` prints 0
clips that differ. `./port baseline check` has `0 different`.

### 6. The game test

Only with the permission of the user. [game-test.md](game-test.md) has the rules.

```sh
esx probe status
./port destiny game session M77 LABEL --no-build
./port destiny game record --session ID --weapon M77 --capacity 30 --auto --out DIR
esx probe stop --session ID
```

`--no-build` starts the session with the release that is on record. For a new weapon, leave it
out: the program then builds the mod.

**Gate.** 0 failed ops. In the frames of the reload no finger has a wrong shape. In the
sights the sight is at the center of the picture.

## The M77

The set file is `marathon/port/sets/m77_omnipositor.toml`, with the template `combatrifle`.
The input is `data/marathon/extract/out/m77_omnipositor/m77_omnipositor_first_person.glb`: 91
bones, 68 clips of the arms and 10 clips of the weapon.

| Fallout 4 clip | Source |
| --- | --- |
| `WPNIdleReady`, `A` to `D` | The state `idle` (stand), `fp_049_80A5E5CA`, 97 frames |
| `WPNIdleSighted`, `WPNIdleSightedWobble` | `iron_sight_idle`, `fp_012_80A5E5B1`, 97 frames, one pose |
| `WPNFireSingleReady`, `A`, `B` | `fire`: three clips with the thresholds 0.333, 0.667 and 1.0, 15 frames each |
| `WPNFireSingleSighted` | `iron_sight_fire`, `fp_020_80A5E66F`, 14 frames |
| `WPNFireAutoReadyForward`, `WPNFireAutoReadyBack`, `WPNFireAutoSighted` | `[auto]`: the clip of one shot, with the length and the events of the vanilla clip (67 frames, 20 shots) |
| `WPNEquip`, `WPNEquipFast` | `ready`, `fp_004_80A5E847`, 22 frames |
| `WPNUnEquip` | `put_away`, `fp_003_80A5E6E8`, 12 frames, and 3 more frames of its last pose |
| `WPNReload` | The reload of an empty gun, `fp_088_80A5E82E`, 104 frames, with the gun parts of `weapon_000_80A5E484` |
| `WPNSprint`, walk (2), run (3), run gun down, jump, idle gun down | `[synth]` and `[static]`: the weapon motion of the vanilla combat rifle on a pose of Marathon |

The two keys that this port added to the converter:

| Key | What it does | The numbers of the M77 |
| --- | --- | --- |
| `knuckles = "align"` | Each wrist of the Fallout 4 rig moves so that the thumb root and the mean of the four knuckles are at the same distance from those of the source hand. Default: each wrist is at the source wrist. | With the wrists at one place the knuckles are 1.42 units (2 cm) from the source knuckles (Destiny: 0.50), and the thumb root is 0.64 units away (Destiny: 0.35). With the rule the wrist moves 1.02 units, and the two distances are 0.41 units. The mean distance of a fingertip to its place went from 1.06 to 0.64 units. |
| `closed_fingers = true` | A closed finger (a hook on a handle, a fist) keeps the bends of its last two bones, with its tip at the source fingertip. Default: each joint is on the line of the source finger. | In the reload the left index finger is a hook on the bolt handle (frames 74 to 83). The default rule turned its first bone 170 degrees in one frame. The largest distance of a fingertip to its place in the reload went from 6.20 to 2.15 units. |

The two keys are off by default, and no set file of Destiny has them. The rule for a closed
finger changes 4 of the 5 clip sets of Destiny (1.4 units at most), and those are tested in
the game. After the changes of the tools each pose file of the five Destiny sets was equal
to the file before the changes (largest difference 0.0).

Other values of the set file:

* `[sight] point = [0.0, 0.49, 7.62]`, the top of the front post. In the clip the eye is at
  z 11.18, so each clip in the sights moves 3.56 units up.
* `[events] WPNReload = [[76, "SoundPlay.WPNShotgunCombatReloadBoltOpen"]]`. The tools find
  `MagOut` (frame 15), `MagIn` (58), `reloadComplete` (60) and `BoltClose` (82).
* `[hold_end] WPNUnEquip = 3`.
* The item: capacity 30 (a choice), ammunition `.45`, `reload_seconds = 3.0333` (the event
  `reloadEnd` of the clip is at 3.0000 s: see step 5).

## The state of the M77 port

The port was made on 2026-10-06, in one chat. Its last message is a final report: no step
was in progress.

Finished:

* The extraction: 4 pieces on the weapon skeleton, 13 textures of 7 materials, the
  first-person rig, 160 files.
* 27 Fallout 4 clips: 18 from clips of Marathon and 9 with the weapon motion of vanilla clips
  on a pose of Marathon.
* The mod `M77` (`mods/M77/`): 294 records, one model with 12 shapes (17,783 vertices, 54.4
  units long), 7 materials, 21 textures.
* The game test: 40 ops, 0 failed. Two bursts use 16 of 30 rounds. The reload fills the gun
  (14 to 30 rounds). In the sights the top of the front post is at the center of the
  picture.

Not done:

* The mod has the name and the look of the base item `M77 Assault Rifle`. The table that
  makes the `M77 Omnipositor` different is not decoded.
* The muzzle device, the magazine and the sight unit are gray: Marathon calculates their
  colors when the game runs.
* The hand mesh of Marathon is not extracted. The solver uses the measurements of the
  Destiny hand mesh (`destiny/port/rig/d2_hands.json`).
* One reload clip (an empty gun, 104 frames). Marathon has a shorter one for a gun with
  rounds (72 frames).
* In one frame of the reload (frame 83) a finger turns 61.8 degrees more than the source.
* Each third-person clip is a vanilla clip of the combat rifle.
* Not in the model: the decals of the body, a mesh for the bolt, the light of the rear
  sight, the second magazine in the left hand.
* The validation folder of the M77 has numbers and pictures, and no video of each clip.
* No comparison with Marathon. Not tested at the weapons workbench or in the installed game.

## What is proved

* `./port marathon regress` printed `m77_omnipositor: same (160 files, 37620297 bytes)` on
  2026-10-06: the extraction of this repository gives the files of the first work.
* `./port marathon regress-clips` gave 27 clips with 0 differences on 2026-10-06, for each of
  the two baseline folders ([marathon/port/README.md](../../marathon/port/README.md)).
* The three release files of `data/mods/M77/build/release/` have the sha256 values of the
  release of the game test (`data/destiny/port/validation/m77/release_tested.sha`). The same
  values are in `baselines.sha256`, and `./port baseline check` compares with them.
* On 2026-10-06 esx at the commit `d3e520c` built the mod `M77` from nothing (a copy of the
  project with no `build/` folder): the three release files had the bytes on record.
* `data/destiny/port/validation/m77/summary.txt` has the numbers of each clip, and
  `reload_bolt_handle_frames.jpg` shows the left hand on the bolt handle in the frames 74 to
  84, the source above the result.

## What is not proved

* No picture or video of Marathon is the reference. "Correct" is from the files of the game
  and from pictures of Blender.
* The game test of the M77 was not repeated in this repository
  ([game-test.md](game-test.md), "The state of the game test programs").
* The two hand rules are tested on one weapon and one template.
* A second weapon of Marathon is not ported. `Overrun AR` extracts with no change of the
  tools. `V75 SCAR` has other gun bones, and its first-person file is not correct.
* The meaning of the two named points of the sight unit is a reading of the chat. The game
  test agrees: the front post is at the center of the picture.
* The pair of a clip of the arms and a clip of the weapon is from the frame counts. The
  pictures agree.
* Which of the two animation systems of an arm entity the game uses for a state. The graph
  that the tools read gives clips that fit.
* A build of the game after 2026-10-06 is not tested.
* The setup of `m2x` ran on one computer (Linux, x86-64).
