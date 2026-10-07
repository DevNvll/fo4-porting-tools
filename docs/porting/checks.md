# The checks: what each one measures, and what it does not prove

Each check in this repository answers one question. For each check this document gives the
question, the command, how to read the result, and the fault that got past it in the chats.
The numbers come from the ported weapons.

Run every command from the repository root. `./port AREA COMMAND --help` shows the
arguments, and [commands.md](../reference/commands.md) has every command. The examples use
these variables:

```sh
GLB=data/destiny/port/extract/NAME/NAME_first_person.glb     # the first-person file
SET=destiny/port/sets/NAME.toml                              # the set file
W=data/destiny/port/work/NAME                                # the work folder of the converter
O=data/mods/MOD/behavior/WEAPON/animations/first_person      # the clips (or data/destiny/port/out/NAME)
V=data/destiny/port/validation/NAME                          # the results of the checks
```

## The checks in one table

| Check | Command | It proves | It does not prove |
| --- | --- | --- | --- |
| The repository | `./port selftest` | Every Python file compiles, every `port.toml` is correct, the tests of `portkit` pass, and git has no file that is not source. | That a converter gives a correct clip. It reads no game file. |
| The setup | `./port doctor [AREA]` | Every setting has a value and every necessary file exists. | That a file has the correct content. |
| The stored results | `./port baseline check` | Every stored result in `data/` has the sha256 on record in `baselines.sha256`, so nobody replaced one. That covers the baseline clips of the regress commands and the clips and the release of each mod. | That the bytes on record are correct. |
| The regression of New Vegas | `./port fnv regress` | A new conversion of each fixture gives the bytes of `data/fnv/out/`. | That a clip is correct. It does not look at the hands. |
| The regression of the Destiny converter | `./port destiny regress` | A new conversion of each weapon in `destiny/port/regress.toml` gives the bytes of the baseline clips. | That a clip is correct. |
| The regression of the Marathon extraction | `./port marathon regress` | A new extraction of each weapon in `data/marathon/extract/out/` gives the same files. | That a layout is correct for a second weapon or a new build of the game. |
| A glTF file for Blender | `./port destiny check-glb FILE.glb` | One armature, weights for every vertex, finite keys, keys for every bone. | That a clip belongs to the state you think it does. |
| The gun in the hand | `./port destiny check gun-on-grip MANIFEST.json` | The distance from the gun bone to the grip bone, for each full-pose clip of an extraction. | That the hands hold the gun at the correct place. |
| The lines of the converter | `./port destiny convert`, `./port fnv convert` | Each shape is on a bone. The wrists and the gun are at the source. The HKX file has the poses. | That the source pose is correct. |
| The gun | `./port destiny check gun` | Each gun vertex of the HKX clip is at its place in the source. | A rule that changes the source: `[gun]`, `[compose]`, `[hand_pose]`. |
| The finger joints | `./port destiny check fingers` | Each joint between two finger bones is a hinge. No joint bends back. The largest turn in one frame against the source. | That a finger is at the correct place on the gun. |
| The hands in the gun | `./port destiny check contact`, `contact-table` | The percent of hand vertices inside the gun and the depth of each bone, for the source and for the result. | A hand that is off the gun. It has no vertex in the gun. |
| The hands on the gun | `./port destiny check touch`, `touch-table` | The distance from each hand to the gun, for the source hand and for the Fallout 4 hand. | That the pose is the pose of the source game. |
| Pictures | `./port destiny check render`, with `sheet`, `look-sheet`, `frame-sheet`, `hand-sheet`, `video` | What you see: the source beside the result through one camera. | A number. A fault that the source also has. |
| The third-person clip | `./port destiny check third-sheet` | The source above the result as lines. | The hand IK of the game. The fingers. |
| All numbers of a set | `./port destiny check validate` | The gun check, the contact check and the finger check for each clip, and the videos. | See the single checks. |
| The built mod | `./port mod build`, `esx plugin check-weapons`, `esx scene weapon`, `esx render weapon` | The records, the slots, the meshes, the materials and the textures resolve. | The look in the light of the game. A glass. A clip. |
| The game | `./port destiny game ...` ([game-test.md](game-test.md)) | The game loads the weapon, starts its graphs and its clips, fires, and fills the gun. | The look of the hands. The clips that did not play. The sound. |

