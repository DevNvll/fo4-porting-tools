# The port of a New Vegas weapon to Fallout 4

The tools in `fnv/` convert the first-person animations of a Fallout: New Vegas weapon mod to
Fallout 4 clips, with one command. They make only the clips, not the model, the textures, the
sounds, the weapon record or the behavior graph.

* [fnv/README.md](../../fnv/README.md) is the reference: the options, the animation names,
  the keys of a conversion file, the steps, what the conversion does, the limits.
* [overview.md](overview.md) has the rules for each source, and
  [troubleshooting.md](troubleshooting.md) has the signs.

## The weapons

| Weapon | Source mod | Input | Template | Clips | Mod project |
| --- | --- | --- | --- | --- | --- |
| Walther PPK | "FNV Anim Set - Walther PPK" | 9 `.kf` clips | `pistol10mm` | 27 | `mods/PPK` |
| FAMAS F1 | "FAMAS F1" | One `.kf` reload | `smg` | 26 | `mods/FAMAS` |

The first weapon of the chat was an HK MP7, and its source was 47 scenes of 3ds Max. The
tools read them at the time. Today they do not, and the input is `.kf` and `.nif` only.

## The procedure

Run every command from the repository root.

### 1. Check the input

1. Extract the mod archive into a new empty folder below `data/`, for example
   `data/fnv/work/_source/NAME`. The tools do not read an archive. Do not extract it into
   `data/fnv/fixtures/`, because every folder there is a fixture of the regression (step 5).
2. Look for first-person `.kf` files and a `.nif` model. The `.kf` files are in
   `meshes/characters/_male/`, in `meshes/characters/_1stperson/`, or in
   `meshes/AnimGroupOverride/NAME/_1stPerson/`.
3. `./port fnv inspect FILE` prints the nodes and shapes of a model, or the tracks and text
   keys of an animation.
4. Read the mod's readme for its permissions and state them in the report. The FAMAS readme
   forbids redistribution without permission.

**Gate.** The folder has a model and at least one first-person animation. If it has no
animation file, stop and tell the user. One archive of the chat had 4 models, textures, one
sound and the plugin, and it used the vanilla revolver animations of New Vegas. The user
wrote: "if theres no animation, don'tport it I'll find another".

### 2. Make the rig folder (one time)

```sh
./port fnv make-rig --nvcs /path/to/NVCS/Meshes/Characters/_1stPerson/Skeleton.nif
./port doctor fnv
```

The rig folder `data/fnv/rig` holds the Fallout 4 first-person skeleton `1st_skeleton.hkx`,
the vanilla clips of each template, and the New Vegas first-person skeleton `nvcs_1st.json`.
The program reads `Fallout4 - Animations.ba2` from the setting `fo4_data`. The skeleton file
comes from the New Vegas compatibility skeleton mod, NVCS. In the chat it came from the
archive "NVCS Vanilla Weights".

**Gate.** `./port doctor fnv` prints `Result: each setting and each check is ok.`

### 3. Convert

```sh
./port fnv convert /path/to/extracted-mod
```

You need no conversion file. The tool selects these values:

| Value | How |
| --- | --- |
| The model | The `.nif` of the source with the fewest shapes, then the shortest name |
| The animations | The folder `_1stperson` of the source with the most `.kf` files |
| The template | `pistol10mm` when the animations have the grip code `1hp`, else `smg` |
| The name | The name of the model file |
| The gun parts | Each node `##NAME` of the model that has a shape, by a word in its name (bar, bolt, slide, lever, clip, mag, shell, bullet, trigger, hammer) |
| The events of a reload | From the motion of the magazine, the bolt and the left hand |

Read what the command prints. It shows the animation each clip comes from as
`[port] CLIP <- SOURCE`, and the events and the end time of each reload.

```sh
./port fnv convert CONFIG show      # each value that the tools assume
./port fnv convert CONFIG plan      # the source of each clip and the events of each reload
```

