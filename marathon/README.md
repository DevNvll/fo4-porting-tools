# Marathon

This area ports a weapon of the game Marathon to Fallout 4. Marathon has a later version of
the engine of Destiny 2, and its first-person rig is the rig of Destiny 2 (the same bone
names and bone axes). So this area has an extraction tool of its own, and it uses the
converter of `destiny/port/`. The weapon that is ported is the M77 (the item `M77
Omnipositor`).

## The two folders

| Folder | What it is | Its document |
| --- | --- | --- |
| `extract/` | `m2x`: a weapon of Marathon as glTF files (the model, the textures, the skeleton, the clips of the weapon, the first-person rig with the clip of each game state). It reads the game folder, and it uses the modules of `d2x` (`destiny/extract/`). Commands: `marathon setup`, `tag64`, `find`, `extract`, `render`, `regress`, `notes NAME`. | `extract/README.md` |
| `port/` | The set file of each Marathon weapon, for the converter `destiny/port/` (`d2fo4`). It has no program. Commands: `marathon convert`, `marathon model`, `marathon regress-clips` (the programs of `destiny convert`, `destiny model`, `destiny regress`). | `port/README.md` |

The results are below `data/` (not in git): the extraction in `data/marathon/extract/`, the
clips and the checks of the port in `data/destiny/port/`, the mod project in `data/mods/M77/`.
The sources of the mod are in `mods/M77/`.

## What you need

`./port doctor` shows each thing: there or missing, and the command that makes it.

* The game Marathon (the setting `marathon_game`). The tools only read it. Do not start the
  game for this work: it has an anti-cheat program (BattlEye).
* For `extract/`: Linux on x86-64, a C compiler, cargo, and the environment of `d2x`.
* For the port: Blender, the Data folder of Fallout 4, esx, the two rig folders
  (`./port fnv make-rig`, `./port destiny make-rig`).

## From the game to Fallout 4: the order of the commands

The example is the M77. Each command runs from the root of the repository.

```sh
# 1. The tools
./port destiny setup                 # the environment of d2x
./port marathon setup                # the Oodle 9 shim, the link to the Oodle library, tag64, the table of the 64-bit tag hashes

# 2. The item. An item with "no entity of its own" is a variant: give its base item with --art.
./port marathon find "M77"

# 3. The extraction (15 s). --hands puts the hand mesh of a Destiny 2 file on the rig, for the check pictures.
./port marathon extract "M77 Omnipositor" --art "M77 Assault Rifle" \
    --hands data/destiny/port/extract/khvostov_7g_02/khvostov_7g_02_first_person.glb
./port marathon render data/marathon/extract/out/m77_omnipositor/m77_omnipositor_weapon.glb \
    data/marathon/extract/work/m77.png --views side,quarter

# 4. The set file: marathon/port/sets/NAME.toml (destiny/port/PORTING.md has the procedure;
#    states.json beside the .glb file has the clip of each game state)

# 5. The clips, the model, the mod
GLB=data/marathon/extract/out/m77_omnipositor/m77_omnipositor_first_person.glb
SET=marathon/port/sets/m77_omnipositor.toml
./port marathon convert $GLB --set $SET -o data/mods/M77/behavior/m77/animations/first_person
./port marathon model $GLB --set $SET
./port mod build M77 --update-lock

# 6. The checks
./port marathon regress              # the extraction: the same bytes as the stored result
./port marathon regress-clips        # the clips: the same bytes as the baseline clips
./port destiny check validate $GLB --set $SET --out data/destiny/port/validation/m77 \
    --clips data/mods/M77/behavior/m77/animations/first_person --no-video

# 7. The game test (one session for the computer: look at `esx probe status` first)
./port destiny game session M77 LABEL
./port destiny game record --session ID --weapon M77 --capacity 30 --auto --out DIR
esx probe stop --session ID
```

A new weapon needs step 4. For a rig of Marathon, keep `knuckles = "align"` and
`closed_fingers = true` in the set file (see "The state of the M77 port").

## The state of the M77 port

