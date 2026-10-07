# The port of a Marathon weapon to Fallout 4

This folder has the set file of each Marathon weapon that is ported to Fallout 4. It has no
converter of its own. A first-person file from `m2x` (`marathon/extract/`) has the form of
one from `d2x`, because the Marathon rig has the bone names and the bone axes of the
Destiny 2 rig. So the converter is `destiny/port/` (`d2fo4`), with a set file from this
folder.

| File | Content |
| --- | --- |
| `sets/m77_omnipositor.toml` | The clip set of the M77, an assault rifle, and the data of its model. Each rule has a comment with the measurement that gave it. |
| `port.toml` | The commands `marathon convert`, `marathon model` and `marathon regress-clips`. |

`destiny/port/README.md` has every key of a set file, every step and every check. Its
section "The M77 of Marathon" has the clip table, the two rules for the Marathon hand and
what is proved. `docs/porting/marathon.md` and `docs/porting/destiny.md` have the procedure
for a new weapon. `marathon/README.md` has the extraction, and `mods/M77/README.md` has the
mod.

## What you need

* The extraction of the weapon, from `./port marathon extract`. That is
  `data/marathon/extract/out/m77_omnipositor/` with `m77_omnipositor_first_person.glb` and
  the folder `textures`.
* Everything that `destiny/port/` needs: Blender, the two rig folders, and esx for the model.
  `./port doctor` shows each one.

## The commands

```sh
GLB=data/marathon/extract/out/m77_omnipositor/m77_omnipositor_first_person.glb
SET=marathon/port/sets/m77_omnipositor.toml
M=data/mods/M77

# the 27 first-person clips, into the mod project
./port marathon convert $GLB --set $SET -o $M/behavior/m77/animations/first_person
# the model, the 7 materials and the 21 textures, into the mod project (the default of --mod is M77)
./port marathon model $GLB --set $SET
# the mod: sync of mods/M77, esx build, the release in data/mods/M77/build/release
./port mod build M77 --update-lock
```

`./port marathon convert` and `./port marathon model` are the programs of
`./port destiny convert` and `./port destiny model`. Without `-o`, the clips go to
`data/destiny/port/out/m77_omnipositor/`. The work files are `parts.json`, the bake and the
poses, in `data/destiny/port/work/m77_omnipositor/`. `marathon model` reads `parts.json`
from there, so run the convert first.

A file or a folder that a set file names is beside the `.glb` file. The set file of the M77
names none. The model program reads the folder `textures` beside the `.glb` file.

## The checks

```sh
# the regression: the 27 clips have the bytes of data/destiny/port/out/m77_omnipositor and of the mod project
./port marathon regress-clips
# the numbers of each clip (the gun against the source gun, the hands in the gun, the finger joints)
./port destiny check validate $GLB --set $SET --out data/destiny/port/validation/m77 \
    --clips $M/behavior/m77/animations/first_person --no-video
# how near each hand is to the gun, in each clip (the table of the M77 is in its validation
# folder: 23.4 percent for the left hand in the hold pose)
./port destiny check touch-table $GLB --set $SET --clips $M/behavior/m77/animations/first_person \
    --out data/destiny/port/validation/m77/hand_distance.txt
# no stored result (a baseline clip, the release) was replaced
./port baseline check
```

`./port marathon regress-clips` is `./port destiny regress --only m77_omnipositor`, and
`destiny/port/regress.toml` has the weapon. The result of 2026-10-06 was 27 clips, 0 differ,
for each of the two baseline folders. On the same day the model program, with `--project`
and a scratch project, made the 30 files of `meshes/` and `assets/` of `data/mods/M77` again
with the same bytes.

The game test uses a headless test copy of the game. The probe has one session at a time for
the whole computer, so look at `esx probe status` before you start one.

```sh
./port destiny game session M77 LABEL --no-build    # starts a session with the release on record, prints its ID
./port destiny game record --session ID --weapon M77 --capacity 30 --auto --out DIR
esx probe stop --session ID                    # only the ID that the start command printed
```

## What is not proved

* The game test commands of this page were not run in the new folder layout. The earlier
  game test of the M77 is in `data/destiny/port/validation/m77/`, and `mods/M77/README.md`
  has its result.
* The port of these tools to the new folder layout did not run `./port mod build M77`. One
  build was compared. On 2026-10-06, esx at commit `d3e520c` built a copy of `data/mods/M77`
  without its `build/` folder in a scratch folder, and the three release files had the bytes
  of `baselines.sha256`.
* The M77 port has limits, among them the colors of three pieces, the hand measurements, the
  one reload clip and the third-person clips of the vanilla combat rifle. "What is not
  correct or not done" in `mods/M77/README.md` has the list.