When a clip, a part or the trigger is wrong, write a small conversion file with only the
wrong values. [fnv/README.md](../../fnv/README.md#the-conversion-file) lists the keys. The
PPK conversion file went from 165 lines to 2 keys.

The command runs the steps `bake`, `parts`, `retarget`, `synth`, `hkx` and `install`. The
`hkx` step writes the clips into `out/fo4/hkx` of the work folder. Only `install` copies them
to the output folder.

**Time.** 27 seconds for the PPK, 6 of them in the `retarget` step.

**Gate.** Each clip in the list has the animation you expect. Each reload has
`reloadComplete` and `reloadEnd`. In the `[retarget]` lines, `wrist` is 0 and `length` is
below 0.0001. Each line of the `hkx` step has a small `pos err`, 0.023 to 0.086 units for the
two weapons.

### 4. Check the hands

The work tree of `fnv/` has no program that shows the result. That is the area's largest gap.
In the chat the user found every hand fault in a picture, and none of the agent's numbers
found one. The user's first correction was: "validate the retarget with blender before
testing ingame."

The chat's check programs are in git at the tag `before-animation-only`:
`tools/validate_clip.sh`, `tools/closeup.sh`, `tools/fpcmp.sh`,
`tools/blender/render_fo4.py`, `tools/blender/render_source.py` and
`tools/blender/hand_contact.py`. `git ls-tree -r --name-only before-animation-only` lists
them, and `git show before-animation-only:tools/validate_clip.sh` prints one. They still have
the paths and the configuration of the old layout. Nobody has adapted them to this repository
or run them in it.

With those programs the chat made these checks before each game test:

1. Pictures in Blender from the game camera, the bone `Camera` with a horizontal view angle
   of about 87 degrees at 16:9. The source hands and gun are above and the Fallout 4 result
   below, at the same frames.
2. Close views of each hand, and a look at every visible finger at 300 percent zoom. Compare
   the place of each thumb with the source panel.
3. The count of hand skin vertices inside the gun parts, with the largest depth, for the
   source and for the result. The result must not be deeper than the source.
4. The joint bends against the range of the vanilla clips. No finger joint bends back, and
   the last thumb joint bends at most 17 degrees back.
5. The largest turn of a finger from one frame to the next, the old poses against the new
   poses.

In this repository you can take the check programs from the tag and adapt them, or look at
the clips in an animation tool. The check programs in `destiny/port/` read a Destiny 2
first-person file, not a New Vegas source.

**Gate.** You looked at each hand in every clip that has hand motion from the source, and you
found none of the four defects in [overview.md](overview.md). Without pictures this gate is
not true. Do not start a game test until the user accepts that, and say so in the report.

### 5. The byte checks

```sh
./port fnv regress                  # each fixture of data/fnv/fixtures against data/fnv/out
./port destiny regress              # after a change of fnv/tools: destiny/port uses these modules
./port baseline check               # no stored clip and no release was replaced
```

For a weapon with no fixture, convert twice into two work folders with `--work` and `-o`, and
compare each `.hkx` file. Make sure the `parts` step ran, because the collision step does not
run without the parts file.

To add a weapon to the regression, copy the extracted mod to `data/fnv/fixtures/NAME`, run
`./port fnv convert data/fnv/fixtures/NAME --name NAME`, and check the clips. From then on
the regression compares against them. `./port baseline check` reports the new clips as files
that the list does not have. When the user accepts them, run `./port baseline update`.

**Gate.** `./port fnv regress` prints `same` for each fixture. `./port baseline check` has
`0 different`.

### 6. The mod project

The clips fit only the gun of the source mod. A Fallout 4 mod with that gun needs a model,
and today's tools do not make one. `out/fo4mesh/parts.json` in the work folder has each shape
of the gun in the space of its weapon bone, and a Fallout 4 model of the gun must have its
shapes at these places.

The mods `PPK` and `FAMAS` are the examples. Their models, attachments and textures came from
the tools at the git tag `before-animation-only`, which had steps for them. Today's tools
make their clips.

| Where | Content |
| --- | --- |
| `mods/NAME/` (in git) | `esx.toml`, `items/10-NAME.toml`, `behavior/NAME/NAME.bhv`, `conversion.toml`, `tests/*.toml`, the lock files, `README.md` |
| `data/mods/NAME/` (not in git) | A copy of those files, `source/` (the extracted mod), `meshes/`, `assets/`, the clips of `behavior/NAME/animations/first_person/`, `docs/`, `build/` |

```sh
./port mod sync PPK                                   # copy the files of mods/PPK into data/mods/PPK
./port fnv convert data/mods/PPK/conversion.toml      # the 27 clips, into the project
./port mod build PPK                                  # esx build; the release is data/mods/PPK/build/release
```

`conversion.toml` has the name, the template and the output folder. A path in it is relative
to the folder of the file, so the source is `data/mods/PPK/source` and the clips go to
`data/mods/PPK/behavior/ppk/animations/first_person`.

Points of the project:

* The weapon is a copy of a vanilla weapon, `from = "10mm"` or `from = "SubmachineGun"`. The
  template gives the graph, the sounds and the third-person clips.
* The behavior source is `weapon PPK like AnimsFP10mm`, and `like AnimsSubmachineGun` for the
  FAMAS. The game plays `WPNReloadEmpty` only with the line `when empty play WPNReloadEmpty`
  in a `reload` block.
* `reload_seconds` in the item file is the time of `reloadEnd` that the convert command
  prints: 3.6333 s for the PPK, 2.8667 s for the FAMAS.
* The vanilla Deliverer is a PPK, but it does not draw in the test game of `esx probe`, even
  with no mod. So the template of the PPK is the 10mm pistol.

**Gate.** The build has 0 warnings and 0 release issues.

### 7. The game test

Run it only with the user's permission. Both mods have test plans in `mods/NAME/tests/`.
"The game test of a New Vegas mod" in [game-test.md](game-test.md) has the commands and the
rules for a plan. Look at every picture of a test. A pass count is not a look.

On 2026-10-05 the PPK passed 34 of 34 steps and 27 of 27, and the FAMAS 32 of 32 and 55 of
55.

**Gate.** Every step of every plan passed. You looked at every picture of every report. The
release files have the sha256 values of `baselines.sha256`. Check that with
`./port baseline check`.

## The rules of the conversion, with their numbers

[fnv/README.md](../../fnv/README.md#what-the-conversion-does) says what the conversion does.
This table gives the measurement behind each rule.

| Rule | Value | Reason |
| --- | --- | --- |
| The place of the gun | The trigger of the gun is at the trigger of the template, with x = 0 | The hands of the vanilla clips then hold the grip. Those are the third-person clips and the clips that the mod does not replace. |
| The wrist | At the source wrist. No shift. | With the wrists at the same place, the palms of the two hands agree to 0.5 units. A shift of 0.6 units put the magazine through the palm. |
| The arm | A two-bone solve for the Fallout 4 lengths, with the elbow direction of the source | The bone lengths are different. |
| The fingers | Each joint on the line of the source finger | The Fallout 4 index finger is 6.96 units long, the New Vegas one 8.02. A copy of the rotations put 1563 of 6209 hand vertices in the gun at the idle. |
| The collision floor | The center line of a finger bone is at least 0.65 of its radius from a gun surface | With these values the hand vertices in the gun went to about a third, less than in the source animation. |
| The largest move | 1.15 units for each joint | A cap, so that a finger does not open. |
| The time filter | Gaussian, 1.5 frames, on the moves of the collision step | The collision step works on one frame. |
| `min_bend` | 0.3. Each joint has at least 0.3 of its rest bend, about the hinge of its bone. | The Fallout 4 hand mesh has bent fingers at rest (42 to 52 and 28 to 50 degrees). A straight finger has lumps. |
| The thumb | The last thumb joint can bend 17 degrees back | The vanilla 10mm clips hold the left thumb at that value. No other finger joint bends back in 53 vanilla clips. |
| `skin_center` | The center of the skin of the Fallout 4 finger goes to the center of the skin of the source finger | The Fallout 4 thumb skin is 0.4 units to the pad side of its bones, the New Vegas thumb skin 0.13 units to the nail side. |
| The four `WeaponIKTarget` bones | They keep the reference transform | Every vanilla clip has them so. |
| Additive clips | The tools do not write `WPNIdleSightedWobble` or a clip whose name ends with `Add` | They are additive clips in the vanilla graph of the submachine gun. |
| The idle variants | `WPNIdleReadyA` to `D` are the plain idle | The graph plays them at random, one directly after the draw. |
| The sighted pose | The aim pose, moved until the node `##SightingNode` is on the view axis | New Vegas moves the camera to that node. Fallout 4 has the sights in the clip. |
| Automatic fire | 67 frames, 20 shots at the frames of the vanilla clip, each shot the first frames of a single-shot clip | The mods have one clip for one shot. |
| The reload events | Magazine out is the first frame where the magazine is more than 0.3 units from its last place. Magazine in is the last such frame. `reloadComplete` is 2 frames later. `reloadEnd` is when the left hand is within 6 units of its last place and stays there, and `initiateStart` is the frame before it. | From the motion of the parts. The PPK: 21, 87, 89, 108, 109. |

The source hands are partly inside the gun, 4 to 16 percent of the skin in the MP7 reload.
The result has less. Zero is not the target.

## A new template weapon

The two templates fit a magazine gun on the graph of the submachine gun or of the 10mm
pistol. Any other weapon, such as a revolver, a bolt action or a shotgun with single shells,
needs a new template file, the clips of that vanilla weapon in the rig folder, and different
events. These steps come from the work on the pistol template:

1. Find the first-person clip folder of the vanilla weapon in `Fallout4 - Animations.ba2`
   with `./port fnv list-archive ARCHIVE PATTERN`.
2. Test that the vanilla weapon draws in the test game before you build on it.
3. Read the rest place and the rest rotation of each weapon bone from a vanilla clip where
   every part is at rest (the walk clip).
4. Write `fnv/templates/NAME.toml`.
5. Make the rig folder again. Convert. Check the hands. Add a fixture.

No template was added after the pistol, so these steps are not proved.

## What is proved

* The two fixtures give 27 clips for the PPK and 26 for the FAMAS, and a new run gives the
  same bytes as the results in `data/fnv/out/`. `./port fnv regress` checks this.
* The clips in `data/fnv/out/ppk` and `data/fnv/out/famas` have the same bytes as the clips
  of `data/mods/PPK` and `data/mods/FAMAS`, compared with `cmp` on 2026-10-06.
* On 2026-10-06 `./port mod sync PPK`, `./port fnv convert data/mods/PPK/conversion.toml` and
  `./port mod build PPK` ran in this repository, and the 27 clips have the same bytes as
  before. The release files of the two mods have the sha256 values they had before the move
  into this repository, which are in `data/mods/NAME/release_before_import.sha`.
  `baselines.sha256` has these values now.
* On 2026-10-06 esx at the commit `d3e520c` built `PPK` and `FAMAS` from nothing, from a copy
  of each project with no `build/` folder. Every release file had the bytes on record.
* A rig folder that `./port fnv make-rig` makes from the game files gives the same clips. See
  [fnv/README.md](../../fnv/README.md#what-is-proved).

## What is not proved

* No command of this repository proves that the clips are correct in the game. The game
  tests of the two weapons ran on 2026-10-05, on clips with the same bytes as today's. No
  game test ran on 2026-10-06.
* The regression compares bytes. It does not look at the hands. The check programs at the tag
  `before-animation-only` were not run in this repository.
* A weapon class that is not a magazine gun.
* The finger values on other grips. The first four values were tuned with pictures of the
  MP7.
* The defaults on a mod by a different author. They are rules for the names and the motion
  of the mods of these weapons.
* A source with B-spline keys, a skinned gun, or a NIF version other than 20.2.0.7.
* The effect of the 40-bit rotations of these clips. The Destiny work found a noise of 0.03
  to 0.09 units at the muzzle in an idle clip with 40 bits, and its clips have 48 bits. No
  test looked at a New Vegas clip for this.
* The clip `WPNIdleSightedWobble`. The tools of `fnv/` do not write it, and the Destiny sets
  do. See "Two areas, two answers" in [lessons.md](lessons.md).
* Power armor, held automatic fire, the sound, the weapons workbench.

## Limits of a result

* The two thumbs cannot agree at every place, because the thumb of the Fallout 4 hand starts
  1.6 units from the start of the New Vegas thumb. The tools put the fingertip at its place
  first.
* Third person, melee and throw clips are the vanilla clips of the template. The gun can be
  smaller than the template gun.
* The sounds are those of the template. The tools do not use the mod's sound files.
* A source clip with no place in the vanilla graph gets no clip: a jam, the poses of the
  empty gun, a last shot, draw variants.
* The FAMAS has hand motion from the source only in the reload.
