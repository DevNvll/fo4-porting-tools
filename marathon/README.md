# Marathon

This area ports a Marathon weapon to Fallout 4. Marathon has a later version of the Destiny 2
engine, and its first-person rig is the Destiny 2 rig, with the same bone names and bone
axes. So this area has its own extraction tool, and it uses the converter of `destiny/port/`.
The ported weapon is the M77, the item `M77 Omnipositor`.

## The two folders

| Folder | What it is | Its document |
| --- | --- | --- |
| `extract/` | `m2x` exports a Marathon weapon as glTF files: the model, the textures, the skeleton, the clips of the weapon, and the first-person rig with the clip of each game state. It reads the game folder and uses the `d2x` modules of `destiny/extract/`. Commands: `marathon setup`, `tag64`, `find`, `extract`, `render`, `regress`, `notes NAME`. | `extract/README.md` |
| `port/` | The set file of each Marathon weapon, for the converter `destiny/port/` (`d2fo4`). It has no program. Commands: `marathon convert`, `marathon model`, `marathon regress-clips`. They are the programs of `destiny convert`, `destiny model` and `destiny regress`. | `port/README.md` |

The results go below `data/`, which is not in git. The extraction is in
`data/marathon/extract/`, the clips and the checks of the port in `data/destiny/port/`, and
the mod project in `data/mods/M77/`. The sources of the mod are in `mods/M77/`.

## What you need

`./port doctor` shows what is there, what is missing, and the command that makes it.

* The game Marathon, the setting `marathon_game`. The tools only read it. Do not start the
  game for this work, because it has an anti-cheat program, BattlEye.
* For `extract/`: Linux on x86-64, a C compiler, cargo, and the environment of `d2x`.
* For the port: Blender, the Data folder of Fallout 4, esx, and the two rig folders that
  `./port fnv make-rig` and `./port destiny make-rig` make.

## From the game to Fallout 4: the order of the commands

The example is the M77. Run every command from the repository root.

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

# 4. The set file: marathon/port/sets/NAME.toml (docs/porting/marathon.md has the procedure;
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
./port baseline check                # no stored result (the extraction, the clips, the release) was replaced
./port destiny check validate $GLB --set $SET --out data/destiny/port/validation/m77 \
    --clips data/mods/M77/behavior/m77/animations/first_person --no-video

# 7. The game test (one session for the computer: look at `esx probe status` first).
#    --no-build: the release that is on record. For a new weapon, leave it out.
./port destiny game session M77 LABEL --no-build
./port destiny game record --session ID --weapon M77 --capacity 30 --auto --out DIR
esx probe stop --session ID
```

A new weapon needs step 4. For a Marathon rig, keep `knuckles = "align"` and
`closed_fingers = true` in the set file. "The state of the M77 port" says why.

## The state of the M77 port

The port was made on 2026-10-06, in one chat. Its last message is a final report, so no step
was in progress. The numbers below are from that work. They come from "The M77 of Marathon"
in `../destiny/port/README.md`, from `../mods/M77/README.md` and from
`data/destiny/port/validation/m77/`.

Finished:

* The extraction. It has 4 pieces on the weapon skeleton, 13 textures, the first-person rig
  with 91 bones, and 68 clips of the arms and 10 clips of the weapon in one file.
* 27 Fallout 4 clips with the template `combatrifle`. 18 come from Marathon clips: idle,
  sights, three shot clips, automatic fire, draw, put-away and reload. The other 9 put the
  weapon motion of vanilla clips on a Marathon pose: walk, run, jump, sprint and gun down.
* Two rules for the Marathon hand, in the set file:
  * `knuckles = "align"`. The Marathon hand bone is at another place in the hand. With the
    two wrists in the same place, the Fallout 4 knuckles are 1.42 units, or 2 cm, from the
    source knuckles. For Destiny that distance is 0.50. The thumb root is 0.64 units away.
    With the rule the wrist moves 1.02 units, and the two distances are 0.41 units.
  * `closed_fingers = true`. In frames 74 to 83 of the reload, the left index finger is a
    hook on the bolt handle. The usual finger rule turned its first bone 170 degrees, so the
    finger pointed to the wrist. The user saw it at frame 78. With the rule, a closed finger
    keeps the bends of its last two bones. The largest distance of a fingertip to its place
    in the reload went from 6.20 to 2.15 units.
* The mod `M77`, in `mods/M77/`. It is a copy of the combat rifle with the automatic
  receiver, and it has 294 records and one model with 12 shapes, 7 materials and 21 textures.
* The game test, with 40 ops and 0 failed. The weapon loads, fires, reloads from 14 to 30
  rounds, goes into the sights, sprints, and is put away and drawn. In the sights the top of
  the front post is at the center of the picture.

Not done:

* The mod has the name and the look of the base item `M77 Assault Rifle`. The table that
  makes the `M77 Omnipositor` different is not decoded.
* The muzzle device, the magazine and the sight unit are gray, because Marathon calculates
  their colors when the game runs.
* The Marathon hand mesh is not extracted. The solver uses the measurements of the Destiny
  hand mesh.
* There is one reload clip, of an empty gun, 104 frames. Marathon has a shorter one for a gun
  with rounds.
* In frame 83 of the reload, a finger turns 61.8 degrees more than the source.
* Every third-person clip is a vanilla clip of the combat rifle.
* Not in the model: the decals of the body, a mesh for the bolt, the light of the rear sight.
* The check folder of the M77 has numbers and pictures, but no video of each clip.
* Nothing was compared with Marathon, and nothing was tested at the weapons workbench or in
  the installed game.

## What is proved

* `./port marathon regress` prints `m77_omnipositor: same (160 files, 37620297 bytes)`, so
  the extraction of this repository gives the files of the first work. I ran it on
  2026-10-06.
* `./port marathon setup`, `find`, `extract`, `render` and each `notes` command ran on
  2026-10-06. See "What is proved" in `extract/README.md`.
* The agent that adapted `destiny/port/` ran `./port marathon regress-clips` on 2026-10-06
  and reports 27 clips with 0 differences. See `port/README.md`.
* The three release files in `data/mods/M77/build/release/` have the sha256 values of the
  release of the game test, which are in
  `data/destiny/port/validation/m77/release_tested.sha`. The same values are in
  `baselines.sha256`, and `./port baseline check` compares with them.
* On 2026-10-06, esx at commit `d3e520c` built the mod from nothing, from a copy of
  `data/mods/M77` without its `build/` folder in a scratch folder. The three release files
  had the bytes on record.

## What is not proved

* The author of this page did not run steps 5 and 7 of the list above: `marathon convert`,
  `marathon model`, `mod build` and the game commands. `port/README.md` says what its author
  ran.
* The game test was not repeated in this repository. Its recording is from the first work.
* No second Marathon weapon is ported. `Overrun AR` extracts with no change to the tools.
  `V75 SCAR` has other gun bones, and its first-person file is not correct. See
  `extract/README.md`.
* The two hand rules are tested on one weapon and one template.

The models, textures and animations are Marathon assets and belong to Bungie. Do not publish
them, and do not publish a mod that has them.