## The repository and the setup

```sh
./port selftest
./port doctor            # or: ./port doctor fnv | destiny | marathon
```

`./port selftest` prints one line per part. This is a run from 2026-10-06. The counts change
when someone adds a file.

```
ok    python     107 files, 0 do not compile
ok    port.toml  6 files, 74 commands, 28 checks, 0 faults
ok    tests      32 tests, unittest exit code 0
ok    git        259 files that git has or can add, 0 that are not source
```

A part that fails shows `FAIL`, and the lines below it name each fault. The part `git` fails
for a file with a game file ending, such as `.hkx`, `.nif`, `.glb` or `.png`, or with a NUL
byte. Such a file is not source and belongs below `data/`.

`./port doctor` prints `ok` or `MISSING` for each setting and each check of the `port.toml`
files, with the command that makes whatever is missing. When nothing is missing, the last
line is `Result: each setting and each check is ok.` The exit code is 1 if a line is not ok
or Python has no `numpy`. The line `pillow` is a report only. AREA is `fnv`, `destiny`,
`marathon`, or a path such as `destiny/port`.

## The stored results: `./port baseline check`

A regress command compares new results with the stored results in `data/`. It cannot tell
you that something replaced a stored result, and a convert run with `-o` into a baseline
folder, a new extraction or a build can each do that. `baselines.sha256`, which is in git,
has the sha256 of every stored result: the baseline clips of the regress commands, the clips
of each mod and the three release files of each of the 7 mods.

```sh
./port baseline check      # compare the files of data/ with baselines.sha256
./port baseline update     # write baselines.sha256 again
```

The result on 2026-10-06:
`baseline: 602 files in baselines.sha256; 602 the same, 0 different, 0 not there, 0 in data/ that the list does not have.`

* `DIFFERENT` marks a file whose bytes changed. The exit code is then 1.
* A file that is not there, or a file in `data/` that the list does not have, is reported
  with the exit code 0. A new weapon gives such files until the next update.
* Run the check after a regress command passes and after you build a mod.
* Run `./port baseline update` only for a change that the user accepted, and commit the file
  with that change.
* The file patterns are the `[[baseline]]` tables of the `port.toml` files. There are 8, and
  `docs/ARCHITECTURE.md` describes them.

## The regress commands

A regress command makes the results of every ported weapon again in a scratch folder below
`data/`, compares the bytes with the stored results, and exits with 1 if a file is
different. Run the command of an area after every change to a tool of that area.
`fnv/tools/` is the Fallout 4 library of `destiny/port/`, so after a change there, run both
commands.

### `./port fnv regress`

It converts every folder in `data/fnv/fixtures/` again and compares each clip with
`data/fnv/out/NAME/`. It prints one line per fixture:

```
ppk     same       27 clips
famas   DIFFERENT  2 of 26 clips: WPNReload.hkx WPNSprint.hkx
```

The first line is a real result. The PPK has 27 clips and the FAMAS 26. The second line only
shows what a difference looks like, and comes from the help text. `NO RESULT` means that
`data/fnv/out/NAME` has no clip. `FAILED` means that the conversion stopped, and the log is
in `data/fnv/work/_regress/NAME/log.txt`.

### `./port destiny regress` and `./port marathon regress-clips`

It makes the clips of every weapon in `destiny/port/regress.toml` again in
`data/destiny/port/work/_regress/NAME/` and compares each HKX file with the baseline
folders, which are clips of `data/destiny/port/out/` and of `data/mods/`. `--only NAME` does
one weapon. `./port marathon regress-clips` is
`./port destiny regress --only m77_omnipositor`.