The port was made on 2026-10-06, in one chat. Its last message is a final report: no step was
in progress. The numbers below are from that work (`../destiny/port/README.md`, "The M77 of
Marathon"; `../mods/M77/README.md`; `data/destiny/port/validation/m77/`).

Finished:

* **The extraction.** 4 pieces on the weapon skeleton, 13 textures, the first-person rig (91
  bones), 68 clips of the arms and 10 clips of the weapon in one file.
* **27 Fallout 4 clips** with the template `combatrifle`: 18 from clips of Marathon (idle,
  sights, three shot clips, automatic fire, draw, put-away, reload) and 9 with the weapon
  motion of vanilla clips on a pose of Marathon (walk, run, jump, sprint, gun down).
* **Two rules for the hand of Marathon**, in the set file:
  * `knuckles = "align"`. The hand bone of Marathon is at another place in the hand. With the
    two wrists at one place, the Fallout 4 knuckles are 1.42 units (2 cm) from the source
    knuckles (Destiny: 0.50), and the thumb root is 0.64 units away. With the rule the wrist
    moves 1.02 units, and the two distances are 0.41 units.
  * `closed_fingers = true`. In the reload the left index finger is a hook on the bolt handle
    (frames 74 to 83). The usual finger rule turned its first bone 170 degrees: the finger
    pointed to the wrist. The user saw it at frame 78. With the rule a closed finger keeps
    the bends of its last two bones. The largest distance of a fingertip to its place in the
    reload went from 6.20 to 2.15 units.
* **The mod** `M77` (`mods/M77/`): a copy of the combat rifle with the automatic receiver,
  294 records, one model with 12 shapes, 7 materials, 21 textures.
* **The game test**: 40 steps, 0 failed. The weapon loads, fires, reloads (14 to 30 rounds),
  goes into the sights (the top of the front post is at the center of the picture), sprints,
  is put away and drawn.

Not done:

* The mod has the name and the look of the base item `M77 Assault Rifle`. The table that
  makes the `M77 Omnipositor` different is not decoded.
* The muzzle device, the magazine and the sight unit are gray: Marathon calculates their
  colors when the game runs.
* The hand mesh of Marathon is not extracted. The solver uses the measurements of the
  Destiny hand mesh.
* One reload clip (an empty gun, 104 frames). Marathon has a shorter one for a gun with rounds.
* In one frame of the reload (frame 83) a finger turns 61.8 degrees more than the source.
* Each third-person clip is a vanilla clip of the combat rifle.
* Not in the model: the decals of the body, a mesh for the bolt, the light of the rear sight.
* The check folder of the M77 has numbers and pictures, and no video of each clip.
* No comparison with Marathon. Not tested at the weapons workbench or in the installed game.

## What is proved

* `./port marathon regress` prints `m77_omnipositor: same (160 files, 37620297 bytes)`: the
  extraction of this repository gives the files of the first work. I ran it on 2026-10-06.
* `./port marathon setup`, `find`, `extract`, `render` and each `notes` command ran on
  2026-10-06 (`extract/README.md`, "What is proved").
* `./port marathon regress-clips`: the agent that adapted `destiny/port/` ran it on
  2026-10-06 and reports 27 clips with 0 differences (`port/README.md`).
* The three release files of `data/mods/M77/build/release/` have the sha256 values of the
  release of the game test (`data/destiny/port/validation/m77/release_tested.sha`).

## What is not proved

* Steps 5 and 7 of the list above (`marathon convert`, `marathon model`, `mod build`, the
  game commands) were not run by the author of this page. `port/README.md` says what its
  author ran.
* The game test was not repeated in this repository. Its recording is from the first work.
* A second weapon of Marathon is not ported. `Overrun AR` extracts with no change of the
  tools; `V75 SCAR` has other gun bones, and its first-person file is not correct
  (`extract/README.md`).
* The two hand rules are tested on one weapon and one template.

The models, the textures and the animations are assets of Marathon (Bungie). Do not publish
them, and do not publish a mod that has them.