The result on 2026-10-06, after the tools moved into this repository: 6 weapons, the five
guns of Destiny 2 and the M77, with 162 first-person clips, 16 third-person clips and 6
clips of the power armor. 0 differ.

To add a weapon, add a table `[[weapon]]` to `destiny/port/regress.toml` with the clip
folders of its mod as the baseline.

### `./port marathon regress`

It extracts every weapon in `data/marathon/extract/out/` again into a scratch folder and
compares the sha256 of each file. The result on 2026-10-06 was
`m77_omnipositor: same (160 files, 37620297 bytes)`, in 17 seconds.

It cannot repeat a result that was made with `--stages` or `--all-detail`, because the
manifest does not record these two options.

### The extraction of Destiny 2

This area has no regress command. Extract into a scratch folder and compare each file with
`cmp`. [destiny/extract/README.md](../../destiny/extract/README.md#checks) has the commands.
In this repository no file was different for The Last Word (154 files), The Chaperone (141),
The Huckleberry (151), the Khvostov (222) and Hammerhead (128).

## The checks of an extraction

```sh
./port destiny check-glb FILE.glb                         # prints NO PROBLEMS, or the list of problems (exit code 1)
./port destiny check gun-on-grip MANIFEST.json            # the gun bone against the grip bone, for each full-pose clip
./port destiny video FILE.glb --clip NAME --out sheet.png # a frame sheet from the first-person camera
./port marathon render FILE.glb OUT.png --views side,quarter
./port destiny pose MANIFEST.json --measure --hold CLIP:0 # the distance of each Destiny hand to the gun
```

* `check-glb` reports an action that has bones with no keys. That fault put the gun 0.9 m
  from the hand in one picture.
* `check gun-on-grip` prints the distance from the gun bone to the grip bone for each
  full-pose clip, then the count of correct clips for each node count. A correct clip has
  0.000 m. A run on 2026-10-06 gave `2 of 59 full-pose clips have the gun on the grip bone`
  for The Huckleberry. With `--clip CLIP` it checks only those clips and exits with 1 if one
  of them is not correct. A set file that uses such a clip needs `[gun] rest = true`.
* A frame sheet proves that a clip is the one you think it is. Look at it. In
  `iron_sight_idle` the sight is in the middle of every frame.
* `pose --measure` counts the vertices of each Destiny hand that are nearer than 0.5 cm and
  nearer than 1.5 cm to the gun. For The Chaperone without a pose clip, the nearest vertex
  of the left hand was 0.89 cm away and 0 of 1903 vertices were nearer than 0.5 cm. With the
  pose clip `80BBD62D`, 33 vertices were nearer than 0.5 cm and 267 nearer than 1.5 cm.
* No program compares an extraction with a picture of the source game.

## The lines of the converter

`./port destiny convert` prints one line for each shape, each clip and each HKX file.

| Line | Value | Expected |
| --- | --- | --- |
| `[parts] SHAPE BONE -> FALLOUT4_BONE verts N tris N min ... max ...` | The Fallout 4 bone of each shape. The line `[parts] hold pose ... bbox ...` has the box of the gun. | Each shape on the bone you expect. The box has the size of the gun. The Chaperone is 48.6 units, 69 cm. |
| `[retarget] CLIP frames N wrist X weapon X shoulder X ... tip max X mean X moved N max move X ... closed N` | `wrist` and `weapon` are the largest distance to the source. `shoulder` is the distance from the shoulder to the source shoulder. `moved` counts the fingers that the collision step moved. `closed` counts the fingers with the rule for a closed finger. | `wrist` and `weapon` 0.00 units. `shoulder` was 1.7 units at most for The Last Word. |
| `[retarget] CLIP the sight goes to the view axis: each bone but the camera moves ...` | The move of `[sight]`. | The ported guns have 0.75 to 3.56 units. |
| `[hkx] NAME frames N  X s  pos err X  rot err X deg  events N` | The HKX file, read again, against the poses. Then one line for each event with its frame and its time. | `pos err` below 0.02 units. Each reload has `reloadComplete` and `reloadEnd` at the frames that the pictures show. |
| `[third] NAME frames N  left hand to gun X  bone length X  shoulder shift X  gun move X turn N  right hand on the grip N frames ...` | The third-person clip. | `left hand to gun` 0.0000 units. For a large `shoulder shift`, use `gun = "source"`. |

`./port fnv convert` prints these lines:

| Line | Value | Expected |
| --- | --- | --- |
| `[port] CLIP <- SOURCE` | The animation that each clip comes from. | Each clip of the mod has its animation. |
| `[port] CLIP events: ...`, `[port] CLIP ends at X s` | The events of each reload, and the time of `reloadEnd`. | The PPK: 21, 87, 89, 108, 109 (3.6333 s). That time is `reload_seconds` of an item file. |
| `[retarget] NAME frames N wrist X length X shoulder X tip max X mean X moved N max move X filtered X missing ...` | `wrist` is the wrist error, `length` the arm length error, and `shoulder` the move of the collarbone for an arm that is out of reach. | `wrist` 0. `length` below 0.0001. `shoulder` 0, except 10 units in the jump clip of the PPK, where the gun is out of the view. |
| `NAME frames N  X s  pos err X  rot err X deg  ann N` | The HKX file, read again. | The PPK: 0.023 to 0.053 units and 0.056 to 0.060 degrees. The FAMAS: 0.026 to 0.086 units and 0.056 degrees. These clips have 40-bit rotations. |

These lines compare the result with the source. In the reload of The Huckleberry the source
had the gun bone at the origin of the world, and every line was still good, because the
numbers compared with the same wrong source.

## The numbers of each clip

```sh
./port destiny check validate $GLB --set $SET --out $V --clips $O --no-video           # the numbers of each clip
./port destiny check validate $GLB --set $SET --out $V --clips $O --left-hand --only WPNReload   # the videos of one clip
```

`--no-video` makes `NAME.txt` for each clip, and `summary.txt`. The videos of one clip take
about 10 minutes, so make the numbers first. `--left-hand` is for a two-handed gun and also
makes `NAME_left_hand.mp4`. `--resume` keeps the files of every clip that already has its
`NAME.txt`.

A line of `summary.txt`, here the reload of the M77:

```
WPNReload  fp_088_80A5E82E  104 frames | gun 0.0085 units | vertices in the gun: source  8.3 %, result  6.1 % | deeper than the source: RArm_Finger11, LArm_Finger12, LArm_Finger23, LArm_Finger32 | joints bent back: LArm_Finger11-2 -4.9, RArm_Finger11-2 -3.3 | largest finger turn in one frame that the source does not have: 61.8 degrees
```

| Field | Meaning | How to read it |
| --- | --- | --- |
| `gun` | The largest distance of a gun vertex from its place in the source, on each frame. | At most about 0.015 units. The largest value of each ported weapon is 0.009 to 0.015, and one clip can have less (0.0030). A larger value is a fault of the parts or of the clip format. 40-bit rotations gave 0.15 units. |
| `vertices in the gun` | The percent of hand vertices inside the gun, source and result, all frames. | The result must not be much above the source. The Khvostov: 8.0 to 9.4 against 8.1 to 9.8. Hammerhead is worse: 9.0 to 11.5 against 7.7 to 9.5. |
| `deeper than the source` | The hand bones that are deeper in the gun than the same bone of the source. | `NAME.txt` has the depth of each bone. Look at these bones in a picture. |
| `joints bent back` | Each joint that bends to the back of the finger, with the angle. | `none` for the Destiny ports. The M77 has the first joint of a thumb at 3.3 to 4.9 degrees. |
| `largest finger turn in one frame that the source does not have` | A jump of a finger. | The largest value of each weapon, from the `summary.txt` of its validation folder: The Last Word 9.8 degrees, Hammerhead 14.1, The Chaperone 19.0, the Khvostov 31.5, The Huckleberry 34.4, the M77 61.8. For a large value, look at the frames. The 61.8 degrees in the reload of the M77 is the frame where the hand lets the bolt handle go, and the source finger turns 92 degrees there. 170 degrees was the dislocated finger of the M77. |

A clip with vanilla weapon motion has the line `vanilla weapon motion: the result only`,
because it has no source to compare with.

`NAME.txt` has the tables. The first part is the gun check, with one line per shape and
then:

```
wrist L: largest distance to the source wrist 1.0248 units
camera: largest distance to the source camera 0.0000 units; the camera moves 2.90 units in the clip
gun: largest distance of a vertex to its place in the source 0.0085 units (104 frames)
```

For a Destiny weapon the wrist value is at most 0.003 units. For the M77 it is 1.02 units,
because `knuckles = "align"` moves each wrist by that length. The second part is the contact
table. For each hand bone it gives the largest depth in the gun, its frame, the count of
frames and the gun part, for the source and for the result. A line that ends with
`<- deeper than the source` is one of the bones in that field of `summary.txt`.

For a clip that `[sight]` moves, the numbers compare the result with the source after the
same move. For a set file with `[gun]`, `[compose]` or `[hand_pose]`, the checks take the
clip after these rules as their source. So for The Huckleberry and The Chaperone the checks
prove the retarget, not the rules.

## The single programs

```sh
./port destiny check gun $GLB CLIP $W/parts.json $O/WPNReload.hkx
./port destiny check fingers $O/WPNReload.hkx --bake $W/bake/CLIP.npz --vanilla data/destiny/port/rig/combatrifle
./port destiny check contact --glb $GLB --bake $W/bake/CLIP.npz --poses $O/WPNReload.hkx \
    --parts $W/parts.json --frames all --quiet --out contact.json
./port destiny check contact-table contact.json
./port destiny check touch --glb $GLB --bake $W/bake/CLIP.npz --poses $O/WPNIdleReady.hkx \
    --parts $W/parts.json --frames 0
./port destiny check touch-table $GLB --set $SET --clips $O --out $V/hand_distance.txt
```

`check fingers` compares with the vanilla clips of one folder. `--vanilla` defaults to the
folder of the revolver, `data/destiny/port/rig/revolver44`. For the templates `combatrifle`
and `combatrifle_parts`, give `data/destiny/port/rig/combatrifle`, because the rig folder
has no folder `combatrifle_parts`. `check validate` picks the correct folder itself.

### The hands on the gun

For each hand, `check touch` prints the distance from the nearest vertex to the surface of
the gun, and the percent of vertices nearer than 0.5 cm and nearer than 1.5 cm. It does this
for the Destiny hand of the source and for the Fallout 4 hand of the result. `touch-table`
runs it for every clip of a set file. These lines are from the `hand_distance.txt` of The
Chaperone:

```
clip          from             frames | left hand, source          | left hand, result          | right hand, source          | right hand, result
WPNIdleReady  fp_002_80BBD611      99 |  1.8 % mean,  1.7 % least  |  5.2 % mean,  5.2 % least  | 35.3 % mean, 35.2 % least   | 31.9 % mean, 31.9 % least
```

| Value | The ported weapons |
| --- | --- |
| Vertices of the left Fallout 4 hand nearer than 0.5 cm to the gun in the hold pose | The Last Word 10.6 percent, the Khvostov 5.6, Hammerhead 5.1, The Chaperone 5.2, The Huckleberry 20.9 |
| A Fallout 4 hand that holds a gun | 5 to 42 percent |
| The Chaperone before its pose clip | 0.0 percent, and the nearest vertex 1.02 cm away |
| The Huckleberry before its pose clip | 12.4 percent, with the wrist 2.5 cm from its place |

Run this check for every new gun. If the source has 0 percent in the hold pose, the gun
needs a pose clip. A value above 0 does not prove where the hand is, as The Huckleberry
showed, so measure each pose clip candidate of the gun too.

`hand_distance.txt` is in the validation folders of The Chaperone and of The Huckleberry.
The values of The Last Word, the Khvostov and Hammerhead, and the range of 5 to 42 percent,
come from runs of `check touch` on the hold pose in the first chat, on 2026-10-06. No file
stores them. The M77 has no table of the hand distance.

### Pictures

```sh
./port destiny check render --glb $GLB --clip CLIP --poses $O/WPNReload.hkx --parts $W/parts.json \
    --out DIR --template TEMPLATE --frames all --views fp,r_thumb,r_back,l_thumb,l_palm,gun_left
./port destiny check sheet DIR CLIP VIEW "0 12 24" OUT.jpg          # the source above the result
./port destiny check look-sheet DIR CLIP FRAME OUT.jpg VIEW,VIEW    # one frame from more views
./port destiny check frame-sheet DIR CLIP OUT.jpg --view fp         # each frame of one view
./port destiny check video DIR CLIP OUT.mp4 VIEW [VIEW2] [RATE]     # the source at the left, the result at the right
./port destiny check strip VIDEO.mp4 OUT.jpg [COUNT] [WIDTH]        # frames of a video at equal steps
./port destiny check video-sheet VIDEO.mp4 OUT.jpg --count 20       # the same, with the time of each frame
./port destiny check hand-sheet --before DIR --after DIR --clip CLIP --out OUT.jpg
./port destiny check third-sheet SOURCE.npz RESULT.npz OUT.png
```

`check render` has these views. `fp` is the first-person camera. `r_thumb`, `r_back`,
`r_front`, `r_under`, `r_palm` and the same with `l_` look at one hand. `gun_left`,
`gun_right`, `gun_top`, `gun_back` and `gun_under` look at the grip from a side of the gun.
The source and the result of a frame have the same camera. The camera bone of the source is
on the camera bone of Fallout 4, so you can compare a game picture with a check picture.
Give `--template` the template of the set file. It defaults to `revolver44`, and the
template gives the place of the source camera. Every check program has a help text under
`--help`.

Look for fingers through the gun, broken or deformed fingers, a wrong wrist rotation and a
thumb that is not aligned. Look at each hand in a close view. In the New Vegas chat, a sheet
at a normal zoom did not show a thumb that was 0.7 units from its place. A close view at 300
percent, the source above the result, showed every fault that the user found.

The work tree of `fnv/` has no picture program. The check programs of the New Vegas chat
made pictures from the game camera and measured the contact count, the joint bends against
the vanilla range, and the jitter. They are in git at the tag `before-animation-only`:
`tools/validate_clip.sh`, `tools/closeup.sh`, `tools/blender/render_fo4.py`,
`render_source.py` and `hand_contact.py`. They have the paths of the old layout, and nobody
adapted them or ran them in this repository.

## The checks of a built mod

```sh
./port mod build NAME --update-lock          # 0 issues and 0 warnings; it prints the sha256 of each release file
./port baseline check                        # the release of a tested mod has the bytes on record
esx --data "/path/to/Fallout 4/Data" plugin check-weapons data/mods/NAME/build/release/NAME.esp
esx --data "/path/to/Fallout 4/Data" scene weapon data/mods/NAME/build/release/NAME.esp WEAPON
esx --data "/path/to/Fallout 4/Data" render weapon data/mods/NAME/build/release/NAME.esp WEAPON --sheet -o data/mods/NAME/docs/WEAPON.png
```

* `check-weapons` must have 0 findings. With `--reference WEAPON=RECORD` it compares the
  mesh with the vanilla mesh.
* `scene weapon` must have 0 findings, or 2 notes for the two effect materials of a sight.
* In `render weapon`, each shape has its texture and no shape is pink. It does not draw a
  glass.
* These checks found the flag `Bolt Action`, the missing nodes of a template, the keyword
  with no rules for power armor, and the missing clip for power armor. The light gray guns
  and the reticle that was too large passed them. The game showed those two.

## The numbers of a correct port

| Value | The ported weapons |
| --- | --- |
| A gun vertex against the source | The Last Word 0.009 units, the Khvostov, The Chaperone and The Huckleberry 0.012, Hammerhead 0.015, the M77 0.0102 |
| A wrist against the source wrist | 0.003 units at most (Destiny 2) |
| Hand vertices inside the gun, result against source | The Last Word 2.2 to 5.7 percent against 3.3 to 10.5. The Khvostov 8.0 to 9.4 against 8.1 to 9.8. Hammerhead 9.0 to 11.5 against 7.7 to 9.5. The M77 6.1 to 10.6 against 8.3 to 24.1. |
| Hand skin vertices inside the gun (New Vegas, from the chat) | The PPK: 1 to 6 percent in the source, 0.3 to 1.7 percent in the result |
| The reticle in the sights, picture of 1280 x 720 | (639.6, 359.4) Hammerhead, (639.1, 359.6) the Khvostov, (639, 359) The Chaperone and The Huckleberry. The center is (640, 360). |
| The built mesh against the parts file | 0.008 units at most |
| The reloads of The Chaperone in the game | `WPNReload6` to `WPNReload1`: 7.23 s to 2.75 s in first person, 6.28 s to 2.45 s in third person, 6 rounds after each one |

## The faults that passed a check

| Fault | The checks that passed with it | What found it |
| --- | --- | --- |
| The fingers in the gun (New Vegas, the first build) | The game test (30 of 30), the wrist error, the arm length error, the HKX file read again, the Blender sheets | The user, in a game picture |
| Fingers that were open and wrong | The contact count (it was better) | The user, in a close view |
| A straight thumb with lumps | The Blender sheets, the contact count, the game tests (32 of 32, 55 of 55) | The user, in a crop of 70 x 89 pixels of a game picture |
| A thumb 0.7 units from its place | The contact count, the game tests, the second run with the same bytes | The user, in one panel of a check sheet |
| The gun at the origin of the world | The lines of the converter, the gun check | A render of the source file |
| The left hand 1 cm from the gun | Each check against the source, the contact count, the game tests (44 and 40 ops, 0 failed) | The user, in a game picture |
| The left hand that the game pulled to the grip in third person | The line picture of the third-person clip | A game picture |
| A third-person reload that ended 12 frames early, with sounds of a different clip | The game test (0 failed ops) | The trace of the events |
| A reticle 5 times too large, and light gray guns | The checks of esx | The game |
| A finger that pointed to the wrist | Pictures from the camera only | The user, in a picture. The finger check then found a turn of 170 degrees. |

## What is not proved

* No check compares a result with a picture of Destiny 2 or of Marathon.
* The regress commands compare bytes on one computer, with Blender 4.5.13 and `numpy` 2.3.
  No test shows that a different version gives the same bytes.
* The documents give 0.008 units for the built mesh against the parts file, but they name no
  command for that measurement.
* The work tree of `fnv/` has no check with pictures, and nobody ran the programs at the tag
  `before-animation-only` here. After a change that moves a finger of a New Vegas clip, a
  person or an agent has to look at pictures of the hands on the gun.
* `./port baseline check` proves that a stored result has the bytes on record, not that
  those bytes are correct. On 2026-10-06, esx at the commit `d3e520c` built each of the 7
  mods from nothing and got the release bytes on record. That is the one comparison of two
  esx versions.
* The value "5 percent" for a hand that holds a gun is the lowest value of five guns, not a
  limit that a test proved.
